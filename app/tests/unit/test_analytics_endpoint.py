import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.db.base_class import Base
from app.db.models.url import URL
from app.db.models.click import Click
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
    """Create test client with database override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_analytics_returns_correct_data(client, db_session):
    """Test that analytics returns correct summary and clicks_by_day."""
    # Create test URL
    test_url = URL(
        short_code="testcode",
        target_url="https://example.com",
        created_at=datetime.utcnow()
    )
    db_session.add(test_url)
    await db_session.commit()
    await db_session.refresh(test_url)
    
    # Create test clicks
    now = datetime.utcnow()
    clicks = [
        Click(url_id=test_url.id, ip_address="192.168.1.1", created_at=now),
        Click(url_id=test_url.id, ip_address="192.168.1.2", created_at=now - timedelta(hours=1)),
        Click(url_id=test_url.id, ip_address="192.168.1.1", created_at=now - timedelta(hours=2)),  # Duplicate IP
    ]
    for click in clicks:
        db_session.add(click)
    await db_session.commit()
    
    # Test analytics
    response = await client.get("/api/v1/analytics/testcode")
    
    assert response.status_code == 200
    data = response.json()
    
    # Check basic structure
    assert data["short_code"] == "testcode"
    assert data["target_url"] == "https://example.com"
    
    # Check summary
    assert data["summary"]["total_clicks"] == 3
    assert data["summary"]["unique_visitors"] == 2  # Only 2 unique IPs
    assert data["summary"]["first_click"] is not None
    assert data["summary"]["last_click"] is not None
    
    # Check clicks_by_day
    assert len(data["clicks_by_day"]) == 1
    assert data["clicks_by_day"][0]["clicks"] == 3


@pytest.mark.asyncio
async def test_analytics_with_no_clicks(client, db_session):
    """Test analytics for URL with no clicks."""
    # Create test URL without clicks
    test_url = URL(
        short_code="noclicks",
        target_url="https://example.com",
        created_at=datetime.utcnow()
    )
    db_session.add(test_url)
    await db_session.commit()
    
    response = await client.get("/api/v1/analytics/noclicks")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["summary"]["total_clicks"] == 0
    assert data["summary"]["unique_visitors"] == 0
    assert data["summary"]["first_click"] is None
    assert data["summary"]["last_click"] is None
    assert data["clicks_by_day"] == []


@pytest.mark.asyncio
async def test_analytics_period_filtering(client, db_session):
    """Test that period parameter filters clicks correctly."""
    # Create test URL
    test_url = URL(
        short_code="periodtest",
        target_url="https://example.com",
        created_at=datetime.utcnow()
    )
    db_session.add(test_url)
    await db_session.commit()
    await db_session.refresh(test_url)
    
    # Create clicks at different times
    now = datetime.utcnow()
    clicks = [
        Click(url_id=test_url.id, ip_address="192.168.1.1", created_at=now),  # Today
        Click(url_id=test_url.id, ip_address="192.168.1.2", created_at=now - timedelta(days=5)),  # 5 days ago
        Click(url_id=test_url.id, ip_address="192.168.1.3", created_at=now - timedelta(days=10)),  # 10 days ago
    ]
    for click in clicks:
        db_session.add(click)
    await db_session.commit()
    
    # Test 7d period (should exclude 10 days ago)
    response_7d = await client.get("/api/v1/analytics/periodtest?period=7d")
    assert response_7d.status_code == 200
    data_7d = response_7d.json()
    assert data_7d["summary"]["total_clicks"] == 2
    
    # Test all period (should include everything)
    response_all = await client.get("/api/v1/analytics/periodtest?period=all")
    assert response_all.status_code == 200
    data_all = response_all.json()
    assert data_all["summary"]["total_clicks"] == 3


@pytest.mark.asyncio
async def test_analytics_nonexistent_code_returns_404(client):
    """Test that analytics returns 404 for non-existent short code."""
    response = await client.get("/api/v1/analytics/doesnotexist")
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()
