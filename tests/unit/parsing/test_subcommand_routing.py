from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.enums import UngroupedPositionalStrategy
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import UnknownSubcommandError

if TYPE_CHECKING:
    from flagrant.specification import (
        CommandSpecificationFactory,
        FlagOptionSpecificationFactory,
    )


class TestUnknownSubcommandConditions:
    def test_subcommand_only_command_raises_unknown_for_invalid_arg(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            subcommands={
                "build": make_command("build"),
                "clean": make_command("clean"),
            },
        )

        with pytest.raises(UnknownSubcommandError) as exc_info:
            _ = parse_command_line_args(spec, ["invalid_subcommand"])

        assert exc_info.value.subcommand == "invalid_subcommand"

    def test_subcommand_only_command_with_multiple_invalid_args(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            subcommands={
                "build": make_command("build"),
                "clean": make_command("clean"),
            },
        )

        with pytest.raises(UnknownSubcommandError) as exc_info:
            _ = parse_command_line_args(spec, ["first_invalid", "second_invalid"])

        assert exc_info.value.subcommand == "first_invalid"

    def test_delimiter_prevents_unknown_subcommand_error(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            subcommands={"build": make_command("build")},
        )
        config = ParserConfiguration(
            ungrouped_positional_strategy=UngroupedPositionalStrategy.COLLECT,
            ungrouped_positional_name="args",
        )

        result = parse_command_line_args(spec, ["--", "unknown"], config=config)

        assert result.subcommand is None
        assert len(result.positionals) == 0

    def test_valid_subcommand_then_unknown_arg_in_subcommand(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        build_cmd = make_command(
            "build", subcommands={"docker": make_command("docker")}
        )
        spec = make_command(name="test", subcommands={"build": build_cmd})

        with pytest.raises(UnknownSubcommandError) as exc_info:
            _ = parse_command_line_args(spec, ["build", "unknown_arg"])

        assert exc_info.value.subcommand == "unknown_arg"

    def test_option_before_unknown_subcommand_still_raises_error(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="verbose")
        spec = make_command(
            name="test",
            options={"verbose": opt},
            subcommands={"build": make_command("build")},
        )

        with pytest.raises(UnknownSubcommandError) as exc_info:
            _ = parse_command_line_args(spec, ["--verbose", "unknown_subcommand"])

        assert exc_info.value.subcommand == "unknown_subcommand"
