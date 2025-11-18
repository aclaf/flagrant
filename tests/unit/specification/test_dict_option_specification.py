"""Unit tests for DictOptionSpecification."""

from flagrant.specification import dict_option
from flagrant.specification._options import (
    is_dict_list_option,
    is_dict_option,
)


class TestDictOptionSpecificationNames:
    def test_name_returns_first_name(self) -> None:
        opt = dict_option(["config", "c"])

        assert opt.name == "config"

    def test_long_names_filters_correctly(self) -> None:
        opt = dict_option(["config", "c", "settings"])

        assert opt.long_names == ("config", "settings")

    def test_short_names_filters_correctly(self) -> None:
        opt = dict_option(["config", "c", "s"])

        assert opt.short_names == ("c", "s")


class TestDictOptionSpecificationArity:
    def test_default_arity_is_star(self) -> None:
        opt = dict_option(["config"])

        assert opt.arity == "*"


class TestDictOptionSpecificationAccumulationMode:
    def test_default_accumulation_mode_is_merge(self) -> None:
        opt = dict_option(["config"])

        assert opt.accumulation_mode == "merge"


class TestDictOptionSpecificationIsList:
    def test_is_list_true_for_append_mode(self) -> None:
        opt = dict_option(["config"], accumulation_mode="append")

        assert opt.is_list is True

    def test_is_list_false_for_merge_mode(self) -> None:
        opt = dict_option(["config"], accumulation_mode="merge")

        assert opt.is_list is False

    def test_is_list_false_for_other_modes(self) -> None:
        for mode in ("last", "first", "error"):
            opt = dict_option(["config"], accumulation_mode=mode)  # type: ignore[arg-type]

            assert opt.is_list is False


class TestDictOptionSpecificationMergeStrategy:
    def test_default_merge_strategy_is_deep(self) -> None:
        opt = dict_option(["config"])

        assert opt.merge_strategy == "deep"


class TestDictOptionSpecificationNestingOptions:
    def test_allow_nested_true_by_default(self) -> None:
        opt = dict_option(["config"])

        assert opt.allow_nested is True


class TestDictOptionSpecificationJsonOptions:
    def test_allow_json_object_false_by_default(self) -> None:
        opt = dict_option(["config"])

        assert opt.allow_json_object is False

    def test_allow_json_list_false_by_default(self) -> None:
        opt = dict_option(["config"])

        assert opt.allow_json_list is False


class TestDictOptionSpecificationTypeGuards:
    def test_is_dict_option_returns_true(self) -> None:
        opt = dict_option(["config"])

        assert is_dict_option(opt) is True

    def test_is_dict_list_option_true_for_append_mode(self) -> None:
        opt = dict_option(["config"], accumulation_mode="append")

        assert is_dict_list_option(opt) is True

    def test_is_dict_list_option_false_for_merge_mode(self) -> None:
        opt = dict_option(["config"], accumulation_mode="merge")

        assert is_dict_list_option(opt) is False
