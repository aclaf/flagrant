"""Specifications for commands and their parameters."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ParameterSpecification:
    """Base class for parameter specifications."""

    name: str


class FlagSpecification(ParameterSpecification):
    """Describes a flag parameter (boolean switch)."""


class OptionSpecification(ParameterSpecification):
    """Describes an option parameter (key-value pair)."""


class PositionalSpecification(ParameterSpecification):
    """Describes a positional parameter (ordered argument)."""


@dataclass(slots=True, frozen=True)
class CommandSpecification:
    """Describes a command, including its parameters and subcommands."""

    name: str
