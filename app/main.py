from contextlib import asynccontextmanager
from app.db import get_session, Base, engine
from app.utils.hashing import get_shard_for_key
from app.models import URL
from fastapi import FastAPI, HTTPException, status, Request, Response, BackgroundTasks, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.future import select
import random
import string
import uvicorn
from pydantic import BaseModel
from prometheus_client import generate_latest, Counter, Histogram, CONTENT_TYPE_LATEST
from app.services.cache import get_url, set_url, set_null_url
from app.services.producer import start_kafka_producer, stop_kafka_producer, send_click_event, send_new_url_event


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created")
    await start_kafka_producer()
    print("Kafka producer started")
    yield
    # Shutdown
    await stop_kafka_producer()
    print("Kafka producer stopped")


app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="app/templates")

# Prometheus Metrics
requests_total = Counter(
    "http_requests_total", "Total HTTP Requests", ["method", "endpoint", "status_code"]
)
request_duration_seconds = Histogram(
    "http_request_duration_seconds", "HTTP Request Duration", ["method", "endpoint"]
)
cache_hits_total = Counter(
    "cache_hits_total", "Total Redis cache hits on redirect"
)
cache_misses_total = Counter(
    "cache_misses_total", "Total Redis cache misses on redirect"
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    endpoint = request.url.path
    method = request.method
    with request_duration_seconds.labels(method=method, endpoint=endpoint).time():
        response = await call_next(request)
        requests_total.labels(method=method, endpoint=endpoint, status_code=response.status_code).inc()
    return response


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def get_all_urls():
    # Aggregation query: reads from shard0 only.
    # In a true multi-DB setup this would fan out to all shards and merge.
    all_urls = []
    async for session in get_session("shard0"):
        result = await session.execute(select(URL).order_by(URL.created_at.desc()))
        all_urls.extend(result.scalars().all())
    return all_urls


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    urls = await get_all_urls()
    return templates.TemplateResponse("index.html", {"request": request, "urls": urls})


class ShortenURLRequest(BaseModel):
    long_url: str


@app.post("/shorten", response_class=HTMLResponse)
async def shorten_url(request: Request, background_tasks: BackgroundTasks, long_url: str = Form(...)):
    short_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    shard = get_shard_for_key(short_code)
    async for session in get_session(shard):
        new_url = URL(short_code=short_code, long_url=long_url)
        session.add(new_url)
        await session.commit()
        await session.refresh(new_url)

    background_tasks.add_task(send_new_url_event, short_code, long_url)
    urls = await get_all_urls()
    return templates.TemplateResponse("index.html", {"request": request, "urls": urls, "short_url": f"/{new_url.short_code}"})


@app.get("/{short_code}")
async def redirect_to_long_url(short_code: str, background_tasks: BackgroundTasks):
    # --- PATH 1: Cache hit ---
    cached = await get_url(short_code)
    if cached is not None:
        if cached == "":
            # Negative cache hit: known missing key — skip DB
            cache_hits_total.inc()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found")
        cache_hits_total.inc()
        background_tasks.add_task(send_click_event, short_code)
        return RedirectResponse(url=cached, status_code=status.HTTP_301_MOVED_PERMANENTLY)

    # --- PATH 2 & 3: Cache miss — query DB, then populate cache ---
    cache_misses_total.inc()
    shard = get_shard_for_key(short_code)
    async for session in get_session(shard):
        result = await session.execute(
            select(URL).filter(URL.short_code == short_code)
        )
        url_entry = result.scalar_one_or_none()
        if url_entry:
            # PATH 3: Populate cache for future requests
            await set_url(short_code, url_entry.long_url)
            background_tasks.add_task(send_click_event, short_code)
            return RedirectResponse(url=url_entry.long_url, status_code=status.HTTP_301_MOVED_PERMANENTLY)
        else:
            # PATH 4: Negative cache — prevent repeated DB lookups for bad keys
            await set_null_url(short_code)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
