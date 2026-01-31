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
async def test_create_url_with_random_code(mock_db_session, mock_httpx_success):
    """Test: Create URL with random code (mock DB)."""
    # Setup: mock DB query returns None (code available)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    # Mock refresh to simulate object has ID and DB fields
    async def mock_refresh_side_effect(obj):
        obj.id = 1
        obj.created_at = datetime.now()
        obj.clicks = 0

    mock_db_session.refresh.side_effect = mock_refresh_side_effect

    # Create request
    url_data = URLCreate(url="https://google.com")

    # Mock generate_code to return a known code
    with patch("app.services.url_service.generate_code", return_value="abc123"):
        result = await create_short_url(url_data, mock_db_session)

    # Verificar
    assert result.short_code == "abc123"
    assert "google.com" in str(result.target_url)
    assert result.id == 1
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_url_with_custom_code_available(mock_db_session, mock_httpx_success):
    """Test: Create URL with custom code available."""
    # Setup: mock DB query returns None (custom code available)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    async def mock_refresh_side_effect(obj):
        obj.id = 2
        obj.created_at = datetime.now()
        obj.clicks = 0

    mock_db_session.refresh.side_effect = mock_refresh_side_effect

    # Create request with custom code
    url_data = URLCreate(url="https://example.com", custom_code="my-link")

    result = await create_short_url(url_data, mock_db_session)

    # Assert custom code is used
    assert result.short_code == "my-link"
    assert result.id == 2


@pytest.mark.asyncio
async def test_duplicate_custom_code_raises_exception(mock_db_session, mock_httpx_success):
    """Test: Duplicate custom code raises exception."""
    # Setup: mock DB query returns an object (code already exists)
    mock_existing_url = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=mock_existing_url)
    mock_db_session.execute = AsyncMock(return_value=mock_result)

    # Create request with custom code that already exists
    url_data = URLCreate(url="https://example.com", custom_code="existing")

    # Assert CustomCodeAlreadyExistsException is raised
    with pytest.raises(CustomCodeAlreadyExistsException) as exc_info:
        await create_short_url(url_data, mock_db_session)

    assert exc_info.value.code == "existing"


@pytest.mark.asyncio
async def test_invalid_url_raises_exception(mock_db_session):
    """Test: Invalid URL (localhost) raises exception."""
    # Mock httpx.head to return 200; service rejects localhost in host validation
    with patch("app.services.url_service.httpx.head") as mock_head:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        url_data = URLCreate(url="https://localhost:8000")

        with pytest.raises(URLNotReachableException) as exc_info:
            await create_short_url(url_data, mock_db_session)

        assert "localhost" in str(exc_info.value.details).lower()


@pytest.mark.asyncio
async def test_random_code_collision_retries_correctly(mock_db_session, mock_httpx_success):
    """Test: Random code collision retries correctly."""
    # Setup: first call returns existing code, second returns None (available)
    mock_result_exists = MagicMock()
    mock_result_exists.scalar_one_or_none = MagicMock(return_value=MagicMock())  # Exists

    mock_result_available = MagicMock()
    mock_result_available.scalar_one_or_none = MagicMock(return_value=None)  # Available

    # Simulate: first code exists, second available (AsyncMock returns each value on await)
    mock_db_session.execute = AsyncMock(side_effect=[mock_result_exists, mock_result_available])

    async def mock_refresh_side_effect(obj):
        obj.id = 3
        obj.created_at = datetime.now()
        obj.clicks = 0

    mock_db_session.refresh.side_effect = mock_refresh_side_effect

    url_data = URLCreate(url="https://example.org")

    # Mock generate_code to return specific codes
    codes = ["collision", "success"]
    with patch("app.services.url_service.generate_code", side_effect=codes):
        result = await create_short_url(url_data, mock_db_session)

    # Assert second code is used (after retry)
    assert result.short_code == "success"
    assert mock_db_session.execute.call_count == 2  # 2 queries (one per generated code)


@pytest.mark.asyncio
async def test_random_code_fails_after_max_retries(mock_db_session, mock_httpx_success):
    """Test: If all generated codes collide, raises CodeGenerationError."""
    # Setup: all queries return that code exists
    mock_result_exists = MagicMock()
    mock_result_exists.scalar_one_or_none = MagicMock(return_value=MagicMock())
    mock_db_session.execute = AsyncMock(return_value=mock_result_exists)

    url_data = URLCreate(url="https://example.com")

    # All generated codes collide
    with patch("app.services.url_service.generate_code", return_value="taken"):
        with pytest.raises(CodeGenerationError) as exc_info:
            await create_short_url(url_data, mock_db_session)

        assert exc_info.value.retries == 3
