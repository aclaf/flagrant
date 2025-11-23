import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.enums import UngroupedPositionalStrategy
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import UnknownSubcommandError
from flagrant.specification import (
    Arity,
    CommandSpecification,
    FlagOptionSpecification,
)


class TestUnknownSubcommandConditions:
    def test_subcommand_only_command_raises_unknown_for_invalid_arg(self):
        spec = CommandSpecification(
            "test",
            subcommands={
                "build": CommandSpecification("build"),
                "clean": CommandSpecification("clean"),
            },
        )

        with pytest.raises(UnknownSubcommandError) as exc_info:
            _ = parse_command_line_args(spec, ["invalid_subcommand"])

        assert exc_info.value.subcommand == "invalid_subcommand"

    def test_subcommand_only_command_with_multiple_invalid_args(self):
        spec = CommandSpecification(
            "test",
            subcommands={
                "build": CommandSpecification("build"),
                "clean": CommandSpecification("clean"),
            },
        )

        with pytest.raises(UnknownSubcommandError) as exc_info:
            _ = parse_command_line_args(spec, ["first_invalid", "second_invalid"])

        assert exc_info.value.subcommand == "first_invalid"

    def test_delimiter_prevents_unknown_subcommand_error(self):
        spec = CommandSpecification(
            "test",
            subcommands={
                "build": CommandSpecification("build"),
            },
        )
        config = ParserConfiguration(
            ungrouped_positional_strategy=UngroupedPositionalStrategy.COLLECT,
            ungrouped_positional_name="args",
        )

        result = parse_command_line_args(spec, ["--", "unknown"], config=config)

        assert result.subcommand is None
        assert len(result.positionals) == 0

    def test_valid_subcommand_then_unknown_arg_in_subcommand(self):
        spec = CommandSpecification(
            "test",
            subcommands={
                "build": CommandSpecification(
                    "build",
                    subcommands={
                        "docker": CommandSpecification("docker"),
                    },
                ),
            },
        )

        with pytest.raises(UnknownSubcommandError) as exc_info:
            _ = parse_command_line_args(spec, ["build", "unknown_arg"])

        assert exc_info.value.subcommand == "unknown_arg"

    def test_option_before_unknown_subcommand_still_raises_error(self):
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

        with pytest.raises(UnknownSubcommandError) as exc_info:
            _ = parse_command_line_args(spec, ["--verbose", "unknown_subcommand"])

        assert exc_info.value.subcommand == "unknown_subcommand"
