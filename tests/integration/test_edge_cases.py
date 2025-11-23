"""Integration tests for edge cases and boundary conditions."""

from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import UnknownOptionError
from flagrant.specification import (
    Arity,
    CommandSpecification,
)

if TYPE_CHECKING:
    from flagrant.specification import (
        CommandSpecificationFactory,
        FlagOptionSpecificationFactory,
        ValueOptionSpecificationFactory,
    )


class TestLongCommandLines:
    def test_command_with_many_options(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        options = {
            f"opt{i}": make_flag_opt(name=f"opt{i}") for i in range(50)
        }
        spec = make_command(name="test", options=options)

        args = [f"--opt{i}" for i in range(50)]
        result = parse_command_line_args(spec, args)

        for i in range(50):
            assert result.options[f"opt{i}"] is True

    def test_command_with_many_positionals(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            positionals={"files": Arity.zero_or_more()},
        )

        files = [f"file{i}.txt" for i in range(100)]
        result = parse_command_line_args(spec, files)

        assert result.positionals["files"] == tuple(files)


class TestDeeplyNestedSubcommands:
    def test_three_level_subcommand_nesting(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        flag = make_flag_opt(name="flag")
        level3 = make_command("level3", options={"flag": flag})
        level2 = make_command("level2", subcommands={"level3": level3})
        level1 = make_command("level1", subcommands={"level2": level2})
        spec = make_command("test", subcommands={"level1": level1})

        result = parse_command_line_args(spec, ["level1", "level2", "level3", "--flag"])

        assert result.subcommand is not None
        assert result.subcommand.command == "level1"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "level2"
        assert result.subcommand.subcommand.subcommand is not None
        assert result.subcommand.subcommand.subcommand.command == "level3"
        assert result.subcommand.subcommand.subcommand.options["flag"] is True


class TestSpecialCharactersInValues:
    def test_values_with_unicode_characters(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        message = make_value_opt(name="message", short_names=("m",))
        spec = make_command(options={"message": message})

        result = parse_command_line_args(spec, ["--message", "Hello 世界 🌍"])

        assert result.options["message"] == "Hello 世界 🌍"

    def test_values_with_special_characters(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            positionals={"pattern": Arity.exactly_one()},
        )

        result = parse_command_line_args(spec, ["*.{py,txt}[0-9]"])

        assert result.positionals["pattern"] == "*.{py,txt}[0-9]"

    def test_values_with_equals_signs(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        env = make_value_opt(name="env", short_names=("e",))
        spec = make_command(options={"env": env})

        result = parse_command_line_args(spec, ["--env", "KEY=VALUE"])

        assert result.options["env"] == "KEY=VALUE"


class TestEmptyValuesAndWhitespace:
    def test_empty_string_as_option_value(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        value = make_value_opt(name="value")
        spec = make_command(options={"value": value})

        result = parse_command_line_args(spec, ["--value", ""])

        assert result.options["value"] == ""

    def test_whitespace_only_value(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            positionals={"text": Arity.exactly_one()},
        )

        result = parse_command_line_args(spec, ["   "])

        assert result.positionals["text"] == "   "


class TestValuesThatLookLikeOptions:
    def test_negative_number_as_positional_value(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            positionals={"number": Arity.exactly_one()},
        )

        result = parse_command_line_args(spec, ["--", "-42"])

        assert result.extra_args == ("-42",)

    def test_option_like_value_after_separator(
        self,
        make_command: "CommandSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            positionals={"args": Arity.zero_or_more()},
        )

        result = parse_command_line_args(spec, ["--", "--help", "-v", "--version"])

        assert result.extra_args == ("--help", "-v", "--version")


class TestKnownIssues:
    def test_prefix_match_on_flag_raises_correct_exception(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        verbose = make_flag_opt(name="verbose")
        value = make_value_opt(name="value")
        spec = make_command(options={"verbose": verbose, "value": value})
        config = ParserConfiguration(allow_abbreviated_options=True)

        with pytest.raises(UnknownOptionError):
            parse_command_line_args(spec, ["--v"], config=config)

    def test_separator_stops_value_collection_in_real_command(
        self, git_like_spec: CommandSpecification
    ):
        spec = git_like_spec

        result = parse_command_line_args(
            spec, ["commit", "-m", "message", "--", "extra.txt"]
        )

        assert result.subcommand is not None
        assert result.subcommand.options["message"] == "message"
        assert result.subcommand.extra_args == ("extra.txt",)

    @pytest.mark.xfail(
        reason=(
            "BUG: StopIteration raised when range arity option is followed "
            "by positionals"
        )
    )
    def test_range_arity_option_followed_by_positionals(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        files = make_value_opt(
            name="files",
            arity=Arity.exact(2),
            short_names=("f",),
        )
        spec = make_command(
            options={"files": files},
            positionals={"target": Arity.exactly_one()},
        )

        result = parse_command_line_args(
            spec, ["--files", "a.txt", "b.txt", "target_dir"]
        )

        assert result.options["files"] == ("a.txt", "b.txt")
        assert result.positionals["target"] == ("target_dir",)
