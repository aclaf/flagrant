"""Enumerations for command-line argument parsing."""

from enum import Enum


class AccumulationMode(str, Enum):
    """Defines how the parser should handle multiple occurrences of the same value option."""  # noqa: E501

    COUNT = "count"
    """
    Increments a counter each time the option is encountered.

    Example:
        >>> opt = flag_option("verbose", accumulation_mode=AccumulationMode.COUNT)
        >>> cmd = command("run", options=(opt,))
        >>> result = parse_command_line_args(
        ...     cmd, ["--verbose", "--verbose", "--verbose"]
        ... )
        >>> result.options["verbose"]
        3
    """

    FIRST = "first"
    """
    Keeps only the first occurrence; all subsequent occurrences are ignored.

    Example:
        >>> opt = scalar_option("output", accumulation_mode=AccumulationMode.FIRST)
        >>> cmd = command("run", options=(opt,))
        >>> result = parse_command_line_args(
        ...     cmd, ["--output", "first.txt", "--output", "second.txt"]
        ... )
        >>> result.options["output"]
        "first.txt"
    """

    LAST = "last"
    """
    Keeps only the last occurrence; previous occurrences are overwritten. (Default)

    Example:
        >>> opt = scalar_option("output", accumulation_mode=AccumulationMode.LAST)
        >>> cmd = command("run", options=(opt,))
        >>> result = parse_command_line_args(
        ...     cmd, ["--output", "first.txt", "--output", "second.txt"]
        ... )
        >>> result.options["output"]
        "second.txt"
    """

    APPEND = "append"
    """
    Appends each occurrence as a distinct group.

    For a [FLAG][flagrant.specification.OptionKind.FLAG] or
    [SCALAR][flagrant.specification.OptionKind.SCALAR] option, the final result is a
    list of values.

    For a [DICT][flagrant.specification.OptionKind.DICT] option, the final result is a
    tuple of dictionaries.

    For a [LIST][flagrant.specification.OptionKind.LIST] option, the final result is a
    tuple of tuples.

    Examples:
        With a [FLAG][flagrant.specification.OptionKind.FLAG] option:

        >>> opt = flag_option("verbose", accumulation_mode=AccumulationMode.APPEND)
        >>> cmd = command("run", options=(opt,))
        >>> result = parse_command_line_args(
        ...     cmd, ["--verbose", "--verbose", "--verbose"]
        ... )
        >>> result.options["verbose"]
        (True, True, True)

        With a [SCALAR][flagrant.specification.OptionKind.SCALAR] option:

        >>> opt = scalar_option("output", accumulation_mode=AccumulationMode.APPEND)
        >>> cmd = command("run", options=(opt,))
        >>> result = parse_command_line_args(
        ...     cmd, ["--output", "first.txt", "--output", "second.txt"]
        ... )
        >>> result.options["output"]
        ("first.txt", "second.txt")

        With a [SCALAR][flagrant.specification.OptionKind.SCALAR] option with an
        optional value:

        >>> opt = scalar_option(
        ...     "level", require_value=True, accumulation_mode=AccumulationMode.APPEND
        ... )
        >>> cmd = command("run", options=(opt,))
        >>> result = parse_command_line_args(
        ...     cmd, ["--level", "info", "--level", "--level", "debug"]
        ... )
        >>> result.options["level"]
        ("info", None, "debug")

        With a [DICT][flagrant.specification.OptionKind.DICT] option:

        >>> opt = dict_option("config", accumulation_mode=AccumulationMode.APPEND)
        >>> cmd = command("run", options=(opt,))
        >>> result = parse_command_line_args(
        ...     cmd,
        ...     ["--config", "key1=value1", "--config", "key2=value2"])
        >>> result.options["config"]
        ({"key1": "value1"}, {"key2": "value2"})

        With a [LIST][flagrant.specification.OptionKind.LIST] option:

        >>> opt = list_option(
        ...     "point", arity=2, accumulation_mode=AccumulationMode.APPEND
        ... )
        >>> cmd = command("run", options=(opt,))
        >>> result = parse_command_line_args(
        ...     cmd, ["--point", "1", "2", "--point", "3", "4"]
        ... )
        >>> result.options["point"]
        (("1", "2"), ("3", "4"))
    """

    EXTEND = "extend"
    """
    Extends a single tuple with all values from all occurrences.

    For a [FLAG][flagrant.specification.OptionKind.FLAG] or
    [SCALAR][flagrant.specification.OptionKind.SCALAR] option, the behavior is the same
    as [APPEND][flagrant.specification.AccumulationMode.APPEND].

    For a [LIST][flagrant.specification.OptionKind.LIST] option with an arity of N,
    the final result is a flattened tuple of all values.
    with an arity of N, the final result is a flattened list of all values.
    """

    MERGE = "merge"
    """
    Merges key-value pairs from all occurrences into a single dictionary.

    The merging behavior is controlled by the
    [DictMergeStrategy][flagrant.specification.DictMergeStrategy].
    Default when used with [DICT][flagrant.specification.OptionKind.DICT] options.

    Example:
        >>> opt = dict_option("config", accumulation_mode=AccumulationMode.MERGE)
        >>> cmd = command("run", options=(opt,))
        >>> result = parse_command_line_args(
        ...     cmd, ["--config", "key1=value1", "--config", "key2=value2"]
        ... )
        >>> result.options["config"]
        {"key1": "value1", "key2": "value2"}
    """

    ERROR = "error"
    """
    Raises an [OptionNotRepeatableError][flagrant.errors.OptionNotRepeatableError]
    if the option is specified more than once.

    Example:
        >>> opt = scalar_option("output", accumulation_mode=AccumulationMode.ERROR)
        >>> cmd = command("run", options=(opt,))
        >>> result = parse_command_line_args(
        ...     cmd, ["--output", "first.txt"]
        ... )
        >>> result.options["output"]
        "first.txt"
        >>> result = parse_command_line_args(
        ...     cmd, ["--output", "first.txt", "--output", "second.txt"]
        ... )
        Traceback (most recent call last):
            ...OptionNotRepeatableError: Option 'output' is not repeatable.
    """


class OptionKind(str, Enum):
    """Specifies the kind of an option."""

    FLAG = "flag"
    """A boolean flag that does not accept a value."""

    SCALAR = "scalar"
    """An option that requires at most one value."""

    LIST = "list"
    """An option that can accept multiple values."""

    DICT = "dict"
    """An option that accepts key-value pairs."""


class DictMergeStrategy(str, Enum):
    """Defines the merging strategy when `DictAccumulationMode.MERGE` is used."""

    SHALLOW = "shallow"
    """A shallow merge where keys from later occurrences overwrite earlier ones."""

    DEEP = "deep"
    """
    A deep merge where nested dictionaries are merged recursively. (Default)
    """


DEFAULT_MERGE_STRATEGY: "DictMergeStrategy" = DictMergeStrategy.DEEP
