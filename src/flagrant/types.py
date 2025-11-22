"""Types for command-line argument parsing and completion."""

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Literal, TypedDict
from typing_extensions import Doc

ErrorContextValue = (
    str
    | int
    | float
    | bool
    | None
    | Path
    | list["ErrorContextValue"]
    | dict[str, "ErrorContextValue"]
)
ErrorContext = dict[str, ErrorContextValue]

CommandName = str
FrozenCommandNames = tuple[CommandName, ...]
FrozenCommandNameSet = frozenset[CommandName]
CommandPath = tuple[CommandName, ...]

Arg = str
Args = Sequence[Arg]
FrozenArgs = tuple[Arg, ...]

ArgPosition = Annotated[int, Doc("Zero-indexed position in an argument list")]
Consumed = Annotated[int, Doc("Number of arguments consumed")]

FlagOptionValue = bool | int
ValueOptionValue = str | tuple[str, ...] | tuple[tuple[str, ...], ...]
DictOptionDictValue = dict[str, "DictValue"]
DictOptionListValue = tuple[DictOptionDictValue, ...]
DictOptionValue = DictOptionDictValue | DictOptionListValue
DictValue = str | dict[str, "DictValue"] | tuple["DictValue"]
MultiValue = tuple[str, ...] | tuple[tuple[str, ...], ...]
OptionValue = FlagOptionValue | ValueOptionValue | DictOptionValue | MultiValue
FrozenOptionValues = tuple[OptionValue, ...]
PositionalValue = str | tuple[str, ...]

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
    """Dictionary representation of a [ParseResult][flagrant.parsing.ParseResult] for serialization."""  # noqa: E501

    command: str
    args: tuple[str, ...]
    options: dict[str, "OptionValue"]
    positionals: dict[str, "PositionalValue"]
    subcommand: "ParseResultDict | None"
