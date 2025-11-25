from typing import TYPE_CHECKING, Literal

from flagrant.specification._options import (
    DictAccumulationMode,
    DictMergeStrategy,
    DictOptionSpecification,
    FlagAccumulationMode,
    FlagOptionSpecification,
    ListAccumulationMode,
    ListOptionSpecification,
    ScalarAccumulationMode,
    ScalarOptionSpecification,
)

from ._command import CommandSpecification, PositionalSpecification

if TYPE_CHECKING:
    import re
    from collections.abc import Iterable

    from flagrant.specification._arity import Arity

    from ._options import OptionType


def command(
    name: str,
    *,
    aliases: "Iterable[str] | None" = None,
    options: "Iterable[OptionType] | None" = None,
    positionals: "Iterable[PositionalSpecification] | None" = None,
    subcommands: "Iterable[CommandSpecification] | None" = None,
) -> CommandSpecification:
    """Factory function to create a CommandSpecification.

    Args:
        name: The canonical name of the command.
        aliases: A tuple of alternative names for the command.
        options: A tuple of `OptionSpecification` objects for the command.
        positionals: A tuple of `PositionalSpecification` objects for the command.
        subcommands: A tuple of nested `CommandSpecification` objects.

    Returns:
        A CommandSpecification instance.
    """
    return CommandSpecification(
        name=name,
        aliases=tuple(aliases) if aliases is not None else None,
        options=tuple(options) if options is not None else None,
        positionals=tuple(positionals) if positionals is not None else None,
        subcommands=tuple(subcommands) if subcommands is not None else None,
    )


def dict_option(  # noqa: PLR0913
    names: "Iterable[str]",
    arity: "Arity" = "*",
    *,
    accumulation_mode: DictAccumulationMode = "merge",
    allow_auto_list_indices: bool = False,
    allow_duplicate_list_indices: bool = False,
    allow_item_separator: bool = False,
    allow_json_list: bool = False,
    allow_json_object: bool = False,
    allow_nested: bool = True,
    allow_sparse_lists: bool = False,
    escape_character: str | None = None,
    item_separator: str | None = None,
    key_value_separator: str | None = None,
    merge_strategy: DictMergeStrategy = "deep",
    nesting_separator: str | None = None,
    require_json_list: bool = False,
    require_json_object: bool = False,
    strict_structure: bool | None = None,
) -> "DictOptionSpecification":
    """Create a new DictOptionSpecification."""
    return DictOptionSpecification(
        names=tuple(names),
        accumulation_mode=accumulation_mode,
        allow_auto_list_indices=allow_auto_list_indices,
        allow_duplicate_list_indices=allow_duplicate_list_indices,
        allow_item_separator=allow_item_separator,
        allow_json_list=allow_json_list,
        allow_json_object=allow_json_object,
        allow_nested=allow_nested,
        allow_sparse_lists=allow_sparse_lists,
        arity=arity,
        escape_character=escape_character,
        item_separator=item_separator,
        key_value_separator=key_value_separator,
        merge_strategy=merge_strategy,
        nesting_separator=nesting_separator,
        require_json_list=require_json_list,
        require_json_object=require_json_object,
        strict_structure=strict_structure,
    )


def dict_list_option(  # noqa: PLR0913
    names: "Iterable[str]",
    arity: "Arity" = "*",
    *,
    allow_auto_list_indices: bool = False,
    allow_duplicate_list_indices: bool = False,
    allow_item_separator: bool = False,
    allow_json_list: bool = False,
    allow_json_object: bool = False,
    allow_nested: bool = True,
    allow_sparse_lists: bool = False,
    escape_character: str | None = None,
    item_separator: str | None = None,
    key_value_separator: str | None = None,
    merge_strategy: DictMergeStrategy = "deep",
    nesting_separator: str | None = None,
    require_json_list: bool = False,
    require_json_object: bool = False,
    strict_structure: bool | None = None,
) -> "DictOptionSpecification":
    """Create a new DictOptionSpecification."""
    return DictOptionSpecification(
        names=tuple(names),
        accumulation_mode="append",
        allow_auto_list_indices=allow_auto_list_indices,
        allow_duplicate_list_indices=allow_duplicate_list_indices,
        allow_item_separator=allow_item_separator,
        allow_json_list=allow_json_list,
        allow_json_object=allow_json_object,
        allow_nested=allow_nested,
        allow_sparse_lists=allow_sparse_lists,
        arity=arity,
        escape_character=escape_character,
        item_separator=item_separator,
        key_value_separator=key_value_separator,
        merge_strategy=merge_strategy,
        nesting_separator=nesting_separator,
        require_json_list=require_json_list,
        require_json_object=require_json_object,
        strict_structure=strict_structure,
    )


