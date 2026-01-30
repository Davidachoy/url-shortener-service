from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.session import get_db
from app.db.models.url import URL

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}

# ENDPOINT DE PRUEBA - borrarás después
@app.get("/test-db")
async def test_database(db: AsyncSession = Depends(get_db)):
    # Crear URL de prueba
    test_url = URL(
        short_code="test123",
        target_url="https://example.com"
    )
    
    db.add(test_url)
    await db.commit()
    
    # Leer todas las URLs
    result = await db.execute(select(URL))
    urls = result.scalars().all()
    
    return {
        "message": "Database connection works!",
        "urls_count": len(urls)
    }