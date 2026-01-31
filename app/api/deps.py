from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.core.config import settings, Settings


# ============================================
# Database Dependencies
# ============================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to inject a database session into endpoints.

    Runs before the endpoint and provides a session.
    When the request finishes, the session is closed automatically.

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ============================================
# Configuration Dependencies
# ============================================

def get_settings() -> Settings:
    """
    Dependency to inject configuration into endpoints.

    Useful for:
    - Accessing settings in endpoints without importing directly
    - Easier testing (override settings in tests)
    - Documenting which configuration each endpoint uses

    Usage:
        @app.get("/info")
        async def get_info(settings: Settings = Depends(get_settings)):
            return {"environment": settings.ENVIRONMENT}
    """
    return settings