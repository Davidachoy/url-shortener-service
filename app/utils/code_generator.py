import secrets
import re

SAFE_CHARACTERS = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789-"
RESERVED_CODES = ['api', 'admin', 'user', 'login', 'logout', 'register', 'reset', 'forgot']

def generate_code(length: int = 6) -> str:
    return ''.join(secrets.choice(SAFE_CHARACTERS) for _ in range(length))

def is_valid_custom_code(code: str) -> bool:
    if len(code) < 3 or len(code) > 20:
        return False
    if not re.match(r'^[a-zA-Z0-9\-]+$', code):
        return False
    if code.startswith('-') or code.endswith('-'):
        return False
    if code in RESERVED_CODES:
        return False
    return True
