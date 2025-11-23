import pytest

from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import OptionMissingValueError
from flagrant.specification import (
    Arity,
    CommandSpecification,
    ValueOptionSpecification,
)


class TestEmptyValueHandling:
    def test_option_with_empty_string_value_via_equals(self):
        spec = CommandSpecification(
            "test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=("output",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--output="])

        assert result.options["output"] == ""

    def test_option_with_whitespace_only_value_preserves_whitespace(self):
        spec = CommandSpecification(
            "test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=("output",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--output", "   "])

        assert result.options["output"] == "   "


class TestSpecialCharacterValues:
    def test_value_containing_equals_sign_preserved(self):
        spec = CommandSpecification(
            "test",
            options={
                "config": ValueOptionSpecification(
                    name="config",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="config",
                    long_names=("config",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--config", "key=value"])

        assert result.options["config"] == "key=value"

    def test_value_with_leading_hyphen_when_negative_numbers_allowed(self):
        spec = CommandSpecification(
            "test",
            options={
                "number": ValueOptionSpecification(
                    name="number",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="number",
                    long_names=("number",),
                    short_names=(),
                    allow_negative_numbers=True,
                )
            },
        )

        result = parse_command_line_args(spec, ["--number", "-42"])

        assert result.options["number"] == "-42"

    def test_separator_moves_remaining_args_to_extra_args(self):
        spec = CommandSpecification(
            "test",
            options={
                "flag": ValueOptionSpecification(
                    name="flag",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="flag",
                    long_names=("flag",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--flag", "value", "--", "--other"])

        assert result.options["flag"] == "value"
        assert result.extra_args == ("--other",)


class TestBoundaryConditions:
    def test_option_at_end_of_args_with_satisfied_arity(self):
        spec = CommandSpecification(
            "test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=("output",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--output", "file.txt"])

        assert result.options["output"] == "file.txt"

    def test_option_at_end_of_args_with_unsatisfied_arity_raises_error(self):
        spec = CommandSpecification(
            "test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=("output",),
                    short_names=(),
                )
            },
        )

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--output"])
