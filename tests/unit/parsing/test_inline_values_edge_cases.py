import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import (
    AmbiguousOptionError,
    OptionMissingValueError,
    OptionValueNotAllowedError,
    UnknownOptionError,
)
from flagrant.specification import (
    Arity,
    CommandSpecification,
    FlagOptionSpecification,
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


class TestSpecialCharactersInInlineValues:
    def test_inline_value_containing_equals_sign(self):
        spec = CommandSpecification(
            name="test",
            options={
                "config": ValueOptionSpecification(
                    name="config",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="config",
                    long_names=("config",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--config", "key=value"], config)

        assert result.options["config"] == "key=value"

    def test_inline_value_containing_hyphens(self):
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
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--pattern", "foo-bar-baz"], config)

        assert result.options["pattern"] == "foo-bar-baz"

    def test_inline_value_containing_dots(self):
        spec = CommandSpecification(
            name="test",
            options={
                "file": ValueOptionSpecification(
                    name="file",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="file",
                    long_names=("file",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--file", "my.file.txt"], config)

        assert result.options["file"] == "my.file.txt"

    def test_inline_value_with_prefix_matching_containing_dots(self):
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
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--outputfile.tar.gz"], config)

        assert result.options["output"] == "file.tar.gz"

    def test_empty_inline_value_with_equals(self):
        spec = CommandSpecification(
            name="test",
            options={
                "message": ValueOptionSpecification(
                    name="message",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="message",
                    long_names=("message",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--message="], config)

        assert result.options["message"] == ""

    def test_inline_value_without_equals_versus_with_equals(self):
        spec = CommandSpecification(
            name="test",
            options={
                "option": ValueOptionSpecification(
                    name="option",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="option",
                    long_names=("option",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result_with_equals = parse_command_line_args(spec, ["--option="], config)
        assert result_with_equals.options["option"] == ""

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--option"], config)

    def test_value_that_looks_like_option_with_equals(self):
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
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--pattern=--value"], config)

        assert result.options["pattern"] == "--value"

    def test_value_containing_multiple_special_characters(self):
        spec = CommandSpecification(
            name="test",
            options={
                "url": ValueOptionSpecification(
                    name="url",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="url",
                    long_names=("url",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(
            spec, ["--url", "https://example.com/path?key=value&foo=bar"], config
        )

        assert result.options["url"] == "https://example.com/path?key=value&foo=bar"

    def test_inline_value_with_whitespace(self):
        spec = CommandSpecification(
            name="test",
            options={
                "message": ValueOptionSpecification(
                    name="message",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="message",
                    long_names=("message",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--message", "hello world"], config)

        assert result.options["message"] == "hello world"


class TestInlineValuesWithDifferentArities:
    def test_inline_value_with_unbounded_arity(self):
        spec = CommandSpecification(
            name="test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity.at_least_one(),
                    greedy=False,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(
            spec, ["--files=first.txt", "second.txt", "third.txt"], config
        )

        assert result.options["files"] == ("first.txt", "second.txt", "third.txt")

    def test_inline_value_with_exact_arity_greater_than_one(self):
        spec = CommandSpecification(
            name="test",
            options={
                "coords": ValueOptionSpecification(
                    name="coords",
                    arity=Arity.exact(3),
                    greedy=False,
                    preferred_name="coords",
                    long_names=("coords",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--coords=10", "20", "30"], config)

        assert result.options["coords"] == ("10", "20", "30")

    def test_inline_value_with_exact_arity_insufficient_values_raises_error(self):
        spec = CommandSpecification(
            name="test",
            options={
                "coords": ValueOptionSpecification(
                    name="coords",
                    arity=Arity.exact(3),
                    greedy=False,
                    preferred_name="coords",
                    long_names=("coords",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        with pytest.raises(OptionMissingValueError) as exc_info:
            parse_command_line_args(spec, ["--coords=10", "20"], config)

        assert exc_info.value.option == "coords"
        assert exc_info.value.required.min == 3

    def test_inline_value_with_optional_arity(self):
        spec = CommandSpecification(
            name="test",
            options={
                "level": ValueOptionSpecification(
                    name="level",
                    arity=Arity.at_most_one(),
                    greedy=False,
                    preferred_name="level",
                    long_names=("level",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--level=3"], config)

        assert result.options["level"] == "3"

    def test_inline_value_with_range_arity(self):
        spec = CommandSpecification(
            name="test",
            options={
                "items": ValueOptionSpecification(
                    name="items",
                    arity=Arity(2, 4),
                    greedy=False,
                    preferred_name="items",
                    long_names=("items",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--items=a", "b", "c"], config)

        assert result.options["items"] == ("a", "b", "c")

    def test_prefix_match_inline_value_with_unbounded_arity(self):
        spec = CommandSpecification(
            name="test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.at_least_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=("output",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(
            spec, ["--outputfirst.txt", "second.txt"], config
        )

        assert result.options["output"] == ("first.txt", "second.txt")


class TestErrorCasesAndValidation:
    def test_flag_option_with_inline_value_without_equals_raises_error(self):
        spec = CommandSpecification(
            name="test",
            options={
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
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        with pytest.raises(OptionValueNotAllowedError) as exc_info:
            parse_command_line_args(spec, ["--verbose=true"], config)

        assert exc_info.value.option == "verbose"
        assert exc_info.value.received == "true"

    @pytest.mark.xfail(
        reason=(
            "Parser matches flag prefix and raises "
            "OptionValueNotAllowedError instead of UnknownOptionError"
        ),
        strict=True,
    )
    def test_prefix_match_on_flag_option_raises_unknown_option(self):
        spec = CommandSpecification(
            name="test",
            options={
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
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        with pytest.raises(UnknownOptionError) as exc_info:
            parse_command_line_args(spec, ["--verbosesomething"], config)

        assert exc_info.value.option == "verbosesomething"

    def test_nonexistent_option_prefix_raises_unknown_option(self):
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
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        with pytest.raises(UnknownOptionError) as exc_info:
            parse_command_line_args(spec, ["--inputfile.txt"], config)

        assert exc_info.value.option == "inputfile.txt"

    def test_inline_value_without_required_following_values_raises_error(self):
        spec = CommandSpecification(
            name="test",
            options={
                "point": ValueOptionSpecification(
                    name="point",
                    arity=Arity.exact(2),
                    greedy=False,
                    preferred_name="point",
                    long_names=("point",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        with pytest.raises(OptionMissingValueError) as exc_info:
            parse_command_line_args(spec, ["--point=10"], config)

        assert exc_info.value.option == "point"

    def test_option_missing_value_with_prefix_match(self):
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

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--output"], config)


class TestInteractionWithAbbreviation:
    def test_inline_value_without_equals_with_abbreviation_enabled(self):
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
                "optimize": ValueOptionSpecification(
                    name="optimize",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="optimize",
                    long_names=("optimize",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(
            allow_inline_values_without_equals=True,
            allow_abbreviated_options=True,
        )

        result = parse_command_line_args(spec, ["--outputfile.txt"], config)

        assert result.options["output"] == "file.txt"

    def test_abbreviation_takes_precedence_over_inline_prefix_match(self):
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
        config = ParserConfiguration(
            allow_inline_values_without_equals=True,
            allow_abbreviated_options=True,
        )

        result = parse_command_line_args(spec, ["--out", "value"], config)

        assert result.options["out"] == "value"
        assert "output" not in result.options

    def test_ambiguous_abbreviation_with_inline_values(self):
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
        config = ParserConfiguration(
            allow_inline_values_without_equals=True,
            allow_abbreviated_options=True,
        )

        with pytest.raises(AmbiguousOptionError) as exc_info:
            parse_command_line_args(spec, ["--ver", "value"], config)

        assert exc_info.value.option == "ver"
        assert "verbose" in exc_info.value.matched
        assert "version" in exc_info.value.matched


class TestSecurityConsiderations:
    def test_path_traversal_in_inline_value(self):
        spec = CommandSpecification(
            name="test",
            options={
                "file": ValueOptionSpecification(
                    name="file",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="file",
                    long_names=("file",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--file", "../../etc/passwd"], config)

        assert result.options["file"] == "../../etc/passwd"

    def test_null_byte_in_inline_value(self):
        spec = CommandSpecification(
            name="test",
            options={
                "data": ValueOptionSpecification(
                    name="data",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="data",
                    long_names=("data",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--data", "hello\x00world"], config)

        assert result.options["data"] == "hello\x00world"

    def test_shell_metacharacters_in_inline_value(self):
        spec = CommandSpecification(
            name="test",
            options={
                "command": ValueOptionSpecification(
                    name="command",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="command",
                    long_names=("command",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(
            spec, ["--command", "echo hello; rm -rf /"], config
        )

        assert result.options["command"] == "echo hello; rm -rf /"

    def test_unicode_in_inline_value(self):
        spec = CommandSpecification(
            name="test",
            options={
                "name": ValueOptionSpecification(
                    name="name",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="name",
                    long_names=("name",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        result = parse_command_line_args(spec, ["--name", "hello🌍world"], config)

        assert result.options["name"] == "hello🌍world"

    def test_very_long_inline_value(self):
        spec = CommandSpecification(
            name="test",
            options={
                "data": ValueOptionSpecification(
                    name="data",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="data",
                    long_names=("data",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        long_value = "A" * 10000
        result = parse_command_line_args(spec, ["--data", long_value], config)

        data_value = result.options["data"]
        assert data_value == long_value
        assert isinstance(data_value, str)
        assert len(data_value) == 10000
