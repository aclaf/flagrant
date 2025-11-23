"""Static constraints for specifications, configuration, and parsing."""

import re
from typing import Final

COMMAND_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-zA-Z0-9][a-zA-Z0-9-_]*$"
)

MINIMUM_LONG_OPTION_NAME_LENGTH = 2

LONG_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-_]*$")

NEGATIVE_PREFIX_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-zA-Z0-9][a-zA-Z0-9-_]*$"
)

NEGATIVE_PREFIX_SEPARATOR: Final[str] = "-"

PARAMETER_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[a-zA-Z_][a-zA-Z0-9_-]*$"
)

SHORT_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-zA-Z0-9]$")
