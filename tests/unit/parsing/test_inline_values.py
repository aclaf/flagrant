from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import (
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

if TYPE_CHECKING:
    from flagrant.specification import (
        CommandSpecificationFactory,
        FlagOptionSpecificationFactory,
        ValueOptionSpecificationFactory,
    )


class TestLongOptionEqualsBasic:
    def test_long_option_with_equals_assigns_single_value(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="output")
        spec = make_command(options={"output": opt})

        result = parse_command_line_args(spec, ["--output=file.txt"])

        assert result.options["output"] == "file.txt"

    def test_long_option_equals_splits_on_first_equals_only(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="config")
        spec = make_command(options={"config": opt})

        result = parse_command_line_args(spec, ["--config=key=value"])

        assert result.options["config"] == "key=value"

    def test_long_option_equals_with_multiple_equals_preserves_all_after_first(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="equation")
        spec = make_command(options={"equation": opt})

        result = parse_command_line_args(spec, ["--equation=x=y+z"])

        assert result.options["equation"] == "x=y+z"

    def test_long_option_equals_with_empty_value_assigns_empty_string(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="output")
        spec = make_command(options={"output": opt})

        result = parse_command_line_args(spec, ["--output="])

        assert result.options["output"] == ""

    def test_long_option_equals_satisfies_arity_of_one(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="value")
        spec = make_command(options={"value": opt})

        result = parse_command_line_args(spec, ["--value=data"])

        assert result.options["value"] == "data"


class TestLongOptionEqualsArityValidation:
    def test_long_option_equals_with_arity_two_raises_insufficient_values_error(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="coords", arity=Arity.exact(2))
        spec = make_command(options={"coords": opt})

        with pytest.raises(OptionMissingValueError) as exc_info:
            _ = parse_command_line_args(spec, ["--coords=10"])

        assert exc_info.value.option == "coords"
        assert exc_info.value.required == Arity.exact(2)

    def test_long_option_equals_with_arity_zero_or_one_succeeds(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="optional", arity=Arity.at_most_one())
        spec = make_command(options={"optional": opt})

        result = parse_command_line_args(spec, ["--optional=value"])

        assert result.options["optional"] == "value"

    def test_long_option_equals_with_unbounded_arity_also_consumes_following_args(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="files", arity=Arity.at_least_one())
        spec = make_command(options={"files": opt})

        result = parse_command_line_args(spec, ["--files=first.txt", "second.txt"])

        assert result.options["files"] == ("first.txt", "second.txt")


class TestShortOptionEqualsBasic:
    def test_short_option_with_equals_assigns_value(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="output", long_names=(), short_names=("o",)
        )
        spec = make_command(options={"output": opt})

        result = parse_command_line_args(spec, ["-o=file.txt"])

        assert result.options["output"] == "file.txt"

    def test_short_option_equals_splits_on_first_equals(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="config", long_names=(), short_names=("c",)
        )
        spec = make_command(options={"config": opt})

        result = parse_command_line_args(spec, ["-c=key=value"])

        assert result.options["config"] == "key=value"

    def test_short_option_equals_with_empty_value_assigns_empty_string(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="output", long_names=(), short_names=("o",)
        )
        spec = make_command(options={"output": opt})

        result = parse_command_line_args(spec, ["-o="])

        assert result.options["output"] == ""


class TestShortOptionConcatenatedBasic:
    def test_short_option_concatenated_value_without_separator(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="output", long_names=(), short_names=("o",)
        )
        spec = make_command(options={"output": opt})

        result = parse_command_line_args(spec, ["-ofile.txt"])

        assert result.options["output"] == "file.txt"

    def test_short_option_concatenated_value_is_remainder_after_option_char(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="name", long_names=(), short_names=("n",)
        )
        spec = make_command(options={"name": opt})

        result = parse_command_line_args(spec, ["-nvalue123"])

        assert result.options["name"] == "value123"

    def test_short_option_concatenated_with_single_char_value(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="mode", long_names=(), short_names=("m",)
        )
        spec = make_command(options={"mode": opt})

        result = parse_command_line_args(spec, ["-ma"])

        assert result.options["mode"] == "a"


class TestClusteringWithInlineValues:
    def test_clustered_options_with_equals_assigns_to_last_option(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        verbose = make_flag_opt(
            name="verbose", long_names=(), short_names=("v",)
        )
        quiet = make_flag_opt(
            name="quiet", long_names=(), short_names=("q",)
        )
        output = make_value_opt(
            name="output", long_names=(), short_names=("o",)
        )
        spec = make_command(
            options={"verbose": verbose, "quiet": quiet, "output": output}
        )

        result = parse_command_line_args(spec, ["-vqo=file.txt"])

        assert result.options["verbose"] is True
        assert result.options["quiet"] is True
        assert result.options["output"] == "file.txt"

    def test_clustered_options_with_concatenated_value_to_last_option(
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

        result = parse_command_line_args(spec, ["-abcvalue"])

        assert result.options["all"] is True
        assert result.options["build"] is True
        assert result.options["config"] == "value"

    def test_clustered_equals_assigns_value_even_if_equals_char_defined_as_option(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        all_opt = make_flag_opt(
            name="all", long_names=(), short_names=("a",)
        )
        build = make_value_opt(
            name="build", long_names=(), short_names=("b",)
        )
        config = make_flag_opt(
            name="config", long_names=(), short_names=("c",)
        )
        spec = make_command(options={"all": all_opt, "build": build, "config": config})

        result = parse_command_line_args(spec, ["-ab=c"])

        assert result.options["all"] is True
        assert result.options["build"] == "c"


class TestFlagInlineValueProhibition:
    def test_long_flag_with_equals_raises_value_not_allowed_error(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="verbose")
        spec = make_command(options={"verbose": opt})

        with pytest.raises(OptionValueNotAllowedError) as exc_info:
            _ = parse_command_line_args(spec, ["--verbose=true"])

        assert exc_info.value.option == "verbose"
        assert exc_info.value.received == "true"

    def test_short_flag_with_equals_raises_value_not_allowed_error(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(
            name="verbose", long_names=(), short_names=("v",)
        )
        spec = make_command(options={"verbose": opt})

        with pytest.raises(OptionValueNotAllowedError) as exc_info:
            _ = parse_command_line_args(spec, ["-v=true"])

        assert exc_info.value.option == "v"
        assert exc_info.value.received == "true"

    def test_negative_flag_with_equals_raises_value_not_allowed_error(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="color", negative_prefixes=("no",))
        spec = make_command(options={"color": opt})

        with pytest.raises(OptionValueNotAllowedError) as exc_info:
            _ = parse_command_line_args(spec, ["--no-color=false"])

        assert exc_info.value.option == "no-color"
        assert exc_info.value.received == "false"


class TestSpecialCharactersInInlineValues:
    def test_inline_value_containing_equals_sign(self):
        spec = CommandSpecification(
            name="test",
            options={
                "config": ValueOptionSpecification(
                    name="config",
                    arity=Arity.exactly_one(),
                    greedy=False,
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
                    long_names=("output",),
                    short_names=(),
                ),
                "outputdir": ValueOptionSpecification(
                    name="outputdir",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    long_names=("outputdir",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_inline_values_without_equals=True)

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ["--output"], config)


class TestSecurityConsiderations:
    def test_path_traversal_in_inline_value(self):
        spec = CommandSpecification(
            name="test",
            options={
                "file": ValueOptionSpecification(
                    name="file",
                    arity=Arity.exactly_one(),
                    greedy=False,
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
