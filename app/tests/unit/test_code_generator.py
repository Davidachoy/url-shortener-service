import pytest

from app.utils.code_generator import (
    SAFE_CHARACTERS,
    generate_code,
    is_valid_custom_code,
)


def test_generar_1000_codigos_unicidad():
    """Generar 1000 códigos y verificar que todos son únicos."""
    codes = [generate_code() for _ in range(1000)]
    assert len(codes) == len(set(codes)), "Todos los códigos deben ser únicos"


@pytest.mark.parametrize("length", [4, 6, 8, 10])
def test_longitud_correcta(length: int):
    """El código generado tiene la longitud especificada."""
    code = generate_code(length=length)
    assert len(code) == length


def test_solo_caracteres_validos():
    """Todos los caracteres del código están en el alfabeto permitido."""
    for _ in range(100):
        code = generate_code(length=8)
        for char in code:
            assert char in SAFE_CHARACTERS, f"Carácter '{char}' no permitido en {code}"


def test_custom_code_valido_pasa():
    """Un custom code válido pasa la validación."""
    assert is_valid_custom_code("abc123") is True
    assert is_valid_custom_code("my-link") is True
    assert is_valid_custom_code("xYz9") is True


def test_custom_code_con_espacios_falla():
    """Custom code con espacios falla."""
    assert is_valid_custom_code("ab c") is False
    assert is_valid_custom_code("a b c") is False
    assert is_valid_custom_code(" ") is False


def test_custom_code_admin_falla():
    """Custom code 'admin' (reservado) falla."""
    assert is_valid_custom_code("admin") is False