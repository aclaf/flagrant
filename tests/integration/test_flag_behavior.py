import pytest

from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import (
    OptionNotRepeatableError,
    OptionValueNotAllowedError,
    UnknownOptionError,
)
from flagrant.specification import (
    FlagAccumulationMode,
    FlagOptionSpecification,
    command,
    flag_option,
)


class TestBasicFlagBehavior:
    def test_long_flag_present_sets_true(self):
        opt = flag_option(["verbose"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--verbose",))

        assert result.options["verbose"] is True

    def test_short_flag_present_sets_true(self):
        opt = flag_option(["v"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("-v",))

        assert result.options["v"] is True

    def test_flag_absent_creates_no_entry_in_result(self):
        opt = flag_option(["verbose"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ())

        assert "verbose" not in result.options

    def test_flag_has_arity_zero(self):
        opt = flag_option(["verbose"])
        spec = command("test", options=[opt])

        _ = parse_command_line_args(spec, ("--verbose",))

        assert spec.options is not None
        flag_spec = spec.options[0]
        assert isinstance(flag_spec, FlagOptionSpecification)
        assert flag_spec.arity == 0


class TestShortFlagClustering:
    def test_clustered_short_flags_expand_to_separate_flags(self):
        a_opt = flag_option(["a"])
        b_opt = flag_option(["b"])
        c_opt = flag_option(["c"])
        spec = command("test", options=[a_opt, b_opt, c_opt])

        result = parse_command_line_args(spec, ("-abc",))

        assert result.options["a"] is True
        assert result.options["b"] is True
        assert result.options["c"] is True

    def test_clustered_flags_all_set_correctly(self):
        verbose = flag_option(["v"])
        quiet = flag_option(["q"])
        spec = command("test", options=[verbose, quiet])

        result = parse_command_line_args(spec, ("-vq",))

        assert result.options["v"] is True
        assert result.options["q"] is True

    def test_repeated_flag_in_cluster_counts_each_occurrence(self):
        opt = flag_option(["v"], accumulation_mode="count")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("-vvv",))

        assert result.options["v"] == 3


class TestFlagNegativeWithPrefixes:
    @pytest.mark.xfail(
        reason="prefixed_names missing hyphen separator - produces 'noverbose'"
    )
    def test_negative_flag_with_no_prefix_returns_false(self):
        opt = flag_option(["verbose"], negative_prefixes=["no"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--no-verbose",))

        assert result.options["verbose"] is False

    @pytest.mark.xfail(reason="prefixed_names missing hyphen separator")
    def test_negative_flag_with_disable_prefix_returns_false(self):
        opt = flag_option(["color"], negative_prefixes=["no", "disable"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--disable-color",))

        assert result.options["color"] is False

    @pytest.mark.xfail(reason="prefixed_names missing hyphen separator")
    def test_negative_flag_with_multiple_names_returns_false(self):
        opt = flag_option(["verbose", "v"], negative_prefixes=["no"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--no-verbose",))

        assert result.options["verbose"] is False

    @pytest.mark.xfail(reason="negative_names handling not implemented in resolver")
    def test_negative_short_flag_returns_false(self):
        opt = flag_option(["v"], negative_names=["q"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("-q",))

        assert result.options["v"] is False

    def test_negative_prefix_on_non_negatable_flag_raises_unknown_option_error(self):
        opt = flag_option(["verbose"])
        spec = command("test", options=[opt])

        with pytest.raises(UnknownOptionError):
            _ = parse_command_line_args(spec, ("--no-verbose",))


class TestFlagAccumulationModes:
    @pytest.mark.parametrize(
        ("accumulation_mode", "input_args", "expected_result"),
        [
            ("last", ("--verbose", "--verbose"), True),
            ("first", ("--verbose", "--verbose"), True),
            ("count", ("--verbose", "--verbose", "--verbose"), 3),
            ("count", ("--verbose",), 1),
        ],
    )
    def test_flag_accumulation_modes(
        self,
        accumulation_mode: FlagAccumulationMode,
        input_args: tuple[str, ...],
        expected_result: bool | int,
    ):
        opt = flag_option(["verbose"], accumulation_mode=accumulation_mode)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, input_args)

        assert result.options["verbose"] == expected_result

    @pytest.mark.xfail(
        reason="negative flag prefixes not properly implemented", strict=False
    )
    @pytest.mark.parametrize(
        ("accumulation_mode", "input_args", "expected_result"),
        [
            ("last", ("--verbose", "--no-verbose"), False),
            ("last", ("--no-verbose", "--verbose"), True),
            ("first", ("--verbose", "--no-verbose"), True),
            ("first", ("--no-verbose", "--verbose", "--no-verbose"), False),
            ("count", ("--verbose", "--no-verbose", "--verbose"), 2),
        ],
    )
    def test_flag_accumulation_modes_with_negation(
        self,
        accumulation_mode: FlagAccumulationMode,
        input_args: tuple[str, ...],
        expected_result: bool | int,
    ):
        opt = flag_option(
            ["verbose"],
            negative_prefixes=["no"],
            accumulation_mode=accumulation_mode,
        )
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, input_args)

        assert result.options["verbose"] == expected_result

    def test_clustered_short_flags_count_correctly(self):
        opt = flag_option(["v"], accumulation_mode="count")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("-vvv",))

        assert result.options["v"] == 3


class TestFlagAccumulationModeError:
    def test_first_occurrence_succeeds_in_error_mode(self):
        opt = flag_option(["verbose"], accumulation_mode="error")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--verbose",))

        assert result.options["verbose"] is True

    @pytest.mark.xfail(reason="error accumulation mode not implemented for flags")
    def test_second_occurrence_raises_option_not_repeatable_error(self):
        opt = flag_option(["verbose"], accumulation_mode="error")
        spec = command("test", options=[opt])

        with pytest.raises(OptionNotRepeatableError):
            _ = parse_command_line_args(spec, ("--verbose", "--verbose"))

    @pytest.mark.xfail(reason="negative flag prefixes and error mode not implemented")
    def test_positive_then_negative_raises_error_in_error_mode(self):
        opt = flag_option(
            ["verbose"],
            negative_prefixes=["no"],
            accumulation_mode="error",
        )
        spec = command("test", options=[opt])

        with pytest.raises(OptionNotRepeatableError):
            _ = parse_command_line_args(spec, ("--verbose", "--no-verbose"))


class TestFlagResultTypes:
    @pytest.mark.parametrize(
        ("accumulation_mode", "expected_type"),
        [
            ("last", bool),
            ("first", bool),
            ("count", int),
        ],
    )
    def test_flag_result_types(
        self,
        accumulation_mode: FlagAccumulationMode,
        expected_type: type,
    ):
        opt = flag_option(["verbose"], accumulation_mode=accumulation_mode)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--verbose",))

        assert isinstance(result.options["verbose"], expected_type)


class TestNegativeFlagCaseSensitivity:
    @pytest.mark.xfail(
        reason="is_negative method not implemented on FlagOptionSpecification"
    )
    def test_case_sensitive_match_finds_exact_negative_name(self):
        flag_spec = flag_option(["verbose"], negative_prefixes=["no"])

        result = flag_spec.is_negative("no-verbose", case_sensitive=True)  # pyright: ignore[reportAttributeAccessIssue]

        assert result is True

    @pytest.mark.xfail(
        reason="is_negative method not implemented on FlagOptionSpecification"
    )
    def test_case_sensitive_match_rejects_different_case(self):
        flag_spec = flag_option(["verbose"], negative_prefixes=["no"])

        result = flag_spec.is_negative("NO-VERBOSE", case_sensitive=True)  # pyright: ignore[reportAttributeAccessIssue]

        assert result is False

    @pytest.mark.xfail(
        reason="is_negative method not implemented on FlagOptionSpecification"
    )
    def test_case_insensitive_match_finds_different_case(self):
        flag_spec = flag_option(["verbose"], negative_prefixes=["no"])

        result = flag_spec.is_negative("NO-VERBOSE", case_sensitive=False)  # pyright: ignore[reportAttributeAccessIssue]

        assert result is True

    @pytest.mark.xfail(
        reason="is_negative method not implemented on FlagOptionSpecification"
    )
    def test_case_insensitive_match_finds_mixed_case(self):
        flag_spec = flag_option(["verbose"], negative_prefixes=["no"])

        result = flag_spec.is_negative("No-Verbose", case_sensitive=False)  # pyright: ignore[reportAttributeAccessIssue]

        assert result is True


class TestFlagInlineValueProhibition:
    def test_long_flag_with_equals_raises_value_not_allowed_error(self):
        opt = flag_option(["verbose"])
        spec = command("test", options=[opt])

        with pytest.raises(OptionValueNotAllowedError) as exc_info:
            _ = parse_command_line_args(spec, ("--verbose=true",))

        assert exc_info.value.option == "verbose"
        assert exc_info.value.received == "true"

    def test_short_flag_with_equals_raises_value_not_allowed_error(self):
        opt = flag_option(["v"])
        spec = command("test", options=[opt])

        with pytest.raises(OptionValueNotAllowedError) as exc_info:
            _ = parse_command_line_args(spec, ("-v=true",))

        assert exc_info.value.option == "v"
        assert exc_info.value.received == "true"

    @pytest.mark.xfail(reason="negative flag prefixes not properly implemented")
    def test_negative_flag_with_equals_raises_value_not_allowed_error(self):
        opt = flag_option(["color"], negative_prefixes=["no"])
        spec = command("test", options=[opt])

        with pytest.raises(OptionValueNotAllowedError) as exc_info:
            _ = parse_command_line_args(spec, ("--no-color=false",))

        assert exc_info.value.option == "no-color"
        assert exc_info.value.received == "false"
