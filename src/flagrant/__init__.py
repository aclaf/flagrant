"""Specification-driven parsing and completion for command-line arguments, options, and subcommands."""  # noqa: E501

from .configuration import ParserConfiguration
from .parser import ParseResult, parse_command_line_args
from .specification import (
    CommandSpecification,
    DictAccumulationMode,
    DictMergeStrategy,
    DictOptionSpecification,
    FlagAccumulationMode,
    FlagOptionSpecification,
    ValueAccumulationMode,
    ValueOptionSpecification,
)

try:
    from importlib.metadata import version

    __version__ = version("flagrant")
except Exception:  # noqa: BLE001
    __version__ = "unknown"

__all__ = [
    "CommandSpecification",
    "DictAccumulationMode",
    "DictMergeStrategy",
    "DictOptionSpecification",
    "FlagAccumulationMode",
    "FlagOptionSpecification",
    "ParseResult",
    "ParserConfiguration",
    "ValueAccumulationMode",
    "ValueOptionSpecification",
    "parse_command_line_args",
]
