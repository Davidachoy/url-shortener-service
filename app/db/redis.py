from redis.asyncio import Redis
from app.core.config import settings

def get_redis_client() -> Redis:
    """
    Create and return a Redis client connection.
    
    Returns:
        Redis: Redis async client instance
    """
    return Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,  # Auto-decode bytes to strings
        max_connections=settings.REDIS_MAX_CONNECTIONS
    )