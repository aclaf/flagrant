"""Unit tests for ListOptionSpecification."""

from flagrant.specification import list_option
from flagrant.specification._options import (
    is_list_option,
    is_nested_list_option,
)


class TestListOptionSpecificationNames:
    def test_name_returns_first_name(self) -> None:
        opt = list_option(["files", "f"])

        assert opt.name == "files"

    def test_long_names_filters_correctly(self) -> None:
        opt = list_option(["files", "f", "inputs"])

        assert opt.long_names == ("files", "inputs")

    def test_short_names_filters_correctly(self) -> None:
        opt = list_option(["files", "f", "i"])

        assert opt.short_names == ("f", "i")


class TestListOptionSpecificationArity:
    def test_default_arity_is_star(self) -> None:
        opt = list_option(["files"])

        assert opt.arity == "*"


class TestListOptionSpecificationGetMinMaxArgs:
    def test_get_min_args_star_returns_zero(self) -> None:
        opt = list_option(["files"], arity="*")

        assert opt.get_min_args() == 0

    def test_get_min_args_one_or_more_returns_one(self) -> None:
        opt = list_option(["files"], arity=(1, "*"))

        assert opt.get_min_args() == 1

    def test_get_min_args_explicit_number(self) -> None:
        opt = list_option(["files"], arity=3)

        assert opt.get_min_args() == 3

    def test_get_min_args_tuple_returns_first(self) -> None:
        opt = list_option(["files"], arity=(2, 5))

        assert opt.get_min_args() == 2

    def test_get_min_args_with_inline_subtracts_one(self) -> None:
        opt = list_option(["files"], arity=3)

        assert opt.get_min_args(inline=True) == 2

    def test_get_max_args_star_returns_none(self) -> None:
        opt = list_option(["files"], arity="*")

        assert opt.get_max_args() is None

    def test_get_max_args_one_or_more_returns_none(self) -> None:
        opt = list_option(["files"], arity=(1, "*"))

        assert opt.get_max_args() is None

    def test_get_max_args_explicit_number(self) -> None:
        opt = list_option(["files"], arity=3)

        assert opt.get_max_args() == 3

    def test_get_max_args_tuple_returns_second(self) -> None:
        opt = list_option(["files"], arity=(2, 5))

        assert opt.get_max_args() == 5

    def test_get_max_args_with_inline_subtracts_one(self) -> None:
        opt = list_option(["files"], arity=3)

        assert opt.get_max_args(inline=True) == 2


class TestListOptionSpecificationAccumulationMode:
    def test_default_accumulation_mode_is_last(self) -> None:
        opt = list_option(["files"])

        assert opt.accumulation_mode == "last"


class TestListOptionSpecificationIsNested:
    def test_is_nested_true_for_append_mode(self) -> None:
        opt = list_option(["files"], accumulation_mode="append")

        assert opt.is_nested is True

    def test_is_nested_false_for_other_modes(self) -> None:
        for mode in ("last", "first", "extend", "error"):
            opt = list_option(["files"], accumulation_mode=mode)  # type: ignore[arg-type]

            assert opt.is_nested is False


class TestListOptionSpecificationTypeGuards:
    def test_is_list_option_returns_true(self) -> None:
        opt = list_option(["files"])

        assert is_list_option(opt) is True

    def test_is_nested_list_option_true_for_append_mode(self) -> None:
        opt = list_option(["files"], accumulation_mode="append")

        assert is_nested_list_option(opt) is True

    def test_is_nested_list_option_false_for_other_modes(self) -> None:
        opt = list_option(["files"], accumulation_mode="extend")

        assert is_nested_list_option(opt) is False
