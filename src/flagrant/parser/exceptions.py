"""Exceptions raised by Flagrant."""

from typing import TYPE_CHECKING

from flagrant.exceptions import ErrorContext, FlagrantError

if TYPE_CHECKING:
    from flagrant.specification._arity import Arity
    from flagrant.types import (
        Arg,
        ArgList,
        ArgPosition,
        CommandName,
        CommandPath,
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


class ParseError(FlagrantError):
    """Base class for errors that occur when parsing command-line arguments.

    This error indicates a problem with the user-provided arguments, such as an
    unknown option, a missing value, or incorrect syntax.
    """

    def __init__(
        self,
        message: str,
        path: "CommandPath",
        args: "ArgList",
        position: "ArgPosition",
        context: "ErrorContext | None" = None,
    ) -> None:
        """Initialize a ParseError.

        Args:
            message: The error message.
            path: The command path where the error occurred.
            args: The full list of arguments being parsed.
            position: The index in `args` where the error occurred.
            context: Optional context providing additional information about the error.
        """
        super().__init__(message, context)
        self.path: CommandPath = path
        self.args: ArgList = args
        self.position: ArgPosition = position

    @property
    def command(self) -> "CommandName":
        """The command where the error occurred."""
        return self.path[-1]


class OptionParseError(ParseError):
    """Base class for errors related to option parsing."""

    def __init__(  # noqa: PLR0913
        self,
        message: str,
        option: "OptionName",
        path: "CommandPath",
        args: "ArgList",
        position: "ArgPosition",
        context: "ErrorContext | None" = None,
    ) -> None:
        """Initialize an OptionParseError.

        Args:
            message: The error message.
            option: The name of the option related to the error.
            path: The command path where the error occurred.
            args: The full list of arguments being parsed.
            position: The index in `args` where the error occurred.
            context: Optional context providing additional information about the error.
        """
        super().__init__(message, path, args, position, context)
        self.option: OptionName = option


class OptionMissingValueError(OptionParseError):
    """Raised when an option did not receive the required number of values."""

    def __init__(  # noqa: PLR0913
        self,
        option: "OptionName",
        required: "Arity",
        received: "Arg | ArgList | None",
        path: "CommandPath",
        args: "ArgList",
        position: "ArgPosition",
        context: "ErrorContext | None" = None,
    ) -> None:
        """Initialize an OptionMissingValueError.

        Args:
            option: The name of the option related to the error.
            required: The number of values that were required.
            received: The values that were actually provided to the option.
            path: The command path where the error occurred.
            args: The full list of arguments being parsed.
            position: The index in `args` where the error occurred.
            context: Optional context providing additional information about the error.
        """
        message = (
            f"Option '{option}' is missing required value(s). "
            f"Expected {required}, received "
            f"{'none' if received is None else len(received)}."
        )
        super().__init__(message, option, path, args, position, context)
        self.required: Arity = required
        self.received: Arg | ArgList | None = received


class OptionValueNotAllowedError(OptionParseError):
    """Raised when an option does not accept any values."""

    def __init__(  # noqa: PLR0913
        self,
        option: "OptionName",
        received: "OptionValue",
        path: "CommandPath",
        args: "ArgList",
        position: "ArgPosition",
        context: "ErrorContext | None" = None,
    ) -> None:
        """Initialize an OptionValueNotAllowedError.

        Args:
            option: The name of the option related to the error.
            received: The value(s) that were provided to the option.
            path: The command path where the error occurred.
            args: The full list of arguments being parsed.
            position: The index in `args` where the error occurred.
            context: Optional context providing additional information about the error.
        """
        message = (
            f"Option '{option}' does not accept any values, but received {received}."
        )
        super().__init__(message, option, path, args, position, context)
        self.received: OptionValue = received


class OptionNotRepeatableError(OptionParseError):
    """Raised when an option was specified more than once but is not repeatable."""

    def __init__(  # noqa: PLR0913
        self,
        option: "OptionName",
        current: "OptionValue",
        received: "OptionValue",
        path: "CommandPath",
        args: "ArgList",
        position: "ArgPosition",
        context: "ErrorContext | None" = None,
    ) -> None:
        """Initialize an OptionNotRepeatableError.

        Args:
            option: The name of the option related to the error.
            received: The value(s) that were provided to the option.
            path: The command path where the error occurred.
            args: The full list of arguments being parsed.
            position: The index in `args` where the error occurred.
            context: Optional context providing additional information about the error.
        """
        message = (
            f"Option '{option}' does not accept any values, but received {received}."
        )
        super().__init__(message, option, path, args, position, context)
        self.current: OptionValue = current
        self.received: OptionValue = received


class UnknownOptionError(OptionParseError):
    """Raised when an option name is not recognized."""

    def __init__(
        self,
        option: "OptionName",
        path: "CommandPath",
        args: "ArgList",
        position: "ArgPosition",
        context: "ErrorContext | None" = None,
    ) -> None:
        """Initialize an UnknownOptionError.

        Args:
            option: The name of the unrecognized option.
            path: The command path where the error occurred.
            args: The full list of arguments being parsed.
            position: The index in `args` where the error occurred.
            context: Optional context providing additional information about the error.
        """
        message = f"Unknown option: {option}"
        super().__init__(message, option, path, args, position, context)


class AmbiguousOptionError(OptionParseError):
    """Raised when an abbreviated option name matches multiple options."""

    def __init__(  # noqa: PLR0913
        self,
        option: "OptionName",
        matched: "FrozenOptionNames",
        path: "CommandPath",
        args: "ArgList",
        position: "ArgPosition",
        context: "ErrorContext | None" = None,
    ) -> None:
        """Initialize an AmbiguousOptionError.

        Args:
            option: The abbreviated option name that is ambiguous.
            matched: The set of option names that match the abbreviation.
            path: The command path where the error occurred.
            args: The full list of arguments being parsed.
            position: The index in `args` where the error occurred.
            context: Optional context providing additional information about the error.
        """
        message = (
            f"Option '{option}' is ambiguous and matches multiple options: {matched}."
        )
        super().__init__(message, option, path, args, position, context)
        self.matched: FrozenOptionNames = matched


class PositionalParseError(ParseError):
    """Base class for errors related to positional argument parsing."""

    def __init__(  # noqa: PLR0913
        self,
        message: str,
        positional: "PositionalName",
        path: "CommandPath",
        args: "ArgList",
        position: "ArgPosition",
        context: "ErrorContext | None" = None,
    ) -> None:
        """Initialize a PositionalParseError.

        Args:
            message: The error message.
            positional: The name of the positional argument related to the error.
            path: The command path where the error occurred.
            args: The full list of arguments being parsed.
            position: The index in `args` where the error occurred.
            context: Optional context providing additional information about the error.
        """
        super().__init__(message, path, args, position, context)
        self.positional: PositionalName = positional


class PositionalMissingValueError(PositionalParseError):
    """Raised when a positional argument did not receive enough values."""

    def __init__(  # noqa: PLR0913
        self,
        message: str,
        positional: "PositionalName",
        required: "Arity",
        received: "FrozenOptionValues | None",
        path: "CommandPath",
        args: "ArgList",
        position: "ArgPosition",
        context: "ErrorContext | None" = None,
    ) -> None:
        """Initialize a PositionalMissingValueError.

        Args:
            message: The error message.
            positional: The name of the positional argument related to the error.
            required: The number of values that were required.
            received: The values that were actually provided to the positional argument.
            path: The command path where the error occurred.
            args: The full list of arguments being parsed.
            position: The index in `args` where the error occurred.
            context: Optional context providing additional information about the error.
        """
        super().__init__(message, positional, path, args, position, context)
        self.required: Arity = required
        self.received: FrozenOptionValues | None = received


class PositionalUnexpectedValueError(PositionalParseError):
    """Raised when a positional argument does not accept any values."""

    def __init__(  # noqa: PLR0913
        self,
        positional: "PositionalName",
        received: "OptionValue",
        path: "CommandPath",
        args: "ArgList",
        position: "ArgPosition",
        context: "ErrorContext | None" = None,
    ) -> None:
        """Initialize a PositionalUnexpectedValueError.

        Args:
            positional: The name of the positional argument related to the error.
            received: The value(s) that were provided to the positional argument.
            path: The command path where the error occurred.
            args: The full list of arguments being parsed.
            position: The index in `args` where the error occurred.
            context: Optional context providing additional information about the error.
        """
        message = (
            f"Positional argument '{positional}' does not accept any values, "
            f"but received {received}."
        )
        super().__init__(message, positional, path, args, position, context)
        self.received: OptionValue = received


class SubcommandParseError(ParseError):
    """Base class for errors related to subcommand parsing."""

    def __init__(  # noqa: PLR0913
        self,
        message: str,
        subcommand: "str",
        path: "CommandPath",
        args: "ArgList",
        position: "ArgPosition",
        context: "ErrorContext | None" = None,
    ) -> None:
        """Initialize a SubcommandParseError.

        Args:
            message: The error message.
            subcommand: The name of the subcommand related to the error.
            path: The command path where the error occurred.
            args: The full list of arguments being parsed.
            position: The index in `args` where the error occurred.
            context: Optional context providing additional information about the error.
        """
        super().__init__(message, path, args, position, context)
        self.subcommand: CommandName = subcommand


class AmbiguousSubcommandError(SubcommandParseError):
    """Raised when an abbreviated subcommand name matches multiple subcommands."""

    def __init__(  # noqa: PLR0913
        self,
        subcommand: "str",
        matched: tuple["CommandName", ...],
        path: "CommandPath",
        args: "ArgList",
        position: "ArgPosition",
        context: "ErrorContext | None" = None,
    ) -> None:
        """Initialize an AmbiguousSubcommandError.

        Args:
            subcommand: The abbreviated subcommand name that is ambiguous.
            matched: The set of subcommand names that match the abbreviation.
            path: The command path where the error occurred.
            args: The full list of arguments being parsed.
            position: The index in `args` where the error occurred.
            context: Optional context providing additional information about the error.
        """
        message = (
            f"Subcommand '{subcommand}' is ambiguous and matches multiple "
            f"subcommands: {matched}."
        )
        super().__init__(message, subcommand, path, args, position, context)
        self.matched: tuple[CommandName, ...] = matched


class UnknownSubcommandError(SubcommandParseError):
    """Raised when a subcommand name is not recognized."""

    def __init__(
        self,
        subcommand: "str",
        path: "CommandPath",
        args: "ArgList",
        position: "ArgPosition",
        context: "ErrorContext | None" = None,
    ) -> None:
        """Initialize an UnknownSubcommandError.

        Args:
            subcommand: The name of the unrecognized subcommand.
            path: The command path where the error occurred.
            args: The full list of arguments being parsed.
            position: The index in `args` where the error occurred.
            context: Optional context providing additional information about the error.
        """
        message = f"Unknown subcommand: {subcommand}"
        super().__init__(message, subcommand, path, args, position, context)
