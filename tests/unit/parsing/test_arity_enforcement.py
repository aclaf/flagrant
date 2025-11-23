import pytest

from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import OptionMissingValueError
from flagrant.specification import (
    Arity,
    CommandSpecification,
    CommandSpecificationFactory,
    FlagOptionSpecification,
    FlagOptionSpecificationFactory,
    ValueOptionSpecification,
    ValueOptionSpecificationFactory,
)
from flagrant.specification.enums import ValueAccumulationMode


class TestExactArityPatterns:
    def test_exactly_one_arity_option_consumes_one_value(
        self,
        make_command: CommandSpecificationFactory,
        make_value_opt: ValueOptionSpecificationFactory,
    ):
        output_option = make_value_opt(name="output", arity=Arity.exactly_one())
        spec = make_command(options={"output": output_option})

        result = parse_command_line_args(spec, ["--output", "file.txt"])

        assert result.options["output"] == "file.txt"

    def test_exactly_two_arity_option_consumes_two_values(self):
        spec = CommandSpecification(
            "test",
            options={
                "coordinate": ValueOptionSpecification(
                    name="coordinate",
                    arity=Arity(2, 2),
                    greedy=False,
                    preferred_name="coordinate",
                    long_names=("coordinate",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--coordinate", "10", "20"])

        assert result.options["coordinate"] == ("10", "20")

    def test_exactly_three_arity_option_consumes_three_values(self):
        spec = CommandSpecification(
            "test",
            options={
                "rgb": ValueOptionSpecification(
                    name="rgb",
                    arity=Arity(3, 3),
                    greedy=False,
                    preferred_name="rgb",
                    long_names=("rgb",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--rgb", "255", "128", "0"])

        assert result.options["rgb"] == ("255", "128", "0")

    def test_exactly_one_arity_stops_at_maximum_when_more_available(self):
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
            positionals={"args": Arity.zero_or_more()},
        )

        result = parse_command_line_args(spec, ["--output", "file.txt", "extra.txt"])

        assert result.options["output"] == "file.txt"
        assert result.positionals["args"] == ("extra.txt",)


class TestInsufficientValuesErrors:
    def test_option_requires_one_value_gets_none_raises_error(self):
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

    def test_option_requires_two_values_gets_one_raises_error(self):
        spec = CommandSpecification(
            "test",
            options={
                "coordinate": ValueOptionSpecification(
                    name="coordinate",
                    arity=Arity(2, 2),
                    greedy=False,
                    preferred_name="coordinate",
                    long_names=("coordinate",),
                    short_names=(),
                )
            },
        )

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--coordinate", "10"])

    def test_option_requires_three_values_gets_two_raises_error(self):
        spec = CommandSpecification(
            "test",
            options={
                "rgb": ValueOptionSpecification(
                    name="rgb",
                    arity=Arity(3, 3),
                    greedy=False,
                    preferred_name="rgb",
                    long_names=("rgb",),
                    short_names=(),
                )
            },
        )

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--rgb", "255", "128"])

    def test_option_stops_at_next_option_causing_insufficient_values(
        self,
        make_command: CommandSpecificationFactory,
        make_value_opt: ValueOptionSpecificationFactory,
        make_flag_opt: FlagOptionSpecificationFactory,
    ):
        files_option = make_value_opt(name="files", arity=Arity(2, 2))
        verbose_flag = make_flag_opt(name="verbose")
        spec = make_command(
            options={"files": files_option, "verbose": verbose_flag}
        )

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--files", "a.txt", "--verbose"])


class TestBoundedArityRanges:
    def test_zero_or_one_arity_option_accepts_zero_values(self):
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

        result = parse_command_line_args(spec, ["--output"])

        assert result.options["output"] == ()

    def test_zero_or_one_arity_option_accepts_one_value(self):
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

        result = parse_command_line_args(spec, ["--output", "file.txt"])

        assert result.options["output"] == "file.txt"

    def test_zero_or_one_arity_option_stops_at_maximum_one(self):
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
            positionals={"args": Arity.zero_or_more()},
        )

        result = parse_command_line_args(spec, ["--output", "file.txt", "extra.txt"])

        assert result.options["output"] == "file.txt"
        assert result.positionals["args"] == ("extra.txt",)

    def test_one_to_two_arity_option_accepts_one_value(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity(1, 2),
                    greedy=False,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--files", "a.txt"])

        assert result.options["files"] == ("a.txt",)

    def test_one_to_two_arity_option_accepts_two_values(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity(1, 2),
                    greedy=False,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--files", "a.txt", "b.txt"])

        assert result.options["files"] == ("a.txt", "b.txt")

    def test_one_to_two_arity_option_stops_at_maximum_two(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity(1, 2),
                    greedy=False,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
            positionals={"args": Arity.zero_or_more()},
        )

        result = parse_command_line_args(spec, ["--files", "a.txt", "b.txt", "c.txt"])

        assert result.options["files"] == ("a.txt", "b.txt")
        assert result.positionals["args"] == ("c.txt",)

    def test_two_to_five_arity_option_accepts_minimum_two(self):
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

    def test_two_to_five_arity_option_accepts_maximum_five(self):
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

        result = parse_command_line_args(spec, ["--values", "1", "2", "3", "4", "5"])

        assert result.options["values"] == ("1", "2", "3", "4", "5")

    def test_two_to_five_arity_option_stops_at_maximum_five(self):
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
            positionals={"args": Arity.zero_or_more()},
        )

        result = parse_command_line_args(
            spec, ["--values", "1", "2", "3", "4", "5", "6"]
        )

        assert result.options["values"] == ("1", "2", "3", "4", "5")
        assert result.positionals["args"] == ("6",)


class TestUnboundedArity:
    def test_zero_or_more_arity_option_accepts_zero_values(self):
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

        result = parse_command_line_args(spec, ["--files"])

        assert result.options["files"] == ()

    def test_zero_or_more_arity_option_accepts_multiple_values(self):
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

        result = parse_command_line_args(spec, ["--files", "a.txt", "b.txt", "c.txt"])

        assert result.options["files"] == ("a.txt", "b.txt", "c.txt")

    def test_one_or_more_arity_option_requires_at_least_one(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity.at_least_one(),
                    greedy=False,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
        )

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--files"])

    def test_one_or_more_arity_option_accepts_one_value(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity.at_least_one(),
                    greedy=False,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--files", "a.txt"])

        assert result.options["files"] == ("a.txt",)

    def test_one_or_more_arity_option_accepts_multiple_values(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity.at_least_one(),
                    greedy=False,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--files", "a.txt", "b.txt", "c.txt"])

        assert result.options["files"] == ("a.txt", "b.txt", "c.txt")

    def test_two_or_more_arity_option_requires_at_least_two(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity(2, None),
                    greedy=False,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
        )

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--files", "a.txt"])

    def test_two_or_more_arity_option_accepts_two_values(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity(2, None),
                    greedy=False,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--files", "a.txt", "b.txt"])

        assert result.options["files"] == ("a.txt", "b.txt")

    def test_two_or_more_arity_option_accepts_many_values(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity(2, None),
                    greedy=False,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--files", "a.txt", "b.txt", "c.txt", "d.txt", "e.txt"]
        )

        assert result.options["files"] == ("a.txt", "b.txt", "c.txt", "d.txt", "e.txt")


class TestStoppingConditions:
    def test_value_consumption_stops_at_next_option(self):
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
        )

        result = parse_command_line_args(
            spec, ["--files", "a.txt", "b.txt", "--verbose"]
        )

        assert result.options["files"] == ("a.txt", "b.txt")
        assert result.options["verbose"] is True

    def test_value_consumption_stops_at_subcommand(self):
        subcommand_spec = CommandSpecification("build")
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
            subcommands={"build": subcommand_spec},
        )

        result = parse_command_line_args(spec, ["--files", "a.txt", "b.txt", "build"])

        assert result.options["files"] == ("a.txt", "b.txt")
        assert result.subcommand is not None
        assert result.subcommand.command == "build"

    def test_value_consumption_stops_at_maximum_arity(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity(1, 3),
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

        assert result.options["files"] == ("a.txt", "b.txt", "c.txt")
        assert result.positionals["args"] == ("d.txt",)

    def test_value_consumption_stops_at_end_of_arguments(self):
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

        result = parse_command_line_args(spec, ["--files", "a.txt", "b.txt"])

        assert result.options["files"] == ("a.txt", "b.txt")

    def test_single_dash_does_not_stop_value_consumption(self):
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

        result = parse_command_line_args(spec, ["--files", "a.txt", "-", "b.txt"])

        assert result.options["files"] == ("a.txt", "-", "b.txt")


class TestInlineValueCounting:
    def test_inline_value_provides_exactly_one_value(self):
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

        result = parse_command_line_args(spec, ["--output=file.txt"])

        assert result.options["output"] == "file.txt"

    def test_inline_value_satisfies_zero_or_one_arity(self):
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

        result = parse_command_line_args(spec, ["--output=file.txt"])

        assert result.options["output"] == "file.txt"

    def test_inline_value_with_min_arity_two_raises_error(self):
        spec = CommandSpecification(
            "test",
            options={
                "coordinate": ValueOptionSpecification(
                    name="coordinate",
                    arity=Arity(2, 2),
                    greedy=False,
                    preferred_name="coordinate",
                    long_names=("coordinate",),
                    short_names=(),
                )
            },
        )

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--coordinate=10"])

    def test_inline_value_with_unbounded_arity_succeeds(self):
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

        result = parse_command_line_args(spec, ["--files=a.txt"])

        assert result.options["files"] == ("a.txt",)


class TestPositionalArityGrouping:
    def test_single_positional_with_exactly_one_arity(self):
        spec = CommandSpecification("test", positionals={"file": Arity.exactly_one()})

        result = parse_command_line_args(spec, ["input.txt"])

        assert result.positionals["file"] == "input.txt"

    def test_two_positionals_with_exact_arities(self):
        spec = CommandSpecification(
            "test",
            positionals={"source": Arity.exactly_one(), "dest": Arity.exactly_one()},
        )

        result = parse_command_line_args(spec, ["input.txt", "output.txt"])

        assert result.positionals["source"] == "input.txt"
        assert result.positionals["dest"] == "output.txt"

    def test_unbounded_positional_consumes_all_remaining(self):
        spec = CommandSpecification("test", positionals={"files": Arity.zero_or_more()})

        result = parse_command_line_args(spec, ["a.txt", "b.txt", "c.txt"])

        assert result.positionals["files"] == ("a.txt", "b.txt", "c.txt")

    def test_unbounded_positional_reserves_for_later_positionals(self):
        spec = CommandSpecification(
            "test",
            positionals={
                "files": Arity.at_least_one(),
                "output": Arity.exactly_one(),
            },
        )

        result = parse_command_line_args(spec, ["a.txt", "b.txt", "result.txt"])

        assert result.positionals["files"] == ("a.txt", "b.txt")
        assert result.positionals["output"] == "result.txt"

    def test_three_positionals_with_mixed_arities(self):
        spec = CommandSpecification(
            "test",
            positionals={
                "command": Arity.exactly_one(),
                "files": Arity.at_least_one(),
                "output": Arity.exactly_one(),
            },
        )

        result = parse_command_line_args(
            spec, ["build", "a.txt", "b.txt", "c.txt", "result.txt"]
        )

        assert result.positionals["command"] == "build"
        assert result.positionals["files"] == ("a.txt", "b.txt", "c.txt")
        assert result.positionals["output"] == "result.txt"

    def test_bounded_positional_respects_maximum(self):
        spec = CommandSpecification(
            "test",
            positionals={"files": Arity(1, 2), "output": Arity.exactly_one()},
        )

        result = parse_command_line_args(spec, ["a.txt", "b.txt", "result.txt"])

        assert result.positionals["files"] == ("a.txt", "b.txt")
        assert result.positionals["output"] == "result.txt"


class TestResultTypeScalarVsTuple:
    def test_exactly_one_arity_with_last_mode_returns_scalar(self):
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

        result = parse_command_line_args(spec, ["--output", "file.txt"])

        assert isinstance(result.options["output"], str)
        assert result.options["output"] == "file.txt"

    def test_exactly_one_arity_with_first_mode_returns_scalar(self):
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
                    accumulation_mode=ValueAccumulationMode.FIRST,
                )
            },
        )

        result = parse_command_line_args(spec, ["--output", "file.txt"])

        assert isinstance(result.options["output"], str)
        assert result.options["output"] == "file.txt"

    def test_zero_or_one_arity_with_value_returns_scalar(self):
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
                    accumulation_mode=ValueAccumulationMode.LAST,
                )
            },
        )

        result = parse_command_line_args(spec, ["--output", "file.txt"])

        assert isinstance(result.options["output"], str)
        assert result.options["output"] == "file.txt"

    def test_zero_or_one_arity_without_value_returns_empty_tuple(self):
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
                    accumulation_mode=ValueAccumulationMode.LAST,
                )
            },
        )

        result = parse_command_line_args(spec, ["--output"])

        assert isinstance(result.options["output"], tuple)
        assert result.options["output"] == ()

    def test_exactly_two_arity_returns_tuple(self):
        spec = CommandSpecification(
            "test",
            options={
                "coordinate": ValueOptionSpecification(
                    name="coordinate",
                    arity=Arity(2, 2),
                    greedy=False,
                    preferred_name="coordinate",
                    long_names=("coordinate",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--coordinate", "10", "20"])

        assert isinstance(result.options["coordinate"], tuple)
        assert result.options["coordinate"] == ("10", "20")

    def test_unbounded_arity_returns_tuple(self):
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

        result = parse_command_line_args(spec, ["--files", "a.txt", "b.txt"])

        assert isinstance(result.options["files"], tuple)
        assert result.options["files"] == ("a.txt", "b.txt")

    def test_exactly_one_positional_returns_scalar(self):
        spec = CommandSpecification("test", positionals={"file": Arity.exactly_one()})

        result = parse_command_line_args(spec, ["input.txt"])

        assert isinstance(result.positionals["file"], str)
        assert result.positionals["file"] == "input.txt"

    def test_unbounded_positional_returns_tuple(self):
        spec = CommandSpecification("test", positionals={"files": Arity.zero_or_more()})

        result = parse_command_line_args(spec, ["a.txt", "b.txt"])

        assert isinstance(result.positionals["files"], tuple)
        assert result.positionals["files"] == ("a.txt", "b.txt")
