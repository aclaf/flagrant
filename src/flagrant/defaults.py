"""Defaults for specifications, configuration, and parsing."""

import re
from typing import Final

from flagrant.enums import DictMergeStrategy, UngroupedPositionalStrategy

DEFAULT_ARGUMENT_FILE_COMMENT_CHARACTER: Final[str] = "#"

DEFAULT_ARGUMENT_FILE_PREFIX: Final[str] = "@"

DEFAULT_CONVERT_UNDERSCORES: Final[bool] = True

DEFAULT_DICT_ESCAPE_CHARACTER: Final[str] = "\\"

DEFAULT_IMPLICIT_POSITIONAL_NAME: Final[str] = "_"

DEFAULT_KEY_VALUE_SEPARATOR: Final[str] = "="

DEFAULT_LONG_NAME_PREFIX: Final[str] = "--"

DEFAULT_MAX_ARGUMENT_FILE_DEPTH: Final[int] = 5

DEFAULT_MERGE_STRATEGY: Final[DictMergeStrategy] = DictMergeStrategy.DEEP

DEFAULT_MINIMUM_ABBREVIATION_LENGTH: Final[int] = 3

DEFAULT_NEGATIVE_NUMBER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^-\d+\.?\d*([eE][+-]?\d+)?([+-]\d+\.?\d*([eE][+-]?\d+)?j|j)?$"
)

DEFAULT_NESTING_SEPARATOR: Final[str] = "."

DEFAULT_OPTION_VALUE_SEPARATOR: Final[str] = "="

DEFAULT_SHORT_NAME_PREFIX: Final[str] = "-"

DEFAULT_TRAILING_ARGUMENTS_SEPARATOR: Final[str] = "--"

DEFAULT_UNGROUPED_POSITIONAL_STRATEGY: Final["UngroupedPositionalStrategy"] = (
    UngroupedPositionalStrategy.IGNORE
)

DEFAULT_VALUE_ESCAPE_CHARACTER: Final[str] = "\\"

DEFAULT_VALUE_ITEM_DELIMITER: Final[str] = ","
