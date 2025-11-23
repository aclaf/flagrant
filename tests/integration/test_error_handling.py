"""Integration tests for error handling in realistic scenarios."""

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
    Arity,
    CommandSpecification,
    FlagOptionSpecification,
    ValueAccumulationMode,
    ValueOptionSpecification,
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

    def test_insufficient_values_for_option_with_required_arity(self):
        spec = CommandSpecification(
            "test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=("output",),
                    short_names=("o",),
                ),
            },
        )

        with pytest.raises(OptionMissingValueError) as exc_info:
            parse_command_line_args(spec, ["--output"])

        assert exc_info.value.option == "output"

    def test_repeated_non_repeatable_option(self):
        spec = CommandSpecification(
            "test",
            options={
                "config": ValueOptionSpecification(
                    name="config",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="config",
                    long_names=("config",),
                    short_names=("c",),
                    accumulation_mode=ValueAccumulationMode.ERROR,
                ),
            },
        )

        with pytest.raises(OptionNotRepeatableError) as exc_info:
            parse_command_line_args(spec, ["--config", "a.yaml", "--config", "b.yaml"])

        assert exc_info.value.option == "config"


class TestAmbiguousInputs:
    def test_ambiguous_subcommand_abbreviation(self):
        spec = CommandSpecification(
            "test",
            subcommands={
                "build": CommandSpecification("build"),
                "backup": CommandSpecification("backup"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        with pytest.raises(UnknownSubcommandError):
            parse_command_line_args(spec, ["b"], config=config)

    def test_ambiguous_option_abbreviation(self):
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
    def test_value_option_at_end_of_arguments(self):
        spec = CommandSpecification(
            "test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=("output",),
                    short_names=("o",),
                ),
            },
        )

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--output"])

    def test_value_option_followed_by_another_option(self):
        spec = CommandSpecification(
            "test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=("output",),
                    short_names=("o",),
                ),
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

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--output", "--verbose"])
