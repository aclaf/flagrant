from flagrant.specification import (
    dict_list_option,
    flat_list_option,
    nested_list_option,
)


class TestDictListOption:
    def test_creates_dict_option_with_append_mode(self) -> None:
        opt = dict_list_option(["config"])

        assert opt.name == "config"
        assert opt.accumulation_mode == "append"

    def test_accepts_custom_arity(self) -> None:
        opt = dict_list_option(["config"], arity=(1, "*"))

        assert opt.arity == (1, "*")


class TestFlatListOption:
    def test_creates_list_option_with_extend_mode(self) -> None:
        opt = flat_list_option(["files"])

        assert opt.name == "files"
        assert opt.accumulation_mode == "extend"

    def test_accepts_custom_arity(self) -> None:
        opt = flat_list_option(["files"], arity=(1, 3))

        assert opt.arity == (1, 3)


class TestNestedListOption:
    def test_creates_list_option_with_append_mode(self) -> None:
        opt = nested_list_option(["groups"])

        assert opt.name == "groups"
        assert opt.accumulation_mode == "append"

    def test_accepts_custom_arity(self) -> None:
        opt = nested_list_option(["groups"], arity="*")

        assert opt.arity == "*"
