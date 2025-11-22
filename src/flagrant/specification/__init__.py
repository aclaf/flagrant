"""Specifications for defining commands and parameters."""

from ._arity import Arity
from ._command import CommandSpecification, OptionResult
from ._options import (
    DictOptionSpecification,
    FlagOptionSpecification,
    NonFlagOptionSpecificationType,
    OptionSpecification,
    OptionSpecificationType,
    ValueOptionSpecification,
    is_dict_option,
    is_flag_option,
    is_value_option,
)
from .enums import (
    DictAccumulationMode,
    DictMergeStrategy,
    FlagAccumulationMode,
    ValueAccumulationMode,
)

__all__ = [
    "Arity",
    "CommandSpecification",
    "DictAccumulationMode",
    "DictMergeStrategy",
    "DictOptionSpecification",
    "FlagAccumulationMode",
    "FlagOptionSpecification",
    "NonFlagOptionSpecificationType",
    "OptionResult",
    "OptionSpecification",
    "OptionSpecificationType",
    "ValueAccumulationMode",
    "ValueOptionSpecification",
    "is_dict_option",
    "is_flag_option",
    "is_value_option",
]
