

# Cache disabled for Render deployment (no Redis available)
# Redis caching is active in full local Docker setup

async def get_url(short_code: str):
    return None

async def set_url(short_code: str, long_url: str):
    pass

async def set_null_url(short_code: str):
    pass
