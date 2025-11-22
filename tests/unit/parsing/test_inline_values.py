import pytest

from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import (
    OptionMissingValueError,
    OptionValueNotAllowedError,
)
from flagrant.specification import (
    Arity,
    CommandSpecification,
    FlagOptionSpecification,
    ValueOptionSpecification,
)


class TestLongOptionEqualsBasic:
    def test_long_option_with_equals_assigns_single_value(self):
        spec = CommandSpecification(
            "test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=("output",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--output=file.txt"])

        assert result.options["output"] == "file.txt"

    def test_long_option_equals_splits_on_first_equals_only(self):
        spec = CommandSpecification(
            "test",
            options={
                "config": ValueOptionSpecification(
                    name="config",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="config",
                    long_names=("config",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--config=key=value"])

        assert result.options["config"] == "key=value"

    def test_long_option_equals_with_multiple_equals_preserves_all_after_first(self):
        spec = CommandSpecification(
            "test",
            options={
                "equation": ValueOptionSpecification(
                    name="equation",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="equation",
                    long_names=("equation",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--equation=x=y+z"])

        assert result.options["equation"] == "x=y+z"

    def test_long_option_equals_with_empty_value_assigns_empty_string(self):
        spec = CommandSpecification(
            "test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=("output",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--output="])

        assert result.options["output"] == ""

    def test_long_option_equals_satisfies_arity_of_one(self):
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
                )
            },
        )

        result = parse_command_line_args(spec, ["--value=data"])

        assert result.options["value"] == "data"


class TestLongOptionEqualsArityValidation:
    def test_long_option_equals_with_arity_two_raises_insufficient_values_error(self):
        spec = CommandSpecification(
            "test",
            options={
                "coords": ValueOptionSpecification(
                    name="coords",
                    arity=Arity.exact(2),
                    greedy=False,
                    preferred_name="coords",
                    long_names=("coords",),
                    short_names=(),
                )
            },
        )

        with pytest.raises(OptionMissingValueError) as exc_info:
            _ = parse_command_line_args(spec, ["--coords=10"])

        assert exc_info.value.option == "coords"
        assert exc_info.value.required == Arity.exact(2)

    def test_long_option_equals_with_arity_zero_or_one_succeeds(self):
        spec = CommandSpecification(
            "test",
            options={
                "optional": ValueOptionSpecification(
                    name="optional",
                    arity=Arity.at_most_one(),
                    greedy=False,
                    preferred_name="optional",
                    long_names=("optional",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--optional=value"])

        assert result.options["optional"] == "value"

    def test_long_option_equals_with_unbounded_arity_also_consumes_following_args(
        self,
    ):
        spec = CommandSpecification(
            "test",
            options={
                "files": ValueOptionSpecification(
                    name="files",
                    arity=Arity.at_least_one(),
                    greedy=False,
                    preferred_name="files",
                    long_names=("files",),
                    short_names=(),
                )
            },
        )

        result = parse_command_line_args(spec, ["--files=first.txt", "second.txt"])

        assert result.options["files"] == ("first.txt", "second.txt")


class TestShortOptionEqualsBasic:
    def test_short_option_with_equals_assigns_value(self):
        spec = CommandSpecification(
            "test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="o",
                    long_names=(),
                    short_names=("o",),
                )
            },
        )

        result = parse_command_line_args(spec, ["-o=file.txt"])

        assert result.options["output"] == "file.txt"

    def test_short_option_equals_splits_on_first_equals(self):
        spec = CommandSpecification(
            "test",
            options={
                "config": ValueOptionSpecification(
                    name="config",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="c",
                    long_names=(),
                    short_names=("c",),
                )
            },
        )

        result = parse_command_line_args(spec, ["-c=key=value"])

        assert result.options["config"] == "key=value"

    def test_short_option_equals_with_empty_value_assigns_empty_string(self):
        spec = CommandSpecification(
            "test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="o",
                    long_names=(),
                    short_names=("o",),
                )
            },
        )

        result = parse_command_line_args(spec, ["-o="])

        assert result.options["output"] == ""


class TestShortOptionConcatenatedBasic:
    def test_short_option_concatenated_value_without_separator(self):
        spec = CommandSpecification(
            "test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="o",
                    long_names=(),
                    short_names=("o",),
                )
            },
        )

        result = parse_command_line_args(spec, ["-ofile.txt"])

        assert result.options["output"] == "file.txt"

    def test_short_option_concatenated_value_is_remainder_after_option_char(self):
        spec = CommandSpecification(
            "test",
            options={
                "name": ValueOptionSpecification(
                    name="name",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="n",
                    long_names=(),
                    short_names=("n",),
                )
            },
        )

        result = parse_command_line_args(spec, ["-nvalue123"])

        assert result.options["name"] == "value123"

    def test_short_option_concatenated_with_single_char_value(self):
        spec = CommandSpecification(
            "test",
            options={
                "mode": ValueOptionSpecification(
                    name="mode",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="m",
                    long_names=(),
                    short_names=("m",),
                )
            },
        )

        result = parse_command_line_args(spec, ["-ma"])

        assert result.options["mode"] == "a"


class TestClusteringWithInlineValues:
    def test_clustered_options_with_equals_assigns_to_last_option(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="v",
                    long_names=(),
                    short_names=("v",),
                ),
                "quiet": FlagOptionSpecification(
                    name="quiet",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="q",
                    long_names=(),
                    short_names=("q",),
                ),
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

        result = parse_command_line_args(spec, ["-vqo=file.txt"])

        assert result.options["verbose"] is True
        assert result.options["quiet"] is True
        assert result.options["output"] == "file.txt"

    def test_clustered_options_with_concatenated_value_to_last_option(self):
        spec = CommandSpecification(
            "test",
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

        result = parse_command_line_args(spec, ["-abcvalue"])

        assert result.options["all"] is True
        assert result.options["build"] is True
        assert result.options["config"] == "value"

    def test_clustered_equals_assigns_value_even_if_equals_char_defined_as_option(self):
        spec = CommandSpecification(
            "test",
            options={
                "all": FlagOptionSpecification(
                    name="all",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="a",
                    long_names=(),
                    short_names=("a",),
                ),
                "build": ValueOptionSpecification(
                    name="build",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="b",
                    long_names=(),
                    short_names=("b",),
                ),
                "config": FlagOptionSpecification(
                    name="config",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="c",
                    long_names=(),
                    short_names=("c",),
                ),
            },
        )

        result = parse_command_line_args(spec, ["-ab=c"])

        assert result.options["all"] is True
        assert result.options["build"] == "c"


class TestFlagInlineValueProhibition:
    def test_long_flag_with_equals_raises_value_not_allowed_error(self):
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
                )
            },
        )

        with pytest.raises(OptionValueNotAllowedError) as exc_info:
            _ = parse_command_line_args(spec, ["--verbose=true"])

        assert exc_info.value.option == "verbose"
        assert exc_info.value.received == "true"

    def test_short_flag_with_equals_raises_value_not_allowed_error(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="v",
                    long_names=(),
                    short_names=("v",),
                )
            },
        )

        with pytest.raises(OptionValueNotAllowedError) as exc_info:
            _ = parse_command_line_args(spec, ["-v=true"])

        assert exc_info.value.option == "v"
        assert exc_info.value.received == "true"

    def test_negative_flag_with_equals_raises_value_not_allowed_error(self):
        spec = CommandSpecification(
            "test",
            options={
                "color": FlagOptionSpecification(
                    name="color",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="color",
                    long_names=("color",),
                    short_names=(),
                    negative_prefixes=("no",),
                )
            },
        )

        with pytest.raises(OptionValueNotAllowedError) as exc_info:
            _ = parse_command_line_args(spec, ["--no-color=false"])

        assert exc_info.value.option == "no-color"
        assert exc_info.value.received == "false"
