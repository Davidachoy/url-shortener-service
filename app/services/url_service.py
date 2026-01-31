from app.schemas.url import URLCreate, URLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.utils.code_generator import generate_code, is_valid_custom_code
from app.db.models.url import URL
from sqlalchemy import select
import httpx
from ipaddress import ip_address
from urllib.parse import urlparse, urlunparse


async def create_short_url(url: URLCreate, db: AsyncSession) -> URLResponse:

    #1. Validate url 

    if not url.url.scheme or not url.url.netloc:
        raise HTTPException(status_code=400, detail="Invalid URL")
    try:
        response = httpx.head(str(url.url), allow_redirects=True, timeout=10)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"URL is not reachable (status code: {response.status_code})")
    except httpx.RequestError as e:
        raise HTTPException(status_code=400, detail=f"URL is not reachable (error: {str(e)})")

    host = url.url.netloc.split(':')[0]
    try:
        ip = ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise HTTPException(status_code=400, detail="URL is not allowed (private IP)")
    except ValueError:
        if host.lower() in ('localhost', '127.0.0.1', '::1'):
            raise HTTPException(status_code=400, detail="URL is not allowed (localhost)")

    parsed = urlparse(str(url.url))

    netloc = parsed.netloc.lower()
    if netloc.startswith('www.'):
        netloc = netloc[4:]

    path = parsed.path.rstrip('/') if parsed.path != '/' else parsed.path

    normalized = urlunparse((parsed.scheme, netloc, path, parsed.params, parsed.query, parsed.fragment))

    #2. Validate custom code

    if url.custom_code:
        if not is_valid_custom_code(url.custom_code):
            raise HTTPException(status_code=400, detail="Invalid custom code")
        existing_url = await db.execute(select(URL).where(URL.short_code == url.custom_code))
        if existing_url.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Custom code already exists")
    else:
        for _ in range(3):
            code = generate_code()
            if is_valid_custom_code(code):
                existing_url = await db.execute(select(URL).where(URL.short_code == code))
                if not existing_url.scalar_one_or_none():
                    url.custom_code = code
                    break
        else:
            raise HTTPException(status_code=400, detail="Failed to generate a unique custom code")
    
    #3. Create URL in the database
    new_url = URL(
        short_code=url.custom_code,
        target_url=normalized,
        expires_at=url.expires_at
    )
