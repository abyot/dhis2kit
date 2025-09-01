"""Typed exception hierarchy for dhis2kit."""


class Dhis2Error(Exception):
    """Base error for dhis2kit."""


class AuthenticationError(Dhis2Error):
    """Raised for 401/403 responses (authentication/authorization errors)."""


class NotFoundError(Dhis2Error):
    """Raised for 404 responses (resource not found)."""


class ServerError(Dhis2Error):
    """Raised for 5xx responses and unexpected JSON decoding errors."""


class ValidationError(Dhis2Error):
    """Raised when user payload validation fails client-side."""
