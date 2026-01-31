import pytest

from app.utils.code_generator import (
    SAFE_CHARACTERS,
    generate_code,
    is_valid_custom_code,
)


def test_generate_1000_codes_uniqueness():
    """Generate 1000 codes and verify all are unique."""
    codes = [generate_code() for _ in range(1000)]
    assert len(codes) == len(set(codes)), "All codes must be unique"


@pytest.mark.parametrize("length", [4, 6, 8, 10])
def test_correct_length(length: int):
    """Generated code has the specified length."""
    code = generate_code(length=length)
    assert len(code) == length


def test_only_valid_characters():
    """All code characters are in the allowed alphabet."""
    for _ in range(100):
        code = generate_code(length=8)
        for char in code:
            assert char in SAFE_CHARACTERS, f"Character '{char}' not allowed in {code}"


def test_valid_custom_code_passes():
    """A valid custom code passes validation."""
    assert is_valid_custom_code("abc123") is True
    assert is_valid_custom_code("my-link") is True
    assert is_valid_custom_code("xYz9") is True


def test_custom_code_with_spaces_fails():
    """Custom code with spaces fails."""
    assert is_valid_custom_code("ab c") is False
    assert is_valid_custom_code("a b c") is False
    assert is_valid_custom_code(" ") is False


def test_custom_code_admin_fails():
    """Custom code 'admin' (reserved) fails."""
    assert is_valid_custom_code("admin") is False