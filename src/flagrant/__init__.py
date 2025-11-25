"""Specification-driven parsing for command-line arguments, options, and subcommands."""

from .configuration import ParserConfiguration
from .parser import Parser, ParseResult, parse_command_line_args
from .specification import (
    CommandSpecification,
    DictAccumulationMode,
    DictMergeStrategy,
    DictOptionSpecification,
    FlagAccumulationMode,
    FlagOptionSpecification,
    ListAccumulationMode,
    ListOptionSpecification,
    ScalarAccumulationMode,
    ScalarOptionSpecification,
    command,
    dict_list_option,
    dict_option,
    flag_option,
    flat_list_option,
    list_option,
    nested_list_option,
    scalar_option,
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
    "ListAccumulationMode",
    "ListOptionSpecification",
    "ParseResult",
    "Parser",
    "ParserConfiguration",
    "ScalarAccumulationMode",
    "ScalarOptionSpecification",
    "command",
    "dict_list_option",
    "dict_option",
    "flag_option",
    "flat_list_option",
    "list_option",
    "nested_list_option",
    "parse_command_line_args",
    "scalar_option",
]
