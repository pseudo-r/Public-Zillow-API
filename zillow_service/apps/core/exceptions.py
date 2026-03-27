"""Core exceptions for the Zillow service."""


class ZillowClientError(Exception):
    """Base exception for Zillow client errors."""


class ZillowNotFoundError(ZillowClientError):
    """Raised when a Zillow resource is not found (404)."""


class ZillowRateLimitError(ZillowClientError):
    """Raised when Zillow rate limits or blocks the request (403/429)."""
