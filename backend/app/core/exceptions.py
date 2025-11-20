"""
Custom Exception Classes
"""


class SORHDException(Exception):
    """Base exception for FlamenGO! application"""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(SORHDException):
    """Authentication failed"""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(SORHDException):
    """User not authorized to perform this action"""

    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, status_code=403)


class NotFoundError(SORHDException):
    """Resource not found"""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(SORHDException):
    """Validation error"""

    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class ConflictError(SORHDException):
    """Resource conflict (e.g., duplicate entry)"""

    def __init__(self, message: str):
        super().__init__(message, status_code=409)


class OptimizationError(SORHDException):
    """Route optimization error"""

    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class ExternalServiceError(SORHDException):
    """External service (e.g., Google Maps, OSRM) error"""

    def __init__(self, message: str):
        super().__init__(message, status_code=503)


# Aliases for convenience
NotFoundException = NotFoundError
ValidationException = ValidationError
ConflictException = ConflictError
