from app.schemas.url import URLCreate, URLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.utils.code_generator import generate_code, is_valid_custom_code
from app.db.models.url import URL
from sqlalchemy import select
import httpx
from ipaddress import ip_address
from urllib.parse import urlparse, urlunparse
from app.core.config import settings
from app.core.exceptions import (
    InvalidURLException,
    URLNotReachableException,
    URLExpiredException,
    CustomCodeAlreadyExistsException,
    CodeGenerationError,
    InvalidCustomCodeError
)

async def create_short_url(url: URLCreate, db: AsyncSession) -> URLResponse:

    #1. Validate url
    parsed = urlparse(str(url.url))

    if not parsed.scheme or not parsed.netloc:
        raise InvalidURLException()
    try:
        response = httpx.head(str(url.url), allow_redirects=True, timeout=10)
        if response.status_code != 200:
            raise URLNotReachableException(details={"status_code": response.status_code})
    except httpx.RequestError as e:
        raise URLNotReachableException(details={"error": str(e)})

    host = parsed.netloc.split(':')[0]
    try:
        ip = ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise URLNotReachableException(details={"reason": "private IP"})
    except ValueError:
        if host.lower() in ('localhost', '127.0.0.1', '::1'):
            raise URLNotReachableException(details={"reason": "localhost"})

    netloc = parsed.netloc.lower()
    if netloc.startswith('www.'):
        netloc = netloc[4:]

    path = parsed.path.rstrip('/') if parsed.path != '/' else parsed.path

    normalized = urlunparse((parsed.scheme, netloc, path, parsed.params, parsed.query, parsed.fragment))

    #2. Validate custom code

    if url.custom_code:
        if not is_valid_custom_code(url.custom_code):
            raise InvalidCustomCodeError(code=url.custom_code, reason="Invalid format")
        existing_url = await db.execute(select(URL).where(URL.short_code == url.custom_code))
        if existing_url.scalar_one_or_none():
            raise CustomCodeAlreadyExistsException(code=url.custom_code)
    else:
        for _ in range(3):
            code = generate_code()
            if is_valid_custom_code(code):
                existing_url = await db.execute(select(URL).where(URL.short_code == code))
                if not existing_url.scalar_one_or_none():
                    url.custom_code = code
                    break
        else:
            raise CodeGenerationError(retries=3)
    
    #3. Create URL in the database
    new_url = URL(
        short_code=url.custom_code,
        target_url=normalized,
    )
    db.add(new_url)
    await db.commit()
    await db.refresh(new_url)
    return URLResponse(
        id=new_url.id,
        short_code=new_url.short_code,
        target_url=new_url.target_url,
        short_url=f"{settings.SHORT_URL_BASE}/{new_url.short_code}",
        created_at=new_url.created_at,
        clicks=new_url.clicks
    )

    
