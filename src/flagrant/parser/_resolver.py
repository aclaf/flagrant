from dataclasses import dataclass, field
from itertools import islice
from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple

from flagrant.specification import (
    PositionalSpecification,
    flatten_string_iterables,
    is_flag_option,
)
from flagrant.types import OptionName

if TYPE_CHECKING:
    from typing_extensions import TypeIs

    from flagrant.configuration import ParserConfiguration
    from flagrant.specification import (
        CommandSpecification,
        OptionType,
    )
    from flagrant.types import Arg, CommandName, InlineValue, PositionalName


MatchedNames = tuple[OptionName, ...]


@dataclass(frozen=True, slots=True)
class AmbiguousNames:
    given_name: OptionName
    matches: MatchedNames


def is_ambiguous_names(obj: object) -> "TypeIs[AmbiguousNames]":
    return isinstance(obj, AmbiguousNames)


@dataclass(frozen=True, slots=True)
class ResolvedOption:
    """The result of resolving an argument to an option specification."""

    given_name: OptionName
    """The name as given in the argument."""

    resolved_name: OptionName
    """The resolved name of the option."""

    spec: "OptionType"
    """The specification of the resolved option."""

    inline: "InlineValue | None" = None
    """The inline value, if any."""

    is_inner: bool = False
    """Whether this option any but the last part of a group of short options."""

    is_last: bool = False
    """Whether this option is the last in a group of short options."""


def is_resolved_option(obj: object) -> "TypeIs[ResolvedOption]":
    return isinstance(obj, ResolvedOption)


class ResolvedCommand(NamedTuple):
    """The result of resolving an argument to a subcommand specification."""

    given_name: "CommandName"
    """The name as given in the argument."""

    resolved_name: "CommandName | None"
    """The resolved name or alias of the subcommand."""

    spec: "CommandSpecification"
    """The specification of the resolved subcommand."""


def is_resolved_command(obj: object) -> "TypeIs[ResolvedCommand]":
    return isinstance(obj, ResolvedCommand)


