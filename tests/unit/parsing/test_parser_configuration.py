"""Tests for parser configuration options including conversion and case settings."""

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import UnknownOptionError, UnknownSubcommandError
from flagrant.specification import (
    Arity,
    CommandSpecification,
    FlagOptionSpecification,
    ValueOptionSpecification,
)


class TestUnderscoreHyphenConversion:
    def test_underscore_to_hyphen_conversion_in_option_names(self):
        spec = CommandSpecification(
            name="test",
            options={
                "log-level": FlagOptionSpecification(
                    name="log-level",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="log-level",
                    long_names=("log-level",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(convert_underscores=True)

        result = parse_command_line_args(spec, ["--log_level"], config)
        assert result.options["log-level"] is True

    def test_hyphen_to_underscore_conversion(self):
        spec = CommandSpecification(
            name="test",
            options={
                "dry-run": FlagOptionSpecification(
                    name="dry-run",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="dry-run",
                    long_names=("dry-run",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(convert_underscores=True)

        result = parse_command_line_args(spec, ["--dry_run"], config)
        assert result.options["dry-run"] is True

    def test_conversion_disabled(self):
        spec = CommandSpecification(
            name="test",
            options={
                "log-level": FlagOptionSpecification(
                    name="log-level",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="log-level",
                    long_names=("log-level",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(convert_underscores=False)

        with pytest.raises(UnknownOptionError) as exc_info:
            parse_command_line_args(spec, ["--log_level"], config)

        assert exc_info.value.option == "log_level"

    def test_conversion_with_abbreviation(self):
        spec = CommandSpecification(
            name="test",
            options={
                "log-level": FlagOptionSpecification(
                    name="log-level",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="log-level",
                    long_names=("log-level",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(
            convert_underscores=True, allow_abbreviated_options=True
        )

        result = parse_command_line_args(spec, ["--log_l"], config)
        assert result.options["log-level"] is True

    def test_conversion_preserves_original_in_error_messages(self):
        spec = CommandSpecification(
            name="test",
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
        )
        config = ParserConfiguration(convert_underscores=True)

        with pytest.raises(UnknownOptionError) as exc_info:
            parse_command_line_args(spec, ["--log_level"], config)

        assert exc_info.value.option == "log_level"

    def test_conversion_with_aliases(self):
        spec = CommandSpecification(
            name="test",
            options={
                "log-level": FlagOptionSpecification(
                    name="log-level",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="log-level",
                    long_names=("log-level", "logging-level"),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(convert_underscores=True)

        result = parse_command_line_args(spec, ["--logging_level"], config)
        assert result.options["log-level"] is True

    def test_conversion_in_subcommand_names(self):
        spec = CommandSpecification(
            name="test",
            subcommands={
                "run-tests": CommandSpecification("run-tests"),
                "build-docs": CommandSpecification("build-docs"),
            },
        )
        config = ParserConfiguration(convert_underscores=True)

        result = parse_command_line_args(spec, ["run_tests"], config)
        assert result.subcommand is not None
        assert result.subcommand.command == "run-tests"


class TestCaseInsensitivity:
    def test_case_insensitive_long_options(self):
        spec = CommandSpecification(
            name="test",
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
        )
        config = ParserConfiguration(case_sensitive_options=False)

        result1 = parse_command_line_args(spec, ["--VERBOSE"], config)
        result2 = parse_command_line_args(spec, ["--Verbose"], config)
        result3 = parse_command_line_args(spec, ["--VeRbOsE"], config)

        assert result1.options["verbose"] is True
        assert result2.options["verbose"] is True
        assert result3.options["verbose"] is True

    def test_case_insensitive_short_options(self):
        spec = CommandSpecification(
            name="test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=(),
                    short_names=("v",),
                ),
            },
        )
        config = ParserConfiguration(case_sensitive_options=False)

        result = parse_command_line_args(spec, ["-V"], config)
        assert result.options["verbose"] is True

    def test_case_insensitive_subcommands(self):
        spec = CommandSpecification(
            name="test",
            subcommands={
                "build": CommandSpecification("build"),
                "test": CommandSpecification("test"),
            },
        )
        config = ParserConfiguration(case_sensitive_commands=False)

        result1 = parse_command_line_args(spec, ["BUILD"], config)
        result2 = parse_command_line_args(spec, ["Test"], config)

        assert result1.subcommand is not None
        assert result1.subcommand.command == "build"
        assert result2.subcommand is not None
        assert result2.subcommand.command == "test"

    def test_case_preservation_in_results(self):
        spec = CommandSpecification(
            name="test",
            options={
                "path": ValueOptionSpecification(
                    name="path",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="path",
                    long_names=("path",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(case_sensitive_options=False)

        result = parse_command_line_args(spec, ["--PATH=MyFile.txt"], config)
        assert result.options["path"] == "MyFile.txt"

    def test_interaction_with_abbreviation(self):
        spec = CommandSpecification(
            name="test",
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
        config = ParserConfiguration(
            case_sensitive_options=False, allow_abbreviated_options=True
        )

        result = parse_command_line_args(spec, ["--VERB"], config)
        assert result.options["verbose"] is True

    def test_partial_case_insensitivity_options_only(self):
        spec = CommandSpecification(
            name="test",
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
        config = ParserConfiguration(
            case_sensitive_options=False, case_sensitive_commands=True
        )

        result = parse_command_line_args(spec, ["--VERBOSE"], config)
        assert result.options["verbose"] is True

        with pytest.raises(UnknownSubcommandError):
            parse_command_line_args(spec, ["BUILD"], config)

    def test_error_messages_with_case_insensitivity(self):
        spec = CommandSpecification(
            name="test",
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
        )
        config = ParserConfiguration(case_sensitive_options=False)

        with pytest.raises(UnknownOptionError) as exc_info:
            parse_command_line_args(spec, ["--UNKNOWN"], config)

        assert exc_info.value.option == "UNKNOWN"

    def test_mixed_case_input_handling(self):
        spec = CommandSpecification(
            name="test",
            options={
                "LogLevel": FlagOptionSpecification(
                    name="LogLevel",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="LogLevel",
                    long_names=("LogLevel",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(case_sensitive_options=False)

        result1 = parse_command_line_args(spec, ["--loglevel"], config)
        result2 = parse_command_line_args(spec, ["--LOGLEVEL"], config)
        result3 = parse_command_line_args(spec, ["--LogLevel"], config)

        assert result1.options["LogLevel"] is True
        assert result2.options["LogLevel"] is True
        assert result3.options["LogLevel"] is True
