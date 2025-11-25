import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import UnknownSubcommandError
from flagrant.specification import (
    CommandSpecification,
)


class TestSubcommandAbbreviation:
    def test_unambiguous_subcommand_prefix(self):
        spec = CommandSpecification(
            name="test",
            subcommands={
                "build": CommandSpecification("build"),
                "clean": CommandSpecification("clean"),
                "deploy": CommandSpecification("deploy"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        result = parse_command_line_args(spec, ["buil"], config)

        assert result.subcommand is not None
        assert result.subcommand.command == "build"

    def test_ambiguous_subcommand_prefix_error(self):
        spec = CommandSpecification(
            name="test",
            subcommands={
                "create": CommandSpecification("create"),
                "clean": CommandSpecification("clean"),
                "check": CommandSpecification("check"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        with pytest.raises(UnknownSubcommandError) as exc_info:
            parse_command_line_args(spec, ["c"], config)

        assert exc_info.value.subcommand == "c"

        spec_with_clone = CommandSpecification(
            name="test",
            subcommands={
                "clean": CommandSpecification("clean"),
                "clone": CommandSpecification("clone"),
            },
        )
        with pytest.raises(UnknownSubcommandError) as exc_info:
            parse_command_line_args(spec_with_clone, ["cl"], config)

        assert exc_info.value.subcommand == "cl"

    def test_exact_match_precedence(self):
        spec = CommandSpecification(
            name="test",
            subcommands={
                "run": CommandSpecification("run"),
                "runner": CommandSpecification("runner"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        result = parse_command_line_args(spec, ["run"], config)

        assert result.subcommand is not None
        assert result.subcommand.command == "run"

    def test_abbreviation_with_subcommand_aliases(self):
        spec = CommandSpecification(
            name="test",
            subcommands={
                "remove": CommandSpecification("remove"),
                "remote": CommandSpecification("remote"),
                "revert": CommandSpecification("revert"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        result = parse_command_line_args(spec, ["remov"], config)

        assert result.subcommand is not None
        assert result.subcommand.command == "remove"

    def test_nested_subcommand_abbreviation(self):
        spec = CommandSpecification(
            name="test",
            subcommands={
                "database": CommandSpecification(
                    "database",
                    subcommands={
                        "migrate": CommandSpecification("migrate"),
                        "backup": CommandSpecification("backup"),
                        "restore": CommandSpecification("restore"),
                    },
                ),
            },
        )
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        result = parse_command_line_args(spec, ["data", "migr"], config)

        assert result.subcommand is not None
        assert result.subcommand.command == "database"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "migrate"

    def test_abbreviation_disabled_in_config(self):
        spec = CommandSpecification(
            name="test",
            subcommands={
                "build": CommandSpecification("build"),
                "deploy": CommandSpecification("deploy"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_subcommands=False)

        with pytest.raises(UnknownSubcommandError) as exc_info:
            parse_command_line_args(spec, ["buil"], config)

        assert exc_info.value.subcommand == "buil"

    def test_case_sensitivity(self):
        spec = CommandSpecification(
            name="test",
            subcommands={
                "Build": CommandSpecification("Build"),
                "build": CommandSpecification("build"),
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
