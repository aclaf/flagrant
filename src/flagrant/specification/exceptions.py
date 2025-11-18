"""Exceptions raised by Flagrant."""

from typing import TYPE_CHECKING

from flagrant.exceptions import ErrorContext, FlagrantError

if TYPE_CHECKING:
    from flagrant.types import (
        CommandName,
        OptionName,
    )


__all__ = [
    "CommandSpecificationError",
    "OptionSpecificationError",
    "SpecificationError",
]


class SpecificationError(FlagrantError):
    """Raised for an invalid CommandSpecification.

    This error indicates a problem with the structure or definition of the command
    specification itself, such as duplicate names or conflicting rules, detected
    before parsing begins.
    """


class OptionSpecificationError(SpecificationError):
    """Raised for an invalid OptionSpecification.

    This error indicates a problem with the structure or definition of an option
    specification itself, such as duplicate names or conflicting rules, detected
    before parsing begins.
    """

    def __init__(
        self,
        option_name: "OptionName",
        message: str,
        context: "ErrorContext | None" = None,
    ) -> None:
        """Initialize OptionSpecificationError.

        Args:
            option_name: The name of the option with the specification error.
            message: Description of the specification error.
            context: Optional context providing additional information about the error.
        """
        full_message = f"Option '{option_name}' is invalid. {message}"
        super().__init__(full_message, context)


class CommandSpecificationError(SpecificationError):
    """Raised for an invalid CommandSpecification.

    This error indicates a problem with the structure or definition of a command
    specification itself, such as duplicate names or conflicting rules, detected
    before parsing begins.
    """

    def __init__(
        self,
        command_name: "CommandName",
        message: str,
        context: "ErrorContext | None" = None,
    ) -> None:
        """Initialize CommandSpecificationError.

        Args:
            command_name: The name of the command with the specification error.
            message: Description of the specification error.
            context: Optional context providing additional information about the error.
        """
        full_message = f"Command '{command_name}' is invalid. {message}"
        super().__init__(full_message, context)
