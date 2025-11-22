from dataclasses import dataclass
from functools import cached_property
from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple

from flagrant.validations import (
    validate_command_aliases,
    validate_command_positionals,
    validate_parameter_names,
    validate_subcommand_names,
)

from ._options import FlagOptionSpecification

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from flagrant._arity import Arity
    from flagrant.types import (
        FrozenCommandNames,
        FrozenCommandNameSet,
        FrozenOptionNames,
        FrozenOptionNameSet,
        OptionName,
    )

    from ._options import (
        OptionSpecificationType,
    )


class OptionResult(NamedTuple):
    """Result of looking up an option by name.

    Attributes:
        matched_name: The actual name matched.
        specification: The specification for the matched option.
    """

    matched_name: "OptionName"
    specification: "OptionSpecificationType"


@dataclass(frozen=True)
class CommandSpecification:
    """The complete specification for a command and its entire hierarchy.

    Attributes:
        name: The canonical name of the command.
        aliases: A tuple of alternative names for the command.
        options: A tuple of `OptionSpecification` objects for the command.
        positionals: A tuple of `PositionalSpecification` objects for the command.
        subcommands: A tuple of nested `CommandSpecification` objects.
    """

    name: str
    aliases: tuple[str, ...] | None = None
    options: "Mapping[str, OptionSpecificationType] | None" = None
    positionals: "Mapping[str, Arity] | None" = None
    subcommands: "Mapping[str, CommandSpecification] | None" = None

    def __init__(
        self,
        name: str,
        *,
        aliases: "Iterable[str] | None" = None,
        options: "Mapping[str, OptionSpecificationType] | None" = None,
        positionals: "Mapping[str, Arity] | None" = None,
        subcommands: "Mapping[str, CommandSpecification] | None" = None,
    ) -> None:
        """Initialize a new `CommandSpecification`.

        Args:
            name: The canonical name for the command (e.g., "git").
            aliases: An iterable of alternative names (e.g., ["g"]).
            options: A mapping of option specifications for this command.
            positionals: A mapping of positional specifications for this
                command.
            subcommands: A mapping of nested subcommand specifications.
        """
        object.__setattr__(self, "name", name)

        if aliases:
            validate_command_aliases(name, aliases)
        object.__setattr__(self, "aliases", tuple(aliases or ()))

        parameter_names: list[str] = []

        if options is not None:
            object.__setattr__(self, "options", MappingProxyType(options))
            parameter_names.extend(options.keys())

        if positionals is not None:
            validate_command_positionals(name, positionals)
            object.__setattr__(self, "positionals", MappingProxyType(positionals))
            parameter_names.extend(positionals.keys())

        validate_parameter_names(name, parameter_names)

        if subcommands:
            validate_subcommand_names(
                name, [names for cmd in subcommands.values() for names in cmd.all_names]
            )
            object.__setattr__(self, "subcommands", MappingProxyType(subcommands))

    @cached_property
    def all_names(self) -> "FrozenCommandNameSet":
        """Get all names for this command (canonical + aliases)."""
        all_names = {self.name}
        if self.aliases:
            all_names.update(self.aliases)
        return frozenset(all_names)

    @cached_property
    def all_option_names(self) -> "FrozenOptionNameSet":
        """Get all option names (long and short) for this command."""
        if not self.options:
            return frozenset()
        return frozenset(self.options.keys())

    @cached_property
    def all_subcommand_names(self) -> "FrozenCommandNames":
        """Get all subcommand names including aliases."""
        if not self.subcommands:
            return ()
        return tuple(self.subcommands.keys())

    @cached_property
    def long_option_names(self) -> "FrozenOptionNames":
        """Get all long option names for this command."""
        if not self.options:
            return ()
        long_names: list[OptionName] = []
        for option in self.options.values():
            long_names.extend(option.all_long_names)
        return tuple(long_names)

    @cached_property
    def option_name_mapping(self) -> MappingProxyType[str, str]:
        """Map all option names (case-sensitive) to canonical names."""
        if not self.options:
            return MappingProxyType({})
        return MappingProxyType(self._build_option_name_map(case_sensitive=True))

    @cached_property
    def option_name_mapping_ci(self) -> MappingProxyType[str, str]:
        """Map all option names (case-insensitive) to canonical names."""
        if not self.options:
            return MappingProxyType({})
        return MappingProxyType(self._build_option_name_map(case_sensitive=False))

    @cached_property
    def short_flag_name_mapping(self) -> MappingProxyType[str, str]:
        """Map all short flag names (case-sensitive) to canonical names."""
        if not self.options:
            return MappingProxyType({})
        return MappingProxyType(self._build_short_flag_map(case_sensitive=True))

    @cached_property
    def short_flag_name_mapping_ci(self) -> MappingProxyType[str, str]:
        """Map all short flag names (case-insensitive) to canonical names."""
        if not self.options:
            return MappingProxyType({})
        return MappingProxyType(self._build_short_flag_map(case_sensitive=False))

    @cached_property
    def subcommand_name_mapping(self) -> MappingProxyType[str, str]:
        """Map all subcommand names (case-sensitive) to canonical names."""
        if not self.subcommands:
            return MappingProxyType({})
        return MappingProxyType(self._build_subcommand_map(case_sensitive=True))

    @cached_property
    def subcommand_name_mapping_ci(self) -> MappingProxyType[str, str]:
        """Map all subcommand names (case-insensitive) to canonical names."""
        if not self.subcommands:
            return MappingProxyType({})
        return MappingProxyType(self._build_subcommand_map(case_sensitive=False))

    def get_option(self, name: str) -> "OptionSpecificationType":
        """Get option specification by canonical name.

        Args:
            name: The canonical name of the option.

        Returns:
            The `OptionSpecification` for the given name.

        Raises:
            KeyError: If no option with the given name exists.
        """
        if not self.options:
            msg = f"No options defined for command '{self.name}'."
            raise KeyError(msg)
        return self.options[name]

    def _build_option_name_map(self, *, case_sensitive: bool) -> dict[str, str]:
        """Build mapping of all option names to canonical names.

        Args:
            case_sensitive: Whether to preserve case in mapping keys.

        Returns:
            Dictionary mapping option names to canonical names.
        """
        name_map: dict[str, str] = {}
        if not self.options:
            return name_map

        for option in self.options.values():
            for name in option.all_names:
                key = name if case_sensitive else name.lower()
                name_map[key] = option.name

        return name_map

    def _build_short_flag_map(self, *, case_sensitive: bool) -> dict[str, str]:
        """Build mapping of short flag names to canonical option names.

        Args:
            case_sensitive: Whether to preserve case in mapping keys.

        Returns:
            Dictionary mapping short flags to canonical option names.
        """
        flag_map: dict[str, str] = {}
        if not self.options:
            return flag_map

        for option in self.options.values():
            if isinstance(option, FlagOptionSpecification):
                for short_name in option.all_short_names:
                    key = short_name if case_sensitive else short_name.lower()
                    flag_map[key] = option.name

        return flag_map

    def _build_subcommand_map(self, *, case_sensitive: bool) -> dict[str, str]:
        """Build mapping of all subcommand names to canonical names.

        Args:
            case_sensitive: Whether to preserve case in mapping keys.

        Returns:
            Dictionary mapping subcommand names to canonical names.
        """
        name_map: dict[str, str] = {}
        if not self.subcommands:
            return name_map

        for subcommand in self.subcommands.values():
            for name in subcommand.all_names:
                key = name if case_sensitive else name.lower()
                name_map[key] = subcommand.name

        return name_map
