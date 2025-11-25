import pytest

from flagrant.specification._arity import (
    get_arity_max,
    get_arity_min,
    is_fixed_range_arity,
    is_greedy_arity,
    is_optional_arity,
    is_optional_scalar_arity,
    is_scalar_arity,
    is_unbounded_arity,
    is_variadic_arity,
    is_zero_arity,
    validate_arity,
)


class TestGetArityMin:
    def test_integer_returns_itself(self) -> None:
        assert get_arity_min(0) == 0
        assert get_arity_min(1) == 1
        assert get_arity_min(5) == 5

    def test_optional_returns_zero(self) -> None:
        assert get_arity_min("?") == 0

    def test_unbounded_returns_zero(self) -> None:
        assert get_arity_min("*") == 0

    def test_greedy_returns_zero(self) -> None:
        assert get_arity_min("...") == 0

    def test_fixed_tuple_returns_first_element(self) -> None:
        assert get_arity_min((1, 3)) == 1
        assert get_arity_min((0, 5)) == 0
        assert get_arity_min((2, 2)) == 2

    def test_unbounded_tuple_returns_first_element(self) -> None:
        assert get_arity_min((1, "*")) == 1
        assert get_arity_min((2, "...")) == 2


class TestGetArityMax:
    def test_integer_returns_itself(self) -> None:
        assert get_arity_max(0) == 0
        assert get_arity_max(1) == 1
        assert get_arity_max(5) == 5

    def test_optional_returns_one(self) -> None:
        assert get_arity_max("?") == 1

    def test_unbounded_returns_none(self) -> None:
        assert get_arity_max("*") is None

    def test_greedy_returns_none(self) -> None:
        assert get_arity_max("...") is None

    def test_fixed_tuple_returns_second_element(self) -> None:
        assert get_arity_max((1, 3)) == 3
        assert get_arity_max((0, 5)) == 5
        assert get_arity_max((2, 2)) == 2

    def test_unbounded_tuple_returns_none(self) -> None:
        assert get_arity_max((1, "*")) is None
        assert get_arity_max((2, "...")) is None


class TestIsGreedyArity:
    def test_greedy_literal_returns_true(self) -> None:
        assert is_greedy_arity("...") is True

    def test_greedy_tuple_returns_true(self) -> None:
        assert is_greedy_arity((1, "...")) is True
        assert is_greedy_arity((0, "...")) is True

    def test_non_greedy_returns_false(self) -> None:
        assert is_greedy_arity(0) is False
        assert is_greedy_arity(1) is False
        assert is_greedy_arity("?") is False
        assert is_greedy_arity("*") is False
        assert is_greedy_arity((1, 3)) is False
        assert is_greedy_arity((1, "*")) is False


class TestIsFixedRangeArity:
    def test_int_tuple_returns_true(self) -> None:
        assert is_fixed_range_arity((1, 3)) is True
        assert is_fixed_range_arity((0, 5)) is True
        assert is_fixed_range_arity((2, 2)) is True

    def test_unbounded_tuple_returns_false(self) -> None:
        assert is_fixed_range_arity((1, "*")) is False
        assert is_fixed_range_arity((2, "...")) is False

    def test_non_tuple_returns_false(self) -> None:
        assert is_fixed_range_arity(1) is False
        assert is_fixed_range_arity("?") is False
        assert is_fixed_range_arity("*") is False
        assert is_fixed_range_arity("...") is False


class TestIsOptionalArity:
    def test_optional_literal_returns_true(self) -> None:
        assert is_optional_arity("?") is True

    def test_zero_returns_true(self) -> None:
        assert is_optional_arity(0) is True

    def test_unbounded_returns_true(self) -> None:
        assert is_optional_arity("*") is True
        assert is_optional_arity("...") is True

    def test_tuple_with_zero_min_returns_true(self) -> None:
        assert is_optional_arity((0, 5)) is True
        assert is_optional_arity((0, "*")) is True

    def test_required_returns_false(self) -> None:
        assert is_optional_arity(1) is False
        assert is_optional_arity(5) is False
        assert is_optional_arity((1, 3)) is False
        assert is_optional_arity((2, "*")) is False


