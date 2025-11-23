"""Integration tests for error handling in realistic scenarios."""

from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import (
    OptionMissingValueError,
    OptionNotRepeatableError,
    UnknownOptionError,
    UnknownSubcommandError,
)
from flagrant.specification import (
    CommandSpecification,
    ValueAccumulationMode,
)

if TYPE_CHECKING:
    from flagrant.specification import (
        CommandSpecificationFactory,
        FlagOptionSpecificationFactory,
        ValueOptionSpecificationFactory,
    )


class TestCommonUserMistakes:
    def test_missing_required_subcommand(self, git_like_spec: CommandSpecification):
        spec = git_like_spec

        with pytest.raises(UnknownSubcommandError) as exc_info:
            parse_command_line_args(spec, ["--version", "invalid"])

        assert exc_info.value.subcommand == "invalid"

    def test_unknown_option_in_complex_command(
        self, git_like_spec: CommandSpecification
    ):
        spec = git_like_spec

        with pytest.raises(UnknownOptionError) as exc_info:
            parse_command_line_args(spec, ["commit", "-m", "test", "--unknown"])

        assert exc_info.value.option == "unknown"

    def test_insufficient_values_for_option_with_required_arity(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="output", short_names=("o",))
        spec = make_command(options={"output": opt})

        with pytest.raises(OptionMissingValueError) as exc_info:
            parse_command_line_args(spec, ["--output"])

        assert exc_info.value.option == "output"

    def test_repeated_non_repeatable_option(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="config",
            short_names=("c",),
            accumulation_mode=ValueAccumulationMode.ERROR,
        )
        spec = make_command(options={"config": opt})

        with pytest.raises(OptionNotRepeatableError) as exc_info:
            parse_command_line_args(spec, ["--config", "a.yaml", "--config", "b.yaml"])

        assert exc_info.value.option == "config"


class TestAmbiguousInputs:
    def test_ambiguous_subcommand_abbreviation(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        spec = make_command(
            subcommands={
                "build": make_command("build"),
                "backup": make_command("backup"),
            }
        )
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        with pytest.raises(UnknownSubcommandError):
            parse_command_line_args(spec, ["b"], config=config)

    def test_ambiguous_option_abbreviation(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        verbose = make_flag_opt(name="verbose")
        version = make_flag_opt(name="version")
        spec = make_command(options={"verbose": verbose, "version": version})
        config = ParserConfiguration(allow_abbreviated_options=True)

        with pytest.raises(UnknownOptionError):
            parse_command_line_args(spec, ["--v"], config=config)


class TestNestedSubcommandErrors:
    def test_unknown_subcommand_at_second_level(
        self, docker_like_spec: CommandSpecification
    ):
        spec = docker_like_spec

        with pytest.raises(UnknownSubcommandError) as exc_info:
            parse_command_line_args(spec, ["compose", "invalid"])

        assert exc_info.value.subcommand == "invalid"

    def test_unknown_option_in_nested_subcommand(
        self, docker_like_spec: CommandSpecification
    ):
        spec = docker_like_spec

        with pytest.raises(UnknownOptionError) as exc_info:
            parse_command_line_args(spec, ["compose", "up", "--invalid"])

        assert exc_info.value.option == "invalid"


class TestMissingRequiredValues:
    def test_value_option_at_end_of_arguments(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="output", short_names=("o",))
        spec = make_command(options={"output": opt})

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--output"])

    def test_value_option_followed_by_another_option(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        output = make_value_opt(name="output", short_names=("o",))
        verbose = make_flag_opt(name="verbose", short_names=("v",))
        spec = make_command(options={"output": output, "verbose": verbose})

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--output", "--verbose"])
