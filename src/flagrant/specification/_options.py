from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING
from typing_extensions import TypeIs, override

from flagrant.defaults import (
    DEFAULT_CONVERT_UNDERSCORES,
)

from ._arity import Arity
from .enums import (
    DictAccumulationMode,
    DictMergeStrategy,
    FlagAccumulationMode,
    ValueAccumulationMode,
)
from .helpers import (
    all_long_option_names,
    all_negative_long_option_names,
    all_negative_names,
    all_option_names,
    negative_prefix_names,
)
from .validations import (
    validate_long_option_names,
    validate_negative_long_option_names,
    validate_negative_prefixes,
    validate_negative_short_option_names,
    validate_parameter_name,
    validate_short_option_names,
    validate_value_option_accumulation_mode,
    validate_value_option_arity,
)

if TYPE_CHECKING:
    import re
    from collections.abc import Iterable, Sequence

    from flagrant.types import FrozenOptionNames


@dataclass(frozen=True)
class OptionSpecification:
    """Base class for named option parameters (e.g., `--verbose`, `-o file`).

    Attributes:
        long_names: A tuple of long names for the option (e.g., "verbose").
        short_names: A tuple of short names for the option (e.g., "v").
        name: The canonical name for the option.
        arity: The number of values expected for each occurrence. See `Arity`.
        greedy: If True, consumes all subsequent arguments as values.
            If False, consumes until the next option or subcommand.
        preferred_name: The preferred name used in parse results.
        case_sensitive: Whether the option names are case sensitive.
    """

    name: str
    arity: Arity
    greedy: bool
    preferred_name: str
    long_names: tuple[str, ...]
    short_names: tuple[str, ...]
    case_sensitive: bool = True

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        *,
        arity: Arity | None = None,
        preferred_name: str | None = None,
        case_sensitive: bool = True,
        convert_underscores: bool = DEFAULT_CONVERT_UNDERSCORES,
        greedy: bool = False,
        long_names: "Sequence[str] | None" = None,
        short_names: "Sequence[str] | None" = None,
    ) -> None:
        """Initializes an `OptionSpecification`.

        Args:
            name: The canonical name for the option.
            arity: The number of values expected for each occurrence.
                See [Arity][flagrant.specification.Arity].
            preferred_name: The preferred name used in parse results.
            case_sensitive: Whether the option names are case sensitive.
            convert_underscores: Whether long and short names have underscores converted
                automatically.
            greedy: If True, consumes all subsequent arguments as values.
                If False, consumes until the next option or subcommand.
            long_names: A sequence of long names (e.g., "verbose").
            short_names: A sequence of short names (e.g., "v").
        """
        validate_parameter_name(name)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "arity", arity or Arity.exactly_one())
        object.__setattr__(self, "greedy", greedy)

        default_name = preferred_name or name
        if not long_names and not short_names:
            if len(name) == 1:
                short_names = (default_name,)
            else:
                long_names = (default_name,)

        if preferred_name is None and long_names:
            preferred_name = long_names[0]
        elif preferred_name is None and short_names:
            preferred_name = short_names[0]
        object.__setattr__(self, "preferred_name", preferred_name)

        normalized_long_names = tuple(n.lstrip("-") for n in (long_names or ()))
        normalized_short_names = tuple(n.lstrip("-") for n in (short_names or ()))

        if convert_underscores:
            normalized_long_names = tuple(
                n.replace("_", "-") for n in normalized_long_names
            )
            normalized_short_names = tuple(
                n.replace("_", "-") for n in normalized_short_names
            )

        validate_long_option_names(
            name, normalized_long_names, case_sensitive=case_sensitive
        )
        validate_short_option_names(
            name, normalized_short_names, case_sensitive=case_sensitive
        )

        object.__setattr__(self, "long_names", tuple(normalized_long_names))
        object.__setattr__(self, "short_names", tuple(normalized_short_names))

    @property
    def accepts_multiple_values(self) -> bool:
        """Check if this parameter can accept multiple values."""
        return self.arity.accepts_multiple_values

    @property
    def accepts_unbounded_values(self) -> bool:
        """Check if this parameter can accept any number of values."""
        return self.arity.accepts_unbounded_values

    @property
    def greedy_accepts_unbounded_values(self) -> bool:
        """Check if this parameter greedily accepts an unbounded number of values."""
        return self.accepts_unbounded_values and self.greedy

    @property
    def accepts_values(self) -> bool:
        """Check if this parameter can accept one or more values."""
        return self.arity.accepts_values

    @property
    def accepts_at_most_one_value(self) -> bool:
        """Check if this parameter can accept at most one value."""
        return self.arity.accepts_at_most_one_value

    @property
    def rejects_values(self) -> bool:
        """Check if this parameter rejects values (accepts none)."""
        return self.arity.rejects_values

    @property
    def requires_multiple_values(self) -> bool:
        """Check if this parameter requires multiple values."""
        return self.arity.requires_multiple_values

    @property
    def requires_value(self) -> bool:
        """Check if this option requires at least one value."""
        return self.arity.min > 0

    @property
    def requires_values(self) -> bool:
        """Check if this parameter requires one or more values."""
        return self.arity.requires_values

    @cached_property
    def all_long_names(self) -> "FrozenOptionNames":
        """Get all long names for this option."""
        return all_long_option_names(self.long_names)

    @cached_property
    def all_short_names(self) -> "FrozenOptionNames":
        """Get all short names for this option."""
        return self.short_names

    @cached_property
    def all_names(self) -> "FrozenOptionNames":
        """Get all names (long and short) for this option."""
        return all_option_names(self.long_names, self.short_names)

    def matches(self, name: str) -> bool:
        """Check if name matches any form of this option (exact match only)."""
        return name in self.all_names


