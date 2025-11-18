"""Exceptions raised by Flagrant."""

from pathlib import Path

ErrorContextValue = (
    str
    | int
    | float
    | bool
    | None
    | Path
    | list["ErrorContextValue"]
    | dict[str, "ErrorContextValue"]
)
ErrorContext = dict[str, ErrorContextValue]

__all__ = [
    "ConfigurationError",
    "ErrorContext",
    "ErrorContextValue",
    "FlagrantError",
]


class FlagrantError(Exception):
    """Base class for all errors raised by the Flagrant library."""

    def __init__(self, message: str, context: ErrorContext | None = None):
        """Initialize a FlagrantError.

        Args:
            message: The error message.
            context: Optional context providing additional information about the error.
        """
        super().__init__(message)
        self.context: ErrorContext = context or {}


class ConfigurationError(FlagrantError):
    """Base class for errors related to invalid configuration."""
