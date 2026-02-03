import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.click import Click
from app.db.session import AsyncSessionLocal, get_db

logger = logging.getLogger(__name__)

async def track_click(url_id: int, ip_address: str) -> None:
    """Track a click for a URL."""
    try:
        async with AsyncSessionLocal() as db:
            click = Click(url_id=url_id, ip_address=ip_address)
            db.add(click)
            await db.commit()
            await db.refresh(click)
            return click
    except Exception as e:
        logger.error(f"Error tracking click: {e}")
        raise e