import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _make_engine(url: str):
    # ssl connect_args are omitted here so this config works for both
    # local Docker (no SSL) and Render (SSL handled via the URL parameter).
    # To enable SSL for a specific deployment, append ?ssl=require to the
    # DATABASE_URL environment variable itself rather than hardcoding here.
    return create_async_engine(
        url,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
    )


SHARD_ENGINES = {
    "shard0": _make_engine(os.environ["DB_SHARD_0_URL"]),
    "shard1": _make_engine(os.environ["DB_SHARD_1_URL"]),
    "shard2": _make_engine(os.environ["DB_SHARD_2_URL"]),
}

# shard0 is used as the primary engine for table creation in lifespan
engine = SHARD_ENGINES["shard0"]


async def get_session(shard_name: str = "shard0"):
    shard_engine = SHARD_ENGINES[shard_name]
    async_session = async_sessionmaker(
        shard_engine, expire_on_commit=False, class_=AsyncSession
    )
    async with async_session() as session:
        yield session
        
