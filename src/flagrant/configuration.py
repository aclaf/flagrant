"""Common configuration settings."""

from dataclasses import dataclass

__all__ = ["Configuration"]


@dataclass(slots=True, frozen=True)
class Configuration:
    """Common configuration settings."""
