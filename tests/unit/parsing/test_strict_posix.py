from typing import TYPE_CHECKING

from flagrant.configuration import ParserConfiguration
from flagrant.enums import UngroupedPositionalStrategy
from flagrant.parser import parse_command_line_args
from flagrant.specification import (
    Arity,
)

if TYPE_CHECKING:
    from flagrant.specification import (
        CommandSpecificationFactory,
        FlagOptionSpecificationFactory,
        ValueOptionSpecificationFactory,
    )

class TestStrictPosixBasic:
    def test_strict_posix_allows_options_before_positionals(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt_verbose = make_flag_opt(name="verbose")
        opt_output = make_value_opt(name="output")
        spec = make_command(
            options={"verbose": opt_verbose, "output": opt_output},
            positionals={"file": Arity.exactly_one()},
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(
            spec, ["--verbose", "--output", "file.txt", "positional.txt"], config=config
        )

        assert result.options["verbose"] is True
        assert result.options["output"] == "file.txt"
        assert result.positionals["file"] == "positional.txt"

    def test_strict_posix_treats_option_after_positional_as_positional(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="verbose")
        spec = make_command(
            options={"verbose": opt},
            positionals={"files": Arity.at_least_one()},
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(
            spec, ["positional.txt", "--verbose"], config=config
        )

        assert result.positionals["files"] == ("positional.txt", "--verbose")
        assert "verbose" not in result.options

    def test_strict_posix_option_like_value_after_positional_captured(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        spec = make_command(
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
    def test_strict_posix_delimiter_drops_trailing_args(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="verbose")
        spec = make_command(
            options={"verbose": opt},
            positionals={"files": Arity.zero_or_more()},
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(
            spec, ["--", "--verbose", "file.txt"], config=config
        )

        assert len(result.positionals) == 0
        assert "verbose" not in result.options

    def test_strict_posix_options_before_delimiter_parsed_normally(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="verbose")
        spec = make_command(
            options={"verbose": opt},
            positionals={"files": Arity.zero_or_more()},
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(
            spec, ["--verbose", "--", "pos1.txt", "pos2.txt"], config=config
        )

        assert result.options["verbose"] is True
        assert len(result.positionals) == 0


class TestStrictPosixWithSubcommands:
    def test_strict_posix_subcommand_before_positionals_works(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="verbose")
        subcmd = make_command("build")
        spec = make_command(options={"verbose": opt}, subcommands={"build": subcmd})
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(spec, ["--verbose", "build"], config=config)

        assert result.options["verbose"] is True
        assert result.subcommand is not None
        assert result.subcommand.command == "build"

    def test_strict_posix_positional_prevents_subcommand_detection(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        subcmd = make_command("build")
        spec = make_command(
            subcommands={"build": subcmd},
            positionals={"args": Arity.at_least_one()},
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(
            spec, ["positional_value", "build"], config=config
        )

        assert result.positionals["args"] == ("positional_value", "build")
        assert result.subcommand is None


class TestStrictPosixWithUngrouped:
    def test_strict_posix_with_ungrouped_collect_captures_options(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt_verbose = make_flag_opt(name="verbose")
        opt_output = make_value_opt(name="output")
        spec = make_command(
            options={"verbose": opt_verbose, "output": opt_output},
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
