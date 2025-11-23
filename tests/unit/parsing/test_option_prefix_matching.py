from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import UnknownOptionError

if TYPE_CHECKING:
    from flagrant.specification import (
        CommandSpecificationFactory,
        ValueOptionSpecificationFactory,
    )


class TestAmbiguousPrefixMatching:
    def test_longer_option_inline_value_matches_shorter_option_prefix(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            options={
                "output": make_value_opt(name="output"),
                "outputdir": make_value_opt(name="outputdir"),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--outputfile.txt"], config)

        assert result.options["output"] == "file.txt"
        assert "outputdir" not in result.options

    def test_exact_option_match_takes_precedence_over_prefix_with_inline_value(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            options={
                "out": make_value_opt(name="out"),
                "output": make_value_opt(name="output"),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--output", "value"], config)

        assert result.options["output"] == "value"
        assert "out" not in result.options

    def test_multiple_prefix_matches_uses_first_match(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            options={
                "verbose": make_value_opt(name="verbose"),
                "version": make_value_opt(name="version"),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--verbose2"], config)

        assert result.options["verbose"] == "2"

    def test_inline_value_without_equals_disabled_raises_unknown_option(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            options={
                "output": make_value_opt(name="output"),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=False)

        with pytest.raises(UnknownOptionError) as exc_info:
            parse_command_line_args(spec, ["--outputfile.txt"], config)

        assert exc_info.value.option == "outputfile.txt"

    def test_nested_prefix_matching_with_three_options(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            options={
                "a": make_value_opt(name="a", long_names=("a",)),
                "ab": make_value_opt(name="ab", long_names=("ab",)),
                "abc": make_value_opt(name="abc", long_names=("abc",)),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--abcvalue"], config)

        assert result.options["a"] == "bcvalue"
        assert "ab" not in result.options
        assert "abc" not in result.options
