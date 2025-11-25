"""Types for command-line argument parsing."""

from collections.abc import Sequence
from typing import Annotated, Final, Literal, NamedTuple, TypedDict
from typing_extensions import Doc, TypeIs, override

CommandName = str
FrozenCommandNames = tuple[CommandName, ...]
FrozenCommandNameSet = frozenset[CommandName]
CommandPath = tuple[CommandName, ...]


Arg = str
Args = Sequence[Arg]
ArgList = tuple[Arg, ...]

ArgPosition = Annotated[int, Doc("Zero-indexed position in an argument list")]
Consumed = Annotated[int, Doc("Number of arguments consumed")]

BooleanFlagOptionValue = bool
CountingFlagOptionValue = int
FlagOptionValue = BooleanFlagOptionValue | CountingFlagOptionValue

DictValue = str | dict[str, "DictValue"] | tuple["DictValue", ...]
DictOptionValue = dict[str, "DictValue"]
DictListOptionValue = tuple["DictOptionValue", ...]

FlatListOptionValue = tuple[str, ...]
NestedListOptionValue = tuple[tuple[str, ...], ...]
ListOptionValue = FlatListOptionValue | NestedListOptionValue

RequiredScalarOptionValue = str
NullScalarOptionValue = None
ScalarOptionValue = RequiredScalarOptionValue | NullScalarOptionValue


class NotGiven:
    """Sentinel value indicating that no value was given."""

    @override
    def __repr__(self) -> str:
        return "<NotGiven>"


NOT_GIVEN: Final[NotGiven] = NotGiven()

OptionValue = (
    CountingFlagOptionValue
    | FlagOptionValue
    | DictListOptionValue
    | DictOptionValue
    | FlagOptionValue
    | ListOptionValue
    | NestedListOptionValue
    | ScalarOptionValue
    | NullScalarOptionValue
    | NotGiven
)

ExtraArg = str

FrozenOptionValues = tuple[OptionValue, ...]

PositionalValue = str


class UngroupedPositional(NamedTuple):
    """A positional value and its position in the argument list."""

    value: PositionalValue
    position: ArgPosition


def is_given(value: OptionValue) -> TypeIs[OptionValue]:
    """True if the value is not the NotGiven sentinel."""
    return not isinstance(value, NotGiven)


def is_not_given(value: OptionValue) -> TypeIs[NotGiven]:
    """True if the value is the NotGiven sentinel."""
    return isinstance(value, NotGiven)


OptionName = str
OptionDictionary = dict[OptionName, OptionValue]
FrozenOptionNames = tuple[OptionName, ...]
FrozenOptionNameSet = frozenset[OptionName]
PositionalName = str
PositionalDictionary = dict[PositionalName, PositionalValue]
FrozenPositionalNames = tuple[PositionalName, ...]
FrozenPositionalNameSet = frozenset[PositionalName]
ParameterName = str
ParameterKind = Literal["option", "positional"]

OptionForm = Literal["long", "short"]

InlineValue = Annotated[str, Doc("An inline value specified with an option")]


class ParseResultDict(TypedDict):
    """Dictionary representation of a [ParseResult][flagrant.parser.ParseResult] for serialization."""  # noqa: E501

    command: str
    args: tuple[Arg, ...]
    options: dict[OptionName, "OptionValue"]
    positionals: dict[PositionalName, "tuple[PositionalValue, ...] | PositionalValue"]
    subcommand: "ParseResultDict | None"


def is_dict_option_value(value: OptionValue) -> TypeIs[DictOptionValue]:
    """True if the option value is a dictionary."""
    return isinstance(value, dict)


def is_dict_list_option_value(value: OptionValue) -> TypeIs[DictListOptionValue]:
    """True if the option value is a list of dictionaries."""
    return isinstance(value, tuple) and all(isinstance(v, dict) for v in value)


def is_flag_option_value(value: OptionValue) -> "TypeIs[FlagOptionValue]":
    """True if the option value is a flag (boolean)."""
    return isinstance(value, bool)


def is_counting_flag_option_value(value: OptionValue) -> "TypeIs[int]":
    """True if the option value is a counting flag (integer)."""
    return isinstance(value, int) and not isinstance(value, bool)


def is_list_option_value(value: OptionValue) -> TypeIs[ListOptionValue]:
    """True if the option value is a list of strings."""
    return isinstance(value, tuple) and all(isinstance(v, str) for v in value)


def is_nested_list_option_value(
    value: OptionValue,
) -> TypeIs[NestedListOptionValue]:
    """True if the option value is a nested list of strings."""
    return isinstance(value, tuple) and all(isinstance(v, tuple) for v in value)


def is_scalar_option_value(value: OptionValue) -> TypeIs[ScalarOptionValue]:
    """True if the option value is a scalar string."""
    return isinstance(value, str)


def is_null_option_value(value: OptionValue) -> TypeIs[None]:
    """True if the option value is None."""
    return value is None
