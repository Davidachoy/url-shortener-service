import logging
import time
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.api.deps import get_db
from app.services.url_service import get_url_by_code
from app.services.cache_service import get_url_cache, set_url_cache, increment_url_clicks
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{short_code}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def redirect_to_url(short_code: str, db: AsyncSession = Depends(get_db)):
    """
    Redirect to the target URL for the given short code.

    Cache behavior:
    - Warm cache: Redis has the URL → fast path (cache HIT).
    - Cold cache: Redis empty (e.g. after restart) → MISS → load from Postgres, then cache.
    - Redis down (degraded mode): Cache read/write fails → treat as MISS, use Postgres only.
      The app does not crash; redirects work but are slower.

    Flow:
    1. Try to get URL from Redis cache (on error → treat as MISS).
    2. If not in cache, get from database.
    3. Check if URL exists (404 if not).
    4. Check if URL has expired (410 if expired).
    5. Optionally cache for next time (on error → skip, redirect still works).
    6. Increment click counter (on error → skip).
    7. Return 307 redirect to target URL.

    Args:
        short_code: The short code to redirect
        db: Database session
        
    Returns:
        RedirectResponse to the target URL
        
    Raises:
        HTTPException 404: URL not found
        HTTPException 410: URL has expired
    """
    timestamps: dict[str, float] = {}
    timestamps["start"] = time.perf_counter()

    # 1. Try cache first (fast path). On Redis failure → treat as MISS (degraded mode).
    target_url = None
    try:
        target_url = await get_url_cache(short_code)
    except Exception:
        # Redis down or error → cold cache / degraded mode: fall through to Postgres
        pass

    timestamps["after_cache_check"] = time.perf_counter()
    cache_hit = target_url is not None
    db_query_ms: float | None = None

    # 2. If not in cache (MISS or Redis down), get from database
    if not target_url:
        t_before_db = time.perf_counter()
        url_obj = await get_url_by_code(short_code, db)
        timestamps["after_db_query"] = time.perf_counter()
        db_query_ms = (timestamps["after_db_query"] - t_before_db) * 1000

        # 3. Check if URL exists
        if not url_obj:
            timestamps["end"] = time.perf_counter()
            _log_redirect_latency(short_code, cache_hit, timestamps, db_query_ms)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Short code '{short_code}' not found"
            )

        # 4. Check if URL has expired
        if url_obj.expires_at:
            now = datetime.now(timezone.utc)
            expires_at = url_obj.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if expires_at <= now:
                timestamps["end"] = time.perf_counter()
                _log_redirect_latency(short_code, cache_hit, timestamps, db_query_ms)
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail=f"This short URL expired on {expires_at.isoformat()}"
                )

        target_url = url_obj.target_url

        # Cache for next time. On Redis failure → skip cache, redirect still works.
        try:
            await set_url_cache(short_code, target_url, settings.CACHE_TTL_SECONDS)
        except Exception:
            pass  # Degraded mode: don't fail the redirect

    # 5. Increment click counter (fire-and-forget; don't fail redirect on error)
    try:
        await increment_url_clicks(short_code)
    except Exception:
        pass

    timestamps["end"] = time.perf_counter()
    _log_redirect_latency(short_code, cache_hit, timestamps, db_query_ms)

    # 6. Redirect to target URL
    return RedirectResponse(url=target_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


def _log_redirect_latency(
    short_code: str,
    cache_hit: bool,
    timestamps: dict[str, float],
    db_query_ms: float | None,
) -> None:
    """Log redirect request with latency metrics."""
    start = timestamps["start"]
    end = timestamps["end"]
    cache_check_ms = (timestamps["after_cache_check"] - start) * 1000
    total_ms = (end - start) * 1000
    extra = {
        "short_code": short_code,
        "cache_hit": cache_hit,
        "cache_check_ms": round(cache_check_ms, 2),
        "total_ms": round(total_ms, 2),
    }
    if db_query_ms is not None:
        extra["db_query_ms"] = round(db_query_ms, 2)
    logger.info("redirect", extra=extra)