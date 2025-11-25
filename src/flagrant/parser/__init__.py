"""Command-line argument parsing."""

from ._parser import Parser, parse_command_line_args
from ._result import ParseResult

__all__ = [
    "ParseResult",
    "Parser",
    "parse_command_line_args",
]
