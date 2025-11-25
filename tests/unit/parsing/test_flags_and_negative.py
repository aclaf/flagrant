import pytest

from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import (
    OptionNotRepeatableError,
    UnknownOptionError,
)
from flagrant.specification import (
    Arity,
    CommandSpecification,
    FlagAccumulationMode,
    FlagOptionSpecification,
)


class TestBasicFlagBehavior:
    def test_long_flag_present_sets_true(self):
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

        result = parse_command_line_args(spec, ["--verbose"])

        assert result.options["verbose"] is True

    def test_short_flag_present_sets_true(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=(),
                    short_names=("v",),
                )
            },
        )

        result = parse_command_line_args(spec, ["-v"])

        assert result.options["verbose"] is True

    def test_flag_absent_creates_no_entry_in_result(self):
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

        result = parse_command_line_args(spec, [])

        assert "verbose" not in result.options

    def test_flag_has_arity_zero_zero(self):
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

        _ = parse_command_line_args(spec, ["--verbose"])

        assert spec.options is not None
        flag_spec = spec.options.get("verbose")
        assert flag_spec is not None
        assert isinstance(flag_spec, FlagOptionSpecification)
        assert flag_spec.arity.min == 0
        assert flag_spec.arity.max == 0


class TestShortFlagClustering:
    def test_clustered_short_flags_expand_to_separate_flags(self):
        spec = CommandSpecification(
            "test",
            options={
                "a": FlagOptionSpecification(
                    name="a",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="a",
                    long_names=(),
                    short_names=("a",),
                ),
                "b": FlagOptionSpecification(
                    name="b",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="b",
                    long_names=(),
                    short_names=("b",),
                ),
                "c": FlagOptionSpecification(
                    name="c",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="c",
                    long_names=(),
                    short_names=("c",),
                ),
            },
        )

        result = parse_command_line_args(spec, ["-abc"])

        assert result.options["a"] is True
        assert result.options["b"] is True
        assert result.options["c"] is True

    def test_clustered_flags_all_set_correctly(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=(),
                    short_names=("v",),
                ),
                "quiet": FlagOptionSpecification(
                    name="quiet",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="quiet",
                    long_names=(),
                    short_names=("q",),
                ),
            },
        )

        result = parse_command_line_args(spec, ["-vq"])

        assert result.options["verbose"] is True
        assert result.options["quiet"] is True

    def test_repeated_flag_in_cluster_counts_each_occurrence(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=(),
                    short_names=("v",),
                    accumulation_mode=FlagAccumulationMode.COUNT,
                )
            },
        )

        result = parse_command_line_args(spec, ["-vvv"])

        assert result.options["verbose"] == 3


class TestFlagNegativeWithPrefixes:
    def test_negative_prefix_with_long_name_sets_false(self):
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
                    negative_prefixes=("no",),
                )
            },
        )

        result = parse_command_line_args(spec, ["--no-verbose"])

        assert result.options["verbose"] is False

    def test_negative_prefix_with_multiple_prefixes(self):
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
                    negative_prefixes=("no", "disable"),
                )
            },
        )

        result = parse_command_line_args(spec, ["--disable-color"])

        assert result.options["color"] is False

    def test_negative_prefix_strips_prefix_and_resolves_base_name(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose", "v"),
                    short_names=(),
                    negative_prefixes=("no",),
                )
            },
        )

        result = parse_command_line_args(spec, ["--no-verbose"])

        assert "verbose" in result.options
        assert result.options["verbose"] is False

    def test_negative_prefix_on_non_negatable_flag_raises_unknown_option_error(self):
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

        with pytest.raises(UnknownOptionError):
            _ = parse_command_line_args(spec, ["--no-verbose"])

    def test_negative_short_name_sets_false(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=("v",),
                    negative_short_names=("q",),
                )
            },
        )

        result = parse_command_line_args(spec, ["-q"])

        assert result.options["verbose"] is False


class TestFlagAccumulationModeLastDefault:
    def test_last_occurrence_wins_with_default_mode(self):
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

        result = parse_command_line_args(spec, ["--verbose", "--verbose"])

        assert result.options["verbose"] is True

    def test_positive_then_negative_sets_false_in_last_mode(self):
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
                    negative_prefixes=("no",),
                    accumulation_mode=FlagAccumulationMode.LAST,
                )
            },
        )

        result = parse_command_line_args(spec, ["--verbose", "--no-verbose"])

        assert result.options["verbose"] is False

    def test_negative_then_positive_sets_true_in_last_mode(self):
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
                    negative_prefixes=("no",),
                    accumulation_mode=FlagAccumulationMode.LAST,
                )
            },
        )

        result = parse_command_line_args(spec, ["--no-verbose", "--verbose"])

        assert result.options["verbose"] is True


