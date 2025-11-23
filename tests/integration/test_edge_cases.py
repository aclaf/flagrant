"""Integration tests for edge cases and boundary conditions."""

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import UnknownOptionError
from flagrant.specification import (
    Arity,
    CommandSpecification,
    FlagOptionSpecification,
    ValueOptionSpecification,
)


class TestLongCommandLines:
    def test_command_with_many_options(self):
        spec = CommandSpecification(
            "test",
            options={
                f"opt{i}": FlagOptionSpecification(
                    name=f"opt{i}",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name=f"opt{i}",
                    long_names=(f"opt{i}",),
                    short_names=(),
                )
                for i in range(50)
            },
        )

        args = [f"--opt{i}" for i in range(50)]
        result = parse_command_line_args(spec, args)

        for i in range(50):
            assert result.options[f"opt{i}"] is True

    def test_command_with_many_positionals(self):
        spec = CommandSpecification(
            "test",
            positionals={
                "files": Arity.zero_or_more(),
            },
        )

        files = [f"file{i}.txt" for i in range(100)]
        result = parse_command_line_args(spec, files)

        assert result.positionals["files"] == tuple(files)


class TestDeeplyNestedSubcommands:
    def test_three_level_subcommand_nesting(self):
        spec = CommandSpecification(
            "test",
            subcommands={
                "level1": CommandSpecification(
                    "level1",
                    subcommands={
                        "level2": CommandSpecification(
                            "level2",
                            subcommands={
                                "level3": CommandSpecification(
                                    "level3",
                                    options={
                                        "flag": FlagOptionSpecification(
                                            name="flag",
                                            arity=Arity.none(),
                                            greedy=False,
                                            preferred_name="flag",
                                            long_names=("flag",),
                                            short_names=(),
                                        ),
                                    },
                                ),
                            },
                        ),
                    },
                ),
            },
        )

        result = parse_command_line_args(spec, ["level1", "level2", "level3", "--flag"])

        assert result.subcommand is not None
        assert result.subcommand.command == "level1"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "level2"
        assert result.subcommand.subcommand.subcommand is not None
        assert result.subcommand.subcommand.subcommand.command == "level3"
        assert result.subcommand.subcommand.subcommand.options["flag"] is True


class TestSpecialCharactersInValues:
    def test_values_with_unicode_characters(self):
        spec = CommandSpecification(
            "test",
            options={
                "message": ValueOptionSpecification(
                    name="message",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="message",
                    long_names=("message",),
                    short_names=("m",),
                ),
            },
        )

        result = parse_command_line_args(spec, ["--message", "Hello 世界 🌍"])

        assert result.options["message"] == "Hello 世界 🌍"

    def test_values_with_special_characters(self):
        spec = CommandSpecification(
            "test",
            positionals={
                "pattern": Arity.exactly_one(),
            },
        )

        result = parse_command_line_args(spec, ["*.{py,txt}[0-9]"])

        assert result.positionals["pattern"] == "*.{py,txt}[0-9]"

    def test_values_with_equals_signs(self):
        spec = CommandSpecification(
            "test",
            options={
                "env": ValueOptionSpecification(
                    name="env",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="env",
                    long_names=("env",),
                    short_names=("e",),
                ),
            },
        )

        result = parse_command_line_args(spec, ["--env", "KEY=VALUE"])

        assert result.options["env"] == "KEY=VALUE"


class TestEmptyValuesAndWhitespace:
    def test_empty_string_as_option_value(self):
        spec = CommandSpecification(
            "test",
            options={
                "value": ValueOptionSpecification(
                    name="value",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="value",
                    long_names=("value",),
                    short_names=(),
                ),
            },
        )

        result = parse_command_line_args(spec, ["--value", ""])

        assert result.options["value"] == ""

    def test_whitespace_only_value(self):
        spec = CommandSpecification(
            "test",
            positionals={
                "text": Arity.exactly_one(),
            },
        )

        result = parse_command_line_args(spec, ["   "])

        assert result.positionals["text"] == "   "


class TestValuesThatLookLikeOptions:
    def test_negative_number_as_positional_value(self):
        spec = CommandSpecification(
            "test",
            positionals={
                "number": Arity.exactly_one(),
            },
        )

        result = parse_command_line_args(spec, ["--", "-42"])

        assert result.extra_args == ("-42",)

    def test_option_like_value_after_separator(self):
        spec = CommandSpecification(
            "test",
            positionals={
                "args": Arity.zero_or_more(),
            },
        )

        result = parse_command_line_args(spec, ["--", "--help", "-v", "--version"])

        assert result.extra_args == ("--help", "-v", "--version")


class TestKnownIssues:
    def test_prefix_match_on_flag_raises_correct_exception(self):
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
                "value": ValueOptionSpecification(
                    name="value",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="value",
                    long_names=("value",),
                    short_names=(),
                ),
            },
        )
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
    def test_range_arity_option_followed_by_positionals(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity.exact(2),
                    greedy=False,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=("f",),
                ),
            },
            positionals={
                "target": Arity.exactly_one(),
            },
        )

        result = parse_command_line_args(
            spec, ["--files", "a.txt", "b.txt", "target_dir"]
        )

        assert result.options["files"] == ("a.txt", "b.txt")
        assert result.positionals["target"] == ("target_dir",)
