import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import OptionMissingValueError, OptionNotRepeatableError
from flagrant.specification import (
    command,
    flag_option,
    flat_list_option,
    list_option,
    nested_list_option,
)


class TestBasicListParsing:
    def test_long_option_captures_single_value(self):
        opt = list_option(["files"], arity=1)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--files", "file.txt"))

        assert result.options["files"] == "file.txt"

    def test_short_option_captures_single_value(self):
        opt = list_option(["f"], arity=1)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("-f", "file.txt"))

        assert result.options["f"] == "file.txt"

    def test_option_absent_creates_no_entry_in_result(self):
        opt = list_option(["files"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ())

        assert "files" not in result.options


class TestExactArity:
    def test_exactly_one_value_returns_scalar(self):
        opt = list_option(["output"], arity=1)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--output", "file.txt"))

        assert result.options["output"] == "file.txt"
        assert isinstance(result.options["output"], str)

    def test_exactly_two_values_returns_tuple(self):
        opt = list_option(["coords"], arity=(2, 2))
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--coords", "10", "20"))

        assert result.options["coords"] == ("10", "20")

    def test_exactly_three_values_returns_tuple(self):
        opt = list_option(["rgb"], arity=(3, 3))
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--rgb", "255", "128", "0"))

        assert result.options["rgb"] == ("255", "128", "0")

    def test_exact_arity_stops_at_maximum(self):
        opt = list_option(["output"], arity=1)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--output", "file.txt", "extra.txt"))

        assert result.options["output"] == "file.txt"
        # extra.txt becomes ungrouped positional, not extra_args
        # (extra_args is for args after --)
        assert "extra.txt" not in result.extra_args


class TestRangeArity:
    @pytest.mark.xfail(reason="peek_n returns empty when remaining < max_args")
    def test_one_to_two_accepts_one_value(self):
        opt = list_option(["files"], arity=(1, 2))
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--files", "a.txt"))

        assert result.options["files"] == ("a.txt",)

    def test_one_to_two_accepts_two_values(self):
        opt = list_option(["files"], arity=(1, 2))
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--files", "a.txt", "b.txt"))

        assert result.options["files"] == ("a.txt", "b.txt")

    def test_one_to_two_stops_at_maximum(self):
        opt = list_option(["files"], arity=(1, 2))
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--files", "a.txt", "b.txt", "c.txt"))

        assert result.options["files"] == ("a.txt", "b.txt")
        # c.txt becomes ungrouped positional, not extra_args
        assert "c.txt" not in result.extra_args

    @pytest.mark.xfail(reason="peek_n returns empty when remaining < max_args")
    def test_two_to_five_accepts_minimum(self):
        opt = list_option(["values"], arity=(2, 5))
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--values", "1", "2"))

        assert result.options["values"] == ("1", "2")

    def test_two_to_five_accepts_maximum(self):
        opt = list_option(["values"], arity=(2, 5))
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--values", "1", "2", "3", "4", "5"))

        assert result.options["values"] == ("1", "2", "3", "4", "5")


class TestUnboundedArity:
    def test_zero_or_more_accepts_zero_values(self):
        opt = list_option(["files"], arity="*")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--files",))

        assert result.options["files"] == ()

    def test_zero_or_more_accepts_multiple_values(self):
        opt = list_option(["files"], arity="*")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--files", "a.txt", "b.txt", "c.txt"))

        assert result.options["files"] == ("a.txt", "b.txt", "c.txt")

    def test_one_or_more_requires_at_least_one(self):
        opt = list_option(["files"], arity=(1, "*"))
        spec = command("test", options=[opt])

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ("--files",))

    def test_one_or_more_accepts_one_value(self):
        opt = list_option(["files"], arity=(1, "*"))
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--files", "a.txt"))

        assert result.options["files"] == ("a.txt",)

    def test_one_or_more_accepts_multiple_values(self):
        opt = list_option(["files"], arity=(1, "*"))
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--files", "a.txt", "b.txt", "c.txt"))

        assert result.options["files"] == ("a.txt", "b.txt", "c.txt")

    def test_two_or_more_requires_at_least_two(self):
        opt = list_option(["files"], arity=(2, "*"))
        spec = command("test", options=[opt])

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ("--files", "a.txt"))


class TestInsufficientValues:
    def test_exact_one_with_none_raises_error(self):
        opt = list_option(["output"], arity=1)
        spec = command("test", options=[opt])

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ("--output",))

    def test_exact_two_with_one_raises_error(self):
        opt = list_option(["coords"], arity=(2, 2))
        spec = command("test", options=[opt])

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ("--coords", "10"))

    def test_exact_three_with_two_raises_error(self):
        opt = list_option(["rgb"], arity=(3, 3))
        spec = command("test", options=[opt])

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ("--rgb", "255", "128"))

    def test_option_before_another_known_option_raises_error(self):
        opt_files = list_option(["files"], arity=(2, 2))
        opt_verbose = flag_option(["verbose"])
        spec = command("test", options=[opt_files, opt_verbose])

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ("--files", "a.txt", "--verbose"))


