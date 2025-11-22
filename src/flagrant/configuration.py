"""Parser configuration settings."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from flagrant.defaults import (
    DEFAULT_ARGUMENT_FILE_COMMENT_CHARACTER,
    DEFAULT_ARGUMENT_FILE_PREFIX,
    DEFAULT_DICT_ESCAPE_CHARACTER,
    DEFAULT_IMPLICIT_POSITIONAL_NAME,
    DEFAULT_KEY_VALUE_SEPARATOR,
    DEFAULT_LONG_NAME_PREFIX,
    DEFAULT_MAX_ARGUMENT_FILE_DEPTH,
    DEFAULT_MINIMUM_ABBREVIATION_LENGTH,
    DEFAULT_NEGATIVE_NUMBER_PATTERN,
    DEFAULT_NESTING_SEPARATOR,
    DEFAULT_OPTION_VALUE_SEPARATOR,
    DEFAULT_SHORT_NAME_PREFIX,
    DEFAULT_TRAILING_ARGUMENTS_SEPARATOR,
    DEFAULT_VALUE_ESCAPE_CHARACTER,
    DEFAULT_VALUE_ITEM_DELIMITER,
)
from flagrant.enums import (
    DEFAULT_UNGROUPED_POSITIONAL_STRATEGY,
    ArgumentFileFormat,
    UngroupedPositionalStrategy,
)
from flagrant.exceptions import ConfigurationError
from flagrant.specification.enums import DEFAULT_MERGE_STRATEGY

if TYPE_CHECKING:
    from pathlib import Path
    from re import Pattern

    from flagrant.specification.enums import DictMergeStrategy


@dataclass(slots=True, frozen=True)
class ParserConfiguration:
    r"""Specifies the behavior of the parser.

    This object contains all configurable settings that control how arguments are
    parsed and how different syntaxes are handled.

    Attributes:
        allow_abbreviated_options: If True, allows long options to be abbreviated
            to any unambiguous prefix. Defaults to False.
        allow_abbreviated_subcommands: If True, allows subcommand names to be
            abbreviated to any unambiguous prefix. Defaults to False.
        allow_command_aliases: If True, allows commands to be invoked by their
            defined aliases. Defaults to True.
        allow_duplicate_list_indices: If True, allows dictionary options to specify
            the same list index multiple times. Defaults to False.
        allow_negative_numbers: If True, allows values that look like negative
            numbers (e.g., "-5") to be parsed as values instead of options.
            Defaults to True.
        allow_sparse_lists: If True, allows dictionary options to define lists
            with non-sequential indices (e.g., `list[0]=a list[2]=b`).
            Defaults to False.
        argument_file_comment_character: The character that indicates a comment
            within an argument file. Defaults to "#".
        argument_file_allowed_path_patterns: Tuple of glob patterns for allowed
            argument file paths. Defaults to None (no restrictions).
        argument_file_allowed_paths: Tuple of specific allowed argument file paths.
            Defaults to None (no restrictions).
        argument_file_denied_path_patterns: Tuple of glob patterns for denied
            argument file paths. Defaults to None (no restrictions).
        argument_file_denied_paths: Tuple of specific denied argument file paths.
            Defaults to None (no restrictions).
        argument_file_format: The default format for parsing argument files.
            See [ArgumentFileFormat][flagrant.enums.ArgumentFileFormat] for options.
            Defaults to `LINE`.
        argument_file_prefix: The character that signals an argument is a path
            to an argument file. Defaults to "@".
        argument_files_enabled: If True, enables support for argument files.
            Defaults to True.
        case_sensitive_commands: If True, subcommand names are case-sensitive.
            Defaults to True.
        case_sensitive_keys: If True, keys in dictionary options are case-sensitive.
            Defaults to True.
        case_sensitive_options: If True, long option names are case-sensitive.
            Defaults to True.
        convert_underscores: If True, automatically treats underscores (`_`) and
            hyphens (`-`) as equivalent in option and subcommand names.
            Defaults to True.
        dict_escape_character: The character used to escape separators within
            dictionary option values. Defaults to "\\".
        dict_item_separator: The character separating key-value pairs within a
            single dictionary option argument. Defaults to None (not enabled).
        key_value_separator: The character that separates a key from its value
            in a dictionary option. Defaults to "=".
        long_name_prefix: The string that prefixes a long option name.
            Defaults to "--".
        max_argument_file_depth: The maximum number of nested argument files
            allowed to prevent infinite recursion. Defaults to 5.
        merge_strategy: The default strategy for merging dictionaries when
            [DictAccumulationMode.MERGE][flagrant.enums.DictAccumulationMode.MERGE]
            is used. See [DictMergeStrategy][flagrant.enums.DictMergeStrategy].
            Defaults to `DEEP`.
        minimum_abbreviation_length: The minimum number of characters required
            for an abbreviated option or subcommand. Defaults to 1.
        negative_number_pattern: The regular expression used to identify strings
            that should be treated as negative numbers.
        nesting_separator: The character used to denote nested keys in a
            dictionary option. Defaults to ".".
        short_name_prefix: The string that prefixes a short option name.
            Defaults to "-".
        strict_structure: If True, enforces strict structural rules during
            dictionary parsing. Defaults to True.
        strict_options_before_positionals: If True, all positional arguments must
            appear after all options. If False, they can be interspersed.
            Defaults to False.
        trailing_arguments_separator: The string that signifies the end of options;
            all subsequent arguments are treated as positionals. Defaults to "--".
        ungrouped_positional_strategy: The strategy for handling ungrouped
            positional arguments. See
            [UngroupedPositionalStrategy][flagrant.enums.UngroupedPositionalStrategy].
            Defaults to `IGNORE`.
        value_escape_character: The character used to escape separators within
            value option values. Defaults to "\\".
        value_item_separator: The character separating multiple values within a
            single value option argument. Defaults to ",".
    """

    allow_abbreviated_options: bool = False
    allow_abbreviated_subcommands: bool = False
    allow_command_aliases: bool = True
    allow_duplicate_list_indices: bool = False
    allow_inline_values_without_equals: bool = False
    allow_negative_numbers: bool = True
    allow_sparse_lists: bool = False
    argument_file_allowed_path_patterns: tuple["Pattern[str]", ...] | None = None
    argument_file_allowed_paths: tuple["Path", ...] | None = None
    argument_file_denied_path_patterns: tuple["Pattern[str]", ...] | None = None
    argument_file_denied_paths: tuple["Path", ...] | None = None
    argument_file_comment_character: str = DEFAULT_ARGUMENT_FILE_COMMENT_CHARACTER
    argument_file_format: ArgumentFileFormat = ArgumentFileFormat.LINE
    argument_files_enabled: bool = True
    argument_file_prefix: str = DEFAULT_ARGUMENT_FILE_PREFIX
    case_sensitive_commands: bool = True
    case_sensitive_keys: bool = True
    case_sensitive_options: bool = True
    convert_underscores: bool = True
    dict_escape_character: str | None = DEFAULT_DICT_ESCAPE_CHARACTER
    dict_item_separator: str | None = None
    ungrouped_positional_name: str = DEFAULT_IMPLICIT_POSITIONAL_NAME
    key_value_separator: str = DEFAULT_KEY_VALUE_SEPARATOR
    long_name_prefix: str = DEFAULT_LONG_NAME_PREFIX
    max_argument_file_depth: int = DEFAULT_MAX_ARGUMENT_FILE_DEPTH
    merge_strategy: "DictMergeStrategy" = DEFAULT_MERGE_STRATEGY
    minimum_abbreviation_length: int = DEFAULT_MINIMUM_ABBREVIATION_LENGTH
    option_value_separator: str = DEFAULT_OPTION_VALUE_SEPARATOR
    negative_number_pattern: "Pattern[str]" = DEFAULT_NEGATIVE_NUMBER_PATTERN
    nesting_separator: str = DEFAULT_NESTING_SEPARATOR
    short_name_prefix: str = DEFAULT_SHORT_NAME_PREFIX
    strict_structure: bool = True
    strict_posix_options: bool = False
    trailing_arguments_separator: str = DEFAULT_TRAILING_ARGUMENTS_SEPARATOR
    ungrouped_positional_strategy: UngroupedPositionalStrategy = (
        DEFAULT_UNGROUPED_POSITIONAL_STRATEGY
    )
    value_escape_character: str = DEFAULT_VALUE_ESCAPE_CHARACTER
    value_item_separator: str = DEFAULT_VALUE_ITEM_DELIMITER

    def __post_init__(self) -> None:
        """Validate configuration settings."""
        if self.key_value_separator == self.dict_item_separator:
            msg = "key_value_separator and dict_item_separator cannot be the same."
            raise ConfigurationError(msg)

        if self.key_value_separator == self.nesting_separator:
            msg = "key_value_separator and nesting_separator cannot be the same."
            raise ConfigurationError(msg)

        if self.long_name_prefix == self.short_name_prefix:
            msg = "long_name_prefix and short_name_prefix cannot be the same."
            raise ConfigurationError(msg)

        if self.max_argument_file_depth < 1:
            msg = "max_argument_file_depth must be at least 1."
            raise ConfigurationError(msg)

        if self.minimum_abbreviation_length < 1:
            msg = "minimum_abbreviation_length must be at least 1."
            raise ConfigurationError(msg)

        if self.short_name_prefix == self.trailing_arguments_separator:
            msg = (
                "short_name_prefix and trailing_arguments_separator cannot be the same."
            )
            raise ConfigurationError(msg)
