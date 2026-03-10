from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

redis_client = None

try:
    import redis.asyncio as aioredis
    redis_client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
except Exception:
    logger.warning("Redis not available — running without cache")


async def get_redis():
    return redis_client
