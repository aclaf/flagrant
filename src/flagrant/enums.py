"""Enumerations for command-line argument parsing and completion."""

from enum import Enum


class ArgumentFileFormat(str, Enum):
    """Specifies how the content of an argument file should be interpreted."""

    LINE = "line"
    """Each line in the file is treated as a single, separate argument. (Default)"""

    SHELL = "shell"
    """The file content is parsed using shell-like quoting and escaping rules."""


class UngroupedPositionalStrategy(str, Enum):
    """Defines how ungrouped positional arguments are handled."""

    IGNORE = "ignore"
    """Ignores any ungrouped positional arguments."""

    COLLECT = "collect"
    """Collects ungrouped positional arguments into a special list."""

    ERROR = "error"
    """
    Raises an error if ungrouped positional arguments are encountered.
    """


DEFAULT_UNGROUPED_POSITIONAL_STRATEGY: "UngroupedPositionalStrategy" = (
    UngroupedPositionalStrategy.IGNORE
)
