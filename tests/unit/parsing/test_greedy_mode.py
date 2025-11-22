import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import OptionMissingValueError
from flagrant.specification import (
    Arity,
    CommandSpecification,
    FlagOptionSpecification,
    ValueOptionSpecification,
)


class TestGreedyModeBasic:
    def test_greedy_option_consumes_all_remaining_arguments(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity.at_least_one(),
                    greedy=True,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--files", "file1.txt", "--output", "file2.txt", "-v"]
        )

        assert result.options["files"] == ("file1.txt", "--output", "file2.txt", "-v")

    def test_greedy_option_at_end_of_arguments(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity.at_least_one(),
                    greedy=True,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--files", "single.txt"])

        assert result.options["files"] == ("single.txt",)


class TestGreedyModeWithDelimiter:
    def test_greedy_option_consumes_delimiter_and_trailing_args(self):
        spec = CommandSpecification(
            "test",
            options={
                "args": ValueOptionSpecification(
                    name="args",
                    arity=Arity.at_least_one(),
                    greedy=True,
                    preferred_name="args",
                    long_names=("args",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--args", "a", "b", "c", "--", "positional"]
        )

        assert result.options["args"] == ("a", "b", "c", "--", "positional")


class TestGreedyModeWithSubcommands:
    def test_greedy_option_stops_at_subcommand(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity.at_least_one(),
                    greedy=True,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
            subcommands={"build": CommandSpecification("build")},
        )

        result = parse_command_line_args(
            spec, ["--files", "file.txt", "build", "other.txt"]
        )

        assert result.options["files"] == ("file.txt",)
        assert result.subcommand is not None
        assert result.subcommand.command == "build"


class TestGreedyModeArityEnforcement:
    def test_greedy_option_enforces_minimum_arity(self):
        spec = CommandSpecification(
            "test",
            options={
                "coords": ValueOptionSpecification(
                    name="coords",
                    arity=Arity(2, None),
                    greedy=True,
                    preferred_name="coords",
                    long_names=("coords",),
                    short_names=(),
                )
            },
        )

        with pytest.raises(OptionMissingValueError) as exc_info:
            _ = parse_command_line_args(spec, ["--coords", "10"])

        assert exc_info.value.option == "coords"


class TestGreedyModeInlineValues:
    def test_greedy_option_with_inline_value_consumes_remaining_args(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity.at_least_one(),
                    greedy=True,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--files=first.txt", "second.txt", "third.txt"]
        )

        assert result.options["files"] == ("first.txt", "second.txt", "third.txt")

    def test_greedy_option_inline_value_satisfies_minimum_arity(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity(2, None),
                    greedy=True,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--files=first.txt", "second.txt"]
        )

        assert result.options["files"] == ("first.txt", "second.txt")

    def test_greedy_option_inline_value_insufficient_arity_raises_error(self):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity(3, None),
                    greedy=True,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
        )

        with pytest.raises(OptionMissingValueError) as exc_info:
            _ = parse_command_line_args(spec, ["--files=first.txt", "second.txt"])

        assert exc_info.value.option == "files"


class TestGreedyModeNegativeNumbers:
    def test_greedy_option_consumes_negative_numbers(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity.at_least_one(),
                    greedy=True,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                )
            },
        )
        config = ParserConfiguration(allow_negative_numbers=True)

        result = parse_command_line_args(
            spec, ["--values", "10", "-5", "3.14", "-99.9"], config=config
        )

        assert result.options["values"] == ("10", "-5", "3.14", "-99.9")

    def test_greedy_option_stops_at_option_not_negative_number(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity.at_least_one(),
                    greedy=True,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                ),
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_negative_numbers=True)

        result = parse_command_line_args(
            spec, ["--values", "10", "-5", "--verbose"], config=config
        )

        assert result.options["values"] == ("10", "-5")
        assert result.options["verbose"] is True

    def test_greedy_option_with_negative_number_config_disabled(self):
        spec = CommandSpecification(
            "test",
            options={
                "values": ValueOptionSpecification(
                    name="values",
                    arity=Arity.at_least_one(),
                    greedy=True,
                    preferred_name="values",
                    long_names=("values",),
                    short_names=(),
                )
            },
        )
        config = ParserConfiguration(allow_negative_numbers=False)

        result = parse_command_line_args(
            spec, ["--values", "10", "-5", "3"], config=config
        )

        assert result.options["values"] == ("10", "-5", "3")
