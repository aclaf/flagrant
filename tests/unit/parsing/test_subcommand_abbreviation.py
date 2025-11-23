from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import UnknownSubcommandError

if TYPE_CHECKING:
    from flagrant.specification import CommandSpecificationFactory


class TestSubcommandAbbreviation:
    @pytest.mark.parametrize(
        ("subcommands", "input_arg", "expected_command"),
        [
            (
                {"build": {}, "clean": {}, "deploy": {}},
                "buil",
                "build",
            ),
            (
                {"run": {}, "runner": {}},
                "run",
                "run",
            ),
            (
                {"remove": {}, "remote": {}, "revert": {}},
                "remov",
                "remove",
            ),
        ],
    )
    def test_subcommand_abbreviation_success(
        self,
        make_command: "CommandSpecificationFactory",
        subcommands: dict[str, dict[str, object]],
        input_arg: str,
        expected_command: str,
    ):
        sub_cmds = {name: make_command(name) for name in subcommands}
        spec = make_command(name="test", subcommands=sub_cmds)
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        result = parse_command_line_args(spec, [input_arg], config)

        assert result.subcommand is not None
        assert result.subcommand.command == expected_command

    @pytest.mark.parametrize(
        ("subcommands", "input_arg", "expected_error_match"),
        [
            (
                {"create": {}, "clean": {}, "check": {}},
                "c",
                "c",
            ),
            (
                {"clean": {}, "clone": {}},
                "cl",
                "cl",
            ),
        ],
    )
    def test_ambiguous_subcommand_prefix_error(
        self,
        make_command: "CommandSpecificationFactory",
        subcommands: dict[str, dict[str, object]],
        input_arg: str,
        expected_error_match: str,
    ):
        sub_cmds = {name: make_command(name) for name in subcommands}
        spec = make_command(name="test", subcommands=sub_cmds)
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        with pytest.raises(UnknownSubcommandError) as exc_info:
            parse_command_line_args(spec, [input_arg], config)

        assert exc_info.value.subcommand == expected_error_match

    def test_nested_subcommand_abbreviation(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        db_cmd = make_command(
            "database",
            subcommands={
                "migrate": make_command("migrate"),
                "backup": make_command("backup"),
                "restore": make_command("restore"),
            },
        )
        spec = make_command(name="test", subcommands={"database": db_cmd})
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        result = parse_command_line_args(spec, ["data", "migr"], config)

        assert result.subcommand is not None
        assert result.subcommand.command == "database"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "migrate"

    def test_abbreviation_disabled_in_config(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            subcommands={
                "build": make_command("build"),
                "deploy": make_command("deploy"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_subcommands=False)

        with pytest.raises(UnknownSubcommandError) as exc_info:
            parse_command_line_args(spec, ["buil"], config)

        assert exc_info.value.subcommand == "buil"

    def test_case_sensitivity(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            subcommands={
                "Build": make_command("Build"),
                "build": make_command("build"),
            },
        )

        config_sensitive = ParserConfiguration(
            allow_abbreviated_subcommands=True, case_sensitive_commands=True
        )

        result = parse_command_line_args(spec, ["Bui"], config_sensitive)
        assert result.subcommand is not None
        assert result.subcommand.command == "Build"

        result = parse_command_line_args(spec, ["bui"], config_sensitive)
        assert result.subcommand is not None
        assert result.subcommand.command == "build"

        config_insensitive = ParserConfiguration(
            allow_abbreviated_subcommands=True, case_sensitive_commands=False
        )

        result = parse_command_line_args(spec, ["bui"], config_insensitive)
        assert result.subcommand is not None
        assert result.subcommand.command in ["Build", "build"]
