"""Validations for specifications and parsing that can be used by downstream packages."""  # noqa: E501

from typing import TYPE_CHECKING

from flagrant.constraints import (
    COMMAND_NAME_PATTERN,
    LONG_NAME_PATTERN,
    MINIMUM_LONG_OPTION_NAME_LENGTH,
    NEGATIVE_PREFIX_PATTERN,
    PARAMETER_NAME_PATTERN,
    SHORT_NAME_PATTERN,
)
from flagrant.enums import ValueAccumulationMode
from flagrant.exceptions import (
    CommandSpecificationError,
    OptionSpecificationError,
)
from flagrant.helpers import find_conflicts, find_duplicates, negative_prefix_names

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from flagrant._arity import Arity


def validate_command_alias(command_name: str, alias: str) -> None:
    """Validate a command alias.

    Args:
        command_name: The name of the command the alias belongs to.
        alias: The command alias to validate.

    Raises:
        CommandSpecificationError: If the alias is invalid.
    """
    if not alias:
        msg = f"Alias '{alias}' is invalid. Must not be empty."
        raise CommandSpecificationError(command_name, msg)

    if not COMMAND_NAME_PATTERN.match(alias):
        msg = (
            f"Alias '{alias}' is invalid."
            f" Must match pattern: {COMMAND_NAME_PATTERN.pattern}"
        )
        raise CommandSpecificationError(command_name, msg)


def validate_command_aliases(
    command_name: str,
    aliases: "Iterable[str]",
    *,
    case_sensitive: bool = True,
) -> None:
    """Validate multiple command aliases.

    See [validate_command_alias][flagrant.validations.validate_command_alias].

    Args:
        command_name: The name of the command the aliases belong to.
        aliases: An iterable of command aliases to validate.
        case_sensitive: Whether command names are case sensitive.

    Raises:
        CommandSpecificationError: If any alias is invalid.
    """
    for alias in aliases:
        validate_command_alias(command_name, alias)

    if not case_sensitive:
        duplicates = find_duplicates(aliases, case_sensitive=False)
        if duplicates:
            msg = f"Duplicate command aliases found (case insensitive): {duplicates}"
            raise CommandSpecificationError(command_name, msg)


def validate_command_name(name: str) -> None:
    """Validate a command name.

    Args:
        name: The command name to validate.

    Raises:
        ParameterSpecificationError: If the name is invalid.
    """
    if not name:
        msg = "Name must not be empty."
        raise CommandSpecificationError(name, msg)

    if not COMMAND_NAME_PATTERN.match(name):
        msg = (
            f"Name '{name}' is invalid."
            f" Must match pattern: {COMMAND_NAME_PATTERN.pattern}"
        )
        raise CommandSpecificationError(name, msg)


def validate_command_options(
    command_name: str, option_names: "Iterable[str]", *, case_sensitive: bool = True
) -> None:
    """Validate option specifications.

    Args:
        command_name: The name of the command to which the options belong.
        option_names: A sequence of option names to validate.
        case_sensitive: Whether option names are case sensitive.

    Raises:
        CommandSpecificationError: If any option specification is invalid.
    """
    duplicates = find_duplicates(option_names, case_sensitive=case_sensitive)
    if duplicates:
        msg = (
            f"Duplicate option names found"
            f"{'' if case_sensitive else ' (case insensitive)'}: {duplicates}"
        )
        raise CommandSpecificationError(command_name, msg)


def validate_command_positionals(
    command_name: str, positionals: "Mapping[str, Arity]"
) -> None:
    """Validate positional specifications.

    Args:
        command_name: The name of the command to which the positionals belong.
        positionals: A sequence of positional specifications to validate.

    Raises:
        CommandSpecificationError: If any positional specification is invalid.
    """
    if (
        len([spec for spec in positionals.values() if spec.accepts_unbounded_values])
        > 1
    ):
        msg = f"Multiple positionals accept unbounded values: {positionals}"
        raise CommandSpecificationError(command_name, msg)


def validate_subcommand_names(
    command_name: str,
    subcommand_names: "Iterable[str]",
    *,
    case_sensitive: bool = True,
) -> None:
    """Validate multiple subcommand names.

    Args:
        command_name: The name of the command to which the subcommands belong.
        subcommand_names: An iterable of subcommand names to validate.
        case_sensitive: Whether command names are case sensitive.

    Raises:
        CommandSpecificationError: If any name is invalid.
    """
    duplicates = find_duplicates(subcommand_names, case_sensitive=case_sensitive)
    if duplicates:
        msg = (
            f"Duplicate subcommand names found"
            f"{'' if case_sensitive else ' (case insensitive)'}: {duplicates}"
        )
        raise CommandSpecificationError(command_name, msg)


