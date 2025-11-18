"""Unit tests for ScalarOptionSpecification."""

from flagrant.specification import scalar_option
from flagrant.specification._options import (
    is_optional_scalar_option,
    is_scalar_option,
)


class TestScalarOptionSpecificationNames:
    def test_name_returns_first_name(self) -> None:
        opt = scalar_option(["output", "o"])

        assert opt.name == "output"

    def test_long_names_filters_correctly(self) -> None:
        opt = scalar_option(["output", "o", "file"])

        assert opt.long_names == ("output", "file")

    def test_short_names_filters_correctly(self) -> None:
        opt = scalar_option(["output", "o", "f"])

        assert opt.short_names == ("o", "f")

    def test_all_names_combines_long_and_short(self) -> None:
        opt = scalar_option(["output", "o"])

        assert set(opt.all_names) == {"output", "o"}


class TestScalarOptionSpecificationArity:
    def test_default_arity_is_1(self) -> None:
        opt = scalar_option(["output"])

        assert opt.arity == 1

    def test_requires_value_true_for_arity_1(self) -> None:
        opt = scalar_option(["output"], arity=1)

        assert opt.requires_value is True

    def test_requires_value_false_for_optional_arity(self) -> None:
        opt = scalar_option(["output"], arity="?")

        assert opt.requires_value is False


class TestScalarOptionSpecificationAccumulationMode:
    def test_default_accumulation_mode_is_last(self) -> None:
        opt = scalar_option(["output"])

        assert opt.accumulation_mode == "last"


class TestScalarOptionSpecificationNegativeNumbers:
    def test_allow_negative_numbers_false_by_default(self) -> None:
        opt = scalar_option(["count"])

        assert opt.allow_negative_numbers is False


class TestScalarOptionSpecificationTypeGuards:
    def test_is_scalar_option_returns_true(self) -> None:
        opt = scalar_option(["output"])

        assert is_scalar_option(opt) is True

    def test_is_optional_scalar_option_returns_true_for_optional_arity(self) -> None:
        opt = scalar_option(["output"], arity="?")

        assert is_optional_scalar_option(opt) is True

    def test_is_optional_scalar_option_returns_false_for_required_arity(self) -> None:
        opt = scalar_option(["output"], arity=1)

        assert is_optional_scalar_option(opt) is False
