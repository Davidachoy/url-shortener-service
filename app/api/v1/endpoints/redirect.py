from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.api.deps import get_db
from app.services.url_service import get_url_by_code
from app.services.cache_service import get_url_cache, set_url_cache, increment_url_clicks
from app.core.config import settings
from app.core.exceptions import URLNotFoundException, URLExpiredException

router = APIRouter()


@router.get("/{short_code}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def redirect_to_url(short_code: str, db: AsyncSession = Depends(get_db)):
    """
    Redirect to the target URL for the given short code.
    
    Flow:
    1. Try to get URL from Redis cache
    2. If not in cache, get from database
    3. Check if URL exists (404 if not)
    4. Check if URL has expired (410 if expired)
    5. Increment click counter
    6. Return 307 redirect to target URL
    
    Args:
        short_code: The short code to redirect
        db: Database session
        
    Returns:
        RedirectResponse to the target URL
        
    Raises:
        HTTPException 404: URL not found
        HTTPException 410: URL has expired
    """
    # 1. Try cache first (fast path)
    target_url = await get_url_cache(short_code)
    
    # 2. If not in cache, get from database
    if not target_url:
        url_obj = await get_url_by_code(short_code, db)
        
        # 3. Check if URL exists
        if not url_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Short code '{short_code}' not found"
            )
        
        # 4. Check if URL has expired
        if url_obj.expires_at:
            now = datetime.now(timezone.utc)
            # Ensure both datetimes are timezone-aware for comparison
            expires_at = url_obj.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if expires_at <= now:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail=f"This short URL expired on {expires_at.isoformat()}"
                )
        
        target_url = url_obj.target_url
        
        # Cache it for next time
        await set_url_cache(short_code, target_url, settings.CACHE_TTL_SECONDS)
    
    # 5. Increment click counter (async, don't await - fire and forget)
    try:
        await increment_url_clicks(short_code)
    except Exception:
        # Don't fail the redirect if click tracking fails
        pass
    
    # 6. Redirect to target URL
    return RedirectResponse(url=target_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)