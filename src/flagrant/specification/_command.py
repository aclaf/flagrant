from dataclasses import dataclass
from typing import TYPE_CHECKING

from flagrant.specification.helpers import flatten_string_iterables

from ._options import OptionType

if TYPE_CHECKING:
    from ._arity import Arity


@dataclass(slots=True, frozen=True)
class PositionalSpecification:
    """Specification for a positional argument.

    Attributes:
        name: The name of the positional argument.
        arity: The arity of the positional argument.
    """

    name: str
    arity: "Arity"


@dataclass(slots=True, frozen=True)
class CommandSpecification:
    """The complete specification for a command and its entire hierarchy.

    Attributes:
        name: The canonical name of the command.
        aliases: A tuple of alternative names for the command.
        options: A mapping of `OptionSpecification` objects for the command.
        positionals: A mapping of `PositionalSpecification` objects for the command.
        subcommands: A mapping of nested `CommandSpecification` objects.
    """

    name: str
    aliases: tuple[str, ...] | None = None
    options: "tuple[OptionType, ...] | None" = None
    positionals: "tuple[PositionalSpecification, ...] | None" = None
    subcommands: "tuple[CommandSpecification, ...] | None" = None

    @property
    def all_aliases(self) -> tuple[str, ...]:
        """Get all aliases for this command (including canonical name)."""
        return (self.name, *(self.aliases or ()))

    @property
    def all_option_names(self) -> tuple[str, ...]:
        """Get all option names (long and short) for this command."""
        return flatten_string_iterables(
            *(option.all_names for option in self.options or ())
        )

    @property
    def all_subcommand_names(self) -> tuple[str, ...]:
        """Get all subcommand names including aliases."""
        if not self.subcommands:
            return ()
        return tuple(subcommand.name for subcommand in self.subcommands)
