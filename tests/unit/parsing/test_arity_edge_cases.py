from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import (
    OptionMissingValueError,
    OptionValueNotAllowedError,
)
from flagrant.specification import (
    Arity,
    ValueAccumulationMode,
)

if TYPE_CHECKING:
    from flagrant.specification import (
        CommandSpecificationFactory,
        FlagOptionSpecificationFactory,
        ValueOptionSpecificationFactory,
    )


class TestCombinedShortOptionsWithArity:
    @pytest.mark.parametrize(
        (
            "name",
            "flag_a_kwargs",
            "flag_b_kwargs",
            "output_kwargs",
            "input_args",
            "expected_a",
            "expected_b",
            "expected_output",
        ),
        [
            (
                "trailing_value_option_consumes_next_arg",
                {"name": "a", "short_names": ("a",)},
                {"name": "b", "short_names": ("b",)},
                {
                    "name": "output",
                    "arity": Arity.exactly_one(),
                    "short_names": ("o",),
                },
                ["-abo", "file.txt"],
                True,
                True,
                "file.txt",
            ),
            (
                "inline_value_for_last_option",
                {"name": "a", "short_names": ("a",)},
                {"name": "b", "short_names": ("b",)},
                {
                    "name": "output",
                    "arity": Arity.exactly_one(),
                    "short_names": ("o",),
                },
                ["-abofile.txt"],
                True,
                True,
                "file.txt",
            ),
        ],
    )
    def test_clustered_short_options_with_values(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
        name: str,
        flag_a_kwargs: dict[str, object],
        flag_b_kwargs: dict[str, object],
        output_kwargs: dict[str, object],
        input_args: list[str],
        expected_a: bool,
        expected_b: bool,
        expected_output: str,
    ):
        flag_a = make_flag_opt(**flag_a_kwargs)  # type: ignore[reportArgumentType]
        flag_b = make_flag_opt(**flag_b_kwargs)  # type: ignore[reportArgumentType]
        opt_out = make_value_opt(**output_kwargs)  # type: ignore[reportArgumentType]
        spec = make_command(
            options={
                flag_a.name: flag_a,
                flag_b.name: flag_b,
                opt_out.name: opt_out,
            }
        )

        result = parse_command_line_args(spec, input_args)

        assert result.options[flag_a.name] is expected_a
        assert result.options[flag_b.name] is expected_b
        assert result.options[opt_out.name] == expected_output

    def test_clustered_short_with_value_option_requiring_two_values(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        flag_a = make_flag_opt(name="a", short_names=("a",))
        opt_coords = make_value_opt(
            name="coords",
            arity=Arity(2, 2),
            short_names=("c",),
        )
        spec = make_command(options={"a": flag_a, "coords": opt_coords})

        result = parse_command_line_args(spec, ["-ac", "10", "20"])

        assert result.options["a"] is True
        assert result.options["coords"] == ("10", "20")

    def test_clustered_short_with_multiple_value_options_raises_runtime_error(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt_out = make_value_opt(
            name="output",
            arity=Arity.exactly_one(),
            short_names=("o",),
        )
        opt_in = make_value_opt(
            name="input",
            arity=Arity.exactly_one(),
            short_names=("i",),
        )
        spec = make_command(options={"output": opt_out, "input": opt_in})

        with pytest.raises(
            RuntimeError,
            match="Unexpected consumption of arguments for inner short option",
        ):
            parse_command_line_args(spec, ["-oi", "file.txt"])

    def test_clustered_short_with_unbounded_arity_consumes_remaining_args(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        flag_a = make_flag_opt(name="a", short_names=("a",))
        opt_files = make_value_opt(
            name="files",
            arity=Arity.at_least_one(),
            short_names=("f",),
        )
        spec = make_command(options={"a": flag_a, "files": opt_files})

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
    @pytest.mark.parametrize(
        ("name", "option_kwargs", "input_args", "expected_value", "expected_extra"),
        [
            (
                "unbounded_arity",
                {"name": "files", "arity": Arity.zero_or_more()},
                ["--files", "a.txt", "--", "b.txt"],
                ("a.txt",),
                ("b.txt",),
            ),
            (
                "bounded_arity",
                {"name": "values", "arity": Arity(1, 3)},
                ["--values", "one", "--", "two"],
                ("one",),
                ("two",),
            ),
            (
                "min_arity_satisfied",
                {"name": "values", "arity": Arity(2, 5)},
                ["--values", "1", "2", "--", "3"],
                ("1", "2"),
                ("3",),
            ),
            (
                "optional_arity_succeeds",
                {"name": "output", "arity": Arity.at_most_one()},
                ["--output", "--", "arg"],
                (),
                ("arg",),
            ),
        ],
    )
    def test_separator_stops_value_collection(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
        name: str,
        option_kwargs: dict[str, object],
        input_args: list[str],
        expected_value: tuple[str, ...],
        expected_extra: tuple[str, ...],
    ):
        opt = make_value_opt(**option_kwargs)  # type: ignore[reportArgumentType]
        spec = make_command(options={opt.name: opt})

        result = parse_command_line_args(spec, input_args)

        assert result.options[opt.name] == expected_value
        assert result.extra_args == expected_extra

    @pytest.mark.xfail(
        reason=(
            "BUG: Non-greedy options consume values through the -- "
            "separator instead of stopping at it"
        )
    )
    def test_separator_causes_insufficient_values_error_when_arity_not_met(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="coords", arity=Arity(2, 2))
        spec = make_command(options={"coords": opt})

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--coords", "10", "--", "20"])


class TestMixedArityInAccumulationModes:
    def test_append_mode_with_different_value_counts_creates_nested_tuples(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="values",
            arity=Arity(1, 3),
            accumulation_mode=ValueAccumulationMode.APPEND,
        )
        spec = make_command(options={"values": opt})

        result = parse_command_line_args(
            spec, ["--values", "1", "--values", "2", "3", "--values", "4", "5", "6"]
        )

        assert result.options["values"] == (("1",), ("2", "3"), ("4", "5", "6"))

    def test_extend_mode_flattens_different_value_counts(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="values",
            arity=Arity(1, 3),
            accumulation_mode=ValueAccumulationMode.EXTEND,
        )
        spec = make_command(options={"values": opt})

        result = parse_command_line_args(
            spec, ["--values", "1", "--values", "2", "3", "--values", "4", "5", "6"]
        )

        assert result.options["values"] == ("1", "2", "3", "4", "5", "6")

    def test_last_mode_keeps_most_recent_value_count(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="values",
            arity=Arity(1, 3),
            accumulation_mode=ValueAccumulationMode.LAST,
        )
        spec = make_command(options={"values": opt})

        result = parse_command_line_args(spec, ["--values", "1", "--values", "2", "3"])

        assert result.options["values"] == ("2", "3")

    def test_first_mode_keeps_first_value_count(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="values",
            arity=Arity(1, 3),
            accumulation_mode=ValueAccumulationMode.FIRST,
        )
        spec = make_command(options={"values": opt})

        result = parse_command_line_args(spec, ["--values", "1", "--values", "2", "3"])

        assert result.options["values"] == ("1",)


class TestArityBoundaryValidation:
    def test_exact_arity_boundary_min_equals_max_one(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="value", arity=Arity(1, 1))
        spec = make_command(options={"value": opt})

        result = parse_command_line_args(spec, ["--value", "item"])

        assert result.options["value"] == "item"

    def test_exact_arity_boundary_min_equals_max_ten(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="values", arity=Arity(10, 10))
        spec = make_command(options={"values": opt})

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
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="values", arity=Arity(10, 10))
        spec = make_command(options={"values": opt})

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(
                spec, ["--values", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
            )

    def test_zero_arity_flag_behavior_confirmed(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="flag")
        spec = make_command(options={"flag": opt})

        result = parse_command_line_args(spec, ["--flag"])

        assert result.options["flag"] is True

    def test_very_large_exact_arity_boundary_fifty_values(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="values", arity=Arity(50, 50))
        spec = make_command(options={"values": opt})

        args = ["--values"] + [str(i) for i in range(1, 51)]
        result = parse_command_line_args(spec, args)

        values = result.options["values"]
        assert isinstance(values, tuple)
        assert len(values) == 50
        assert values[0] == "1"
        assert values[49] == "50"


class TestGreedyModeArityInteractions:
    def test_greedy_mode_stops_at_subcommand_respecting_minimum_arity(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt_files = make_value_opt(
            name="files", arity=Arity(2, None), greedy=True
        )
        subcmd = make_command("build")
        spec = make_command(options={"files": opt_files}, subcommands={"build": subcmd})

        result = parse_command_line_args(spec, ["--files", "a.txt", "b.txt", "build"])

        assert result.options["files"] == ("a.txt", "b.txt")
        assert result.subcommand is not None
        assert result.subcommand.command == "build"

    def test_greedy_mode_with_negative_numbers_when_allowed(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="numbers",
            arity=Arity.at_least_one(),
            greedy=True,
            allow_negative_numbers=True,
        )
        spec = make_command(options={"numbers": opt})
        config = ParserConfiguration(allow_negative_numbers=True)

        result = parse_command_line_args(
            spec, ["--numbers", "10", "-5", "-3.14", "20"], config=config
        )

        assert result.options["numbers"] == ("10", "-5", "-3.14", "20")

    def test_greedy_mode_with_negative_numbers_disabled_consumes_as_values(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="values", arity=Arity.at_least_one(), greedy=True
        )
        spec = make_command(options={"values": opt})
        config = ParserConfiguration(allow_negative_numbers=False)

        result = parse_command_line_args(
            spec, ["--values", "a", "-b", "-c"], config=config
        )

        assert result.options["values"] == ("a", "-b", "-c")

    def test_greedy_mode_stops_at_known_option_even_with_negative_numbers(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt_values = make_value_opt(
            name="values",
            arity=Arity.at_least_one(),
            greedy=True,
            allow_negative_numbers=True,
        )
        opt_output = make_value_opt(name="output")
        spec = make_command(options={"values": opt_values, "output": opt_output})
        config = ParserConfiguration(allow_negative_numbers=True)

        result = parse_command_line_args(
            spec, ["--values", "10", "-5", "--output", "file.txt"], config=config
        )

        assert result.options["values"] == ("10", "-5")
        assert result.options["output"] == "file.txt"


class TestArityWithInlineValues:
    def test_inline_value_counts_toward_arity_minimum(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="files", arity=Arity(2, 3))
        spec = make_command(options={"files": opt})

        result = parse_command_line_args(spec, ["--files=a.txt", "b.txt"])

        assert result.options["files"] == ("a.txt", "b.txt")

    def test_inline_value_with_unbounded_arity_collects_additional_values(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="files", arity=Arity.zero_or_more())
        spec = make_command(options={"files": opt})

        result = parse_command_line_args(spec, ["--files=a.txt", "b.txt", "c.txt"])

        assert result.options["files"] == ("a.txt", "b.txt", "c.txt")

    def test_inline_value_insufficient_for_minimum_arity_raises_error(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="coords", arity=Arity(3, 3))
        spec = make_command(options={"coords": opt})

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--coords=10", "20"])

    def test_short_option_inline_value_counts_toward_arity(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="files", arity=Arity(2, 2), short_names=("f",)
        )
        spec = make_command(options={"files": opt})

        result = parse_command_line_args(spec, ["-f=a.txt", "b.txt"])

        assert result.options["files"] == ("a.txt", "b.txt")

    def test_clustered_short_with_inline_value_counts_toward_arity(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        flag_a = make_flag_opt(name="a", short_names=("a",))
        opt_files = make_value_opt(
            name="files", arity=Arity(2, 2), short_names=("f",)
        )
        spec = make_command(options={"a": flag_a, "files": opt_files})

        result = parse_command_line_args(spec, ["-afone.txt", "two.txt"])

        assert result.options["a"] is True
        assert result.options["files"] == ("one.txt", "two.txt")


class TestArityErrorCasesAndEdgeBehaviors:
    def test_arity_cannot_be_satisfied_due_to_end_of_input(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="values", arity=Arity(3, 5))
        spec = make_command(options={"values": opt})

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--values", "1", "2"])

    def test_arity_satisfied_at_end_of_input(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="values", arity=Arity(2, 5))
        spec = make_command(options={"values": opt})

        result = parse_command_line_args(spec, ["--values", "1", "2"])

        assert result.options["values"] == ("1", "2")

    def test_values_that_look_like_unknown_options_consumed_as_values(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="values", arity=Arity(2, 2))
        spec = make_command(options={"values": opt})

        result = parse_command_line_args(spec, ["--values", "--other", "value"])

        assert result.options["values"] == ("--other", "value")

    def test_values_with_special_characters_counted_correctly(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="values", arity=Arity(3, 3))
        spec = make_command(options={"values": opt})

        result = parse_command_line_args(
            spec, ["--values", "key=value", "foo:bar", "path/to/file"]
        )

        assert result.options["values"] == ("key=value", "foo:bar", "path/to/file")

    def test_single_dash_value_counted_in_arity(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="values", arity=Arity(3, 3))
        spec = make_command(options={"values": opt})

        result = parse_command_line_args(spec, ["--values", "-", "a", "b"])

        assert result.options["values"] == ("-", "a", "b")

    def test_empty_string_values_counted_in_arity(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="values", arity=Arity(2, 2))
        spec = make_command(options={"values": opt})

        result = parse_command_line_args(spec, ["--values=", "nonempty"])

        assert result.options["values"] == ("", "nonempty")


class TestArityWithPositionalsInteraction:
    def test_option_arity_consumes_before_positionals(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="files", arity=Arity(2, 2))
        spec = make_command(
            options={"files": opt}, positionals={"args": Arity.zero_or_more()}
        )

        result = parse_command_line_args(
            spec, ["--files", "a.txt", "b.txt", "c.txt", "d.txt"]
        )

        assert result.options["files"] == ("a.txt", "b.txt")
        assert result.positionals["args"] == ("c.txt", "d.txt")

    def test_option_unbounded_arity_stops_before_positionals_when_next_option_appears(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt_files = make_value_opt(name="files", arity=Arity.zero_or_more())
        flag_verbose = make_flag_opt(name="verbose")
        spec = make_command(
            options={"files": opt_files, "verbose": flag_verbose},
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
    def test_option_with_range_arity_leaves_values_for_positionals(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="prefix", arity=Arity(1, 2))
        spec = make_command(
            options={"prefix": opt},
            positionals={"file": Arity.exactly_one(), "output": Arity.exactly_one()},
        )

        result = parse_command_line_args(
            spec, ["--prefix", "pre", "input.txt", "output.txt"]
        )

        assert result.options["prefix"] == ("pre",)
        assert result.positionals["file"] == "input.txt"
        assert result.positionals["output"] == "output.txt"


class TestArityZeroEdgeCases:
    def test_zero_arity_option_with_equals_value_raises_error(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="flag")
        spec = make_command(options={"flag": opt})

        with pytest.raises(OptionValueNotAllowedError):
            parse_command_line_args(spec, ["--flag=value"])

    def test_zero_arity_short_option_with_equals_value_raises_error(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="flag", short_names=("f",))
        spec = make_command(options={"flag": opt})

        with pytest.raises(OptionValueNotAllowedError):
            parse_command_line_args(spec, ["-f=value"])

    def test_zero_arity_option_does_not_consume_following_args(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="flag")
        spec = make_command(
            options={"flag": opt}, positionals={"args": Arity.zero_or_more()}
        )

        result = parse_command_line_args(spec, ["--flag", "arg1", "arg2"])

        assert result.options["flag"] is True
        assert result.positionals["args"] == ("arg1", "arg2")
