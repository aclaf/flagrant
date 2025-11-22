"""Exceptions raised by Flagrant."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from flagrant.exceptions import ErrorContext, FlagrantError

if TYPE_CHECKING:
    from flagrant.specification._arity import Arity
    from flagrant.types import (
        ArgPosition,
        CommandName,
        CommandPath,
        FrozenArgs,
        FrozenOptionNames,
        FrozenOptionValues,
        OptionName,
        OptionValue,
        PositionalName,
    )


__all__ = [
    "AmbiguousOptionError",
    "OptionMissingValueError",
    "OptionNotRepeatableError",
    "OptionParseError",
    "OptionValueNotAllowedError",
    "ParseError",
    "PositionalMissingValueError",
    "PositionalParseError",
    "PositionalUnexpectedValueError",
    "SubcommandParseError",
    "UnknownOptionError",
    "UnknownSubcommandError",
]


@dataclass(eq=False, slots=True, kw_only=True)
class ParseError(FlagrantError):
    """Base class for errors that occur when parsing command-line arguments.

    This error indicates a problem with the user-provided arguments, such as an
    unknown option, a missing value, or incorrect syntax.

    Attributes:
        message: A description of the parsing error.
        path: The command path where the error occurred.
        args: The full list of arguments being parsed.
        position: The index in `args` where the error occurred.
        context: Optional context providing additional information about the error.
    """

    message: str = field(default="An unspecified parsing error occurred.")
    path: "CommandPath"
    args: "FrozenArgs"
    position: "ArgPosition"
    context: "ErrorContext" = field(default_factory=dict, kw_only=True)

    @property
    def command(self) -> "CommandName":
        """The command where the error occurred."""
        return self.path[-1]


@dataclass(eq=False, slots=True)
class OptionParseError(ParseError):
    """Base class for errors related to option parsing."""

    option: "OptionName"


@dataclass(eq=False, slots=True)
class OptionMissingValueError(OptionParseError):
    """Raised when an option did not receive the required number of values."""

    required: "Arity"
    received: "FrozenOptionValues | None"


@dataclass(eq=False, slots=True)
class OptionValueNotAllowedError(OptionParseError):
    """Raised when an option does not accept any values."""

    received: "OptionValue"


@dataclass(eq=False, slots=True)
class OptionNotRepeatableError(OptionParseError):
    """Raised when an option was specified more than once but is not repeatable."""

    received: "OptionValue"


@dataclass(eq=False, slots=True)
class UnknownOptionError(OptionParseError):
    """Raised when an option name is not recognized."""


@dataclass(eq=False, slots=True)
class AmbiguousOptionError(OptionParseError):
    """Raised when an abbreviated option name matches multiple options."""

    matched: "FrozenOptionNames"


@dataclass(eq=False, slots=True)
class PositionalParseError(ParseError):
    """Base class for errors related to positional argument parsing."""

    positional: "PositionalName"


@dataclass(eq=False, slots=True)
class PositionalMissingValueError(PositionalParseError):
    """Raised when a positional argument did not receive enough values."""

    required: "Arity"
    received: "FrozenOptionValues | None"


@dataclass(eq=False, slots=True)
class PositionalUnexpectedValueError(PositionalParseError):
    """Raised when a positional argument does not accept any values."""

    received: tuple[str, ...]


@dataclass(eq=False, slots=True)
class SubcommandParseError(ParseError):
    """Base class for errors related to subcommand parsing."""

    subcommand: str


@dataclass(eq=False, slots=True)
class UnknownSubcommandError(SubcommandParseError):
    """Raised when a subcommand name is not recognized."""
