import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.db.base_class import Base
from app.db.models.url import URL
from app.services.url_service import create_short_url
from app.schemas.url import URLCreate
from app.core.exceptions import CustomCodeAlreadyExistsException


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


@pytest.fixture
def mock_httpx_success():
    """Mock successful httpx HEAD request."""
    with patch("app.services.url_service.httpx.head") as mock_head:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        yield mock_head


@pytest.mark.asyncio
async def test_crear_url_end_to_end_con_test_database(db_session, mock_httpx_success):
    """Test: Crear URL end-to-end con test database."""
    # Crear request
    url_data = URLCreate(url="https://example.com")

    # Mock generate_code para código predecible
    with patch("app.services.url_service.generate_code", return_value="test123"):
        result = await create_short_url(url_data, db_session)

    # Verificar respuesta
    assert result.short_code == "test123"
    assert "example.com" in str(result.target_url)
    assert result.id is not None
    assert result.created_at is not None


@pytest.mark.asyncio
async def test_verificar_que_se_guarda_en_db(db_session, mock_httpx_success):
    """Test: Verificar que la URL se guarda en DB."""
    # Crear URL
    url_data = URLCreate(url="https://google.com", custom_code="mylink")

    result = await create_short_url(url_data, db_session)

    # Verificar que existe en la DB
    query_result = await db_session.execute(
        select(URL).where(URL.short_code == "mylink")
    )
    saved_url = query_result.scalar_one_or_none()

    assert saved_url is not None
    assert saved_url.short_code == "mylink"
    assert "google.com" in saved_url.target_url
    assert saved_url.id == result.id


@pytest.mark.asyncio
async def test_dos_requests_mismo_custom_code_segunda_falla(db_session, mock_httpx_success):
    """Test: Dos requests con mismo custom code, segunda falla."""
    # Primera request - debe funcionar
    url_data_1 = URLCreate(url="https://first.com", custom_code="duplicate")
    result_1 = await create_short_url(url_data_1, db_session)

    assert result_1.short_code == "duplicate"

    # Segunda request con mismo código - debe fallar
    url_data_2 = URLCreate(url="https://second.com", custom_code="duplicate")

    with pytest.raises(CustomCodeAlreadyExistsException) as exc_info:
        await create_short_url(url_data_2, db_session)

    assert exc_info.value.code == "duplicate"

    # Verificar que solo existe una URL en la DB con ese código
    query_result = await db_session.execute(
        select(URL).where(URL.short_code == "duplicate")
    )
    all_urls = query_result.scalars().all()

    assert len(all_urls) == 1
    # El servicio normaliza la URL sin trailing slash en la raíz
    assert all_urls[0].target_url.rstrip("/") == "https://first.com"


@pytest.mark.asyncio
async def test_crear_multiples_urls_diferentes(db_session, mock_httpx_success):
    """Test bonus: Crear múltiples URLs y verificar que todas se guardan."""
    urls_data = [
        URLCreate(url="https://example1.com", custom_code="code1"),
        URLCreate(url="https://example2.com", custom_code="code2"),
        URLCreate(url="https://example3.com", custom_code="code3"),
    ]

    # Crear todas las URLs
    for url_data in urls_data:
        await create_short_url(url_data, db_session)

    # Verificar que todas están en la DB
    query_result = await db_session.execute(select(URL))
    all_urls = query_result.scalars().all()

    assert len(all_urls) == 3
    saved_codes = {url.short_code for url in all_urls}
    assert saved_codes == {"code1", "code2", "code3"}
