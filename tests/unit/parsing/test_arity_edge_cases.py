import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import (
    OptionMissingValueError,
    OptionValueNotAllowedError,
)
from flagrant.specification import (
    Arity,
    CommandSpecification,
    FlagOptionSpecification,
    ValueAccumulationMode,
    ValueOptionSpecification,
)


class TestCombinedShortOptionsWithArity:
    def test_clustered_short_flags_with_trailing_value_option_consumes_next_arg(self):
        spec = CommandSpecification(
            "test",
            options={
                "a": FlagOptionSpecification(
                    name="a",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="a",
                    long_names=(),
                    short_names=("a",),
                ),
                "b": FlagOptionSpecification(
                    name="b",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="b",
                    long_names=(),
                    short_names=("b",),
                ),
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="o",
                    long_names=(),
                    short_names=("o",),
                ),
            },
        )

        result = parse_command_line_args(spec, ["-abo", "file.txt"])

        assert result.options["a"] is True
        assert result.options["b"] is True
        assert result.options["output"] == "file.txt"

    def test_clustered_short_with_inline_value_for_last_option(self):
        spec = CommandSpecification(
            "test",
            options={
                "a": FlagOptionSpecification(
                    name="a",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="a",
                    long_names=(),
                    short_names=("a",),
                ),
                "b": FlagOptionSpecification(
                    name="b",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="b",
                    long_names=(),
                    short_names=("b",),
                ),
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="o",
                    long_names=(),
                    short_names=("o",),
                ),
            },
        )

        result = parse_command_line_args(spec, ["-abofile.txt"])

        assert result.options["a"] is True
        assert result.options["b"] is True
        assert result.options["output"] == "file.txt"

    def test_clustered_short_with_value_option_requiring_two_values(self):
        spec = CommandSpecification(
            "test",
            options={
                "a": FlagOptionSpecification(
                    name="a",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="a",
                    long_names=(),
                    short_names=("a",),
                ),
                "coords": ValueOptionSpecification(
                    name="coords",
                    arity=Arity(2, 2),
                    greedy=False,
                    preferred_name="c",
                    long_names=(),
                    short_names=("c",),
                ),
            },
        )

        result = parse_command_line_args(spec, ["-ac", "10", "20"])

        assert result.options["a"] is True
        assert result.options["coords"] == ("10", "20")

    def test_clustered_short_with_multiple_value_options_raises_runtime_error(self):
        spec = CommandSpecification(
            "test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="o",
                    long_names=(),
                    short_names=("o",),
                ),
                "input": ValueOptionSpecification(
                    name="input",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="i",
                    long_names=(),
                    short_names=("i",),
                ),
            },
        )

        with pytest.raises(
            RuntimeError,
            match="Unexpected consumption of arguments for inner short option",
        ):
            parse_command_line_args(spec, ["-oi", "file.txt"])

    def test_clustered_short_with_unbounded_arity_consumes_remaining_args(self):
        spec = CommandSpecification(
            "test",
            options={
                "a": FlagOptionSpecification(
                    name="a",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="a",
                    long_names=(),
                    short_names=("a",),
                ),
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity.at_least_one(),
                    greedy=False,
                    preferred_name="f",
                    long_names=(),
                    short_names=("f",),
                ),
            },
        )

        result = parse_command_line_args(spec, ["-af", "a.txt", "b.txt", "c.txt"])

        assert result.options["a"] is True
        assert result.options["files"] == ("a.txt", "b.txt", "c.txt")