def validate_long_option_name(
    name: str,
) -> None:
    """Validate a long option name.

    Args:
        name: The long option name to validate.
        case_sensitive: Whether option names are case sensitive.

    Raises:
        OptionSpecificationError: If the name is invalid.
    """
    if len(name) < MINIMUM_LONG_OPTION_NAME_LENGTH:
        msg = f"Long name '{name}' is invalid. Must be at least 2 characters."
        raise OptionSpecificationError(name, msg)

    if not LONG_NAME_PATTERN.match(name):
        msg = (
            f"Long name '{name}' is invalid."
            f" Must match pattern: {LONG_NAME_PATTERN.pattern}"
        )
        raise OptionSpecificationError(name, msg)


def validate_long_option_names(
    option_name: str,
    names: "Iterable[str]",
    *,
    case_sensitive: bool = True,
) -> None:
    """Validate multiple long option names.

    See [validate_long_option_name][flagrant.validations.validate_long_option_name].

    Args:
        option_name: The name of the option the long names belong to.
        names: An iterable of long option names to validate.
        case_sensitive: Whether option names are case sensitive.

    Raises:
        OptionSpecificationError: If any name is invalid.
    """
    for name in names:
        validate_long_option_name(name)

    if not case_sensitive:
        duplicates = find_duplicates(names, case_sensitive=False)
        if duplicates:
            msg = f"Duplicate long option names found (case insensitive): {duplicates}"
            raise OptionSpecificationError(option_name, msg)


def validate_negative_long_option_name(option_name: str, name: str) -> None:
    """Validate a negative long option name.

    Args:
        option_name: The name of the option the negative long name belongs to.
        name: The name to validate.

    Raises:
        OptionSpecificationError: If the name is invalid.
    """
    if len(name) < MINIMUM_LONG_OPTION_NAME_LENGTH:
        msg = f"Negative long name '{name}' is invalid. Must be at least 2 characters."
        raise OptionSpecificationError(option_name, msg)

    if not LONG_NAME_PATTERN.match(name):
        msg = (
            f"Negative long name '{name}' is invalid."
            f" Must match pattern: {LONG_NAME_PATTERN.pattern}"
        )
        raise OptionSpecificationError(option_name, msg)


def validate_negative_long_option_names(
    option_name: str,
    names: "Iterable[str]",
    positive_long_names: "Iterable[str]",
    *,
    case_sensitive: bool = True,
) -> None:
    """Validate multiple negative long option names.

    See
    [validate_negative_long_option_name][flagrant.validations.validate_negative_long_option_name].

    Args:
        option_name: The name of the option the negative long names belong to.
        names: An iterable of negative long option names to validate.
        positive_long_names: An iterable of the option's positive long names.
        case_sensitive: Whether option names are case sensitive.

    Raises:
        OptionSpecificationError: If any name is invalid.
    """
    for negative_name in names:
        validate_negative_long_option_name(option_name, negative_name)

    if not case_sensitive:
        duplicates = find_duplicates(names, case_sensitive=False)
        if duplicates:
            msg = (
                f"Duplicate negative long option names found (case insensitive):"
                f" {duplicates}"
            )
            raise OptionSpecificationError(option_name, msg)

    if positive_name_conflicts := find_conflicts(
        names,
        positive_long_names,
        case_sensitive=case_sensitive,
    ):
        msg = (
            f"Negative long names conflict with long names"
            f"{'(case insensitive)' if not case_sensitive else ''}:"
            f" {positive_name_conflicts}"
        )
        raise OptionSpecificationError(option_name, msg)


def validate_negative_prefix(
    option_name: str,
    negative_prefix: str,
) -> None:
    """Validate a negative prefix.

    Args:
        option_name: The name of the option the prefix belongs to.
        negative_prefix: The negative prefix to validate.

    Raises:
        OptionSpecificationError: If the prefix is invalid.
    """
    if len(negative_prefix) < 1:
        msg = (
            f"Negative prefix '{negative_prefix}' is invalid."
            " Must be at least 1 character."
        )
        raise OptionSpecificationError(option_name, msg)

    if not NEGATIVE_PREFIX_PATTERN.match(negative_prefix):
        msg = (
            f"Negative prefix '{negative_prefix}' is invalid."
            f" Must match pattern: {NEGATIVE_PREFIX_PATTERN.pattern}"
        )
        raise OptionSpecificationError(option_name, msg)