def flag_option(
    names: "Iterable[str]",
    *,
    accumulation_mode: FlagAccumulationMode = "toggle",
    negative_names: "Iterable[str] | None" = None,
    negative_prefixes: "Iterable[str] | None" = None,
) -> "FlagOptionSpecification":
    """Create a new FlagOptionSpecification."""
    return FlagOptionSpecification(
        names=tuple(names),
        accumulation_mode=accumulation_mode,
        negative_names=tuple(negative_names) if negative_names is not None else None,
        negative_prefixes=tuple(negative_prefixes)
        if negative_prefixes is not None
        else None,
    )


def list_option(  # noqa: PLR0913
    names: "Iterable[str]",
    arity: "Arity" = "*",
    *,
    accumulation_mode: ListAccumulationMode = "last",
    allow_item_separator: bool = False,
    allow_negative_numbers: bool = False,
    escape_character: str | None = None,
    item_separator: str | None = None,
) -> "ListOptionSpecification":
    """Create a new ListOptionSpecification."""
    return ListOptionSpecification(
        names=tuple(names),
        accumulation_mode=accumulation_mode,
        allow_item_separator=allow_item_separator,
        allow_negative_numbers=allow_negative_numbers,
        arity=arity,
        escape_character=escape_character,
        item_separator=item_separator,
    )


def flat_list_option(  # noqa: PLR0913
    names: "Iterable[str]",
    arity: "Arity" = "*",
    *,
    allow_item_separator: bool = False,
    allow_negative_numbers: bool = False,
    escape_character: str | None = None,
    item_separator: str | None = None,
) -> "ListOptionSpecification":
    """Create a new ListOptionSpecification."""
    return ListOptionSpecification(
        names=tuple(names),
        accumulation_mode="extend",
        allow_item_separator=allow_item_separator,
        allow_negative_numbers=allow_negative_numbers,
        arity=arity,
        escape_character=escape_character,
        item_separator=item_separator,
    )


def nested_list_option(  # noqa: PLR0913
    names: "Iterable[str]",
    arity: "Arity" = "*",
    *,
    allow_item_separator: bool = False,
    allow_negative_numbers: bool = False,
    escape_character: str | None = None,
    item_separator: str | None = None,
) -> "ListOptionSpecification":
    """Create a new ListOptionSpecification."""
    return ListOptionSpecification(
        names=tuple(names),
        accumulation_mode="append",
        allow_item_separator=allow_item_separator,
        allow_negative_numbers=allow_negative_numbers,
        arity=arity,
        escape_character=escape_character,
        item_separator=item_separator,
    )


def scalar_option(  # noqa: PLR0913
    names: "Iterable[str]",
    arity: Literal[1, "?"] = 1,
    *,
    accumulation_mode: ScalarAccumulationMode = "last",
    allow_negative_numbers: bool = False,
    escape_character: str | None = None,
    negative_number_pattern: "re.Pattern[str] | None" = None,
) -> "ScalarOptionSpecification":
    """Create a new ScalarOptionSpecification."""
    return ScalarOptionSpecification(
        names=tuple(names),
        accumulation_mode=accumulation_mode,
        allow_negative_numbers=allow_negative_numbers,
        escape_character=escape_character,
        arity=arity,
        negative_number_pattern=negative_number_pattern,
    )
