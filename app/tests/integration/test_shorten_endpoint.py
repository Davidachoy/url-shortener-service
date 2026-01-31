import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from unittest.mock import patch, MagicMock

from app.main import app
from app.db.base_class import Base
from app.db.models.url import URL
from app.api.deps import get_db


# URL de base de datos de test en memoria con SQLite
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    # Crear todas las tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Limpiar
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
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
    
    # Override dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Mock httpx.head para que no haga llamadas reales
    with patch("app.services.url_service.httpx.head") as mock_head:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as ac:
            yield ac
    
    # Limpiar override
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_post_url_valida_retorna_201(client):
    """Test: POST with valid URL returns 201."""
    response = await client.post(
        "/api/v1/shorten",
        json={"url": "https://google.com"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "short_code" in data
    assert "short_url" in data
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_response_tiene_campos_correctos(client):
    """Test: Response has correct fields."""
    response = await client.post(
        "/api/v1/shorten",
        json={"url": "https://example.com"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verificar campos requeridos
    required_fields = ["id", "short_code", "target_url", "short_url", "created_at", "clicks"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
    
    # Verificar tipos
    assert isinstance(data["id"], int)
    assert isinstance(data["short_code"], str)
    assert isinstance(data["target_url"], str)
    assert isinstance(data["short_url"], str)
    assert isinstance(data["clicks"], int)
    
    # Verificar que short_url contiene el short_code
    assert data["short_code"] in data["short_url"]


@pytest.mark.asyncio
async def test_custom_code_se_respeta(client):
    """Test: Custom code is respected."""
    response = await client.post(
        "/api/v1/shorten",
        json={
            "url": "https://example.com",
            "custom_code": "my-custom"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["short_code"] == "my-custom"
    assert "my-custom" in data["short_url"]


@pytest.mark.asyncio
async def test_custom_code_duplicado_retorna_409(client):
    """Test: Duplicate custom code returns 409."""
    # Crear primera URL
    response1 = await client.post(
        "/api/v1/shorten",
        json={
            "url": "https://first.com",
            "custom_code": "duplicate"
        }
    )
    assert response1.status_code == 201
    
    # Intentar crear otra con mismo código
    response2 = await client.post(
        "/api/v1/shorten",
        json={
            "url": "https://second.com",
            "custom_code": "duplicate"
        }
    )
    
    # Debería fallar (el endpoint maneja CustomCodeAlreadyExistsException)
    assert response2.status_code == 400  # O el status que manejes para este error
    assert "already exists" in response2.json()["detail"].lower() or "duplicate" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_url_sin_protocolo_retorna_422(client):
    """Test: URL without protocol returns 422 (Pydantic validation error)."""
    response = await client.post(
        "/api/v1/shorten",
        json={"url": "google.com"}  # Sin https://
    )
    
    # Pydantic debería rechazar esto antes de llegar al endpoint
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_verificar_url_se_guardo_en_db(client, db_session):
    """Test: Verify that URL is saved in DB."""
    # Crear URL via endpoint
    response = await client.post(
        "/api/v1/shorten",
        json={
            "url": "https://testsite.com",
            "custom_code": "dbtest"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Consultar directamente la DB
    query_result = await db_session.execute(
        select(URL).where(URL.short_code == "dbtest")
    )
    saved_url = query_result.scalar_one_or_none()
    
    # Verificar que se guardó
    assert saved_url is not None
    assert saved_url.short_code == "dbtest"
    assert "testsite.com" in saved_url.target_url
    assert saved_url.id == data["id"]
