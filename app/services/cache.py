

# Cache disabled for Render deployment (no Redis available)
# Redis caching is active in full local Docker setup

import os
import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))   # 1 hour: how long a valid URL stays cached
NULL_TTL = int(os.getenv("NULL_TTL", "60"))         # 1 minute: how long a known-missing key is cached

_client: redis.Redis | None = None


def _get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(REDIS_URL, decode_responses=True)
    return _client


async def get_url(short_code: str) -> str | None:
    """
    Check Redis for a short_code.

    Return values:
      str (non-empty) — cache hit, value is the long_url
      ""  (empty str) — negative cache hit, key is known to not exist in DB
      None            — cache miss, key is not in Redis at all
    """
    client = _get_client()
    value = await client.get(short_code)
    return value  # redis returns None if key absent, str otherwise


async def set_url(short_code: str, long_url: str) -> None:
    """Store a valid short_code -> long_url mapping in Redis."""
    client = _get_client()
    await client.set(short_code, long_url, ex=CACHE_TTL)


async def set_null_url(short_code: str) -> None:
    """
    Cache a known-missing key as an empty string.
    Prevents repeated DB hits for short codes that do not exist.
    """
    client = _get_client()
    await client.set(short_code, "", ex=NULL_TTL)
    