class TestIsOptionalScalarArity:
    def test_optional_literal_returns_true(self) -> None:
        assert is_optional_scalar_arity("?") is True

    def test_integer_returns_false(self) -> None:
        assert is_optional_scalar_arity(0) is False
        assert is_optional_scalar_arity(1) is False

    def test_other_literals_return_false(self) -> None:
        assert is_optional_scalar_arity("*") is False
        assert is_optional_scalar_arity("...") is False

    def test_tuples_return_false(self) -> None:
        assert is_optional_scalar_arity((0, 1)) is False
        assert is_optional_scalar_arity((1, "*")) is False


class TestIsScalarArity:
    def test_integer_returns_true(self) -> None:
        assert is_scalar_arity(0) is True
        assert is_scalar_arity(1) is True
        assert is_scalar_arity(5) is True

    def test_optional_returns_true(self) -> None:
        assert is_scalar_arity("?") is True

    def test_variadic_returns_false(self) -> None:
        assert is_scalar_arity("*") is False
        assert is_scalar_arity("...") is False
        assert is_scalar_arity((1, 3)) is False
        assert is_scalar_arity((1, "*")) is False
        assert is_scalar_arity((2, "...")) is False


class TestIsUnboundedArity:
    def test_unbounded_literal_returns_true(self) -> None:
        assert is_unbounded_arity("*") is True

    def test_unbounded_tuple_returns_true(self) -> None:
        assert is_unbounded_arity((1, "*")) is True
        assert is_unbounded_arity((0, "*")) is True

    def test_bounded_returns_false(self) -> None:
        assert is_unbounded_arity(0) is False
        assert is_unbounded_arity(1) is False
        assert is_unbounded_arity("?") is False
        assert is_unbounded_arity("...") is False
        assert is_unbounded_arity((1, 3)) is False
        assert is_unbounded_arity((2, "...")) is False


class TestIsVariadicArity:
    def test_list_forms_return_true(self) -> None:
        assert is_variadic_arity("*") is True
        assert is_variadic_arity("...") is True
        assert is_variadic_arity((1, 3)) is True
        assert is_variadic_arity((1, "*")) is True
        assert is_variadic_arity((2, "...")) is True

    def test_scalar_forms_return_false(self) -> None:
        assert is_variadic_arity(0) is False
        assert is_variadic_arity(1) is False
        assert is_variadic_arity(5) is False
        assert is_variadic_arity("?") is False


class TestIsZeroArity:
    def test_zero_returns_true(self) -> None:
        assert is_zero_arity(0) is True

    def test_nonzero_returns_false(self) -> None:
        assert is_zero_arity(1) is False
        assert is_zero_arity(5) is False
        assert is_zero_arity("?") is False
        assert is_zero_arity("*") is False
        assert is_zero_arity("...") is False
        assert is_zero_arity((0, 1)) is False
        assert is_zero_arity((1, "*")) is False


class TestValidateArity:
    def test_valid_integer_passes(self) -> None:
        validate_arity(0)
        validate_arity(1)
        validate_arity(100)

    def test_valid_literals_pass(self) -> None:
        validate_arity("?")
        validate_arity("*")
        validate_arity("...")

    def test_valid_tuples_pass(self) -> None:
        validate_arity((0, 1))
        validate_arity((1, 5))
        validate_arity((2, 2))
        validate_arity((0, "*"))
        validate_arity((1, "..."))

    def test_negative_integer_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            validate_arity(-1)

        with pytest.raises(ValueError, match="non-negative"):
            validate_arity(-100)

    def test_negative_tuple_min_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            validate_arity((-1, 5))

    def test_tuple_max_less_than_min_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="max must be >= min"):
            validate_arity((5, 3))

        with pytest.raises(ValueError, match="max must be >= min"):
            validate_arity((10, 1))

    def test_tuple_with_equal_min_max_passes(self) -> None:
        validate_arity((0, 0))
        validate_arity((5, 5))

    def test_tuple_with_unbounded_max_passes(self) -> None:
        validate_arity((5, "*"))
        validate_arity((10, "..."))
