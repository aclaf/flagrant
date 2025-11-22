from dataclasses import InitVar, dataclass
from typing import TYPE_CHECKING, Literal
from typing_extensions import TypeIs, override

from flagrant.specification._arity import (
    get_arity_max,
    get_arity_min,
    is_optional_scalar_arity,
    validate_arity,
)

from .helpers import (
    flatten_string_iterables,
    long_names,
    prefixed_names,
    short_names,
)

if TYPE_CHECKING:
    import re

    from ._arity import Arity


@dataclass(slots=True, frozen=True)
class OptionSpecification:
    """Base class for named option parameters."""

    names: tuple[str, ...]

    @property
    def name(self) -> str:
        """Get the canonical name of this option."""
        return self.names[0]

    @property
    def all_names(self) -> tuple[str, ...]:
        """Get all names (long, short, negative) for this option."""
        return flatten_string_iterables(self.long_names, self.short_names)

    @property
    def long_names(self) -> tuple[str, ...]:
        """Get the long names for this option."""
        return long_names(self.names)

    @property
    def short_names(self) -> tuple[str, ...]:
        """Get the short names for this option."""
        return short_names(self.names)


DictAccumulationMode = Literal["append", "error", "first", "last", "merge"]
DictMergeStrategy = Literal["deep", "shallow"]


@dataclass(slots=True, frozen=True)
class DictOptionSpecification(OptionSpecification):
    """A option that accepts key-value pairs.

    The value of the option in parsed results will be a dictionary or tuple of
    dictionaries (when `accumulation_mode = "append"`).
    """

    accumulation_mode: DictAccumulationMode = "merge"
    allow_auto_list_indices: bool = False
    allow_duplicate_list_indices: bool = False
    allow_item_separator: bool = False
    allow_json_list: bool = False
    allow_json_object: bool = False
    allow_nested: bool = True
    allow_sparse_lists: bool = False
    arity: "Arity" = "*"
    escape_character: str | None = None
    item_separator: str | None = None
    key_value_separator: str | None = None
    merge_strategy: DictMergeStrategy = "deep"
    nesting_separator: str | None = None
    require_json_list: bool = False
    require_json_object: bool = False
    strict_structure: bool | None = None

    def __post_init__(self) -> None:
        validate_arity(self.arity)

    @property
    def is_list(self) -> bool:
        """True if this option returns a list of dictionaries."""
        return self.accumulation_mode == "append"


FlagAccumulationMode = Literal["count", "error", "first", "last", "toggle"]


@dataclass(slots=True, frozen=True)
class FlagOptionSpecification(OptionSpecification):
    """A boolean flag that does not accept a value.

    The value of the option in parsed results will be a boolean or integer (when
    `accumulation_mode = "count"`).
    """

    accumulation_mode: FlagAccumulationMode = "toggle"
    arity: Literal[0] = 0
    negative_names: tuple[str, ...] | None = None

    negative_prefixes: InitVar[tuple[str, ...] | None] = None

    def __post_init__(self, negative_prefixes: tuple[str, ...] | None) -> None:
        if negative_prefixes is not None:
            if self.negative_names is None:
                object.__setattr__(
                    self,
                    "negative_names",
                    prefixed_names(self.long_names, negative_prefixes),
                )
            else:
                object.__setattr__(
                    self,
                    "negative_names",
                    (
                        *self.negative_names,
                        *prefixed_names(self.long_names, negative_prefixes),
                    ),
                )

    @property
    @override
    def long_names(self) -> tuple[str, ...]:
        """Get the long names for this option."""
        return long_names(self.names, self.negative_long_names)

    @property
    @override
    def short_names(self) -> tuple[str, ...]:
        """Get the short names for this option."""
        return short_names(self.names, self.negative_short_names)

    @property
    def negative_long_names(self) -> tuple[str, ...]:
        """Get the long negative names for this option."""
        return long_names(self.negative_names)

    @property
    def negative_short_names(self) -> tuple[str, ...]:
        """Get the short negative names for this option."""
        return short_names(self.negative_names)

    @property
    def has_negative_names(self) -> bool:
        """Check if this option has any negative names."""
        if self.negative_names is None:
            return False
        return bool(self.negative_names)

    @property
    def is_counting(self) -> bool:
        """Check if this flag option uses `counting` accumulation mode."""
        return self.accumulation_mode == "count"


ListAccumulationMode = Literal["append", "error", "extend", "first", "last"]


