from typing import TYPE_CHECKING

import pytest

from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import OptionNotRepeatableError
from flagrant.specification import (
    Arity,
    ValueAccumulationMode,
)

if TYPE_CHECKING:
        from flagrant.specification import (
        CommandSpecificationFactory,
        ValueOptionSpecificationFactory,
        )

class TestValueAccumulationModes:
    @pytest.mark.parametrize(
        ("accumulation_mode", "input_args", "expected_result"),
        [
            (
                ValueAccumulationMode.LAST,
                ["--output", "first.txt", "--output", "second.txt"],
                "second.txt",
            ),
            (
                ValueAccumulationMode.LAST,
                ["--point", "1", "2", "--point", "3", "4"],
                ("3", "4"),
            ),
            (
                ValueAccumulationMode.APPEND,
                ["--output", "first.txt", "--output", "second.txt"],
                ("first.txt", "second.txt"),
            ),
            (
                ValueAccumulationMode.APPEND,
                ["--point", "1", "2", "--point", "3", "4"],
                (("1", "2"), ("3", "4")),
            ),
            (
                ValueAccumulationMode.EXTEND,
                ["--file", "a.txt", "--file", "b.txt", "--file", "c.txt"],
                ("a.txt", "b.txt", "c.txt"),
            ),
            (
                ValueAccumulationMode.EXTEND,
                ["--point", "1", "2", "--point", "3", "4"],
                ("1", "2", "3", "4"),
            ),
        ],
    )
    def test_value_accumulation_modes(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
        accumulation_mode: ValueAccumulationMode,
        input_args: list[str],
        expected_result: str | tuple[str, ...] | tuple[tuple[str, ...], ...],
    ):
        # Extract option name from input arguments
        name = input_args[0].lstrip("-")

        # Determine arity based on the option name used in test cases
        if name == "point":
            arity = Arity(2, 2)
        elif name == "file":
            arity = Arity.at_least_one()
        else:
            arity = Arity.exactly_one()

        opt = make_value_opt(
            name=name, arity=arity, accumulation_mode=accumulation_mode
        )
        spec = make_command(options={name: opt})

        result = parse_command_line_args(spec, input_args)

        assert result.options[name] == expected_result

    def test_value_error_mode_raises_on_second_occurrence(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="output", accumulation_mode=ValueAccumulationMode.ERROR
        )
        spec = make_command(options={"output": opt})

        with pytest.raises(OptionNotRepeatableError):
            parse_command_line_args(
                spec, ["--output", "first.txt", "--output", "second.txt"]
            )