class TestArityWithTrailingSeparator:
    @pytest.mark.xfail(
        reason=(
            "BUG: Non-greedy options consume values through the -- "
            "separator instead of stopping at it"
        )
    )
    def test_separator_stops_value_collection_for_unbounded_arity(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity.zero_or_more(),
                    greedy=False,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--files", "a.txt", "--", "b.txt"])

        assert result.options["files"] == ("a.txt",)
        assert result.extra_args == ("b.txt",)

    @pytest.mark.xfail(
        reason=(
            "BUG: Non-greedy options consume values through the -- "
            "separator instead of stopping at it"
        )
    )
    def test_separator_stops_value_collection_for_bounded_arity(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity(1, 3),
                    greedy=False,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--values", "one", "--", "two"])

        assert result.options["values"] == ("one",)
        assert result.extra_args == ("two",)

    @pytest.mark.xfail(
        reason=(
            "BUG: Non-greedy options consume values through the -- "
            "separator instead of stopping at it"
        )
    )
    def test_separator_causes_insufficient_values_error_when_arity_not_met(self):
        spec = CommandSpecification(
            "test",
            options={
                "coords": ValueOptionSpecification(
                    name="coords",
                    arity=Arity(2, 2),
                    greedy=False,
                    preferred_name="coords",
                    long_names=("coords",),
                    short_names=(),
                )
            },
        )

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--coords", "10", "--", "20"])

    @pytest.mark.xfail(
        reason=(
            "BUG: Non-greedy options consume values through the -- "
            "separator instead of stopping at it"
        )
    )
    def test_separator_after_satisfying_minimum_arity_succeeds(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity(2, 5),
                    greedy=False,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--values", "1", "2", "--", "3"])

        assert result.options["values"] == ("1", "2")
        assert result.extra_args == ("3",)

    @pytest.mark.xfail(
        reason=(
            "BUG: Non-greedy options consume values through the -- "
            "separator instead of stopping at it"
        )
    )
    def test_separator_immediately_after_option_with_optional_arity_succeeds(self):
        spec = CommandSpecification(
            "test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.at_most_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=("output",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--output", "--", "arg"])

        assert result.options["output"] == ()
        assert result.extra_args == ("arg",)


class TestMixedArityInAccumulationModes:
    def test_append_mode_with_different_value_counts_creates_nested_tuples(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity(1, 3),
                    greedy=False,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                    accumulation_mode=ValueAccumulationMode.APPEND,
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--values", "1", "--values", "2", "3", "--values", "4", "5", "6"]
        )

        assert result.options["values"] == (("1",), ("2", "3"), ("4", "5", "6"))

    def test_extend_mode_flattens_different_value_counts(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity(1, 3),
                    greedy=False,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                    accumulation_mode=ValueAccumulationMode.EXTEND,
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--values", "1", "--values", "2", "3", "--values", "4", "5", "6"]
        )

        assert result.options["values"] == ("1", "2", "3", "4", "5", "6")

    def test_last_mode_keeps_most_recent_value_count(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity(1, 3),
                    greedy=False,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                    accumulation_mode=ValueAccumulationMode.LAST,
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--values", "1", "--values", "2", "3"]
        )

        assert result.options["values"] == ("2", "3")

    def test_first_mode_keeps_first_value_count(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity(1, 3),
                    greedy=False,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                    accumulation_mode=ValueAccumulationMode.FIRST,
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--values", "1", "--values", "2", "3"]
        )

        assert result.options["values"] == ("1",)


class TestArityBoundaryValidation:
    def test_exact_arity_boundary_min_equals_max_one(self):
        spec = CommandSpecification(
            "test",
            options={
                "value": ValueOptionSpecification(
                    name="value",
                    arity=Arity(1, 1),
                    greedy=False,
                    preferred_name="value",
                    long_names=("value",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--value", "item"])

        assert result.options["value"] == "item"

    def test_exact_arity_boundary_min_equals_max_ten(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity(10, 10),
                    greedy=False,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--values", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
        )

        assert result.options["values"] == (
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
        )

    def test_exact_arity_boundary_min_equals_max_ten_with_insufficient_raises_error(
        self,
    ):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity(10, 10),
                    greedy=False,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                )
            },
        )

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(
                spec, ["--values", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
            )

    def test_zero_arity_flag_behavior_confirmed(self):
        spec = CommandSpecification(
            "test",
            options={
                "flag": FlagOptionSpecification(
                    name="flag",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="flag",
                    long_names=("flag",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--flag"])

        assert result.options["flag"] is True

    def test_very_large_exact_arity_boundary_fifty_values(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity(50, 50),
                    greedy=False,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                )
            },
        )

        args = ["--values"] + [str(i) for i in range(1, 51)]
        result = parse_command_line_args(spec, args)

        values = result.options["values"]
        assert isinstance(values, tuple)
        assert len(values) == 50
        assert values[0] == "1"
        assert values[49] == "50"


class TestGreedyModeArityInteractions:
    def test_greedy_mode_stops_at_subcommand_respecting_minimum_arity(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity(2, None),
                    greedy=True,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
            subcommands={"build": CommandSpecification("build")},
        )

        result = parse_command_line_args(
            spec, ["--files", "a.txt", "b.txt", "build"]
        )

        assert result.options["files"] == ("a.txt", "b.txt")
        assert result.subcommand is not None
        assert result.subcommand.command == "build"

    def test_greedy_mode_with_negative_numbers_when_allowed(self):
        spec = CommandSpecification(
            "test",
            options={
                "numbers": ValueOptionSpecification(
                    name="numbers",
                    arity=Arity.at_least_one(),
                    greedy=True,
                    preferred_name="numbers",
                    long_names=("numbers",),
                    short_names=(),
                    allow_negative_numbers=True,
                )
            },
        )
        config = ParserConfiguration(allow_negative_numbers=True)

        result = parse_command_line_args(
            spec, ["--numbers", "10", "-5", "-3.14", "20"], config=config
        )

        assert result.options["numbers"] == ("10", "-5", "-3.14", "20")

    def test_greedy_mode_with_negative_numbers_disabled_consumes_as_values(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity.at_least_one(),
                    greedy=True,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                )
            },
        )
        config = ParserConfiguration(allow_negative_numbers=False)

        result = parse_command_line_args(
            spec, ["--values", "a", "-b", "-c"], config=config
        )

        assert result.options["values"] == ("a", "-b", "-c")

    def test_greedy_mode_stops_at_known_option_even_with_negative_numbers(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity.at_least_one(),
                    greedy=True,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                    allow_negative_numbers=True,
                ),
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=("output",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_negative_numbers=True)

        result = parse_command_line_args(
            spec, ["--values", "10", "-5", "--output", "file.txt"], config=config
        )

        assert result.options["values"] == ("10", "-5")
        assert result.options["output"] == "file.txt"


class TestArityWithInlineValues:
    def test_inline_value_counts_toward_arity_minimum(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity(2, 3),
                    greedy=False,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--files=a.txt", "b.txt"])

        assert result.options["files"] == ("a.txt", "b.txt")

    def test_inline_value_with_unbounded_arity_collects_additional_values(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity.zero_or_more(),
                    greedy=False,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--files=a.txt", "b.txt", "c.txt"])

        assert result.options["files"] == ("a.txt", "b.txt", "c.txt")

    def test_inline_value_insufficient_for_minimum_arity_raises_error(self):
        spec = CommandSpecification(
            "test",
            options={
                "coords": ValueOptionSpecification(
                    name="coords",
                    arity=Arity(3, 3),
                    greedy=False,
                    preferred_name="coords",
                    long_names=("coords",),
                    short_names=(),
                )
            },
        )

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--coords=10", "20"])

    def test_short_option_inline_value_counts_toward_arity(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity(2, 2),
                    greedy=False,
                    preferred_name="f",
                    long_names=(),
                    short_names=("f",),
                )
            },
        )

        result = parse_command_line_args(spec, ["-f=a.txt", "b.txt"])

        assert result.options["files"] == ("a.txt", "b.txt")

    def test_clustered_short_with_inline_value_counts_toward_arity(self):
        spec = CommandSpecification(
            "test",
            options={
                "a": FlagOptionSpecification(
                    name="a",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="a",
                    long_names=(),
                    short_names=("a",),
                ),
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity(2, 2),
                    greedy=False,
                    preferred_name="f",
                    long_names=(),
                    short_names=("f",),
                ),
            },
        )

        result = parse_command_line_args(spec, ["-afone.txt", "two.txt"])

        assert result.options["a"] is True
        assert result.options["files"] == ("one.txt", "two.txt")


class TestArityErrorCasesAndEdgeBehaviors:
    def test_arity_cannot_be_satisfied_due_to_end_of_input(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity(3, 5),
                    greedy=False,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                )
            },
        )

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--values", "1", "2"])

    def test_arity_satisfied_at_end_of_input(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity(2, 5),
                    greedy=False,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--values", "1", "2"])

        assert result.options["values"] == ("1", "2")

    def test_values_that_look_like_unknown_options_consumed_as_values(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity(2, 2),
                    greedy=False,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--values", "--other", "value"])

        assert result.options["values"] == ("--other", "value")

    def test_values_with_special_characters_counted_correctly(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity(3, 3),
                    greedy=False,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--values", "key=value", "foo:bar", "path/to/file"]
        )

        assert result.options["values"] == ("key=value", "foo:bar", "path/to/file")

    def test_single_dash_value_counted_in_arity(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity(3, 3),
                    greedy=False,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--values", "-", "a", "b"])

        assert result.options["values"] == ("-", "a", "b")

    def test_empty_string_values_counted_in_arity(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity(2, 2),
                    greedy=False,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--values=", "nonempty"])

        assert result.options["values"] == ("", "nonempty")


class TestArityWithPositionalsInteraction:
    def test_option_arity_consumes_before_positionals(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity(2, 2),
                    greedy=False,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
            positionals={"args": Arity.zero_or_more()},
        )

        result = parse_command_line_args(
            spec, ["--files", "a.txt", "b.txt", "c.txt", "d.txt"]
        )

        assert result.options["files"] == ("a.txt", "b.txt")
        assert result.positionals["args"] == ("c.txt", "d.txt")

    def test_option_unbounded_arity_stops_before_positionals_when_next_option_appears(
        self,
    ):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity.zero_or_more(),
                    greedy=False,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                ),
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=(),
                ),
            },
            positionals={"args": Arity.zero_or_more()},
        )

        result = parse_command_line_args(
            spec, ["--files", "a.txt", "b.txt", "--verbose", "c.txt"]
        )

        assert result.options["files"] == ("a.txt", "b.txt")
        assert result.options["verbose"] is True
        assert result.positionals["args"] == ("c.txt",)

    @pytest.mark.xfail(
        reason=(
            "BUG: Parser fails with StopIteration when positionals "
            "follow option with range arity"
        )
    )
    def test_option_with_range_arity_leaves_values_for_positionals(self):
        spec = CommandSpecification(
            "test",
            options={
                "prefix": ValueOptionSpecification(
                    name="prefix",
                    arity=Arity(1, 2),
                    greedy=False,
                    preferred_name="prefix",
                    long_names=("prefix",),
                    short_names=(),
                )
            },
            positionals={"file": Arity.exactly_one(), "output": Arity.exactly_one()},
        )

        result = parse_command_line_args(
            spec, ["--prefix", "pre", "input.txt", "output.txt"]
        )

        assert result.options["prefix"] == ("pre",)
        assert result.positionals["file"] == "input.txt"
        assert result.positionals["output"] == "output.txt"


class TestArityZeroEdgeCases:
    def test_zero_arity_option_with_equals_value_raises_error(self):
        spec = CommandSpecification(
            "test",
            options={
                "flag": FlagOptionSpecification(
                    name="flag",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="flag",
                    long_names=("flag",),
                    short_names=(),
                )
            },
        )

        with pytest.raises(OptionValueNotAllowedError):
            parse_command_line_args(spec, ["--flag=value"])

    def test_zero_arity_short_option_with_equals_value_raises_error(self):
        spec = CommandSpecification(
            "test",
            options={
                "flag": FlagOptionSpecification(
                    name="flag",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="f",
                    long_names=(),
                    short_names=("f",),
                )
            },
        )

        with pytest.raises(OptionValueNotAllowedError):
            parse_command_line_args(spec, ["-f=value"])

    def test_zero_arity_option_does_not_consume_following_args(self):
        spec = CommandSpecification(
            "test",
            options={
                "flag": FlagOptionSpecification(
                    name="flag",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="flag",
                    long_names=("flag",),
                    short_names=(),
                )
            },
            positionals={"args": Arity.zero_or_more()},
        )

        result = parse_command_line_args(spec, ["--flag", "arg1", "arg2"])

        assert result.options["flag"] is True
        assert result.positionals["args"] == ("arg1", "arg2")
