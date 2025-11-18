"""Exceptions raised by Flagrant."""

__all__ = [
    "CompletionConfigurationError",
    "CompletionError",
    "ConfigurationError",
    "FlagrantError",
    "ParseError",
    "ParserConfigurationError",
    "SpecificationError",
]


class FlagrantError(Exception):
    """Base class for all Flagrant-related errors."""


class ConfigurationError(FlagrantError):
    """Raised when there is an error in configuration settings."""


class CompletionConfigurationError(ConfigurationError):
    """Raised when there is an error in the completion configuration."""


class ParserConfigurationError(ConfigurationError):
    """Raised when there is an error in the parser configuration."""


class SpecificationError(FlagrantError):
    """Raised when there is an error in a command or parameter specification."""


class CompletionError(FlagrantError):
    """Base class for all completion-related errors."""


class ParseError(FlagrantError):
    """Base class for all parsing-related errors."""
