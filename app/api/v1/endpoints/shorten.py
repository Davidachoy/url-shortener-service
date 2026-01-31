from fastapi import APIRouter
from app.schemas.url import URLCreate, URLResponse
from app.services.url_service import create_short_url
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, status
from app.api.deps import get_db
from app.core.exceptions import URLShortenerException
from fastapi import HTTPException

router = APIRouter()

@router.post("/shorten", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
async def shorten_url(url: URLCreate, db: AsyncSession = Depends(get_db)):
    """
    Shorten a URL.

    Args:
        url: The URL to shorten.
        db: The database session.

    Returns:
        The shortened URL.
    """
    try:
        return await create_short_url(url, db)
    except URLShortenerException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



