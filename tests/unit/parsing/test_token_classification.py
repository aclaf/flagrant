import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.enums import UngroupedPositionalStrategy
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import PositionalUnexpectedValueError
from flagrant.specification import (
    Arity,
    CommandSpecification,
    FlagOptionSpecification,
    ValueOptionSpecification,
)


class TestLongOptionClassification:
    def test_classify_argument_with_double_dash_prefix_as_long_option(self):
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
                )
            },
        )

        result = parse_command_line_args(spec, ["--verbose"])

        assert result.options["verbose"] is True

    def test_classify_single_character_after_double_dash_as_long_option(self):
        spec = CommandSpecification(
            "test",
            options={
                "v": FlagOptionSpecification(
                    name="v",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="v",
                    long_names=("v",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--v"])

        assert result.options["v"] is True

    def test_classify_long_option_with_alphanumeric_and_dash_characters(self):
        spec = CommandSpecification(
            "test",
            options={
                "log-level-2": ValueOptionSpecification(
                    name="log-level-2",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="log-level-2",
                    long_names=("log-level-2",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--log-level-2", "debug"])

        assert result.options["log-level-2"] == "debug"

    def test_classify_standalone_double_dash_as_delimiter_not_option(self):
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
                )
            },
        )

        result = parse_command_line_args(spec, ["--verbose", "--", "--not-option"])

        assert result.options["verbose"] is True
        assert result.extra_args == ("--not-option",)
        assert "not-option" not in result.options

    def test_classify_long_option_with_equals_syntax(self):
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


class TestShortOptionClassification:
    def test_classify_argument_with_single_dash_prefix_as_short_option(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="v",
                    long_names=(),
                    short_names=("v",),
                )
            },
        )

        result = parse_command_line_args(spec, ["-v"])

        assert result.options["verbose"] is True

    def test_classify_single_character_after_dash_as_short_option(self):
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
                )
            },
        )

        result = parse_command_line_args(spec, ["-o", "file.txt"])

        assert result.options["output"] == "file.txt"

    def test_classify_clustered_short_options_as_multiple_options(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="v",
                    long_names=(),
                    short_names=("v",),
                ),
                "quiet": FlagOptionSpecification(
                    name="quiet",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="q",
                    long_names=(),
                    short_names=("q",),
                ),
                "force": FlagOptionSpecification(
                    name="force",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="f",
                    long_names=(),
                    short_names=("f",),
                ),
            },
        )

        result = parse_command_line_args(spec, ["-vqf"])

        assert result.options["verbose"] is True
        assert result.options["quiet"] is True
        assert result.options["force"] is True

    def test_classify_single_dash_as_positional_not_option(self):
        spec = CommandSpecification("test", positionals={"args": Arity.zero_or_more()})

        result = parse_command_line_args(spec, ["-"])

        assert result.positionals["args"] == ("-",)


class TestPositionalClassification:
    def test_classify_argument_without_dash_prefix_as_positional(self):
        spec = CommandSpecification("test", positionals={"args": Arity.zero_or_more()})

        result = parse_command_line_args(spec, ["file.txt"])

        assert result.positionals["args"] == ("file.txt",)

    def test_classify_multiple_arguments_without_dash_as_positionals(self):
        spec = CommandSpecification("test", positionals={"args": Arity.zero_or_more()})

        result = parse_command_line_args(spec, ["file1.txt", "file2.txt", "file3.txt"])

        assert result.positionals["args"] == ("file1.txt", "file2.txt", "file3.txt")

    def test_classify_arguments_after_delimiter_as_trailing_args(self):
        spec = CommandSpecification("test")

        result = parse_command_line_args(spec, ["--", "arg1", "arg2"])

        assert result.extra_args == ("arg1", "arg2")
        assert "args" not in result.positionals or result.positionals["args"] == ()

    def test_classify_all_arguments_after_delimiter_as_trailing_including_options(self):
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
                )
            },
        )

        result = parse_command_line_args(spec, ["--", "--verbose", "file.txt"])

        assert result.extra_args == ("--verbose", "file.txt")
        assert "verbose" not in result.options