class TestListAccumulationModes:
    def test_last_mode_keeps_last_occurrence(self):
        opt = list_option(["point"], arity=(2, 2), accumulation_mode="last")
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--point", "1", "2", "--point", "3", "4")
        )

        assert result.options["point"] == ("3", "4")

    def test_first_mode_keeps_first_occurrence(self):
        opt = list_option(["point"], arity=(2, 2), accumulation_mode="first")
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--point", "1", "2", "--point", "3", "4")
        )

        assert result.options["point"] == ("1", "2")

    def test_append_mode_nests_each_occurrence(self):
        opt = nested_list_option(["point"], arity=(2, 2))
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--point", "1", "2", "--point", "3", "4")
        )

        assert result.options["point"] == (("1", "2"), ("3", "4"))

    def test_extend_mode_flattens_all_values(self):
        opt = flat_list_option(["file"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--file", "a.txt", "--file", "b.txt", "--file", "c.txt")
        )

        assert result.options["file"] == ("a.txt", "b.txt", "c.txt")

    def test_error_mode_raises_on_second_occurrence(self):
        opt = list_option(["output"], arity=1, accumulation_mode="error")
        spec = command("test", options=[opt])

        with pytest.raises(OptionNotRepeatableError):
            parse_command_line_args(
                spec, ("--output", "first.txt", "--output", "second.txt")
            )

    def test_error_mode_allows_first_occurrence(self):
        opt = list_option(["output"], arity=1, accumulation_mode="error")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--output", "file.txt"))

        # error mode always returns tuple, even with arity=1
        assert result.options["output"] == ("file.txt",)


class TestMixedArityInAccumulationModes:
    def test_append_mode_with_variable_value_counts(self):
        opt = nested_list_option(["values"], arity=(1, 3))
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--values", "1", "--values", "2", "3", "--values", "4", "5", "6")
        )

        assert result.options["values"] == (("1",), ("2", "3"), ("4", "5", "6"))

    def test_extend_mode_flattens_variable_value_counts(self):
        opt = flat_list_option(["values"], arity=(1, 3))
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--values", "1", "--values", "2", "3", "--values", "4", "5", "6")
        )

        assert result.options["values"] == ("1", "2", "3", "4", "5", "6")


class TestStoppingConditions:
    def test_stops_at_known_option(self):
        opt_files = list_option(["files"], arity="*")
        opt_verbose = flag_option(["verbose"])
        spec = command("test", options=[opt_files, opt_verbose])

        result = parse_command_line_args(
            spec, ("--files", "a.txt", "b.txt", "--verbose")
        )

        assert result.options["files"] == ("a.txt", "b.txt")
        assert result.options["verbose"] is True

    def test_stops_at_subcommand(self):
        opt = list_option(["files"], arity="*")
        subcommand = command("build")
        spec = command("test", options=[opt], subcommands=[subcommand])

        result = parse_command_line_args(spec, ("--files", "a.txt", "b.txt", "build"))

        assert result.options["files"] == ("a.txt", "b.txt")
        assert result.subcommand is not None
        assert result.subcommand.command == "build"

    def test_stops_at_maximum_arity(self):
        opt = list_option(["files"], arity=(1, 3))
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--files", "a.txt", "b.txt", "c.txt", "d.txt")
        )

        assert result.options["files"] == ("a.txt", "b.txt", "c.txt")
        # d.txt becomes ungrouped positional, not extra_args
        assert "d.txt" not in result.extra_args

    def test_single_dash_does_not_stop_consumption(self):
        opt = list_option(["files"], arity="*")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--files", "a.txt", "-", "b.txt"))

        assert result.options["files"] == ("a.txt", "-", "b.txt")

    def test_unknown_option_like_value_consumed_as_value(self):
        opt = list_option(["values"], arity=(2, 2))
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--values", "--other", "value"))

        assert result.options["values"] == ("--other", "value")


class TestGreedyMode:
    def test_greedy_consumes_all_remaining_arguments(self):
        # Use "..." arity for greedy behavior that consumes through options
        opt = list_option(["files"], arity="...")
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--files", "file1.txt", "--output", "file2.txt", "-v")
        )

        assert result.options["files"] == ("file1.txt", "--output", "file2.txt", "-v")

    def test_greedy_at_end_of_arguments(self):
        opt = list_option(["files"], arity="...")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--files", "single.txt"))

        assert result.options["files"] == ("single.txt",)

    def test_greedy_consumes_delimiter_and_trailing_args(self):
        opt = list_option(["args"], arity="...")
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--args", "a", "b", "c", "--", "positional")
        )

        assert result.options["args"] == ("a", "b", "c", "--", "positional")


