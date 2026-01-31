import pytest
from pydantic import ValidationError

from app.schemas.url import URLCreate


def test_url_valida_pasa_validacion():
    """URL válida pasa validación."""
    data = URLCreate(url="https://google.com")
    assert data.url.scheme == "https"
    assert "google.com" in str(data.url)


def test_url_invalida_falla_validacion():
    """URL inválida falla validación."""
    with pytest.raises(ValidationError) as exc_info:
        URLCreate(url="not-a-url")
    assert "url" in str(exc_info.value).lower() or "Input should be a valid URL" in str(exc_info.value)


def test_custom_code_con_caracteres_especiales_falla():
    """custom_code con caracteres especiales falla."""
    with pytest.raises(ValidationError):
        URLCreate(url="https://example.com", custom_code="ab@c")
    with pytest.raises(ValidationError):
        URLCreate(url="https://example.com", custom_code="a b")


def test_custom_code_muy_largo_falla():
    """custom_code muy largo falla (max 20)."""
    with pytest.raises(ValidationError):
        URLCreate(url="https://example.com", custom_code="a" * 21)