class TestNegativeNumberHandling:
    def test_classify_negative_integer_as_value_when_negative_numbers_allowed(self):
        spec = CommandSpecification(
            "test",
            options={
                "threshold": ValueOptionSpecification(
                    name="threshold",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="threshold",
                    long_names=("threshold",),
                    short_names=(),
                )
            },
        )
        config = ParserConfiguration(allow_negative_numbers=True)

        result = parse_command_line_args(spec, ["--threshold", "-5"], config)

        assert result.options["threshold"] == "-5"

    def test_classify_negative_float_as_value_when_negative_numbers_allowed(self):
        spec = CommandSpecification(
            "test",
            options={
                "coefficient": ValueOptionSpecification(
                    name="coefficient",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="coefficient",
                    long_names=("coefficient",),
                    short_names=(),
                )
            },
        )
        config = ParserConfiguration(allow_negative_numbers=True)

        result = parse_command_line_args(spec, ["--coefficient", "-3.14"], config)

        assert result.options["coefficient"] == "-3.14"

    def test_classify_negative_number_as_short_option_when_not_allowed(self):
        spec = CommandSpecification(
            "test",
            options={
                "five": FlagOptionSpecification(
                    name="five",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="5",
                    long_names=(),
                    short_names=("5",),
                )
            },
        )
        config = ParserConfiguration(allow_negative_numbers=False)

        result = parse_command_line_args(spec, ["-5"], config)

        assert result.options["five"] is True

    def test_classify_negative_number_as_positional_when_no_positional_specs(self):
        spec = CommandSpecification("test", positionals={"args": Arity.zero_or_more()})
        config = ParserConfiguration(allow_negative_numbers=True)

        result = parse_command_line_args(spec, ["-5"], config)

        assert result.positionals["args"] == ("-5",)


class TestPosixStrictOrdering:
    def test_classify_option_after_positional_as_positional_in_strict_mode(self):
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
            positionals={"args": Arity.zero_or_more()},
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(
            spec, ["file.txt", "--output", "result.txt"], config
        )

        assert result.positionals["args"] == ("file.txt", "--output", "result.txt")
        assert "output" not in result.options

    def test_classify_option_before_positional_as_option_in_strict_mode(self):
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
                )
            },
            positionals={"args": Arity.zero_or_more()},
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(spec, ["--verbose", "file.txt"], config)

        assert result.options["verbose"] is True
        assert result.positionals["args"] == ("file.txt",)

    def test_classify_mixed_options_positionals_correctly_in_strict_mode(self):
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
                ),
                "config": ValueOptionSpecification(
                    name="config",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="config",
                    long_names=("config",),
                    short_names=(),
                ),
            },
            positionals={"args": Arity.zero_or_more()},
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(
            spec, ["--verbose", "--config", "app.yaml", "file.txt", "--extra"], config
        )

        assert result.options["verbose"] is True
        assert result.options["config"] == "app.yaml"
        assert result.positionals["args"] == ("file.txt", "--extra")

    def test_classify_options_and_positionals_freely_without_strict_mode(self):
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
            positionals={"args": Arity.zero_or_more()},
        )
        config = ParserConfiguration(strict_posix_options=False)

        result = parse_command_line_args(
            spec, ["file.txt", "--verbose", "--output", "result.txt"], config
        )

        assert result.options["verbose"] is True
        assert result.options["output"] == "result.txt"
        assert result.positionals["args"] == ("file.txt",)


class TestSubcommandDetection:
    def test_classify_matching_subcommand_name_as_subcommand(self):
        subcommand_spec = CommandSpecification("build")
        spec = CommandSpecification("test", subcommands={"build": subcommand_spec})

        result = parse_command_line_args(spec, ["build"])

        assert result.subcommand is not None
        assert result.subcommand.command == "build"

    def test_classify_matching_subcommand_alias_as_subcommand(self):
        subcommand_spec = CommandSpecification("build", aliases=["b"])
        spec = CommandSpecification("test", subcommands={"build": subcommand_spec})

        result = parse_command_line_args(spec, ["b"])

        assert result.subcommand is not None
        assert result.subcommand.command == "build"

    def test_delegate_remaining_args_to_subcommand(self):
        subcommand_spec = CommandSpecification(
            "build",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=(),
                )
            },
            positionals={"args": Arity.zero_or_more()},
        )
        spec = CommandSpecification("test", subcommands={"build": subcommand_spec})

        result = parse_command_line_args(spec, ["build", "--verbose", "file.txt"])

        assert result.subcommand is not None
        assert result.subcommand.command == "build"
        assert result.subcommand.options["verbose"] is True
        assert result.subcommand.positionals["args"] == ("file.txt",)

    def test_classify_non_matching_name_as_positional(self):
        subcommand_spec = CommandSpecification("build")
        spec = CommandSpecification(
            "test",
            subcommands={"build": subcommand_spec},
            positionals={"args": Arity.zero_or_more()},
        )

        result = parse_command_line_args(spec, ["deploy"])

        assert result.subcommand is None
        assert result.positionals["args"] == ("deploy",)


