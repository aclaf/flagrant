"""Specification-driven parsing and completion for command-line arguments, options, and subcommands."""  # noqa: E501

from ._arity import Arity
from ._configuration import ParserConfiguration
from ._parser import parse_arguments
from ._result import ParseResult
from .specification import (
    CommandSpecification,
    DictOptionSpecification,
    FlagOptionSpecification,
    OptionSpecification,
    ValueOptionSpecification,
)

try:
    from importlib.metadata import version

    __version__ = version("flagrant")
except Exception:  # noqa: BLE001
    __version__ = "unknown"

__all__ = [
    "Arity",
    "CommandSpecification",
    "DictOptionSpecification",
    "FlagOptionSpecification",
    "OptionSpecification",
    "ParseResult",
    "ParserConfiguration",
    "ValueOptionSpecification",
    "parse_arguments",
]
