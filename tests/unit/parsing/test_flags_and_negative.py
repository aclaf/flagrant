from typing import TYPE_CHECKING

import pytest

from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import (
    OptionNotRepeatableError,
    UnknownOptionError,
)
from flagrant.specification import (
    FlagAccumulationMode,
    FlagOptionSpecification,
)

if TYPE_CHECKING:
    from flagrant.specification import (
        CommandSpecificationFactory,
        FlagOptionSpecificationFactory,
    )


class TestBasicFlagBehavior:
    def test_long_flag_present_sets_true(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="verbose")
        spec = make_command(options={"verbose": opt})

        result = parse_command_line_args(spec, ["--verbose"])

        assert result.options["verbose"] is True

    def test_short_flag_present_sets_true(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="verbose", long_names=(), short_names=("v",))
        spec = make_command(options={"verbose": opt})

        result = parse_command_line_args(spec, ["-v"])

        assert result.options["verbose"] is True

    def test_flag_absent_creates_no_entry_in_result(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="verbose")
        spec = make_command(options={"verbose": opt})

        result = parse_command_line_args(spec, [])

        assert "verbose" not in result.options

    def test_flag_has_arity_zero_zero(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="verbose")
        spec = make_command(options={"verbose": opt})

        _ = parse_command_line_args(spec, ["--verbose"])

        assert spec.options is not None
        flag_spec = spec.options.get("verbose")
        assert flag_spec is not None
        assert isinstance(flag_spec, FlagOptionSpecification)
        assert flag_spec.arity.min == 0
        assert flag_spec.arity.max == 0