class TestListInlineValues:
    def test_long_option_with_equals_assigns_value(self):
        opt = list_option(["output"], arity=1)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--output=file.txt",))

        assert result.options["output"] == "file.txt"

    def test_inline_value_splits_on_first_equals(self):
        opt = list_option(["config"], arity=1)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--config=key=value",))

        assert result.options["config"] == "key=value"

    def test_empty_inline_value_assigns_empty_string(self):
        opt = list_option(["output"], arity=1)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--output=",))

        assert result.options["output"] == ""

    def test_short_option_with_equals_assigns_value(self):
        opt = list_option(["o"], arity=1)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("-o=file.txt",))

        assert result.options["o"] == "file.txt"

    @pytest.mark.xfail(reason="Short option concatenated value not yet implemented")
    def test_short_option_concatenated_value(self):
        opt = list_option(["o"], arity=1)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("-ofile.txt",))

        assert result.options["o"] == "file.txt"

    @pytest.mark.xfail(reason="peek_n returns empty when remaining < max_args")
    def test_inline_value_counts_toward_arity(self):
        opt = list_option(["files"], arity=(2, 3))
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--files=a.txt", "b.txt"))

        assert result.options["files"] == ("a.txt", "b.txt")

    def test_inline_value_with_unbounded_arity_consumes_following(self):
        opt = list_option(["files"], arity=(1, "*"))
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--files=first.txt", "second.txt", "third.txt")
        )

        assert result.options["files"] == ("first.txt", "second.txt", "third.txt")

    def test_inline_value_insufficient_for_arity_raises_error(self):
        opt = list_option(["coords"], arity=(3, 3))
        spec = command("test", options=[opt])

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ("--coords=10", "20"))


class TestListWithTrailingSeparator:
    @pytest.mark.xfail(reason="Non-greedy options consume values through -- separator")
    def test_separator_stops_value_collection_unbounded(self):
        opt = list_option(["files"], arity="*")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--files", "a.txt", "--", "b.txt"))

        assert result.options["files"] == ("a.txt",)
        assert result.extra_args == ("b.txt",)

    @pytest.mark.xfail(reason="Non-greedy options consume values through -- separator")
    def test_separator_stops_value_collection_bounded(self):
        opt = list_option(["values"], arity=(1, 3))
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--values", "one", "--", "two"))

        assert result.options["values"] == ("one",)
        assert result.extra_args == ("two",)

    @pytest.mark.xfail(reason="Non-greedy options consume values through -- separator")
    def test_separator_causes_error_when_arity_not_satisfied(self):
        opt = list_option(["coords"], arity=(2, 2))
        spec = command("test", options=[opt])

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ("--coords", "10", "--", "20"))


class TestNegativeNumbers:
    def test_negative_number_consumed_as_value_when_allowed(self):
        opt = list_option(["values"], arity=(1, "*"), allow_negative_numbers=True)
        spec = command("test", options=[opt])
        config = ParserConfiguration(allow_negative_numbers=True)

        result = parse_command_line_args(
            spec, ("--values", "10", "-5", "3.14"), config=config
        )

        assert result.options["values"] == ("10", "-5", "3.14")

    def test_negative_decimal_consumed_as_value_when_allowed(self):
        opt = list_option(["values"], arity=(1, "*"), allow_negative_numbers=True)
        spec = command("test", options=[opt])
        config = ParserConfiguration(allow_negative_numbers=True)

        result = parse_command_line_args(
            spec, ("--values", "10", "-99.9"), config=config
        )

        assert result.options["values"] == ("10", "-99.9")

    def test_stops_at_known_option_even_with_negative_numbers_allowed(self):
        opt_values = list_option(
            ["values"], arity=(1, "*"), allow_negative_numbers=True
        )
        opt_verbose = flag_option(["verbose"])
        spec = command("test", options=[opt_values, opt_verbose])
        config = ParserConfiguration(allow_negative_numbers=True)

        result = parse_command_line_args(
            spec, ("--values", "10", "-5", "--verbose"), config=config
        )

        assert result.options["values"] == ("10", "-5")
        assert result.options["verbose"] is True


class TestListResultTypes:
    def test_exactly_one_returns_string(self):
        opt = list_option(["output"], arity=1)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--output", "file.txt"))

        assert isinstance(result.options["output"], str)

    def test_exactly_two_returns_tuple(self):
        opt = list_option(["coords"], arity=(2, 2))
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--coords", "10", "20"))

        assert isinstance(result.options["coords"], tuple)

    def test_unbounded_returns_tuple(self):
        opt = list_option(["files"], arity="*")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--files", "a.txt", "b.txt"))

        assert isinstance(result.options["files"], tuple)

    def test_zero_or_one_with_value_returns_scalar(self):
        opt = list_option(["output"], arity="?")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--output", "file.txt"))

        assert isinstance(result.options["output"], str)

    def test_zero_or_one_without_value_returns_none(self):
        opt = list_option(["output"], arity="?")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--output",))

        # arity="?" with no value returns None (like optional scalar)
        assert result.options["output"] is None