@dataclass(frozen=True)
class FlagOptionSpecification(OptionSpecification):
    """A specification for a boolean flag option.

    Flags are options that do not take a value; their presence indicates a state.

    Attributes:
        accumulation_mode: The strategy for handling multiple occurrences.
            See `FlagAccumulationMode`.
        negative_prefix_separator: The separator used for negative prefixes.
        negative_prefixes: A set of prefixes that create negated forms of the
            long names (e.g., "no-" creates "--no-verbose").
        negative_short_names: A set of short names that act as negatives.
    """

    accumulation_mode: FlagAccumulationMode = FlagAccumulationMode.LAST
    negative_long_names: tuple[str, ...] = field(default_factory=tuple)
    negative_prefixes: tuple[str, ...] = field(default_factory=tuple)
    negative_short_names: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.negative_long_names:
            validate_negative_long_option_names(
                self.name,
                self.negative_long_names,
                self.long_names,
                case_sensitive=self.case_sensitive,
            )

        if self.negative_prefixes:
            validate_negative_prefixes(
                self.name,
                self.negative_prefixes,
                self.negative_long_names or (),
                self.long_names,
                case_sensitive=self.case_sensitive,
            )

        if self.negative_short_names:
            validate_negative_short_option_names(
                self.name,
                self.negative_short_names,
                self.short_names,
                case_sensitive=self.case_sensitive,
            )

    @cached_property
    @override
    def all_names(self) -> "FrozenOptionNames":
        """Get all names (long, short, negative) for this flag."""
        return all_option_names(
            self.long_names,
            self.short_names,
            self.negative_long_names,
            self.negative_prefixes,
            self.negative_short_names,
        )

    @cached_property
    @override
    def all_long_names(self) -> "FrozenOptionNames":
        """Get all long names for this flag, including negative names."""
        return all_long_option_names(
            self.long_names,
            self.negative_long_names,
            self.negative_prefixes,
        )

    @cached_property
    @override
    def all_short_names(self) -> "FrozenOptionNames":
        """Get all short names for this flag, including negative short names."""
        return (*self.short_names, *self.negative_short_names)

    @cached_property
    def all_negative_long_names(self) -> "FrozenOptionNames":
        """Get all long negative names for this flag."""
        return all_negative_long_option_names(
            self.long_names,
            self.negative_long_names,
            self.negative_prefixes,
        )

    @cached_property
    def all_negative_prefix_names(self) -> "FrozenOptionNames":
        """Get all negative prefix names for this flag."""
        return negative_prefix_names(
            self.long_names,
            self.negative_prefixes,
        )

    @cached_property
    def all_negative_names(self) -> "FrozenOptionNames":
        """Get all negative names for this flag."""
        return all_negative_names(
            self.long_names,
            self.negative_long_names,
            self.negative_prefixes,
            self.negative_short_names,
        )

    @cached_property
    def all_negative_short_names(self) -> "FrozenOptionNames":
        """Get all short names for this flag."""
        return self.negative_short_names

    @cached_property
    def has_negative_names(self) -> bool:
        """Check if this flag has any negative names."""
        return bool(
            self.negative_long_names
            or self.negative_prefixes
            or self.negative_short_names
        )

    def is_negative(self, name: str, *, case_sensitive: bool = True) -> bool:
        """Check if name is a negative form of this flag."""
        if case_sensitive:
            return name in self.all_negative_names
        return name.lower() in {n.lower() for n in self.all_negative_names}


