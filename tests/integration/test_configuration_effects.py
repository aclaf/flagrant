"""Integration tests for configuration effects on command parsing."""

from typing import TYPE_CHECKING

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.specification import (
    Arity,
    CommandSpecification,
)

if TYPE_CHECKING:
    from flagrant.specification import (
        CommandSpecificationFactory,
        FlagOptionSpecificationFactory,
        ValueOptionSpecificationFactory,
    )


class TestStrictPosixMode:
    def test_strict_posix_rejects_options_after_positionals(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        verbose = make_flag_opt(name="verbose", short_names=("v",))
        spec = make_command(
            options={"verbose": verbose},
            positionals={"file": Arity.exactly_one()},
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(spec, ["file.txt", "--verbose"], config=config)

        assert result.positionals["file"] == "file.txt"
        assert result.extra_args == ()
        assert "verbose" not in result.options

    def test_strict_posix_allows_options_before_positionals(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        verbose = make_flag_opt(name="verbose", short_names=("v",))
        spec = make_command(
            options={"verbose": verbose},
            positionals={"file": Arity.exactly_one()},
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(spec, ["--verbose", "file.txt"], config=config)

        assert result.options["verbose"] is True
        assert result.positionals["file"] == "file.txt"

    def test_strict_posix_with_separator_allows_option_like_values(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        spec = make_command(positionals={"args": Arity.zero_or_more()})
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(
            spec, ["--", "--not-an-option", "-v"], config=config
        )

        assert result.extra_args == ("--not-an-option", "-v")


class TestCaseSensitivity:
    def test_case_insensitive_subcommand_matching(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        spec = make_command(
            subcommands={
                "build": make_command("build"),
                "clean": make_command("clean"),
            },
        )
        config = ParserConfiguration(
            case_sensitive_commands=False,
            case_sensitive_options=False,
        )

        result = parse_command_line_args(spec, ["BUILD"], config=config)

        assert result.subcommand is not None
        assert result.subcommand.command == "build"

    def test_case_insensitive_option_matching(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        verbose = make_flag_opt(name="verbose", short_names=("v",))
        spec = make_command(options={"verbose": verbose})
        config = ParserConfiguration(
            case_sensitive_commands=False,
            case_sensitive_options=False,
        )

        result = parse_command_line_args(spec, ["--VERBOSE"], config=config)

        assert result.options["verbose"] is True


class TestAbbreviation:
    def test_subcommand_abbreviation_with_unique_prefix(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        spec = make_command(
            subcommands={
                "build": make_command("build"),
                "clean": make_command("clean"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        result = parse_command_line_args(spec, ["bui"], config=config)

        assert result.subcommand is not None
        assert result.subcommand.command == "build"

    def test_option_abbreviation_with_unique_prefix(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        verbose = make_flag_opt(name="verbose")
        version = make_flag_opt(name="version")
        spec = make_command(options={"verbose": verbose, "version": version})
        config = ParserConfiguration(allow_abbreviated_options=True)

        result = parse_command_line_args(spec, ["--verb"], config=config)

        assert result.options["verbose"] is True

    def test_abbreviation_with_real_world_git_command(
        self, git_like_spec: CommandSpecification
    ):
        spec = git_like_spec
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        result = parse_command_line_args(spec, ["com", "-m", "test"], config=config)

        assert result.subcommand is not None
        assert result.subcommand.command == "commit"
        assert result.subcommand.options["message"] == "test"


class TestGreedyMode:
    def test_greedy_option_consumes_all_available_values(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        files = make_value_opt(
            name="files", arity=Arity.zero_or_more(), greedy=True, short_names=("f",)
        )
        spec = make_command(
            options={"files": files},
            positionals={"target": Arity.at_most_one()},
        )

        result = parse_command_line_args(
            spec, ["--files", "a.txt", "b.txt", "c.txt"]
        )

        assert result.options["files"] == ("a.txt", "b.txt", "c.txt")
        assert "target" not in result.positionals

    def test_greedy_option_with_explicit_separator(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        files = make_value_opt(
            name="files", arity=Arity.zero_or_more(), greedy=True, short_names=()
        )
        spec = make_command(
            options={"files": files},
            positionals={"target": Arity.at_most_one()},
        )

        result = parse_command_line_args(
            spec, ["--files", "a.txt", "b.txt", "--", "extra"]
        )

        assert result.options["files"] == ("a.txt", "b.txt", "--", "extra")


class TestInlineValuesWithoutEquals:
    def test_inline_value_without_equals_for_short_option(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        output = make_value_opt(
            name="output", long_names=(), short_names=("o",)
        )
        spec = make_command(options={"output": output})
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["-ofile.txt"], config=config)

        assert result.options["output"] == "file.txt"