class TestFlagAccumulationModeFirst:
    def test_first_occurrence_wins_in_first_mode(self):
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
                    accumulation_mode=FlagAccumulationMode.FIRST,
                )
            },
        )

        result = parse_command_line_args(spec, ["--verbose", "--verbose"])

        assert result.options["verbose"] is True

    def test_positive_then_negative_keeps_true_in_first_mode(self):
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
                    negative_prefixes=("no",),
                    accumulation_mode=FlagAccumulationMode.FIRST,
                )
            },
        )

        result = parse_command_line_args(spec, ["--verbose", "--no-verbose"])

        assert result.options["verbose"] is True

    def test_later_occurrences_ignored_in_first_mode(self):
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
                    negative_prefixes=("no",),
                    accumulation_mode=FlagAccumulationMode.FIRST,
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--no-verbose", "--verbose", "--no-verbose"]
        )

        assert result.options["verbose"] is False


class TestFlagAccumulationModeCount:
    def test_count_mode_counts_positive_occurrences_as_integer(self):
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
                    accumulation_mode=FlagAccumulationMode.COUNT,
                )
            },
        )

        result = parse_command_line_args(spec, ["--verbose", "--verbose", "--verbose"])

        assert result.options["verbose"] == 3

    def test_clustered_short_flags_count_correctly(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=(),
                    short_names=("v",),
                    accumulation_mode=FlagAccumulationMode.COUNT,
                )
            },
        )

        result = parse_command_line_args(spec, ["-vvv"])

        assert result.options["verbose"] == 3

    def test_count_mode_counts_only_positive_occurrences(self):
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
                    negative_prefixes=("no",),
                    accumulation_mode=FlagAccumulationMode.COUNT,
                )
            },
        )

        result = parse_command_line_args(
            spec, ["--verbose", "--no-verbose", "--verbose"]
        )

        assert result.options["verbose"] == 2

    def test_single_occurrence_in_count_mode_returns_one(self):
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
                    accumulation_mode=FlagAccumulationMode.COUNT,
                )
            },
        )

        result = parse_command_line_args(spec, ["--verbose"])

        assert result.options["verbose"] == 1


class TestFlagAccumulationModeError:
    def test_first_occurrence_succeeds_in_error_mode(self):
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
                    accumulation_mode=FlagAccumulationMode.ERROR,
                )
            },
        )

        result = parse_command_line_args(spec, ["--verbose"])

        assert result.options["verbose"] is True

    def test_second_occurrence_raises_option_not_repeatable_error(self):
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
                    accumulation_mode=FlagAccumulationMode.ERROR,
                )
            },
        )

        with pytest.raises(OptionNotRepeatableError):
            _ = parse_command_line_args(spec, ["--verbose", "--verbose"])

    def test_positive_then_negative_raises_error_in_error_mode(self):
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
                    negative_prefixes=("no",),
                    accumulation_mode=FlagAccumulationMode.ERROR,
                )
            },
        )

        with pytest.raises(OptionNotRepeatableError):
            _ = parse_command_line_args(spec, ["--verbose", "--no-verbose"])


class TestFlagResultTypes:
    def test_last_mode_returns_bool(self):
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
                    accumulation_mode=FlagAccumulationMode.LAST,
                )
            },
        )

        result = parse_command_line_args(spec, ["--verbose"])

        assert isinstance(result.options["verbose"], bool)

    def test_first_mode_returns_bool(self):
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
                    accumulation_mode=FlagAccumulationMode.FIRST,
                )
            },
        )

        result = parse_command_line_args(spec, ["--verbose"])

        assert isinstance(result.options["verbose"], bool)

    def test_count_mode_returns_int(self):
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
                    accumulation_mode=FlagAccumulationMode.COUNT,
                )
            },
        )

        result = parse_command_line_args(spec, ["--verbose"])

        assert isinstance(result.options["verbose"], int)


class TestNegativeFlagCaseSensitivity:
    def test_case_sensitive_match_finds_exact_negative_name(self):
        flag_spec = FlagOptionSpecification(
            name="verbose",
            arity=Arity.none(),
            greedy=False,
            preferred_name="verbose",
            long_names=("verbose",),
            short_names=(),
            negative_prefixes=("no",),
        )

        result = flag_spec.is_negative("no-verbose", case_sensitive=True)

        assert result is True

    def test_case_sensitive_match_rejects_different_case(self):
        flag_spec = FlagOptionSpecification(
            name="verbose",
            arity=Arity.none(),
            greedy=False,
            preferred_name="verbose",
            long_names=("verbose",),
            short_names=(),
            negative_prefixes=("no",),
        )

        result = flag_spec.is_negative("NO-VERBOSE", case_sensitive=True)

        assert result is False

    def test_case_insensitive_match_finds_different_case(self):
        flag_spec = FlagOptionSpecification(
            name="verbose",
            arity=Arity.none(),
            greedy=False,
            preferred_name="verbose",
            long_names=("verbose",),
            short_names=(),
            negative_prefixes=("no",),
        )

        result = flag_spec.is_negative("NO-VERBOSE", case_sensitive=False)

        assert result is True

    def test_case_insensitive_match_finds_mixed_case(self):
        flag_spec = FlagOptionSpecification(
            name="verbose",
            arity=Arity.none(),
            greedy=False,
            preferred_name="verbose",
            long_names=("verbose",),
            short_names=(),
            negative_prefixes=("no",),
        )

        result = flag_spec.is_negative("No-Verbose", case_sensitive=False)

        assert result is True