@dataclass(slots=True, frozen=True)
class ValueOptionSpecification(OptionSpecification):
    """A specification for an option that accepts one or more values.

    Attributes:
        arity: The number of values expected for each occurrence. See `Arity`.
        accumulation_mode: The strategy for handling multiple occurrences.
            See [ValueAccumulationMode][flagrant.specification.ValueAccumulationMode].
        allow_negative_numbers: If True, allows values that look like negative
            numbers (e.g., "-5") to be parsed as values for this option.
        greedy: If True, consumes all subsequent arguments as values until
            a separator (`--`) is found, ignoring other options.
        item_separator: A character used to split a single argument into
            multiple values. Overrides the global `value_item_separator`.
        allow_item_separator: If True, enables the `item_separator`.
        escape_character: A character used to escape the `item_separator`.
            Overrides the global `value_escape_character`.
        negative_number_pattern: An optional regex to identify negative numbers,
            overriding the global `negative_number_pattern` for this option.
    """

    accumulation_mode: ValueAccumulationMode = ValueAccumulationMode.LAST
    allow_item_separator: bool = False
    allow_negative_numbers: bool = False
    escape_character: str | None = None
    item_separator: str | None = None
    negative_number_pattern: "re.Pattern[str] | None" = None

    def __post_init__(self) -> None:
        validate_value_option_arity(self.name, self.arity, greedy=self.greedy)
        validate_value_option_accumulation_mode(
            self.name, self.accumulation_mode, self.arity
        )


@dataclass(slots=True, frozen=True)
class DictOptionSpecification(OptionSpecification):
    """A specification for an option that accepts key-value pairs.

    Attributes:
        arity: The number of `key=value` arguments expected per occurrence.
        accumulation_mode: The strategy for handling multiple occurrences.
            See [DictAccumulationMode][flagrant.specification.DictAccumulationMode].
        merge_strategy: The strategy for merging dictionaries when `MERGE`
            is used. See [DictMergeStrategy][flagrant.specification.DictMergeStrategy].
        key_value_separator: The character separating a key from a value.
            Overrides the global `key_value_separator`.
        nesting_separator: The character for denoting nested keys (e.g., ".").
            Overrides the global `nesting_separator`.
        allow_nested: If True, allows keys to be nested.
        case_sensitive_keys: If True, keys are case-sensitive.
        allow_duplicate_list_indices: If True, allows `list[0]=a list[0]=b`.
        allow_sparse_lists: If True, allows `list[0]=a list[2]=c`.
        strict_structure: If True, enforces strict structural rules. Overrides
            the global `strict_structure`.
        greedy: If True, consumes all subsequent arguments as values.
        item_separator: A character to split a single argument into multiple
            key-value pairs. Overrides the global `dict_item_separator`.
        allow_item_separator: If True, enables the `item_separator`.
        escape_character: Character to escape separators. Overrides
            the global `dict_escape_character`.
    """

    accumulation_mode: DictAccumulationMode = DictAccumulationMode.MERGE
    allow_duplicate_list_indices: bool = False
    allow_item_separator: bool = True
    allow_nested: bool = True
    allow_sparse_lists: bool = False
    case_sensitive_keys: bool = True
    escape_character: str | None = None
    item_separator: str | None = None
    key_value_separator: str | None = None
    merge_strategy: DictMergeStrategy = DictMergeStrategy.DEEP
    nesting_separator: str | None = None
    strict_structure: bool | None = None

    def __post_init__(self):
        validate_value_option_arity(self.name, self.arity, greedy=self.greedy)


NonFlagOptionSpecificationType = DictOptionSpecification | ValueOptionSpecification
OptionSpecificationType = (
    DictOptionSpecification | FlagOptionSpecification | ValueOptionSpecification
)
OptionSpecificationFactory = Callable[..., OptionSpecificationType]
DictOptionSpecificationFactory = Callable[..., DictOptionSpecification]
FlagOptionSpecificationFactory = Callable[..., FlagOptionSpecification]
ValueOptionSpecificationFactory = Callable[..., ValueOptionSpecification]


