import pytest
from pydantic import ValidationError

from app.schemas.url import URLCreate


def test_valid_url_passes_validation():
    """Valid URL passes validation."""
    data = URLCreate(url="https://google.com")
    assert data.url.scheme == "https"
    assert "google.com" in str(data.url)


def test_invalid_url_fails_validation():
    """Invalid URL fails validation."""
    with pytest.raises(ValidationError) as exc_info:
        URLCreate(url="not-a-url")
    assert "url" in str(exc_info.value).lower() or "Input should be a valid URL" in str(exc_info.value)


def test_custom_code_with_special_characters_fails():
    """custom_code with special characters fails."""
    with pytest.raises(ValidationError):
        URLCreate(url="https://example.com", custom_code="ab@c")
    with pytest.raises(ValidationError):
        URLCreate(url="https://example.com", custom_code="a b")


def test_custom_code_too_long_fails():
    """custom_code too long fails (max 20)."""
    with pytest.raises(ValidationError):
        URLCreate(url="https://example.com", custom_code="a" * 21)