"""Enumerations for command-line argument parsing and completion."""

from enum import Enum


class ArgumentFileFormat(str, Enum):
    """Specifies how the content of an argument file should be interpreted."""

    LINE = "line"
    """Each line in the file is treated as a single, separate argument. (Default)"""

    SHELL = "shell"
    """The file content is parsed using shell-like quoting and escaping rules."""


class FlagAccumulationMode(str, Enum):
    """Defines how the parser should handle multiple occurrences of the same flag."""

    FIRST = "first"
    """Keeps only the first occurrence; all subsequent occurrences are ignored."""

    LAST = "last"
    """Keeps only the last occurrence; previous occurrences are overwritten. (Default)"""  # noqa: E501

    COUNT = "count"
    """Counts the total number of times the flag is provided."""

    ERROR = "error"
    """
    Raises a [OptionNotRepeatableError][flagrant.exceptions.OptionNotRepeatableError]
    if the flag is specified more than once.
    """


class ValueAccumulationMode(str, Enum):
    """Defines how the parser should handle multiple occurrences of the same value option."""  # noqa: E501

    FIRST = "first"
    """Keeps only the first occurrence; all subsequent occurrences are ignored."""

    LAST = "last"
    """Keeps only the last occurrence; previous occurrences are overwritten. (Default)"""  # noqa: E501

    APPEND = "append"
    """
    Appends each occurrence as a distinct group. For an option with an arity of N,
    the final result is a list of N-tuples. For an option with a maximum arity of 1,
    the final result is a flat list.
    """

    EXTEND = "extend"
    """
    Extends a single list with all values from all occurrences. For an option
    with an arity of N, the final result is a flattened list of all values.
    """

    ERROR = "error"
    """
    Raises a [OptionNotRepeatableError][flagrant.exceptions.OptionNotRepeatableError]
    if the option is specified more than once.
    """


class DictAccumulationMode(str, Enum):
    """Defines how the parser should handle multiple occurrences of a dictionary option."""  # noqa: E501

    MERGE = "merge"
    """
    Merges key-value pairs from all occurrences into a single dictionary.
    The merging behavior is controlled by the
    [DictMergeStrategy][flagrant.enums.DictMergeStrategy]. (Default)
    """

    FIRST = "first"
    """Keeps only the first occurrence; all subsequent occurrences are ignored."""

    LAST = "last"
    """Keeps only the last occurrence; previous occurrences are overwritten."""

    APPEND = "append"
    """Appends each dictionary occurrence as a separate item in a list."""

    ERROR = "error"
    """
    Raises a [OptionNotRepeatableError][flagrant.exceptions.OptionNotRepeatableError]
    if the option is specified more than once.
    """


AccumulationModeType = (
    DictAccumulationMode | FlagAccumulationMode | ValueAccumulationMode
)


class DictMergeStrategy(str, Enum):
    """Defines the merging strategy when `DictAccumulationMode.MERGE` is used."""

    SHALLOW = "shallow"
    """A shallow merge where keys from later occurrences overwrite earlier ones."""

    DEEP = "deep"
    """
    A deep merge where nested dictionaries are merged recursively. (Default)
    """


class UngroupedPositionalStrategy(str, Enum):
    """Defines how ungrouped positional arguments are handled."""

    IGNORE = "ignore"
    """Ignores any ungrouped positional arguments."""

    COLLECT = "collect"
    """Collects ungrouped positional arguments into a special list."""

    ERROR = "error"
    """
    Raises a [PositionalUnexpectedValueError][flagrant.exceptions.PositionalUnexpectedValueError]
    if ungrouped positional arguments are encountered.
    """  # noqa: E501
