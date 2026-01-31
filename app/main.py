from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.session import get_db
from app.db.models.url import URL
from app.api.v1.router import api_router
from app.api.v1.endpoints import redirect

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

# Include API routes with /api/v1 prefix
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Include redirect router at root level (for short URLs like /{short_code})
app.include_router(redirect.router, tags=["redirect"])