def validate_negative_prefixes(
    option_name: str,
    negative_prefixes: "Iterable[str]",
    negative_long_names: "Iterable[str]",
    positive_long_names: "Iterable[str]",
    *,
    case_sensitive: bool = True,
) -> None:
    """Validate multiple negative prefixes.

    See [validate_negative_prefix][flagrant.validations.validate_negative_prefix].

    Args:
        option_name: The name of the option the prefixes belong to.
        negative_prefixes: An iterable of negative prefixes to validate.
        negative_long_names: An iterable of the option's negative long names.
        positive_long_names: An iterable of the option's positive long names.
        case_sensitive: Whether option names are case sensitive.

    Raises:
        OptionSpecificationError: If any prefix is invalid.
    """
    for negative_prefix in negative_prefixes:
        validate_negative_prefix(option_name, negative_prefix)

    if not case_sensitive:
        duplicates = find_duplicates(negative_prefixes, case_sensitive=False)
        if duplicates:
            msg = f"Duplicate negative prefixes found (case insensitive): {duplicates}"
            raise OptionSpecificationError(option_name, msg)

    prefix_names = negative_prefix_names(positive_long_names, negative_prefixes)
    if negative_long_name_conflicts := find_conflicts(
        negative_long_names,
        prefix_names,
        case_sensitive=case_sensitive,
    ):
        msg = (
            f"Negative prefix names conflict with negative long names"
            f"{'(case insensitive)' if not case_sensitive else ''}:"
            f" {negative_long_name_conflicts}"
        )
        raise OptionSpecificationError(option_name, msg)

    if positive_long_name_conflicts := find_conflicts(
        positive_long_names,
        prefix_names,
        case_sensitive=case_sensitive,
    ):
        msg = (
            f"Negative prefix names conflict with long names"
            f"{'(case insensitive)' if not case_sensitive else ''}:"
            f" {positive_long_name_conflicts}"
        )
        raise OptionSpecificationError(option_name, msg)


def validate_negative_short_option_name(
    option_name: str,
    name: str,
) -> None:
    """Validate a negative short name.

    Args:
        option_name: The name of the option the negative short name belongs to.
        name: The negative short name to validate.

    Raises:
        OptionSpecificationError: If the negative short name is invalid.
    """
    if len(name) != 1:
        msg = f"negative short name '{name}' is invalid. Must be 1 character"
        raise OptionSpecificationError(option_name, msg)

    if not SHORT_NAME_PATTERN.match(name):
        msg = (
            f"negative short name '{name}' is invalid."
            f" Must match pattern: {SHORT_NAME_PATTERN.pattern}"
        )
        raise OptionSpecificationError(option_name, msg)


def validate_negative_short_option_names(
    option_name: str,
    names: "Iterable[str]",
    positive_short_names: "Iterable[str]",
    *,
    case_sensitive: bool = True,
) -> None:
    """Validate multiple negative short names.

    See [validate_negative_short_name][flagrant.validations.validate_negative_short_name].

    Args:
        option_name: The name of the option the negative short names belong to.
        names: An iterable of negative short names to validate.
        positive_short_names: An iterable of the option's positive short names.
        case_sensitive: Whether option names are case sensitive.

    Raises:
        OptionSpecificationError: If any negative short name is invalid.
    """  # noqa: E501
    for name in names:
        validate_negative_short_option_name(option_name, name)

    if not case_sensitive:
        duplicates = find_duplicates(names, case_sensitive=False)
        if duplicates:
            msg = (
                f"Duplicate negative short option names found (case insensitive):"
                f" {duplicates}"
            )
            raise OptionSpecificationError(option_name, msg)

    if conflicts := find_conflicts(
        names,
        positive_short_names,
        case_sensitive=case_sensitive,
    ):
        msg = (
            f"Negative short option names conflict with positive short option names"
            f"{'(case insensitive)' if not case_sensitive else ''}: {conflicts}"
        )
        raise OptionSpecificationError(option_name, msg)


def validate_parameter_name(name: str) -> None:
    """Validate a parameter name.

    Args:
        name: The parameter name to validate.

    Raises:
        ParameterSpecificationError: If the name is invalid.
    """
    if not name or not PARAMETER_NAME_PATTERN.match(name):
        msg = f"Must match pattern: {PARAMETER_NAME_PATTERN.pattern}"
        raise OptionSpecificationError(name, msg)


