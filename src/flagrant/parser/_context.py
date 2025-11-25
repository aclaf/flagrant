from dataclasses import dataclass, field
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from flagrant.configuration import ParserConfiguration
    from flagrant.specification import (
        CommandSpecification,
    )
    from flagrant.types import (
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
    ) -> dict["PositionalName", tuple["PositionalValue", ...]]:
        return {}
