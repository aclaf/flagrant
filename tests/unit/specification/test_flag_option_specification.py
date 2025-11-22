"""Unit tests for FlagOptionSpecification."""

from flagrant.specification import flag_option
from flagrant.specification._options import (
    is_counting_flag_option,
    is_flag_option,
)


class TestFlagOptionSpecificationNames:
    def test_name_returns_first_name(self) -> None:
        opt = flag_option(["verbose", "v"])

        assert opt.name == "verbose"

    def test_long_names_filters_correctly(self) -> None:
        opt = flag_option(["verbose", "v", "chatty"])

        assert opt.long_names == ("verbose", "chatty")

    def test_short_names_filters_correctly(self) -> None:
        opt = flag_option(["verbose", "v", "c"])

        assert opt.short_names == ("v", "c")

    def test_all_names_combines_long_and_short(self) -> None:
        opt = flag_option(["verbose", "v"])

        assert set(opt.all_names) == {"verbose", "v"}


class TestFlagOptionSpecificationNegativeNames:
    def test_negative_names_is_none_by_default(self) -> None:
        opt = flag_option(["verbose"])

        assert opt.negative_names is None

    def test_negative_prefixes_generate_names(self) -> None:
        opt = flag_option(["verbose"], negative_prefixes=("no-",))

        assert opt.negative_names == ("no-verbose",)

    def test_negative_prefixes_combine_with_explicit_names(self) -> None:
        opt = flag_option(
            ["verbose"], negative_names=("quiet",), negative_prefixes=("no-",)
        )

        assert opt.negative_names is not None
        assert "quiet" in opt.negative_names
        assert "no-verbose" in opt.negative_names

    def test_negative_prefixes_only_apply_to_long_names(self) -> None:
        opt = flag_option(["verbose", "v"], negative_prefixes=("no-",))

        # Should only have no-verbose, not no-v
        assert opt.negative_names == ("no-verbose",)

    def test_negative_long_names_filters_correctly(self) -> None:
        opt = flag_option(["verbose"], negative_names=("no-verbose", "q"))

        assert opt.negative_long_names == ("no-verbose",)

    def test_negative_short_names_filters_correctly(self) -> None:
        opt = flag_option(["verbose"], negative_names=("no-verbose", "q"))

        assert opt.negative_short_names == ("q",)

    def test_has_negative_names_true_when_present(self) -> None:
        opt = flag_option(["verbose"], negative_names=("no-verbose",))

        assert opt.has_negative_names is True

    def test_has_negative_names_false_when_none(self) -> None:
        opt = flag_option(["verbose"])

        assert opt.has_negative_names is False

    def test_has_negative_names_false_when_empty(self) -> None:
        opt = flag_option(["verbose"], negative_names=())

        assert opt.has_negative_names is False


class TestFlagOptionSpecificationAccumulationMode:
    def test_default_accumulation_mode_is_toggle(self) -> None:
        opt = flag_option(["verbose"])

        assert opt.accumulation_mode == "toggle"


class TestFlagOptionSpecificationIsCounting:
    def test_is_counting_true_for_count_mode(self) -> None:
        opt = flag_option(["verbose"], accumulation_mode="count")

        assert opt.is_counting is True

    def test_is_counting_false_for_toggle_mode(self) -> None:
        opt = flag_option(["verbose"], accumulation_mode="toggle")

        assert opt.is_counting is False


class TestFlagOptionSpecificationArity:
    def test_arity_is_always_zero(self) -> None:
        opt = flag_option(["verbose"])

        assert opt.arity == 0


class TestFlagOptionSpecificationTypeGuards:
    def test_is_flag_option_returns_true(self) -> None:
        opt = flag_option(["verbose"])

        assert is_flag_option(opt) is True

    def test_is_counting_flag_option_returns_true_for_count_mode(self) -> None:
        opt = flag_option(["verbose"], accumulation_mode="count")

        assert is_counting_flag_option(opt) is True

    def test_is_counting_flag_option_returns_false_for_toggle_mode(self) -> None:
        opt = flag_option(["verbose"], accumulation_mode="toggle")

        assert is_counting_flag_option(opt) is False