class TestClusteredShortOptionsWithValues:
    def test_trailing_value_option_consumes_next_arg(self):
        flag_a = flag_option(["a"])
        flag_b = flag_option(["b"])
        opt_out = list_option(["o"], arity=1)
        spec = command("test", options=[flag_a, flag_b, opt_out])

        result = parse_command_line_args(spec, ("-abo", "file.txt"))

        assert result.options["a"] is True
        assert result.options["b"] is True
        assert result.options["o"] == "file.txt"

    @pytest.mark.xfail(reason="Short option concatenated value not yet implemented")
    def test_inline_value_for_last_option(self):
        flag_a = flag_option(["a"])
        flag_b = flag_option(["b"])
        opt_out = list_option(["o"], arity=1)
        spec = command("test", options=[flag_a, flag_b, opt_out])

        result = parse_command_line_args(spec, ("-abofile.txt",))

        assert result.options["a"] is True
        assert result.options["b"] is True
        assert result.options["o"] == "file.txt"

    def test_clustered_with_two_value_option(self):
        flag_a = flag_option(["a"])
        opt_coords = list_option(["c"], arity=(2, 2))
        spec = command("test", options=[flag_a, opt_coords])

        result = parse_command_line_args(spec, ("-ac", "10", "20"))

        assert result.options["a"] is True
        assert result.options["c"] == ("10", "20")

    def test_clustered_with_unbounded_arity_consumes_remaining(self):
        flag_a = flag_option(["a"])
        opt_files = list_option(["f"], arity=(1, "*"))
        spec = command("test", options=[flag_a, opt_files])

        result = parse_command_line_args(spec, ("-af", "a.txt", "b.txt", "c.txt"))

        assert result.options["a"] is True
        assert result.options["f"] == ("a.txt", "b.txt", "c.txt")

    def test_clustered_with_multiple_value_options_raises_error(self):
        opt_out = list_option(["o"], arity=1)
        opt_in = list_option(["i"], arity=1)
        spec = command("test", options=[opt_out, opt_in])

        # When clustered, the first option -o consumes nothing (inner option)
        # and then -i expects a value but gets file.txt which satisfies it
        # This raises OptionMissingValueError for -o (no value)
        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ("-oi", "file.txt"))


class TestListEdgeCases:
    def test_empty_string_value_via_equals(self):
        opt = list_option(["option"], arity=1)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--option=",))

        assert result.options["option"] == ""

    def test_whitespace_only_value(self):
        opt = list_option(["option"], arity=1)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--option", "   "))

        assert result.options["option"] == "   "

    def test_value_containing_equals_sign(self):
        opt = list_option(["option"], arity=1)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--option", "key=value"))

        assert result.options["option"] == "key=value"

    def test_value_containing_hyphens(self):
        opt = list_option(["pattern"], arity=1)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--pattern", "foo-bar-baz"))

        assert result.options["pattern"] == "foo-bar-baz"

    def test_values_with_special_characters(self):
        opt = list_option(["values"], arity=(3, 3))
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--values", "key=value", "foo:bar", "path/to/file")
        )

        assert result.options["values"] == ("key=value", "foo:bar", "path/to/file")

    def test_empty_string_counted_in_arity(self):
        opt = list_option(["values"], arity=(2, 2))
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--values=", "nonempty"))

        assert result.options["values"] == ("", "nonempty")

    def test_very_large_arity_works(self):
        opt = list_option(["values"], arity=(50, 50))
        spec = command("test", options=[opt])

        args = ("--values", *(str(i) for i in range(1, 51)))
        result = parse_command_line_args(spec, args)

        values = result.options["values"]
        assert isinstance(values, tuple)
        assert len(values) == 50
        assert values[0] == "1"
        assert values[49] == "50"


class TestListArityBoundaryValidation:
    def test_exact_arity_one_equals_one(self):
        opt = list_option(["value"], arity=(1, 1))
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--value", "item"))

        # Tuple arity returns tuple, not scalar (only int and "?" are scalar arities)
        assert result.options["value"] == ("item",)

    def test_exact_arity_ten_equals_ten(self):
        opt = list_option(["values"], arity=(10, 10))
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--values", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10")
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

    def test_exact_arity_ten_with_nine_raises_error(self):
        opt = list_option(["values"], arity=(10, 10))
        spec = command("test", options=[opt])

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(
                spec, ("--values", "1", "2", "3", "4", "5", "6", "7", "8", "9")
            )
