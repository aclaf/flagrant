"""Specifications for defining commands and parameters."""

from ._command import CommandSpecification
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

__all__ = [
    "CommandSpecification",
    "DictOptionSpecification",
    "FlagOptionSpecification",
    "NonFlagOptionSpecificationType",
    "OptionSpecification",
    "OptionSpecificationType",
    "ValueOptionSpecification",
    "is_dict_option",
    "is_flag_option",
    "is_value_option",
]