class TestStrictPosixWithUngroupedPositionals:
    def test_strict_posix_with_ignore_strategy_drops_extras(self):
        spec = CommandSpecification(
            "test",
            positionals={"file": Arity.exactly_one()},
        )

        config = ParserConfiguration(
            strict_posix_options=True,
            ungrouped_positional_strategy=UngroupedPositionalStrategy.IGNORE,
        )

        result = parse_command_line_args(
            spec,
            ["file.txt", "extra1.txt", "extra2.txt"],
            config=config,
        )

        assert result.positionals["file"] == "file.txt"
        assert len(result.positionals) == 1

    def test_strict_posix_with_collect_strategy_gathers_extras(self):
        spec = CommandSpecification(
            "test",
            positionals={"file": Arity.exactly_one()},
        )

        config = ParserConfiguration(
            strict_posix_options=True,
            ungrouped_positional_strategy=UngroupedPositionalStrategy.COLLECT,
            ungrouped_positional_name="extras",
        )

        result = parse_command_line_args(
            spec,
            ["file.txt", "extra1.txt", "extra2.txt"],
            config=config,
        )

        assert result.positionals["file"] == "file.txt"
        assert result.positionals["extras"] == ("extra1.txt", "extra2.txt")

    def test_strict_posix_with_error_strategy_raises(self):
        spec = CommandSpecification(
            "test",
            positionals={"file": Arity.exactly_one()},
        )

        config = ParserConfiguration(
            strict_posix_options=True,
            ungrouped_positional_strategy=UngroupedPositionalStrategy.ERROR,
        )

        with pytest.raises(PositionalUnexpectedValueError):
            _ = parse_command_line_args(
                spec,
                ["file.txt", "extra.txt"],
                config=config,
            )

    def test_strict_posix_treats_options_after_positionals_as_positionals(self):
        # Design decision: Unbounded arity supersedes ungrouped collection
        # When files has at_least_one() arity, it consumes ALL positionals
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
                )
            },
            positionals={"files": Arity.at_least_one()},
        )

        config = ParserConfiguration(
            strict_posix_options=True,
            ungrouped_positional_strategy=UngroupedPositionalStrategy.COLLECT,
            ungrouped_positional_name="extras",
        )

        result = parse_command_line_args(
            spec,
            ["file.txt", "--verbose", "other.txt"],
            config=config,
        )

        # Unbounded arity consumes all positionals (including option-like
        # strings in strict POSIX mode)
        assert result.positionals["files"] == ("file.txt", "--verbose", "other.txt")
        assert "extras" not in result.positionals  # Nothing left for ungrouped
        assert "verbose" not in result.options  # Correctly not parsed as option

    def test_strict_posix_with_multiple_groups_and_leftovers(self):
        spec = CommandSpecification(
            "test",
            positionals={
                "input": Arity.exactly_one(),
                "output": Arity.exactly_one(),
            },
        )

        config = ParserConfiguration(
            strict_posix_options=True,
            ungrouped_positional_strategy=UngroupedPositionalStrategy.COLLECT,
            ungrouped_positional_name="remaining",
        )

        result = parse_command_line_args(
            spec,
            ["in.txt", "out.txt", "extra1.txt", "extra2.txt"],
            config=config,
        )

        assert result.positionals["input"] == "in.txt"
        assert result.positionals["output"] == "out.txt"
        assert result.positionals["remaining"] == ("extra1.txt", "extra2.txt")
