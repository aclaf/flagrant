from typing import TYPE_CHECKING

import pytest

from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import OptionMissingValueError

if TYPE_CHECKING:
    from flagrant.specification import (
        CommandSpecificationFactory,
        ValueOptionSpecificationFactory,
    )


class TestValueParsingEdgeCases:
    @pytest.mark.parametrize(
        ("name", "option_kwargs", "args", "expected_value"),
        [
            ("empty_string_via_equals", {}, ["--option="], ""),
            ("whitespace_only", {}, ["--option", "   "], "   "),
            ("value_containing_equals", {}, ["--option", "key=value"], "key=value"),
            (
                "negative_number_allowed",
                {"allow_negative_numbers": True},
                ["--option", "-42"],
                "-42",
            ),
        ],
    )
    def test_value_parsing_edge_cases(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
        name: str,
        option_kwargs: dict[str, bool],
        args: list[str],
        expected_value: str,
    ):
        opt = make_value_opt(**option_kwargs)
        spec = make_command(options={"option": opt})

        result = parse_command_line_args(spec, args)

        assert result.options["option"] == expected_value

    def test_separator_moves_remaining_args_to_extra_args(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="flag")
        spec = make_command(options={"flag": opt})

        result = parse_command_line_args(spec, ["--flag", "value", "--", "--other"])

        assert result.options["flag"] == "value"
        assert result.extra_args == ("--other",)


class TestBoundaryConditions:
    def test_option_at_end_of_args_with_satisfied_arity(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="output")
        spec = make_command(options={"output": opt})

        result = parse_command_line_args(spec, ["--output", "file.txt"])

        assert result.options["output"] == "file.txt"

    def test_option_at_end_of_args_with_unsatisfied_arity_raises_error(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="output")
        spec = make_command(options={"output": opt})

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--output"])