@dataclass(slots=True, frozen=True)
class ListOptionSpecification(OptionSpecification):
    """An option that accepts multiple scalar values.

    The value of the option in parsed results will be a tuple of strings or nested
    tuples of strings (one level when `accumulation_mode = "append"`).
    """

    accumulation_mode: ListAccumulationMode = "last"
    allow_item_separator: bool = False
    allow_negative_numbers: bool = False
    arity: "Arity" = "*"
    escape_character: str | None = None
    item_separator: str | None = None

    def __post_init__(self) -> None:
        validate_arity(self.arity)

    @property
    def is_nested(self) -> bool:
        """True if this option returns nested lists."""
        return self.accumulation_mode == "append"

    def get_max_args(self, *, inline: bool = False) -> int | None:
        """Get the maximum number of arguments allowed for this option.

        Args:
            inline: Whether an inline value was provided.
        """
        arity_max = get_arity_max(self.arity)
        if arity_max is None:
            return None
        return arity_max - (1 if inline else 0)

    def get_min_args(self, *, inline: bool = False) -> int:
        """Get the minimum number of arguments required for this option.

        Args:
            inline: Whether an inline value was provided.
        """
        return get_arity_min(self.arity) - (1 if inline else 0)


ScalarAccumulationMode = Literal["error", "first", "last"]


@dataclass(slots=True, frozen=True)
class ScalarOptionSpecification(OptionSpecification):
    """An option that accepts a single or optional scalar value.

    The value of the option in parsed results will be a single string or `None` (when
    `arity = "?"` and value is not provided).
    """

    accumulation_mode: Literal["error", "first", "last"] = "last"
    allow_negative_numbers: bool = False
    escape_character: str | None = None
    arity: Literal[1, "?"] = 1
    negative_number_pattern: "re.Pattern[str] | None" = None

    @property
    def requires_value(self) -> bool:
        """True if this option requires a value to be provided."""
        return not is_optional_scalar_arity(self.arity)


OptionType = (
    DictOptionSpecification
    | FlagOptionSpecification
    | ListOptionSpecification
    | ScalarOptionSpecification
)


def is_dict_option(
    option: OptionType,
) -> "TypeIs[DictOptionSpecification]":
    """True if the option is a [DictOptionSpecification][flagrant.specification.DictOptionSpecification]."""  # noqa: E501
    return isinstance(option, DictOptionSpecification)


def is_dict_list_option(
    option: OptionType,
) -> "TypeIs[DictOptionSpecification]":
    """True if the option is a list [DictOptionSpecification][flagrant.specification.DictOptionSpecification]."""  # noqa: E501
    return is_dict_option(option) and option.is_list


def is_flag_option(
    option: OptionType,
) -> "TypeIs[FlagOptionSpecification]":
    """True if the option is a [FlagOptionSpecification][flagrant.specification.FlagOptionSpecification]."""  # noqa: E501
    return isinstance(option, FlagOptionSpecification)


def is_counting_flag_option(
    option: OptionType,
) -> "TypeIs[FlagOptionSpecification]":
    """True if the option is a counting [FlagOptionSpecification][flagrant.specification.FlagOptionSpecification]."""  # noqa: E501
    return is_flag_option(option) and option.is_counting


def is_list_option(
    option: OptionType,
) -> "TypeIs[ListOptionSpecification]":
    """True if the option is a [ListOptionSpecification][flagrant.specification.ListOptionSpecification]."""  # noqa: E501
    return isinstance(option, ListOptionSpecification)


def is_nested_list_option(
    option: OptionType,
) -> "TypeIs[ListOptionSpecification]":
    """True if the option is a nested [ListOptionSpecification][flagrant.specification.ListOptionSpecification]."""  # noqa: E501
    return is_list_option(option) and option.is_nested


def is_scalar_option(
    option: OptionType,
) -> "TypeIs[ScalarOptionSpecification]":
    """True if the option is a [ScalarOptionSpecification][flagrant.specification.ScalarOptionSpecification]."""  # noqa: E501
    return isinstance(option, ScalarOptionSpecification)


def is_optional_scalar_option(
    option: OptionType,
) -> "TypeIs[ScalarOptionSpecification]":
    """True if the option is a scalar option with optional value."""
    return is_scalar_option(option) and is_optional_scalar_arity(option.arity)


def is_multi_value_option(
    option: OptionType,
) -> "TypeIs[DictOptionSpecification | ListOptionSpecification]":
    """True if the option is a multi-value option (dict list or list)."""
    return (
        is_dict_list_option(option)
        or is_list_option(option)
        or is_nested_list_option(option)
    )
