from flagrant.types import (
    NOT_GIVEN,
    is_counting_flag_option_value,
    is_dict_list_option_value,
    is_dict_option_value,
    is_flag_option_value,
    is_given,
    is_list_option_value,
    is_nested_list_option_value,
    is_not_given,
    is_null_option_value,
    is_scalar_option_value,
)


class TestIsGiven:
    def test_returns_true_for_string(self) -> None:
        assert is_given("value") is True

    def test_returns_true_for_none(self) -> None:
        assert is_given(None) is True

    def test_returns_false_for_not_given(self) -> None:
        assert is_given(NOT_GIVEN) is False


class TestIsNotGiven:
    def test_returns_true_for_not_given(self) -> None:
        assert is_not_given(NOT_GIVEN) is True

    def test_returns_false_for_string(self) -> None:
        assert is_not_given("value") is False


class TestIsDictOptionValue:
    def test_returns_true_for_dict(self) -> None:
        assert is_dict_option_value({"key": "value"}) is True

    def test_returns_false_for_string(self) -> None:
        assert is_dict_option_value("value") is False


class TestIsDictListOptionValue:
    def test_returns_true_for_tuple_of_dicts(self) -> None:
        assert is_dict_list_option_value(({"a": "1"}, {"b": "2"})) is True

    def test_returns_false_for_tuple_of_strings(self) -> None:
        value: object = ("a", "b")
        assert is_dict_list_option_value(value) is False

    def test_returns_false_for_string(self) -> None:
        value: object = "value"
        assert is_dict_list_option_value(value) is False


class TestIsFlagOptionValue:
    def test_returns_true_for_bool(self) -> None:
        assert is_flag_option_value(True) is True
        assert is_flag_option_value(False) is True

    def test_returns_false_for_int(self) -> None:
        value: object = 1
        assert is_flag_option_value(value) is False


class TestIsCountingFlagOptionValue:
    def test_returns_true_for_int(self) -> None:
        assert is_counting_flag_option_value(5) is True

    def test_returns_false_for_bool(self) -> None:
        value: object = True
        assert is_counting_flag_option_value(value) is False

    def test_returns_false_for_string(self) -> None:
        value: object = "5"
        assert is_counting_flag_option_value(value) is False


class TestIsListOptionValue:
    def test_returns_true_for_tuple_of_strings(self) -> None:
        assert is_list_option_value(("a", "b", "c")) is True

    def test_returns_false_for_tuple_of_ints(self) -> None:
        value: object = (1, 2, 3)
        assert is_list_option_value(value) is False  # pyright: ignore[reportArgumentType]


class TestIsNestedListOptionValue:
    def test_returns_true_for_nested_tuples(self) -> None:
        assert is_nested_list_option_value((("a", "b"), ("c",))) is True

    def test_returns_false_for_flat_tuple(self) -> None:
        value: object = ("a", "b")
        assert is_nested_list_option_value(value) is False


class TestIsScalarOptionValue:
    def test_returns_true_for_string(self) -> None:
        assert is_scalar_option_value("value") is True

    def test_returns_false_for_int(self) -> None:
        value: object = 5
        assert is_scalar_option_value(value) is False


class TestIsNullOptionValue:
    def test_returns_true_for_none(self) -> None:
        assert is_null_option_value(None) is True

    def test_returns_false_for_string(self) -> None:
        value: object = "value"
        assert is_null_option_value(value) is False
