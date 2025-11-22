from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from flagrant.specification._arity import get_arity_max, get_arity_min
from flagrant.specification._command import PositionalSpecification
from flagrant.types import (
    NOT_GIVEN,
    ArgPosition,
    CommandPath,
    ExtraArg,
    NotGiven,
    OptionValue,
    PositionalName,
    UngroupedPositional,
)

from .exceptions import PositionalMissingValueError

if TYPE_CHECKING:
    from flagrant.configuration import ParserConfiguration
    from flagrant.specification import (
        CommandSpecification,
    )
    from flagrant.types import (
        ArgList,
        OptionName,
        PositionalValue,
    )

    from ._result import ParseResult


@dataclass(slots=True)
class ParseContext:
    spec: "CommandSpecification"
    path: CommandPath
    config: "ParserConfiguration"
    options: dict["OptionName", "OptionValue"] = field(default_factory=dict)
    ungrouped_positionals: list["UngroupedPositional"] = field(default_factory=list)
    extra_args: list[ExtraArg] = field(default_factory=list)
    subcommand_result: "ParseResult | None" = field(default=None)

    @property
    def positionals_started(self) -> bool:
        return bool(self.ungrouped_positionals)

    @property
    def extra_args_started(self) -> bool:
        return bool(self.extra_args)

    def get_option_value(self, name: "OptionName") -> OptionValue | NotGiven:
        return self.options.get(name, NOT_GIVEN)

    def set_option_value(self, name: "OptionName", value: OptionValue) -> None:
        self.options[name] = value

    def add_positional_value(
        self, value: "PositionalValue", position: ArgPosition
    ) -> None:
        self.ungrouped_positionals.append(UngroupedPositional(value, position))

    def add_extra_arg(self, arg: ExtraArg) -> None:
        self.extra_args.append(arg)

    def group_positionals(
        self,
    ) -> dict["PositionalName", "tuple[PositionalValue, ...] | PositionalValue"]:
        """Group ungrouped positional arguments according to positional specifications.

        Distributes collected positional arguments to their corresponding positional
        specifications based on arity constraints. The algorithm processes positional
        specs left-to-right, making greedy allocation decisions while reserving
        arguments for later positionals with minimum requirements.

        Returns:
            A dictionary mapping positional spec names to their grouped values.
            For arity of exactly 1 (integer 1 or tuple (1, 1)), returns a scalar string.
            For all other arities, returns a tuple of strings.

        Raises:
            PositionalMissingValueError: When there are insufficient positional
                arguments to satisfy all minimum arity requirements.
        """
        # Step 1: Get positional specs
        specs: tuple[PositionalSpecification, ...]
        if self.spec.positionals is None or len(self.spec.positionals) == 0:
            # Create implicit spec that captures all positional arguments
            specs = (PositionalSpecification(name="args", arity=(0, "*")),)
        else:
            specs = self.spec.positionals

        # Extract just the values from ungrouped positionals
        remaining: list[str] = [p.value for p in self.ungrouped_positionals]

        # Step 2: Validate total minimums
        total_min = sum(get_arity_min(spec.arity) for spec in specs)
        if len(remaining) < total_min:
            # Find the first spec that would fail to get its minimum
            # This provides better error context
            first_spec = specs[0] if specs else None
            first_position = (
                self.ungrouped_positionals[0].position
                if self.ungrouped_positionals
                else 0
            )
            msg = (
                f"Insufficient positional arguments: expected at least {total_min}, "
                f"got {len(remaining)}."
            )
            raise PositionalMissingValueError(
                message=msg,
                positional=first_spec.name if first_spec else "args",
                required=total_min,
                received=tuple(remaining) if remaining else None,
                path=self.path,
                args=self._get_args(),
                position=first_position,
            )

        # Step 3 & 4: Process each spec in order and return grouped dict
        grouped: dict[PositionalName, tuple[str, ...] | str] = {}

        for i, spec in enumerate(specs):
            # Calculate later_min: sum of minimums for all following specs
            later_min = sum(get_arity_min(s.arity) for s in specs[i + 1 :])

            # Calculate available values for this spec
            available = len(remaining) - later_min

            # Determine consumption amount based on arity max
            arity_max = get_arity_max(spec.arity)
            if arity_max is None:
                # Unbounded: consume all available after reserving for later specs
                to_consume = max(0, available)
            else:
                # Bounded: consume up to maximum, constrained by availability
                to_consume = min(arity_max, available)

            # Validate minimum requirement
            arity_min = get_arity_min(spec.arity)
            if to_consume < arity_min:
                # Determine position for error reporting
                consumed_count = len(self.ungrouped_positionals) - len(remaining)
                position = (
                    self.ungrouped_positionals[consumed_count].position
                    if remaining and self.ungrouped_positionals
                    else 0
                )
                msg = (
                    f"Positional argument '{spec.name}' requires at least {arity_min} "
                    f"value(s), but only {to_consume} available."
                )
                raise PositionalMissingValueError(
                    message=msg,
                    positional=spec.name,
                    required=spec.arity,
                    received=tuple(remaining[:to_consume]) if remaining else None,
                    path=self.path,
                    args=self._get_args(),
                    position=position,
                )

            # Extract values
            values = remaining[:to_consume]

            # Determine result type based on arity
            # Scalar arity: exactly 1 (integer 1 or tuple (1, 1))
            is_scalar = spec.arity in (1, (1, 1))
            if is_scalar and len(values) == 1:
                grouped[spec.name] = values[0]
            else:
                grouped[spec.name] = tuple(values)

            # Update remaining
            remaining = remaining[to_consume:]

        return grouped

    def _get_args(self) -> "ArgList":
        """Get the full argument list for error reporting.

        Returns:
            The full argument list as a tuple.
        """
        # Reconstruct args from ungrouped positionals and extra args
        # This is a best-effort reconstruction for error reporting
        return tuple(p.value for p in self.ungrouped_positionals)
