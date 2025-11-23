import pytest

from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import OptionNotRepeatableError
from flagrant.specification import (
    Arity,
    CommandSpecification,
    FlagOptionSpecification,
    ValueOptionSpecification,
)
from flagrant.specification.enums import (
    FlagAccumulationMode,
    ValueAccumulationMode,
)


class TestFlagAccumulationModes:
    def test_flag_last_mode_returns_true_when_specified(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=(),
                    accumulation_mode=FlagAccumulationMode.LAST,
                )
            },
        )

        result = parse_command_line_args(spec, ["--verbose"])

        assert result.options["verbose"] is True

    def test_flag_last_mode_overwrites_on_multiple_occurrences(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=("v",),
                    accumulation_mode=FlagAccumulationMode.LAST,
                )
            },
        )

        result = parse_command_line_args(spec, ["--verbose", "-v", "--verbose"])

        assert result.options["verbose"] is True

    def test_flag_count_mode_counts_occurrences(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=("v",),
                    accumulation_mode=FlagAccumulationMode.COUNT,
                )
            },
        )

        result = parse_command_line_args(spec, ["--verbose", "-v", "--verbose"])

        assert result.options["verbose"] == 3

    def test_flag_count_mode_single_occurrence_returns_one(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=("v",),
                    accumulation_mode=FlagAccumulationMode.COUNT,
                )
            },
        )

        result = parse_command_line_args(spec, ["--verbose"])

        assert result.options["verbose"] == 1

    def test_flag_count_mode_with_clustering_counts_each_character(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=("v",),
                    accumulation_mode=FlagAccumulationMode.COUNT,
                )
            },
        )

        result = parse_command_line_args(spec, ["-vvv"])

        assert result.options["verbose"] == 3

    def test_flag_first_mode_keeps_first_occurrence(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=("v",),
                    accumulation_mode=FlagAccumulationMode.FIRST,
                )
            },
        )

        result = parse_command_line_args(spec, ["--verbose", "-v", "--verbose"])

        assert result.options["verbose"] is True

    def test_flag_error_mode_raises_on_second_occurrence(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=(),
                    accumulation_mode=FlagAccumulationMode.ERROR,
                )
            },
        )

        with pytest.raises(OptionNotRepeatableError):
            parse_command_line_args(spec, ["--verbose", "--verbose"])


class TestValueAccumulationModes:
    def test_value_last_mode_returns_most_recent_value(self):
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
                    accumulation_mode=ValueAccumulationMode.LAST,
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--output", "first.txt", "--output", "second.txt"]
        )

        assert result.options["output"] == "second.txt"

    def test_value_last_mode_with_arity_two_returns_last_pair(self):
        spec = CommandSpecification(
            "test",
            options={
                "point": ValueOptionSpecification(
                    name="point",
                    arity=Arity(2, 2),
                    greedy=False,
                    preferred_name="point",
                    long_names=("point",),
                    short_names=(),
                    accumulation_mode=ValueAccumulationMode.LAST,
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--point", "1", "2", "--point", "3", "4"]
        )

        assert result.options["point"] == ("3", "4")

    def test_value_append_mode_creates_list_of_values(self):
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
                    accumulation_mode=ValueAccumulationMode.APPEND,
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--output", "first.txt", "--output", "second.txt"]
        )

        assert result.options["output"] == ("first.txt", "second.txt")

    def test_value_append_mode_with_arity_two_creates_nested_tuples(self):
        spec = CommandSpecification(
            "test",
            options={
                "point": ValueOptionSpecification(
                    name="point",
                    arity=Arity(2, 2),
                    greedy=False,
                    preferred_name="point",
                    long_names=("point",),
                    short_names=(),
                    accumulation_mode=ValueAccumulationMode.APPEND,
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--point", "1", "2", "--point", "3", "4"]
        )

        assert result.options["point"] == (("1", "2"), ("3", "4"))

    def test_value_extend_mode_flattens_all_values(self):
        spec = CommandSpecification(
            "test",
            options={
                "file": ValueOptionSpecification(
                    name="file",
                    arity=Arity.at_least_one(),
                    greedy=False,
                    preferred_name="file",
                    long_names=("file",),
                    short_names=(),
                    accumulation_mode=ValueAccumulationMode.EXTEND,
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--file", "a.txt", "--file", "b.txt", "--file", "c.txt"]
        )

        assert result.options["file"] == ("a.txt", "b.txt", "c.txt")

    def test_value_extend_mode_with_arity_two_flattens_all_values(self):
        spec = CommandSpecification(
            "test",
            options={
                "point": ValueOptionSpecification(
                    name="point",
                    arity=Arity(2, 2),
                    greedy=False,
                    preferred_name="point",
                    long_names=("point",),
                    short_names=(),
                    accumulation_mode=ValueAccumulationMode.EXTEND,
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--point", "1", "2", "--point", "3", "4"]
        )

        assert result.options["point"] == ("1", "2", "3", "4")

    def test_value_error_mode_raises_on_second_occurrence(self):
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
                    accumulation_mode=ValueAccumulationMode.ERROR,
                )
            },
        )

        with pytest.raises(OptionNotRepeatableError):
            parse_command_line_args(
                spec, ["--output", "first.txt", "--output", "second.txt"]
            )
