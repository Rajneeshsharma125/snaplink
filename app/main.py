
from contextlib import asynccontextmanager
from app.db import SHARD_ENGINES, get_session, Base, engine
from app.utils.hashing import get_shard_for_key
from app.models import URL
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response, BackgroundTasks, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import random
import string
import uvicorn
from pydantic import BaseModel
from prometheus_client import generate_latest, Counter, Histogram, CONTENT_TYPE_LATEST

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created")
    yield

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="app/templates")

# Prometheus Metrics
requests_total = Counter(
    "http_requests_total", "Total HTTP Requests", ["method", "endpoint", "status_code"]
)
request_duration_seconds = Histogram(
    "http_request_duration_seconds", "HTTP Request Duration", ["method", "endpoint"]
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
    async for session in get_session("shard0"):
        new_url = URL(short_code=short_code, long_url=long_url)
        session.add(new_url)
        await session.commit()
        await session.refresh(new_url)

    urls = await get_all_urls()
    return templates.TemplateResponse("index.html", {"request": request, "urls": urls, "short_url": f"/{new_url.short_code}"})

@app.get("/{short_code}")
async def redirect_to_long_url(short_code: str, background_tasks: BackgroundTasks):
    async for session in get_session("shard0"):
        result = await session.execute(
            select(URL).filter(URL.short_code == short_code)
        )
        url_entry = result.scalar_one_or_none()
        if url_entry:
            return RedirectResponse(url=url_entry.long_url, status_code=status.HTTP_301_MOVED_PERMANENTLY)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

