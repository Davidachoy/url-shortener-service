class URLShortenerException(Exception):
    """Base exception for all custom exceptions in the project."""
    
    def __init__(self, message: str = None, details: dict = None):
        self.message = message or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

# ============================================
# URL Exceptions
# ============================================

class InvalidURLException(URLShortenerException):
    """Exception raised for invalid URLs."""
    pass

class URLNotReachableException(URLShortenerException):
    """Exception raised for URLs that are not reachable."""
    pass

class URLExpiredException(URLShortenerException):
    """Exception raised for URLs that have expired."""
    pass

class URLNotFoundException(URLShortenerException):
    """Exception raised for URLs that are not found."""
    pass

# ============================================
# Code Generation Exceptions
# ============================================

class CustomCodeAlreadyExistsException(URLShortenerException):
    """Exception raised for custom codes that already exist."""
    
    def __init__(self, code: str):
        self.code = code
        super().__init__(
            message=f"Code '{code}' already exists",
            details={"code": code}
        )

class CodeGenerationError(URLShortenerException):
    """Exception raised for failed to generate a unique custom code after max retries."""
    
    def __init__(self, retries: int):
        self.retries = retries
        super().__init__(
            message=f"Failed to generate unique code after {retries} attempts",
            details={"retries": retries}
        )

class InvalidCustomCodeError(URLShortenerException):
    """Exception raised for invalid custom codes."""
    
    def __init__(self, code: str, reason: str):
        self.code = code
        self.reason = reason
        super().__init__(
            message=f"Invalid custom code '{code}': {reason}",
            details={"code": code, "reason": reason}
        )


# ============================================
# Cache Exceptions
# ============================================

class CacheError(URLShortenerException):
    """Exception raised for Redis cache errors."""
    pass