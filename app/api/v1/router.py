from fastapi import APIRouter
from app.core.config import settings
from app.api.v1.endpoints import shorten, analytics

api_router = APIRouter()

# Include routers from each module
api_router.include_router(
    shorten.router,
    tags=["urls"]  # For Swagger docs organization
)
api_router.include_router(
    analytics.router,
    tags=["analytics"]  # For Swagger docs organization
)