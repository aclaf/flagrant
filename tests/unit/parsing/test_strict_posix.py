from flagrant.configuration import ParserConfiguration
from flagrant.enums import UngroupedPositionalStrategy
from flagrant.parser import parse_command_line_args
from flagrant.specification import (
    Arity,
    CommandSpecification,
    FlagOptionSpecification,
    ValueOptionSpecification,
)


class TestStrictPosixBasic:
    def test_strict_posix_allows_options_before_positionals(self):
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
            positionals={"file": Arity.exactly_one()},
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(
            spec, ["--verbose", "--output", "file.txt", "positional.txt"], config=config
        )

        assert result.options["verbose"] is True
        assert result.options["output"] == "file.txt"
        assert result.positionals["file"] == "positional.txt"

    def test_strict_posix_treats_option_after_positional_as_positional(self):
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
            },
            positionals={"files": Arity.at_least_one()},
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(
            spec, ["positional.txt", "--verbose"], config=config
        )

        assert result.positionals["files"] == ("positional.txt", "--verbose")
        assert "verbose" not in result.options

    def test_strict_posix_option_like_value_after_positional_captured(self):
        spec = CommandSpecification(
            "test",
            positionals={
                "cmd": Arity.exactly_one(),
                "arg1": Arity.exactly_one(),
                "arg2": Arity.exactly_one(),
            },
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(
            spec, ["cmd", "arg1", "--looks-like-option"], config=config
        )

        assert result.positionals["cmd"] == "cmd"
        assert result.positionals["arg1"] == "arg1"
        assert result.positionals["arg2"] == "--looks-like-option"


class TestStrictPosixWithDelimiter:
    def test_strict_posix_delimiter_drops_trailing_args(self):
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
            },
            positionals={"files": Arity.zero_or_more()},
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(
            spec, ["--", "--verbose", "file.txt"], config=config
        )

        assert len(result.positionals) == 0
        assert "verbose" not in result.options

    def test_strict_posix_options_before_delimiter_parsed_normally(self):
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
            },
            positionals={"files": Arity.zero_or_more()},
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(
            spec, ["--verbose", "--", "pos1.txt", "pos2.txt"], config=config
        )

        assert result.options["verbose"] is True
        assert len(result.positionals) == 0


class TestStrictPosixWithSubcommands:
    def test_strict_posix_subcommand_before_positionals_works(self):
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
            },
            subcommands={
                "build": CommandSpecification("build"),
            },
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(
            spec, ["--verbose", "build"], config=config
        )

        assert result.options["verbose"] is True
        assert result.subcommand is not None
        assert result.subcommand.command == "build"

    def test_strict_posix_positional_prevents_subcommand_detection(self):
        spec = CommandSpecification(
            "test",
            subcommands={
                "build": CommandSpecification("build"),
            },
            positionals={"args": Arity.at_least_one()},
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(
            spec, ["positional_value", "build"], config=config
        )

        assert result.positionals["args"] == ("positional_value", "build")
        assert result.subcommand is None


class TestStrictPosixWithUngrouped:
    def test_strict_posix_with_ungrouped_collect_captures_options(self):
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
            positionals={"file": Arity.exactly_one()},
        )
        config = ParserConfiguration(
            strict_posix_options=True,
            ungrouped_positional_strategy=UngroupedPositionalStrategy.COLLECT,
            ungrouped_positional_name="extras",
        )

        result = parse_command_line_args(
            spec, ["first.txt", "--verbose", "--output", "file.txt"], config=config
        )

        assert result.positionals["file"] == "first.txt"
        assert result.positionals["extras"] == ("--verbose", "--output", "file.txt")
        assert "verbose" not in result.options
        assert "output" not in result.options