def is_dict_option(spec: OptionSpecification) -> TypeIs[DictOptionSpecification]:
    """Check if the given specification is a DictOptionSpecification."""
    return isinstance(spec, DictOptionSpecification)


def is_flag_option(spec: OptionSpecification) -> TypeIs[FlagOptionSpecification]:
    """Check if the given specification is a FlagOptionSpecification."""
    return isinstance(spec, FlagOptionSpecification)


def is_value_option(spec: OptionSpecification) -> TypeIs[ValueOptionSpecification]:
    """Check if the given specification is a ValueOptionSpecification."""
    return isinstance(spec, ValueOptionSpecification)


def is_non_flag_option(
    spec: OptionSpecification,
) -> TypeIs[NonFlagOptionSpecificationType]:
    """Check if the given specification is a non-flag option."""
    return is_dict_option(spec) or is_value_option(spec)


def create_dict_option_specification(  # noqa: D417, PLR0913
    name: str,
    *,
    arity: Arity,
    greedy: bool,
    preferred_name: str,
    long_names: "Iterable[str]",
    short_names: "Iterable[str]",
    case_sensitive: bool = True,
    accumulation_mode: DictAccumulationMode = DictAccumulationMode.MERGE,
    allow_duplicate_list_indices: bool = False,
    allow_item_separator: bool = True,
    allow_nested: bool = True,
    allow_sparse_lists: bool = False,
    case_sensitive_keys: bool = True,
    escape_character: str | None = None,
    item_separator: str | None = None,
    key_value_separator: str | None = None,
    merge_strategy: DictMergeStrategy = DictMergeStrategy.DEEP,
    nesting_separator: str | None = None,
    strict_structure: bool | None = None,
) -> DictOptionSpecification:
    """Create a DictOptionSpecification with the given parameters.

    Args:
        name: The canonical name for the option.
        long_names: An iterable of long names for the option (e.g., "verbose").
        short_names: An iterable of short names for the option (e.g., "v").
        name: The canonical name for the option.
        arity: The number of values expected for each occurrence. See `Arity`.
        greedy: If True, consumes all subsequent arguments as values.
            If False, consumes until the next option or subcommand.
        preferred_name: The preferred name used in parse results.
        case_sensitive: Whether the option names are case sensitive.
        merge_strategy: The strategy for merging dictionaries when `MERGE`
            is used. See [DictMergeStrategy][flagrant.enums.DictMergeStrategy].
        key_value_separator: The character separating a key from a value.
            Overrides the global `key_value_separator`.
        nesting_separator: The character for denoting nested keys (e.g., ".").
            Overrides the global `nesting_separator`.
        allow_nested: If True, allows keys to be nested.
        case_sensitive_keys: If True, keys are case-sensitive.
        allow_duplicate_list_indices: If True, allows `list[0]=a list[0]=b`.
        allow_sparse_lists: If True, allows `list[0]=a list[2]=c`.
        strict_structure: If True, enforces strict structural rules. Overrides
            the global `strict_structure`.
        item_separator: A character to split a single argument into multiple
            key-value pairs. Overrides the global `dict_item_separator`.
        allow_item_separator: If True, enables the `item_separator`.
        escape_character: Character to escape separators. Overrides
            the global `dict_escape_character`.

    Returns:
        An instance of DictOptionSpecification.

    Raises:
        OptionSpecificationError: If any of the provided parameters are invalid.
    """
    return DictOptionSpecification(
        name,
        arity=arity,
        greedy=greedy,
        preferred_name=preferred_name,
        long_names=tuple(long_names),
        short_names=tuple(short_names),
        case_sensitive=case_sensitive,
        accumulation_mode=accumulation_mode,
        allow_duplicate_list_indices=allow_duplicate_list_indices,
        allow_item_separator=allow_item_separator,
        allow_nested=allow_nested,
        allow_sparse_lists=allow_sparse_lists,
        case_sensitive_keys=case_sensitive_keys,
        escape_character=escape_character,
        item_separator=item_separator,
        key_value_separator=key_value_separator,
        merge_strategy=merge_strategy,
        nesting_separator=nesting_separator,
        strict_structure=strict_structure,
    )
