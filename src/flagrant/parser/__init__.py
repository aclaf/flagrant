"""Command-line argument parsing."""

from ._parser import parse_command_line_args
from ._result import ParseResult

__all__ = [
    "ParseResult",
    "parse_command_line_args",
]
