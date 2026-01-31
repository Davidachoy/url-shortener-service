from redis.asyncio import Redis
from app.core.config import settings
from app.db.redis import get_redis_client
from app.core.exceptions import CacheError


async def set_url_cache(short_code: str, target_url: str, ttl: int = None):
    """
    Store a URL mapping in Redis cache.
    
    Args:
        short_code: The short code key
        target_url: The target URL to cache
        ttl: Time to live in seconds (defaults to settings.CACHE_TTL_SECONDS)
    """
    try:
        redis_client = get_redis_client()
        if ttl is None:
            ttl = settings.CACHE_TTL_SECONDS
        await redis_client.set(short_code, target_url, ex=ttl)
    except Exception as e:
        raise CacheError(f"Error setting URL cache: {e}")


async def get_url_cache(short_code: str) -> str | None:
    """
    Retrieve a URL from Redis cache.
    
    Args:
        short_code: The short code to look up
        
    Returns:
        The target URL if found, None otherwise
    """
    try:
        redis_client = get_redis_client()
        result = await redis_client.get(short_code)
        return result
    except Exception as e:
        raise CacheError(f"Error getting URL cache: {e}")


async def delete_url_cache(short_code: str):
    """
    Delete a URL from Redis cache.
    
    Args:
        short_code: The short code to delete
    """
    try:
        redis_client = get_redis_client()
        await redis_client.delete(short_code)
    except Exception as e:
        raise CacheError(f"Error deleting URL cache: {e}")


async def increment_url_clicks(short_code: str) -> int:
    """
    Increment the click counter for a short code.
    
    Args:
        short_code: The short code whose counter to increment
        
    Returns:
        The new click count
    """
    try:
        redis_client = get_redis_client()
        clicks_key = f"clicks:{short_code}"
        new_count = await redis_client.incr(clicks_key)
        return new_count
    except Exception as e:
        raise CacheError(f"Error incrementing URL clicks: {e}")
