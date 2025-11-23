from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import OptionMissingValueError
from flagrant.specification import (
    Arity,
)

if TYPE_CHECKING:
    from flagrant.specification import (
        CommandSpecificationFactory,
        FlagOptionSpecificationFactory,
        ValueOptionSpecificationFactory,
    )


class TestInlineValuesWithoutEquals:
    def test_option_value_format_without_equals(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="output", short_names=("o",))
        spec = make_command(options={"output": opt})
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--output", "file.txt"], config)

        assert result.options["output"] == "file.txt"

    def test_interaction_with_greedy_mode(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="files", arity=Arity.at_least_one(), greedy=True)
        spec = make_command(options={"files": opt})
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(
            spec, ["--files", "file1.txt", "file2.txt", "file3.txt"], config
        )

        assert result.options["files"] == ("file1.txt", "file2.txt", "file3.txt")

    def test_with_negative_numbers(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="threshold", short_names=("t",))
        spec = make_command(options={"threshold": opt})
        config = ParserConfiguration(
            allow_inline_values_without_equals=True, allow_negative_numbers=True
        )

        result = parse_command_line_args(spec, ["--threshold", "-42"], config)

        assert result.options["threshold"] == "-42"

    def test_with_option_like_values(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        pat_opt = make_value_opt(name="pattern")
        val_opt = make_flag_opt(name="value")
        spec = make_command(options={"pattern": pat_opt, "value": val_opt})
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        with pytest.raises(OptionMissingValueError) as exc_info:
            parse_command_line_args(spec, ["--pattern", "--value"], config)

        assert exc_info.value.option == "pattern"

    def test_empty_string_values(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="message", short_names=("m",))
        spec = make_command(options={"message": opt})
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--message", ""], config)

        assert result.options["message"] == ""

    def test_inline_value_stops_at_separator(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="option", short_names=("o",))
        spec = make_command(options={"option": opt})
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--option", "value", "more"], config)

        assert result.options["option"] == "value"

        result = parse_command_line_args(spec, ["-o", "shortval"], config)
        assert result.options["option"] == "shortval"

    def test_multiple_values_without_equals(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="names", arity=Arity.exact(3))
        spec = make_command(options={"names": opt})
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(
            spec, ["--names", "alice", "bob", "charlie"], config
        )

        assert result.options["names"] == ("alice", "bob", "charlie")


class TestShortOptionInlineWithoutEquals:
    def test_short_option_inline_value_without_equals(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="output", long_names=(), short_names=("o",)
        )
        spec = make_command(options={"output": opt})
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["-ovalue"], config)

        assert result.options["output"] == "value"

    def test_clustered_short_options_with_inline_value_without_equals(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        all_opt = make_flag_opt(
            name="all", long_names=(), short_names=("a",)
        )
        build = make_flag_opt(
            name="build", long_names=(), short_names=("b",)
        )
        config = make_value_opt(
            name="config", long_names=(), short_names=("c",)
        )
        spec = make_command(options={"all": all_opt, "build": build, "config": config})
        config_parser = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["-abcvalue"], config_parser)

        assert result.options["all"] is True
        assert result.options["build"] is True
        assert result.options["config"] == "value"

    def test_short_option_inline_value_starting_with_hyphen(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="value",
            long_names=(),
            short_names=("v",),
            allow_negative_numbers=True,
        )
        spec = make_command(options={"value": opt})
        config = ParserConfiguration(
            allow_inline_values_without_equals=True,
            allow_negative_numbers=True,
        )

        result = parse_command_line_args(spec, ["-v", "-42"], config)

        assert result.options["value"] == "-42"

    def test_short_option_with_numeric_inline_value(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="level", long_names=(), short_names=("l",)
        )
        spec = make_command(options={"level": opt})
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["-l42"], config)

        assert result.options["level"] == "42"
