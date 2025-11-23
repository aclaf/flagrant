from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import UnknownOptionError, UnknownSubcommandError

if TYPE_CHECKING:
    from flagrant.specification import (
        CommandSpecificationFactory,
        FlagOptionSpecificationFactory,
        ValueOptionSpecificationFactory,
    )


class TestUnderscoreHyphenConversion:
    @pytest.mark.parametrize(
        (
            "name",
            "option_kwargs",
            "convert_underscores",
            "input_arg",
            "expected_key",
            "expect_error",
        ),
        [
            (
                "underscore_to_hyphen",
                {"name": "log-level"},
                True,
                "--log_level",
                "log-level",
                False,
            ),
            (
                "hyphen_to_underscore",
                {"name": "dry-run"},
                True,
                "--dry_run",
                "dry-run",
                False,
            ),
            (
                "conversion_disabled",
                {"name": "log-level"},
                False,
                "--log_level",
                "log_level",  # Error expected
                True,
            ),
            (
                "conversion_with_abbreviation",
                {"name": "log-level"},
                True,
                "--log_l",
                "log-level",
                False,
            ),
            (
                "conversion_with_aliases",
                {"name": "log-level", "long_names": ("log-level", "logging-level")},
                True,
                "--logging_level",
                "log-level",
                False,
            ),
        ],
    )
    def test_underscore_conversion(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        name: str,
        option_kwargs: dict[str, object],
        convert_underscores: bool,
        input_arg: str,
        expected_key: str,
        expect_error: bool,
    ):
        opt = make_flag_opt(**option_kwargs)  # type: ignore[reportArgumentType]
        spec = make_command(options={opt.name: opt})
        config = ParserConfiguration(
            convert_underscores=convert_underscores,
            allow_abbreviated_options=True,  # For abbreviation test
        )

        if expect_error:
            with pytest.raises(UnknownOptionError) as exc_info:
                parse_command_line_args(spec, [input_arg], config)
            assert exc_info.value.option == expected_key
        else:
            result = parse_command_line_args(spec, [input_arg], config)
            assert result.options[expected_key] is True

    def test_conversion_preserves_original_in_error_messages(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="verbose")
        spec = make_command(options={"verbose": opt})
        config = ParserConfiguration(convert_underscores=True)

        with pytest.raises(UnknownOptionError) as exc_info:
            parse_command_line_args(spec, ["--log_level"], config)

        assert exc_info.value.option == "log_level"

    def test_conversion_in_subcommand_names(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        run_tests = make_command("run-tests")
        build_docs = make_command("build-docs")
        spec = make_command(
            subcommands={"run-tests": run_tests, "build-docs": build_docs}
        )
        config = ParserConfiguration(convert_underscores=True)

        result = parse_command_line_args(spec, ["run_tests"], config)
        assert result.subcommand is not None
        assert result.subcommand.command == "run-tests"


class TestCaseInsensitivity:
    @pytest.mark.parametrize(
        ("name", "option_kwargs", "input_arg"),
        [
            (
                "long_uppercase",
                {"name": "verbose"},
                "--VERBOSE",
            ),
            (
                "long_capitalized",
                {"name": "verbose"},
                "--Verbose",
            ),
            (
                "long_mixed",
                {"name": "verbose"},
                "--VeRbOsE",
            ),
            (
                "short_uppercase",
                {"name": "verbose", "long_names": (), "short_names": ("v",)},
                "-V",
            ),
            (
                "mixed_case_name",
                {"name": "LogLevel", "long_names": ("LogLevel",)},
                "--loglevel",
            ),
            (
                "mixed_case_name_uppercase",
                {"name": "LogLevel", "long_names": ("LogLevel",)},
                "--LOGLEVEL",
            ),
        ],
    )
    def test_case_insensitive_option_matching(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        name: str,
        option_kwargs: dict[str, object],
        input_arg: str,
    ):
        opt = make_flag_opt(**option_kwargs)  # type: ignore[reportArgumentType]
        spec = make_command(options={opt.name: opt})
        config = ParserConfiguration(case_sensitive_options=False)

        result = parse_command_line_args(spec, [input_arg], config)

        assert result.options[opt.name] is True

    def test_case_insensitive_subcommands(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        build_cmd = make_command("build")
        test_cmd = make_command("test")
        spec = make_command(subcommands={"build": build_cmd, "test": test_cmd})
        config = ParserConfiguration(case_sensitive_commands=False)

        result1 = parse_command_line_args(spec, ["BUILD"], config)
        result2 = parse_command_line_args(spec, ["Test"], config)

        assert result1.subcommand is not None
        assert result1.subcommand.command == "build"
        assert result2.subcommand is not None
        assert result2.subcommand.command == "test"

    def test_case_preservation_in_results(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="path")
        spec = make_command(options={"path": opt})
        config = ParserConfiguration(case_sensitive_options=False)

        result = parse_command_line_args(spec, ["--PATH=MyFile.txt"], config)
        assert result.options["path"] == "MyFile.txt"

    def test_interaction_with_abbreviation(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            options={
                "verbose": make_flag_opt(name="verbose"),
                "version": make_flag_opt(name="version"),
            },
        )
        config = ParserConfiguration(
            case_sensitive_options=False, allow_abbreviated_options=True
        )

        result = parse_command_line_args(spec, ["--VERB"], config)
        assert result.options["verbose"] is True

    def test_partial_case_insensitivity_options_only(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="verbose")
        build_cmd = make_command("build")
        spec = make_command(options={"verbose": opt}, subcommands={"build": build_cmd})
        config = ParserConfiguration(
            case_sensitive_options=False, case_sensitive_commands=True
        )

        result = parse_command_line_args(spec, ["--VERBOSE"], config)
        assert result.options["verbose"] is True

        with pytest.raises(UnknownSubcommandError):
            parse_command_line_args(spec, ["BUILD"], config)

    def test_error_messages_with_case_insensitivity(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="verbose")
        spec = make_command(options={"verbose": opt})
        config = ParserConfiguration(case_sensitive_options=False)

        with pytest.raises(UnknownOptionError) as exc_info:
            parse_command_line_args(spec, ["--UNKNOWN"], config)

        assert exc_info.value.option == "UNKNOWN"
