from fastapi import APIRouter
from app.core.config import settings
from app.api.v1.endpoints import shorten

api_router = APIRouter()

# Incluir routers de cada módulo
api_router.include_router(
    shorten.router,
    tags=["urls"]  # Para organizar en Swagger docs
)