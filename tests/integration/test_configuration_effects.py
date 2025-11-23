"""Integration tests for configuration effects on command parsing."""

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.specification import (
    Arity,
    CommandSpecification,
    FlagOptionSpecification,
    ValueOptionSpecification,
)


class TestStrictPosixMode:
    def test_strict_posix_rejects_options_after_positionals(self):
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
                ),
            },
            positionals={
                "file": Arity.exactly_one(),
            },
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(spec, ["file.txt", "--verbose"], config=config)

        assert result.positionals["file"] == "file.txt"
        assert result.extra_args == ()
        assert "verbose" not in result.options

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
                    short_names=("v",),
                ),
            },
            positionals={
                "file": Arity.exactly_one(),
            },
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(spec, ["--verbose", "file.txt"], config=config)

        assert result.options["verbose"] is True
        assert result.positionals["file"] == "file.txt"

    def test_strict_posix_with_separator_allows_option_like_values(self):
        spec = CommandSpecification(
            "test",
            positionals={
                "args": Arity.zero_or_more(),
            },
        )
        config = ParserConfiguration(strict_posix_options=True)

        result = parse_command_line_args(
            spec, ["--", "--not-an-option", "-v"], config=config
        )

        assert result.extra_args == ("--not-an-option", "-v")


class TestCaseSensitivity:
    def test_case_insensitive_subcommand_matching(self):
        spec = CommandSpecification(
            "test",
            subcommands={
                "build": CommandSpecification("build"),
                "clean": CommandSpecification("clean"),
            },
        )
        config = ParserConfiguration(
            case_sensitive_commands=False,
            case_sensitive_options=False,
        )

        result = parse_command_line_args(spec, ["BUILD"], config=config)

        assert result.subcommand is not None
        assert result.subcommand.command == "build"

    def test_case_insensitive_option_matching(self):
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
                ),
            },
        )
        config = ParserConfiguration(
            case_sensitive_commands=False,
            case_sensitive_options=False,
        )

        result = parse_command_line_args(spec, ["--VERBOSE"], config=config)

        assert result.options["verbose"] is True


class TestAbbreviation:
    def test_subcommand_abbreviation_with_unique_prefix(self):
        spec = CommandSpecification(
            "test",
            subcommands={
                "build": CommandSpecification("build"),
                "clean": CommandSpecification("clean"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        result = parse_command_line_args(spec, ["bui"], config=config)

        assert result.subcommand is not None
        assert result.subcommand.command == "build"

    def test_option_abbreviation_with_unique_prefix(self):
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
                "version": FlagOptionSpecification(
                    name="version",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="version",
                    long_names=("version",),
                    short_names=(),
                ),
            },
        )
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
    def test_greedy_option_consumes_all_available_values(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity.zero_or_more(),
                    greedy=True,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=("f",),
                ),
            },
            positionals={
                "target": Arity.at_most_one(),
            },
        )

        result = parse_command_line_args(spec, ["--files", "a.txt", "b.txt", "c.txt"])

        assert result.options["files"] == ("a.txt", "b.txt", "c.txt")
        assert "target" not in result.positionals

    def test_greedy_option_with_explicit_separator(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity.zero_or_more(),
                    greedy=True,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                ),
            },
            positionals={
                "target": Arity.at_most_one(),
            },
        )

        result = parse_command_line_args(
            spec, ["--files", "a.txt", "b.txt", "--", "extra"]
        )

        assert result.options["files"] == ("a.txt", "b.txt", "--", "extra")


class TestInlineValuesWithoutEquals:
    def test_inline_value_without_equals_for_short_option(self):
        spec = CommandSpecification(
            "test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=(),
                    short_names=("o",),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["-ofile.txt"], config=config)

        assert result.options["output"] == "file.txt"
