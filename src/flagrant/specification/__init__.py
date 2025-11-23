"""Specifications for defining commands and parameters."""

from ._arity import Arity
from ._command import CommandSpecification, CommandSpecificationFactory, OptionResult
from ._options import (
    DictOptionSpecification,
    DictOptionSpecificationFactory,
    FlagOptionSpecification,
    FlagOptionSpecificationFactory,
    NonFlagOptionSpecificationType,
    OptionSpecification,
    OptionSpecificationFactory,
    OptionSpecificationType,
    ValueOptionSpecification,
    ValueOptionSpecificationFactory,
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
    "CommandSpecificationFactory",
    "DictAccumulationMode",
    "DictMergeStrategy",
    "DictOptionSpecification",
    "DictOptionSpecificationFactory",
    "FlagAccumulationMode",
    "FlagOptionSpecification",
    "FlagOptionSpecificationFactory",
    "NonFlagOptionSpecificationType",
    "OptionResult",
    "OptionSpecification",
    "OptionSpecificationFactory",
    "OptionSpecificationType",
    "ValueAccumulationMode",
    "ValueOptionSpecification",
    "ValueOptionSpecificationFactory",
    "is_dict_option",
    "is_flag_option",
    "is_value_option",
]
