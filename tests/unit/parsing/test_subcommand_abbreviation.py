"""Tests for subcommand abbreviation feature."""

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import UnknownSubcommandError
from flagrant.specification import (
    CommandSpecification,
)


class TestSubcommandAbbreviation:
    def test_unambiguous_subcommand_prefix(self):
        # Arrange
        spec = CommandSpecification(
            name="test",
            subcommands={
                "build": CommandSpecification("build"),
                "clean": CommandSpecification("clean"),
                "deploy": CommandSpecification("deploy"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        # Act
        result = parse_command_line_args(spec, ["buil"], config)

        # Assert
        assert result.subcommand is not None
        assert result.subcommand.command == "build"

    def test_ambiguous_subcommand_prefix_error(self):
        # Arrange
        spec = CommandSpecification(
            name="test",
            subcommands={
                "create": CommandSpecification("create"),
                "clean": CommandSpecification("clean"),
                "check": CommandSpecification("check"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        # Act & Assert
        # "c" is ambiguous between create, clean, and check
        with pytest.raises(UnknownSubcommandError) as exc_info:
            parse_command_line_args(spec, ["c"], config)

        assert exc_info.value.subcommand == "c"

        # "cl" is still ambiguous between clean and clone
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
        # Arrange
        spec = CommandSpecification(
            name="test",
            subcommands={
                "run": CommandSpecification("run"),
                "runner": CommandSpecification("runner"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        # Act
        result = parse_command_line_args(spec, ["run"], config)

        # Assert - exact match should take precedence
        assert result.subcommand is not None
        assert result.subcommand.command == "run"

    def test_abbreviation_with_subcommand_aliases(self):
        # Arrange
        # Note: Subcommand aliases are typically handled differently
        # Testing with multiple similar subcommands instead
        spec = CommandSpecification(
            name="test",
            subcommands={
                "remove": CommandSpecification("remove"),
                "remote": CommandSpecification("remote"),
                "revert": CommandSpecification("revert"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        # Act
        result = parse_command_line_args(spec, ["remov"], config)

        # Assert
        assert result.subcommand is not None
        assert result.subcommand.command == "remove"

    def test_nested_subcommand_abbreviation(self):
        # Arrange
        spec = CommandSpecification(
            name="test",
            subcommands={
                "database": CommandSpecification(
                    "database",
                    subcommands={
                        "migrate": CommandSpecification("migrate"),
                        "backup": CommandSpecification("backup"),
                        "restore": CommandSpecification("restore"),
                    }
                ),
            },
        )
        config = ParserConfiguration(allow_abbreviated_subcommands=True)

        # Act - abbreviate both parent and nested subcommand
        result = parse_command_line_args(spec, ["data", "migr"], config)

        # Assert
        assert result.subcommand is not None
        assert result.subcommand.command == "database"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "migrate"

    def test_abbreviation_disabled_in_config(self):
        # Arrange
        spec = CommandSpecification(
            name="test",
            subcommands={
                "build": CommandSpecification("build"),
                "deploy": CommandSpecification("deploy"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_subcommands=False)

        # Act & Assert
        with pytest.raises(UnknownSubcommandError) as exc_info:
            parse_command_line_args(spec, ["buil"], config)

        assert exc_info.value.subcommand == "buil"

    def test_case_sensitivity(self):
        # Arrange
        spec = CommandSpecification(
            name="test",
            subcommands={
                "Build": CommandSpecification("Build"),
                "build": CommandSpecification("build"),
            },
        )

        # Test case-sensitive abbreviation (default)
        config_sensitive = ParserConfiguration(
            allow_abbreviated_subcommands=True,
            case_sensitive_commands=True
        )

        # Act & Assert - case sensitive
        result = parse_command_line_args(spec, ["Bui"], config_sensitive)
        assert result.subcommand is not None
        assert result.subcommand.command == "Build"

        result = parse_command_line_args(spec, ["bui"], config_sensitive)
        assert result.subcommand is not None
        assert result.subcommand.command == "build"

        # Test case-insensitive abbreviation
        config_insensitive = ParserConfiguration(
            allow_abbreviated_subcommands=True,
            case_sensitive_commands=False
        )

        # When case-insensitive, "bui" should match both but parser picks one
        result = parse_command_line_args(spec, ["bui"], config_insensitive)
        assert result.subcommand is not None
        # Parser picks one when case-insensitive (lowercase in this case)
        assert result.subcommand.command in ["Build", "build"]