class TestShortFlagClustering:
    def test_clustered_short_flags_expand_to_separate_flags(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        spec = make_command(
            options={
                "a": make_flag_opt(name="a", long_names=(), short_names=("a",)),
                "b": make_flag_opt(name="b", long_names=(), short_names=("b",)),
                "c": make_flag_opt(name="c", long_names=(), short_names=("c",)),
            }
        )

        result = parse_command_line_args(spec, ["-abc"])

        assert result.options["a"] is True
        assert result.options["b"] is True
        assert result.options["c"] is True

    def test_clustered_flags_all_set_correctly(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        spec = make_command(
            options={
                "verbose": make_flag_opt(
                    name="verbose", long_names=(), short_names=("v",)
                ),
                "quiet": make_flag_opt(name="quiet", long_names=(), short_names=("q",)),
            }
        )

        result = parse_command_line_args(spec, ["-vq"])

        assert result.options["verbose"] is True
        assert result.options["quiet"] is True

    def test_repeated_flag_in_cluster_counts_each_occurrence(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(
            name="verbose",
            long_names=(),
            short_names=("v",),
            accumulation_mode=FlagAccumulationMode.COUNT,
        )
        spec = make_command(options={"verbose": opt})

        result = parse_command_line_args(spec, ["-vvv"])

        assert result.options["verbose"] == 3


class TestFlagNegativeWithPrefixes:
    @pytest.mark.parametrize(
        ("prefix", "flag_kwargs", "input_args"),
        [
            (
                "no",
                {"name": "verbose", "negative_prefixes": ("no",)},
                ["--no-verbose"],
            ),
            (
                "disable",
                {"name": "color", "negative_prefixes": ("no", "disable")},
                ["--disable-color"],
            ),
            (
                "no",
                {
                    "name": "verbose",
                    "long_names": ("verbose", "v"),
                    "negative_prefixes": ("no",),
                },
                ["--no-verbose"],
            ),
            (
                "q",
                {
                    "name": "verbose",
                    "short_names": ("v",),
                    "negative_short_names": ("q",),
                },
                ["-q"],
            ),
        ],
    )
    def test_negative_flag_parsing(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        prefix: str,
        flag_kwargs: dict[str, object],
        input_args: list[str],
    ):
        opt = make_flag_opt(**flag_kwargs)  # type: ignore[reportArgumentType]
        spec = make_command(options={opt.name: opt})

        result = parse_command_line_args(spec, input_args)

        assert result.options[opt.name] is False

    def test_negative_prefix_on_non_negatable_flag_raises_unknown_option_error(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(name="verbose")
        spec = make_command(options={"verbose": opt})

        with pytest.raises(UnknownOptionError):
            _ = parse_command_line_args(spec, ["--no-verbose"])


class TestFlagAccumulationModes:
    @pytest.mark.parametrize(
        ("accumulation_mode", "input_args", "expected_result"),
        [
            (
                FlagAccumulationMode.LAST,
                ["--verbose", "--verbose"],
                True,
            ),
            (
                FlagAccumulationMode.LAST,
                ["--verbose", "--no-verbose"],
                False,
            ),
            (
                FlagAccumulationMode.LAST,
                ["--no-verbose", "--verbose"],
                True,
            ),
            (
                FlagAccumulationMode.FIRST,
                ["--verbose", "--verbose"],
                True,
            ),
            (
                FlagAccumulationMode.FIRST,
                ["--verbose", "--no-verbose"],
                True,
            ),
            (
                FlagAccumulationMode.FIRST,
                ["--no-verbose", "--verbose", "--no-verbose"],
                False,
            ),
            (
                FlagAccumulationMode.COUNT,
                ["--verbose", "--verbose", "--verbose"],
                3,
            ),
            (
                FlagAccumulationMode.COUNT,
                ["--verbose", "--no-verbose", "--verbose"],
                2,
            ),
            (
                FlagAccumulationMode.COUNT,
                ["--verbose"],
                1,
            ),
        ],
    )
    def test_flag_accumulation_modes(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        accumulation_mode: FlagAccumulationMode,
        input_args: list[str],
        expected_result: bool | int,
    ):
        opt = make_flag_opt(
            name="verbose",
            negative_prefixes=("no",),
            accumulation_mode=accumulation_mode,
        )
        spec = make_command(options={"verbose": opt})

        result = parse_command_line_args(spec, input_args)

        assert result.options["verbose"] == expected_result


    def test_clustered_short_flags_count_correctly(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(
            name="verbose",
            long_names=(),
            short_names=("v",),
            accumulation_mode=FlagAccumulationMode.COUNT,
        )
        spec = make_command(options={"verbose": opt})

        result = parse_command_line_args(spec, ["-vvv"])

        assert result.options["verbose"] == 3


class TestFlagAccumulationModeError:
    def test_first_occurrence_succeeds_in_error_mode(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(
            name="verbose", accumulation_mode=FlagAccumulationMode.ERROR
        )
        spec = make_command(options={"verbose": opt})

        result = parse_command_line_args(spec, ["--verbose"])

        assert result.options["verbose"] is True

    def test_second_occurrence_raises_option_not_repeatable_error(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(
            name="verbose", accumulation_mode=FlagAccumulationMode.ERROR
        )
        spec = make_command(options={"verbose": opt})

        with pytest.raises(OptionNotRepeatableError):
            _ = parse_command_line_args(spec, ["--verbose", "--verbose"])

    def test_positive_then_negative_raises_error_in_error_mode(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt = make_flag_opt(
            name="verbose",
            negative_prefixes=("no",),
            accumulation_mode=FlagAccumulationMode.ERROR,
        )
        spec = make_command(options={"verbose": opt})

        with pytest.raises(OptionNotRepeatableError):
            _ = parse_command_line_args(spec, ["--verbose", "--no-verbose"])


class TestFlagResultTypes:
    @pytest.mark.parametrize(
        ("accumulation_mode", "expected_type"),
        [
            (FlagAccumulationMode.LAST, bool),
            (FlagAccumulationMode.FIRST, bool),
            (FlagAccumulationMode.COUNT, int),
        ],
    )
    def test_flag_result_types(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        accumulation_mode: FlagAccumulationMode,
        expected_type: type,
    ):
        opt = make_flag_opt(
            name="verbose", accumulation_mode=accumulation_mode
        )
        spec = make_command(options={"verbose": opt})

        result = parse_command_line_args(spec, ["--verbose"])

        assert isinstance(result.options["verbose"], expected_type)


class TestNegativeFlagCaseSensitivity:
    def test_case_sensitive_match_finds_exact_negative_name(
        self,
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        flag_spec = make_flag_opt(
            name="verbose",
            negative_prefixes=("no",),
        )

        result = flag_spec.is_negative("no-verbose", case_sensitive=True)

        assert result is True

    def test_case_sensitive_match_rejects_different_case(
        self,
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        flag_spec = make_flag_opt(
            name="verbose",
            negative_prefixes=("no",),
        )

        result = flag_spec.is_negative("NO-VERBOSE", case_sensitive=True)

        assert result is False

    def test_case_insensitive_match_finds_different_case(
        self,
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        flag_spec = make_flag_opt(
            name="verbose",
            negative_prefixes=("no",),
        )

        result = flag_spec.is_negative("NO-VERBOSE", case_sensitive=False)

        assert result is True

    def test_case_insensitive_match_finds_mixed_case(
        self,
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        flag_spec = make_flag_opt(
            name="verbose",
            negative_prefixes=("no",),
        )

        result = flag_spec.is_negative("No-Verbose", case_sensitive=False)

        assert result is True