def validate_parameter_names(
    command_name: str,
    names: "Iterable[str]",
    *,
    case_sensitive: bool = True,
) -> None:
    """Validate multiple parameter names.

    See [validate_parameter_name][flagrant.validations.validate_parameter_name].

    Args:
        command_name: The name of the command to which the parameters belong.
        names: An iterable of parameter names to validate.
        case_sensitive: Whether parameter names are case sensitive.

    Raises:
        ParameterSpecificationError: If any name is invalid.
    """
    for name in names:
        validate_parameter_name(name)

    if not case_sensitive:
        duplicates = find_duplicates(names, case_sensitive=False)
        if duplicates:
            msg = f"Duplicate parameter names found (case insensitive): {duplicates}"
            raise CommandSpecificationError(command_name, msg)


def validate_short_option_name(
    option_name: str,
    name: str,
) -> None:
    """Validate a short option name.

    Args:
        option_name: The name of the option the short name belongs to.
        name: The short option name to validate.

    Raises:
        OptionSpecificationError: If the name is invalid.
    """
    if len(name) != 1:
        msg = f"Short name '{name}' is invalid. Must be 1 character"
        raise OptionSpecificationError(option_name, msg)

    if not SHORT_NAME_PATTERN.match(name):
        msg = (
            f"Short name '{name}' is invalid."
            f" Must match pattern: {SHORT_NAME_PATTERN.pattern}"
        )
        raise OptionSpecificationError(option_name, msg)


def validate_short_option_names(
    option_name: str, names: "Iterable[str] | None", *, case_sensitive: bool = True
) -> None:
    """Validate multiple short option names.

    See [validate_short_option_name][flagrant.validations.validate_short_option_name].

    Args:
        option_name: The name of the option the short names belong to.
        names: An iterable of short option names to validate.
        case_sensitive: Whether option names are case sensitive.

    Raises:
        OptionSpecificationError: If any name is invalid.
    """
    if names is None:
        return

    for name in names:
        validate_short_option_name(option_name, name)

    if not case_sensitive:
        duplicates = find_duplicates(names, case_sensitive=False)
        if duplicates:
            msg = f"Duplicate short option names found (case insensitive): {duplicates}"
            raise OptionSpecificationError(option_name, msg)


def validate_value_option_accumulation_mode(
    option_name: str, accumulation_mode: ValueAccumulationMode, arity: "Arity"
) -> None:
    """Validate the accumulation mode of a value option.

    Args:
        option_name: The name of the option.
        accumulation_mode: The accumulation mode to validate.
        arity: The arity to validate.

    Raises:
        OptionSpecificationError: If the accumulation mode is invalid.
    """
    if (
        accumulation_mode == ValueAccumulationMode.EXTEND
        and arity.accepts_at_most_one_value
    ):
        msg = (
            "Accumulation mode is invalid."
            "EXTEND mode is only allowed for options that accept multiple values."
        )
        raise OptionSpecificationError(option_name, msg)


def validate_value_option_arity(
    option_name: str, arity: "Arity", *, greedy: bool
) -> None:
    """Validate the arity of a value option.

    Args:
        option_name: The name of the option.
        arity: The arity to validate.
        greedy: Whether the option is greedy.

    Raises:
        OptionSpecificationError: If the arity is invalid.
    """
    if greedy and arity.max is not None:
        msg = "Arity is invalid. Must be unbounded for greedy value options."
        raise OptionSpecificationError(option_name, msg)

    if arity.rejects_values:
        msg = "Arity is invalid. Must be non-negative for value options."
        raise OptionSpecificationError(option_name, msg)


def validate_dict_option_arity(
    option_name: str, arity: "Arity", *, greedy: bool
) -> None:
    """Validate the arity of a dictionary option.

    Args:
        option_name: The name of the option.
        arity: The arity to validate.
        greedy: Whether the option is greedy.

    Raises:
        OptionSpecificationError: If the arity is invalid.
    """
    if greedy and arity.max is not None:
        msg = "Arity is invalid. Must be unbounded for greedy value options."
        raise OptionSpecificationError(option_name, msg)

    if arity.rejects_values:
        msg = "Arity is invalid. Must be non-negative for dictionary options."
        raise OptionSpecificationError(option_name, msg)
