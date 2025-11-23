"""Advanced tests for inline values without equals feature."""

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import (
    OptionMissingValueError,
)
from flagrant.specification import (
    Arity,
    CommandSpecification,
    FlagOptionSpecification,
    ValueOptionSpecification,
)


class TestInlineValuesWithoutEquals:
    def test_option_value_format_without_equals(self):
        # Arrange
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

        # Act
        result = parse_command_line_args(spec, ["--output", "file.txt"], config)

        # Assert
        assert result.options["output"] == "file.txt"

    def test_interaction_with_greedy_mode(self):
        # Arrange
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

        # Act - greedy should consume all following args
        result = parse_command_line_args(
            spec, ["--files", "file1.txt", "file2.txt", "file3.txt"], config
        )

        # Assert
        assert result.options["files"] == ("file1.txt", "file2.txt", "file3.txt")

    def test_with_negative_numbers(self):
        # Arrange
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

        # Act
        result = parse_command_line_args(spec, ["--threshold", "-42"], config)

        # Assert
        assert result.options["threshold"] == "-42"

    def test_with_option_like_values(self):
        # Arrange
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

        # Act & Assert - "--value" after "--pattern" is interpreted as a flag,
        # not a value. This causes an error because pattern requires a value
        with pytest.raises(OptionMissingValueError) as exc_info:
            parse_command_line_args(spec, ["--pattern", "--value"], config)

        assert exc_info.value.option == "pattern"

    def test_empty_string_values(self):
        # Arrange
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

        # Act - empty string as value
        result = parse_command_line_args(spec, ["--message", ""], config)

        # Assert
        assert result.options["message"] == ""

    def test_inline_value_stops_at_separator(self):
        # Arrange
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

        # Act - inline value stops at "--" even if greedy
        result = parse_command_line_args(spec, ["--option", "value", "more"], config)

        # Assert - only "value" is captured, "more" is not because arity is 1
        assert result.options["option"] == "value"

        # Test with short option
        result = parse_command_line_args(spec, ["-o", "shortval"], config)
        assert result.options["option"] == "shortval"

    def test_multiple_values_without_equals(self):
        # Arrange
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

        # Act - multiple values for single option
        result = parse_command_line_args(
            spec, ["--names", "alice", "bob", "charlie"], config
        )

        # Assert
        assert result.options["names"] == ("alice", "bob", "charlie")
