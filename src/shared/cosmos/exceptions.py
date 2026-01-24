"""Custom exceptions for CosmosDB operations."""


class NotFoundError(Exception):
    """Raised when a requested resource is not found in CosmosDB."""

    def __init__(self, message: str = "Resource not found"):
        self.message = message
        super().__init__(self.message)


class ConflictError(Exception):
    """Raised when a resource already exists or there's a conflict."""

    def __init__(self, message: str = "Resource conflict"):
        self.message = message
        super().__init__(self.message)


class ValidationError(Exception):
    """Raised when data validation fails."""

    def __init__(self, message: str = "Validation failed"):
        self.message = message
        super().__init__(self.message)
