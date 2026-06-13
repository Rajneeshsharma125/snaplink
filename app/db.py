import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _make_engine(url: str):
    # SSL is handled via the URL parameter, not hardcoded here.
    # Render: append ?ssl=require to DATABASE_URL in the environment panel.
    # Local Docker: no SSL needed, plain URL works as-is.
    return create_async_engine(
        url,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
    )


# Render provides a single DATABASE_URL.
# Local Docker provides DB_SHARD_0/1/2_URL for three separate instances.
# .get() tries the per-shard var first; falls back to DATABASE_URL on Render.
# Routing logic (consistent hashing) runs identically in both environments.
_shard_0 = os.environ.get("DB_SHARD_0_URL") or os.environ["DATABASE_URL"]
_shard_1 = os.environ.get("DB_SHARD_1_URL") or os.environ["DATABASE_URL"]
_shard_2 = os.environ.get("DB_SHARD_2_URL") or os.environ["DATABASE_URL"]

SHARD_ENGINES = {
    "shard0": _make_engine(_shard_0),
    "shard1": _make_engine(_shard_1),
    "shard2": _make_engine(_shard_2),
}

# shard0 engine used for table creation in lifespan
engine = SHARD_ENGINES["shard0"]


async def get_session(shard_name: str = "shard0"):
    shard_engine = SHARD_ENGINES[shard_name]
    async_session = async_sessionmaker(
        shard_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session() as session:
        yield session
