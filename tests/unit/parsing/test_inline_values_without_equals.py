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


class TestInlineValuesWithoutEquals:
    def test_option_value_format_without_equals(self):
        spec = CommandSpecification(
            name="test",
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
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--output", "file.txt"], config)

        assert result.options["output"] == "file.txt"

    def test_interaction_with_greedy_mode(self):
        spec = CommandSpecification(
            name="test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity.at_least_one(),
                    greedy=True,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(
            spec, ["--files", "file1.txt", "file2.txt", "file3.txt"], config
        )

        assert result.options["files"] == ("file1.txt", "file2.txt", "file3.txt")

    def test_with_negative_numbers(self):
        spec = CommandSpecification(
            name="test",
            options={
                "threshold": ValueOptionSpecification(
                    name="threshold",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="threshold",
                    long_names=("threshold",),
                    short_names=("t",),
                ),
            },
        )
        config = ParserConfiguration(
            allow_inline_values_without_equals=True, allow_negative_numbers=True
        )

        result = parse_command_line_args(spec, ["--threshold", "-42"], config)

        assert result.options["threshold"] == "-42"

    def test_with_option_like_values(self):
        spec = CommandSpecification(
            name="test",
            options={
                "pattern": ValueOptionSpecification(
                    name="pattern",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="pattern",
                    long_names=("pattern",),
                    short_names=(),
                ),
                "value": FlagOptionSpecification(
                    name="value",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="value",
                    long_names=("value",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        with pytest.raises(OptionMissingValueError) as exc_info:
            parse_command_line_args(spec, ["--pattern", "--value"], config)

        assert exc_info.value.option == "pattern"

    def test_empty_string_values(self):
        spec = CommandSpecification(
            name="test",
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
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--message", ""], config)

        assert result.options["message"] == ""

    def test_inline_value_stops_at_separator(self):
        spec = CommandSpecification(
            name="test",
            options={
                "option": ValueOptionSpecification(
                    name="option",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="option",
                    long_names=("option",),
                    short_names=("o",),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--option", "value", "more"], config)

        assert result.options["option"] == "value"

        result = parse_command_line_args(spec, ["-o", "shortval"], config)
        assert result.options["option"] == "shortval"

    def test_multiple_values_without_equals(self):
        spec = CommandSpecification(
            name="test",
            options={
                "names": ValueOptionSpecification(
                    name="names",
                    arity=Arity.exact(3),
                    greedy=False,
                    preferred_name="names",
                    long_names=("names",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(
            spec, ["--names", "alice", "bob", "charlie"], config
        )

        assert result.options["names"] == ("alice", "bob", "charlie")


class TestShortOptionInlineWithoutEquals:
    def test_short_option_inline_value_without_equals(self):
        spec = CommandSpecification(
            name="test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="o",
                    long_names=(),
                    short_names=("o",),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["-ovalue"], config)

        assert result.options["output"] == "value"

    def test_clustered_short_options_with_inline_value_without_equals(self):
        spec = CommandSpecification(
            name="test",
            options={
                "all": FlagOptionSpecification(
                    name="all",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="a",
                    long_names=(),
                    short_names=("a",),
                ),
                "build": FlagOptionSpecification(
                    name="build",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="b",
                    long_names=(),
                    short_names=("b",),
                ),
                "config": ValueOptionSpecification(
                    name="config",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="c",
                    long_names=(),
                    short_names=("c",),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["-abcvalue"], config)

        assert result.options["all"] is True
        assert result.options["build"] is True
        assert result.options["config"] == "value"

    def test_short_option_inline_value_starting_with_hyphen(self):
        spec = CommandSpecification(
            name="test",
            options={
                "value": ValueOptionSpecification(
                    name="value",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="v",
                    long_names=(),
                    short_names=("v",),
                    allow_negative_numbers=True,
                ),
            },
        )
        config = ParserConfiguration(
            allow_inline_values_without_equals=True,
            allow_negative_numbers=True,
        )

        result = parse_command_line_args(spec, ["-v", "-42"], config)

        assert result.options["value"] == "-42"

    def test_short_option_with_numeric_inline_value(self):
        spec = CommandSpecification(
            name="test",
            options={
                "level": ValueOptionSpecification(
                    name="level",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="l",
                    long_names=(),
                    short_names=("l",),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["-l42"], config)

        assert result.options["level"] == "42"