@dataclass(slots=True)
class CommandResolver:
    """Resolves command-line arguments to options and subcommands.

    Attributes:
        spec: The command specification to resolve against.
        config: The parser configuration.
    """

    spec: "CommandSpecification"
    config: "ParserConfiguration"

    _long_option_names: tuple["OptionName", ...] = field(init=False)
    _option_names: MappingProxyType["OptionName", "OptionName"] = field(init=False)
    _options: MappingProxyType["OptionName", "OptionType"] = field(init=False)
    _positionals: MappingProxyType["PositionalName", "PositionalSpecification"] = field(
        init=False
    )
    _short_flag_names: MappingProxyType["OptionName", "OptionName"] = field(init=False)
    _subcommand_names: MappingProxyType["CommandName", "CommandName"] = field(
        init=False
    )
    _subcommands: MappingProxyType["CommandName", "CommandSpecification"] = field(
        init=False
    )

    def __post_init__(self) -> None:
        option_name_map: dict[OptionName, OptionName] = {}
        for option in self.spec.options or ():
            for name in option.all_names:
                option_key: OptionName = name
                if self.config.convert_underscores:
                    option_key = option_key.replace("_", "-")
                if not self.config.case_sensitive_options:
                    option_key = option_key.lower()
                option_name_map[option_key] = option.name
        self._option_names = MappingProxyType(option_name_map)
        self._options = MappingProxyType(
            {opt.name: opt for opt in self.spec.options or ()}
        )
        self._long_option_names = flatten_string_iterables(
            *(option.long_names for option in self.spec.options or ())
        )
        self._short_flag_names = MappingProxyType(
            {
                char: char
                for opt in self.spec.options or ()
                if is_flag_option(opt)
                for char in opt.short_names
            }
        )

        self._positionals = MappingProxyType(
            {pos.name: pos for pos in self.spec.positionals or ()}
        )

        subcommand_names: dict[CommandName, CommandName] = {}
        for cmd in self.spec.subcommands or ():
            for name in cmd.all_aliases:
                command_key: CommandName = name
                if self.config.convert_underscores:
                    command_key = command_key.replace("_", "-")
                if not self.config.case_sensitive_commands:
                    command_key = command_key.lower()
                subcommand_names[command_key] = cmd.name
        self._subcommand_names = MappingProxyType(subcommand_names)
        self._subcommands = MappingProxyType(
            {cmd.name: cmd for cmd in self.spec.subcommands or ()}
        )

    @property
    def abbreviated_commands_allowed(self) -> bool:
        """True if abbreviated command names are allowed."""
        return self.config.allow_abbreviated_commands

    @property
    def abbreviated_options_allowed(self) -> bool:
        """True if abbreviated option names are allowed."""
        return self.config.allow_abbreviated_options

    @property
    def minimum_abbreviation_length(self) -> int:
        """The minimum length for abbreviations."""
        return self.config.minimum_abbreviation_length

    @property
    def case_sensitive_commands(self) -> bool:
        """True if command name matching is case-sensitive."""
        return self.config.case_sensitive_commands

    @property
    def case_sensitive_options(self) -> bool:
        """True if option name matching is case-sensitive."""
        return self.config.case_sensitive_options

    @property
    def convert_underscores(self) -> bool:
        """True if underscores are converted to hyphens in option names."""
        return self.config.convert_underscores

    @property
    def long_prefix(self) -> str:
        """The prefix for long option names."""
        return self.config.long_name_prefix

    @property
    def short_prefix(self) -> str:
        """The prefix for short option names."""
        return self.config.short_name_prefix

    @property
    def inline_value_separator(self) -> str:
        """The separator for inline option values."""
        return self.config.inline_value_separator

    def get_option(self, name: str) -> "OptionType":
        if name in self._options:
            return self._options[name]
        if name in self._option_names:
            return self._options[self._option_names[name]]
        msg = f"Option '{name}' not found in command '{self.spec.name}'"
        raise KeyError(msg)

    def is_long_option(self, arg: str) -> bool:
        """True if the argument is a long option."""
        return arg.startswith(self.long_prefix)

    def is_short_option(self, arg: str) -> bool:
        """True if the argument is a short option or group of short options."""
        return arg.startswith(self.short_prefix) and not arg.startswith(
            self.long_prefix
        )

    def extract_inline_value(self, arg: str) -> tuple[OptionName, "InlineValue | None"]:
        """Extract the option name and inline value from an argument."""
        parts = arg.split(self.inline_value_separator, 1)
        name = parts[0]
        # Inline value will be an empty string if separator is at end
        inline = parts[1] if len(parts) == 2 else None  # noqa: PLR2004
        return name, inline

    def is_option_or_subcommand(self, arg: "Arg | None") -> bool:
        if arg is None:
            return False
        if not arg:
            return False
        if arg.startswith(self.long_prefix):
            name = arg[len(self.long_prefix) :]
            return self.resolve_option(name) is not None
        if arg.startswith(self.short_prefix):
            name = arg[len(self.short_prefix) :]
            return self.resolve_option(name) is not None
        return self.resolve_subcommand(arg) is not None

    def resolve_option(self, arg: "Arg") -> "ResolvedOption | None":
        """Resolve an argument to an option specification.

        Does not handle inline values or grouped short options.

        Args:
            arg: The argument to resolve.

        Returns:
            The resolved option, or None if not found.

            If abbreviated options are allowed, may return a tuple of matching
            option names if multiple matches are found.
        """
        if not self._options:
            return None

        if self.convert_underscores:
            arg = arg.replace("_", "-")

        key = arg if self.case_sensitive_options else arg.lower()
        name = self._option_names.get(key)
        if name:
            return ResolvedOption(arg, name, self._options[name])

        return None

    def resolve_option_with_abbreviations(
        self, arg: "Arg"
    ) -> "ResolvedOption | AmbiguousNames | None":
        """Resolve an argument to an option specification, handling abbreviations.

        Args:
            arg: The argument to resolve.
        """
        if not self._options:
            return None

        if self.convert_underscores:
            arg = arg.replace("_", "-")

        key = arg if self.case_sensitive_options else arg.lower()

        if (
            not self.abbreviated_options_allowed
            or len(key) < self.minimum_abbreviation_length
        ):
            return None

        matches_iter = (m for m in self._option_names if m.startswith(key))
        matches = list(islice(matches_iter, None))
        if len(matches) == 1:
            match = matches[0]
            opt = self._options[match]
            return ResolvedOption(arg, match, opt)
        if len(matches) > 1:
            return AmbiguousNames(arg, tuple(matches))

        return None

    def resolve_options(
        self, arg: "Arg"
    ) -> list[ResolvedOption] | AmbiguousNames | None:
        """Resolve an argument to one or more options."""
        is_long = self.is_long_option(arg)
        is_short = self.is_short_option(arg)

        if is_long:
            prefix = self.long_prefix
        elif is_short:
            prefix = self.short_prefix
        else:
            return []

        unprefixed = arg[len(prefix) :]
        name, inline = self.extract_inline_value(unprefixed)

        if is_long:
            long_option = self._resolve_long_option(name, inline)
            if is_ambiguous_names(long_option):
                return long_option
            if is_resolved_option(long_option):
                return [long_option]

        if is_short:
            return self._resolve_short_options(name, inline)

        return None

    def _resolve_long_option(
        self,
        name: "OptionName",
        inline: "InlineValue | None",
    ) -> ResolvedOption | AmbiguousNames | None:
        # First try exact match
        exact = self.resolve_option(name)
        if exact is not None:
            return ResolvedOption(
                name,
                exact.resolved_name,
                exact.spec,
                inline,
                is_inner=False,
                is_last=True,
            )

        # Then try abbreviated matching
        opt = self.resolve_option_with_abbreviations(name)
        if is_resolved_option(opt):
            return ResolvedOption(
                name,
                opt.resolved_name,
                opt.spec,
                inline,
                is_inner=False,
                is_last=True,
            )

        if is_ambiguous_names(opt):
            return opt

        inline_extra: InlineValue | None = None
        if self.config.allow_inline_values_without_separator:
            for long_name in self._long_option_names:
                if name.startswith(long_name):
                    inline_extra = name[len(long_name) :]
                    opt = self._options[self._option_names[long_name]]
                    return ResolvedOption(
                        name,
                        long_name,
                        opt,
                        self._concat_inline_value(inline, inline_extra),
                    )

        return None

    def _resolve_short_options(
        self,
        chars: str,
        inline: "InlineValue | None",
    ) -> list[ResolvedOption]:
        opts: list[ResolvedOption] = []
        for idx, char in enumerate(chars):
            result = self.resolve_option(char)
            if result is None and idx == 0:
                return []
            if result is None:
                inline = self._concat_inline_value(inline, chars[idx:])
                break
            opts.append(
                ResolvedOption(
                    char,
                    result.resolved_name,
                    result.spec,
                    inline,
                    idx < len(chars) - 1,
                    idx == len(chars) - 1,
                )
            )
        return opts

    def _concat_inline_value(
        self, value: "InlineValue | None", extra: "InlineValue | None"
    ) -> "InlineValue | None":
        """Returns a concatenated inline value from two parts.

        Example:
            >>> verbose = flag_option("verbose", "v")
            >>> output = scalar_option("output", "o")
            >>> cmd = command("run", options=(verbose, output))
            >>> resolver = CommandResolver(cmd, ParserConfiguration())
            >>> resolver.resolve_options("-oabc=def.txt")
            [
                ResolvedOption(
                    given_name="o",
                    resolved_name="output",
                    spec=output,
                    inline="abc=def.txt",
                    is_inner=False,
                    is_last=True,
                )
            ]
        """
        if value is None and extra is None:
            return None
        return self.config.inline_value_separator.join(
            v for v in (value, extra) if v is not None
        )

    def resolve_subcommand(
        self, arg: "Arg"
    ) -> "ResolvedCommand | AmbiguousNames | None":
        if not self._subcommands:
            return None

        if self.convert_underscores:
            arg = arg.replace("_", "-")

        key = arg if self.case_sensitive_commands else arg.lower()
        name = self._subcommand_names.get(key)
        if name:
            return ResolvedCommand(arg, name, self._subcommands[name])

        if (
            not self.abbreviated_commands_allowed
            or len(key) < self.minimum_abbreviation_length
        ):
            return None

        matches_iter = (m for m in self._subcommand_names if m.startswith(key))
        matches = list(islice(matches_iter, None))
        if len(matches) == 1:
            match = matches[0]
            cmd = self._subcommands[match]
            return ResolvedCommand(arg, match, cmd)
        if len(matches) > 1:
            return AmbiguousNames(arg, tuple(matches))

        return None
