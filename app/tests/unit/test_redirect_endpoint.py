"""
Unit tests for the redirect endpoint (GET /{short_code}).
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone, timedelta

from app.main import app
from app.db.base_class import Base
from app.db.models.url import URL
from app.api.deps import get_db


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    """Create test client with database override and mocked cache."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Mock cache so redirect always hits DB (no Redis needed)
    with patch(
        "app.api.v1.endpoints.redirect.get_url_cache",
        new_callable=AsyncMock,
        return_value=None,
    ), patch(
        "app.api.v1.endpoints.redirect.increment_url_clicks",
        new_callable=AsyncMock,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_valid_code_returns_307(client, db_session):
    """Test: Valid code returns 307."""
    # Create URL in test DB
    url = URL(
        short_code="abc123",
        target_url="https://example.com",
    )
    db_session.add(url)
    await db_session.commit()

    response = await client.get("/abc123")

    assert response.status_code == 307


@pytest.mark.asyncio
async def test_location_header_is_correct(client, db_session):
    """Test: Location header is correct."""
    target = "https://google.com/search?q=test"
    url = URL(
        short_code="xyz789",
        target_url=target,
    )
    db_session.add(url)
    await db_session.commit()

    response = await client.get("/xyz789")

    assert response.status_code == 307
    assert response.headers["location"] == target


@pytest.mark.asyncio
async def test_nonexistent_code_returns_404(client):
    """Test: Nonexistent code returns 404."""
    response = await client.get("/NoExiste999")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()
    assert "NoExiste999" in data["detail"]


@pytest.mark.asyncio
async def test_expired_url_returns_410(client, db_session):
    """Test: Expired URL returns 410."""
    expired_at = datetime.now(timezone.utc) - timedelta(hours=1)
    url = URL(
        short_code="expired",
        target_url="https://example.com",
        expires_at=expired_at,
    )
    db_session.add(url)
    await db_session.commit()

    response = await client.get("/expired")

    assert response.status_code == 410
    data = response.json()
    assert "expired" in data["detail"].lower()
