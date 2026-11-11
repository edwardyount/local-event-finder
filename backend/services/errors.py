class ServiceError(Exception):
    """Raised by the business layer; app.py turns it into a JSON response."""

    def __init__(self, message, status=400, errors=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.errors = errors or {}   # field-specific messages, e.g. {"email": "..."}
