import pytest

from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import (
    OptionMissingValueError,
    OptionNotRepeatableError,
    UnknownOptionError,
)
from flagrant.specification import (
    command,
    scalar_option,
)


class TestBasicScalarParsing:
    def test_long_option_captures_single_value(self):
        opt = scalar_option(["output"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--output", "file.txt"))

        assert result.options["output"] == "file.txt"

    def test_short_option_captures_single_value(self):
        opt = scalar_option(["o"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("-o", "file.txt"))

        assert result.options["o"] == "file.txt"

    def test_option_absent_creates_no_entry_in_result(self):
        opt = scalar_option(["output"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ())

        assert "output" not in result.options


class TestScalarInlineValues:
    def test_long_option_with_equals_assigns_value(self):
        opt = scalar_option(["output"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--output=file.txt",))

        assert result.options["output"] == "file.txt"

    def test_inline_value_splits_on_first_equals_only(self):
        opt = scalar_option(["config"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--config=key=value",))

        assert result.options["config"] == "key=value"

    def test_inline_value_with_multiple_equals_preserves_all_after_first(self):
        opt = scalar_option(["equation"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--equation=x=y+z",))

        assert result.options["equation"] == "x=y+z"

    def test_empty_inline_value_assigns_empty_string(self):
        opt = scalar_option(["output"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--output=",))

        assert result.options["output"] == ""

    def test_short_option_with_equals_assigns_value(self):
        opt = scalar_option(["o"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("-o=file.txt",))

        assert result.options["o"] == "file.txt"

    def test_short_option_equals_splits_on_first_equals(self):
        opt = scalar_option(["c"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("-c=key=value",))

        assert result.options["c"] == "key=value"


class TestScalarOptionalArity:
    def test_optional_arity_with_value_captures_value(self):
        opt = scalar_option(["level"], arity="?")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--level", "debug"))

        assert result.options["level"] == "debug"

    def test_optional_arity_without_value_returns_none(self):
        opt = scalar_option(["level"], arity="?")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--level",))

        assert result.options["level"] is None

    def test_optional_arity_at_end_of_args_returns_none(self):
        opt = scalar_option(["level"], arity="?")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--level",))

        assert "level" in result.options
        assert result.options["level"] is None


class TestScalarAccumulationModes:
    def test_last_accumulation_mode_keeps_last_value(self):
        opt = scalar_option(["output"], accumulation_mode="last")
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--output", "first.txt", "--output", "second.txt")
        )

        assert result.options["output"] == "second.txt"

    def test_first_accumulation_mode_keeps_first_value(self):
        opt = scalar_option(["output"], accumulation_mode="first")
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--output", "first.txt", "--output", "second.txt")
        )

        assert result.options["output"] == "first.txt"

    def test_error_mode_raises_on_second_occurrence(self):
        opt = scalar_option(["output"], accumulation_mode="error")
        spec = command("test", options=[opt])

        with pytest.raises(OptionNotRepeatableError):
            parse_command_line_args(
                spec, ("--output", "first.txt", "--output", "second.txt")
            )

    def test_error_mode_allows_first_occurrence(self):
        opt = scalar_option(["output"], accumulation_mode="error")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--output", "file.txt"))

        assert result.options["output"] == "file.txt"


class TestScalarMissingValues:
    def test_option_at_end_without_value_raises_error(self):
        opt = scalar_option(["output"])
        spec = command("test", options=[opt])

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ("--output",))

    def test_option_before_another_option_raises_error(self):
        opt1 = scalar_option(["output"])
        opt2 = scalar_option(["verbose"])
        spec = command("test", options=[opt1, opt2])

        with pytest.raises(OptionMissingValueError):
            parse_command_line_args(spec, ("--output", "--verbose", "value"))


class TestScalarEdgeCases:
    def test_empty_string_value_via_equals(self):
        opt = scalar_option(["option"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--option=",))

        assert result.options["option"] == ""

    def test_whitespace_only_value(self):
        opt = scalar_option(["option"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--option", "   "))

        assert result.options["option"] == "   "

    def test_value_containing_equals_sign(self):
        opt = scalar_option(["option"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--option", "key=value"))

        assert result.options["option"] == "key=value"

    def test_value_containing_hyphens(self):
        opt = scalar_option(["pattern"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--pattern", "foo-bar-baz"))

        assert result.options["pattern"] == "foo-bar-baz"


class TestScalarNegativeNumbers:
    def test_negative_number_value_allowed_when_enabled(self):
        opt = scalar_option(["value"], allow_negative_numbers=True)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--value", "-42"))

        assert result.options["value"] == "-42"

    @pytest.mark.xfail(reason="negative number detection not implemented")
    def test_negative_number_value_rejected_when_disabled(self):
        opt = scalar_option(["value"], allow_negative_numbers=False)
        spec = command("test", options=[opt])

        # Without allow_negative_numbers, -42 would be interpreted as an option
        with pytest.raises(UnknownOptionError):
            parse_command_line_args(spec, ("--value", "-42"))

    def test_negative_decimal_allowed(self):
        opt = scalar_option(["value"], allow_negative_numbers=True)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--value", "-3.14"))

        assert result.options["value"] == "-3.14"


class TestScalarResultTypes:
    def test_result_is_string_type(self):
        opt = scalar_option(["output"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--output", "file.txt"))

        assert isinstance(result.options["output"], str)

    def test_result_is_not_tuple(self):
        opt = scalar_option(["output"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--output", "file.txt"))

        assert not isinstance(result.options["output"], tuple)


class TestScalarWithSeparator:
    def test_double_dash_moves_remaining_to_extra_args(self):
        opt = scalar_option(["flag"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--flag", "value", "--", "--other"))

        assert result.options["flag"] == "value"
        assert result.extra_args == ("--other",)
