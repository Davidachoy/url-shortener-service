import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.url_service import create_short_url
from app.schemas.url import URLCreate
from app.core.exceptions import (
    URLNotReachableException,
    CustomCodeAlreadyExistsException,
    CodeGenerationError,
)


@pytest.fixture
def mock_db_session():
    """Mock AsyncSession for database operations."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def mock_httpx_success():
    """Mock successful httpx HEAD request."""
    with patch("app.services.url_service.httpx.head") as mock_head:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        yield mock_head


@pytest.mark.asyncio
async def test_crear_url_con_codigo_random(mock_db_session, mock_httpx_success):
    """Test: Crear URL con código random (mock DB)."""
    # Setup: mock DB query que retorna None (código disponible)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    # Mock refresh para simular que el objeto tiene ID y campos de DB
    async def mock_refresh_side_effect(obj):
        obj.id = 1
        obj.created_at = datetime.now()
        obj.clicks = 0

    mock_db_session.refresh.side_effect = mock_refresh_side_effect

    # Crear request
    url_data = URLCreate(url="https://google.com")

    # Mock generate_code para que devuelva un código conocido
    with patch("app.services.url_service.generate_code", return_value="abc123"):
        result = await create_short_url(url_data, mock_db_session)

    # Verificar
    assert result.short_code == "abc123"
    assert "google.com" in str(result.target_url)
    assert result.id == 1
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_crear_url_con_custom_code_disponible(mock_db_session, mock_httpx_success):
    """Test: Crear URL con custom code disponible."""
    # Setup: mock DB query que retorna None (custom code disponible)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    async def mock_refresh_side_effect(obj):
        obj.id = 2
        obj.created_at = datetime.now()
        obj.clicks = 0

    mock_db_session.refresh.side_effect = mock_refresh_side_effect

    # Crear request con custom code
    url_data = URLCreate(url="https://example.com", custom_code="my-link")

    result = await create_short_url(url_data, mock_db_session)

    # Verificar que usa el custom code
    assert result.short_code == "my-link"
    assert result.id == 2


@pytest.mark.asyncio
async def test_custom_code_duplicado_lanza_exception(mock_db_session, mock_httpx_success):
    """Test: Custom code duplicado lanza exception."""
    # Setup: mock DB query que retorna un objeto (código ya existe)
    mock_existing_url = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=mock_existing_url)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    # Crear request con custom code que ya existe
    url_data = URLCreate(url="https://example.com", custom_code="existing")

    # Verificar que lanza CustomCodeAlreadyExistsException
    with pytest.raises(CustomCodeAlreadyExistsException) as exc_info:
        await create_short_url(url_data, mock_db_session)

    assert exc_info.value.code == "existing"


@pytest.mark.asyncio
async def test_url_invalida_lanza_exception(mock_db_session):
    """Test: URL inválida (localhost) lanza exception."""
    # Mock httpx.head para que retorne 200; el servicio rechaza localhost en la validación de host
    with patch("app.services.url_service.httpx.head") as mock_head:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        url_data = URLCreate(url="https://localhost:8000")

        with pytest.raises(URLNotReachableException) as exc_info:
            await create_short_url(url_data, mock_db_session)

        assert "localhost" in str(exc_info.value.details).lower()


@pytest.mark.asyncio
async def test_colision_codigo_random_retries_correctamente(mock_db_session, mock_httpx_success):
    """Test: Colisión en código random retries correctamente."""
    # Setup: primera llamada retorna código existente, segunda retorna None (disponible)
    mock_result_exists = MagicMock()
    mock_result_exists.scalar_one_or_none = MagicMock(return_value=MagicMock())  # Existe

    mock_result_available = MagicMock()
    mock_result_available.scalar_one_or_none = MagicMock(return_value=None)  # Disponible

    # Simular: primer código existe, segundo disponible (AsyncMock devuelve cada valor al await)
    mock_db_session.execute = AsyncMock(side_effect=[mock_result_exists, mock_result_available])

    async def mock_refresh_side_effect(obj):
        obj.id = 3
        obj.created_at = datetime.now()
        obj.clicks = 0

    mock_db_session.refresh.side_effect = mock_refresh_side_effect

    url_data = URLCreate(url="https://example.org")

    # Mock generate_code para devolver códigos específicos
    codes = ["collision", "success"]
    with patch("app.services.url_service.generate_code", side_effect=codes):
        result = await create_short_url(url_data, mock_db_session)

    # Verificar que usa el segundo código (después del retry)
    assert result.short_code == "success"
    assert mock_db_session.execute.call_count == 2  # 2 queries (uno por cada código generado)


@pytest.mark.asyncio
async def test_codigo_random_falla_tras_max_retries(mock_db_session, mock_httpx_success):
    """Test: Si todos los códigos generados colisionan, lanza CodeGenerationError."""
    # Setup: todas las queries retornan que el código existe
    mock_result_exists = MagicMock()
    mock_result_exists.scalar_one_or_none = MagicMock(return_value=MagicMock())
    mock_db_session.execute = AsyncMock(return_value=mock_result_exists)

    url_data = URLCreate(url="https://example.com")

    # Todos los códigos generados colisionan
    with patch("app.services.url_service.generate_code", return_value="taken"):
        with pytest.raises(CodeGenerationError) as exc_info:
            await create_short_url(url_data, mock_db_session)

        assert exc_info.value.retries == 3
