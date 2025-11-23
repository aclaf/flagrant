import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import UnknownOptionError
from flagrant.specification import (
    Arity,
    CommandSpecification,
    ValueOptionSpecification,
)


class TestAmbiguousPrefixMatching:
    def test_longer_option_inline_value_matches_shorter_option_prefix(self):
        spec = CommandSpecification(
            name="test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=("output",),
                    short_names=(),
                ),
                "outputdir": ValueOptionSpecification(
                    name="outputdir",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="outputdir",
                    long_names=("outputdir",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--outputfile.txt"], config)

        assert result.options["output"] == "file.txt"
        assert "outputdir" not in result.options

    def test_exact_option_match_takes_precedence_over_prefix_with_inline_value(self):
        spec = CommandSpecification(
            name="test",
            options={
                "out": ValueOptionSpecification(
                    name="out",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="out",
                    long_names=("out",),
                    short_names=(),
                ),
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=("output",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--output", "value"], config)

        assert result.options["output"] == "value"
        assert "out" not in result.options

    def test_multiple_prefix_matches_uses_first_match(self):
        spec = CommandSpecification(
            name="test",
            options={
                "verbose": ValueOptionSpecification(
                    name="verbose",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=(),
                ),
                "version": ValueOptionSpecification(
                    name="version",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="version",
                    long_names=("version",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--verbose2"], config)

        assert result.options["verbose"] == "2"

    def test_inline_value_without_equals_disabled_raises_unknown_option(self):
        spec = CommandSpecification(
            name="test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=("output",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=False)

        with pytest.raises(UnknownOptionError) as exc_info:
            parse_command_line_args(spec, ["--outputfile.txt"], config)

        assert exc_info.value.option == "outputfile.txt"

    def test_nested_prefix_matching_with_three_options(self):
        spec = CommandSpecification(
            name="test",
            options={
                "a": ValueOptionSpecification(
                    name="a",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="a",
                    long_names=("a",),
                    short_names=(),
                ),
                "ab": ValueOptionSpecification(
                    name="ab",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="ab",
                    long_names=("ab",),
                    short_names=(),
                ),
                "abc": ValueOptionSpecification(
                    name="abc",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="abc",
                    long_names=("abc",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--abcvalue"], config)

        assert result.options["a"] == "bcvalue"
        assert "ab" not in result.options
        assert "abc" not in result.options
