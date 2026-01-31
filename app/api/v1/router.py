from fastapi import APIRouter
from app.core.config import settings
from app.api.v1.endpoints import shorten

api_router = APIRouter()

# Include routers from each module
api_router.include_router(
    shorten.router,
    tags=["urls"]  # For Swagger docs organization
)