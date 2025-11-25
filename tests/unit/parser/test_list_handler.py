from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser._context import ParseContext
from flagrant.parser._handlers import (
    ListOptionHandler,
    _accumulate_list_values,  # pyright: ignore[reportPrivateUsage]
    _apply_item_separator,  # pyright: ignore[reportPrivateUsage]
    _split_with_escape,  # pyright: ignore[reportPrivateUsage]
)
from flagrant.parser._resolver import CommandResolver, ResolvedOption
from flagrant.parser._state import ParseState
from flagrant.parser.exceptions import OptionMissingValueError, OptionNotRepeatableError
from flagrant.specification import command, flag_option, list_option
from flagrant.types import NOT_GIVEN

if TYPE_CHECKING:
    from flagrant.specification._command import CommandSpecification
    from flagrant.specification._options import ListOptionSpecification, OptionType


def make_handler_context(
    spec: "CommandSpecification | None" = None,
    options: "list[OptionType] | None" = None,
) -> tuple[ParseContext, CommandResolver, ParserConfiguration]:
    if spec is None:
        spec = command("test", options=options or [])
    config = ParserConfiguration()
    return (
        ParseContext(spec=spec, path=(spec.name,), config=config),
        CommandResolver(spec, config),
        config,
    )


def make_resolved_list(
    option_spec: "ListOptionSpecification",
    given_name: str | None = None,
    inline: str | None = None,
) -> ResolvedOption:
    return ResolvedOption(
        given_name=given_name or option_spec.name,
        resolved_name=option_spec.name,
        spec=option_spec,
        inline=inline,
    )


class TestListHandlerTypeEnforcement:
    def test_raises_type_error_for_non_list_option(self) -> None:
        opt = flag_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(())
        resolved = ResolvedOption(
            given_name="verbose",
            resolved_name="verbose",
            spec=opt,
        )

        with pytest.raises(
            TypeError, match="ListOptionHandler can only parse list options"
        ):
            handler.parse(
                state, ctx, resolver, resolved, NOT_GIVEN, "--verbose", config
            )


class TestListHandlerBasicParsing:
    def test_consumes_multiple_values(self) -> None:
        opt = list_option(["files"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a.txt", "b.txt", "c.txt"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files", config
        )

        assert result == ("a.txt", "b.txt", "c.txt")

    def test_stops_at_next_option(self) -> None:
        opt = list_option(["files"])
        verbose = list_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt, verbose])
        handler = ListOptionHandler()
        state = ParseState(("a.txt", "b.txt", "--verbose"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files", config
        )

        # Should stop before --verbose
        assert result == ("a.txt", "b.txt")
        assert state.current == "--verbose"


class TestListHandlerArityConstraints:
    def test_respects_minimum_arity(self) -> None:
        opt = list_option(["files"], arity=(2, "*"))
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a.txt",))  # Only 1 value
        resolved = make_resolved_list(opt)

        # Should raise because minimum arity is 2
        with pytest.raises(OptionMissingValueError):
            handler.parse(state, ctx, resolver, resolved, NOT_GIVEN, "--files", config)

    def test_respects_maximum_arity(self) -> None:
        opt = list_option(["files"], arity=(1, 2))
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a.txt", "b.txt", "c.txt"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files", config
        )

        # Should only consume 2 values
        assert result == ("a.txt", "b.txt")


class TestListHandlerAccumulationModes:
    def test_append_mode_creates_nested_list(self) -> None:
        opt = list_option(["files"], accumulation_mode="append")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("b.txt", "c.txt"))
        resolved = make_resolved_list(opt)
        current: tuple[tuple[str, ...], ...] = (("a.txt",),)

        result = handler.parse(
            state, ctx, resolver, resolved, current, "--files", config
        )

        # append mode should create nested list
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == ("a.txt",)
        assert result[1] == ("b.txt", "c.txt")

    def test_extend_mode_flattens_values(self) -> None:
        opt = list_option(["files"], accumulation_mode="extend")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("b.txt", "c.txt"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, ("a.txt",), "--files", config
        )

        # extend mode should flatten
        assert result == ("a.txt", "b.txt", "c.txt")


class TestListHandlerInlineValues:
    def test_uses_inline_value(self) -> None:
        opt = list_option(["files"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("b.txt",))
        resolved = make_resolved_list(opt, inline="a.txt")

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files=a.txt", config
        )

        # Should include inline value plus additional args
        assert isinstance(result, tuple)
        assert "a.txt" in result

    def test_inline_value_only_no_additional_args(self) -> None:
        opt = list_option(["output"], arity=1)
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(())
        resolved = make_resolved_list(opt, inline="file.txt")

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--output=file.txt", config
        )

        assert result == "file.txt"

    def test_inline_value_counts_toward_arity_max(self) -> None:
        opt = list_option(["files"], arity=(1, 2))
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("b.txt", "c.txt"))
        resolved = make_resolved_list(opt, inline="a.txt")

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files=a.txt", config
        )

        assert result == ("a.txt", "b.txt")
        assert state.current == "c.txt"

    def test_inline_value_counts_toward_arity_min(self) -> None:
        opt = list_option(["files"], arity=(2, 2))
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("b.txt",))
        resolved = make_resolved_list(opt, inline="a.txt")

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files=a.txt", config
        )

        assert result == ("a.txt", "b.txt")

    def test_inline_empty_string_is_valid_value(self) -> None:
        opt = list_option(["output"], arity=1)
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(())
        resolved = make_resolved_list(opt, inline="")

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--output=", config
        )

        assert result == ""


class TestSplitWithEscape:
    def test_basic_split_no_escape(self) -> None:
        result = _split_with_escape("a,b,c", ",", None)

        assert result == ["a", "b", "c"]

    def test_split_with_escape_char(self) -> None:
        result = _split_with_escape(r"a\,b,c", ",", "\\")

        assert result == ["a,b", "c"]

    def test_escape_the_escape_char(self) -> None:
        result = _split_with_escape(r"a\\,b", ",", "\\")

        assert result == ["a\\", "b"]

    def test_no_separator_returns_single_element(self) -> None:
        result = _split_with_escape("abc", ",", None)

        assert result == ["abc"]

    def test_empty_string_returns_single_empty_element(self) -> None:
        result = _split_with_escape("", ",", None)

        assert result == [""]

    def test_trailing_separator_creates_empty_element(self) -> None:
        result = _split_with_escape("a,b,", ",", None)

        assert result == ["a", "b", ""]

    def test_leading_separator_creates_empty_element(self) -> None:
        result = _split_with_escape(",a,b", ",", None)

        assert result == ["", "a", "b"]

    def test_consecutive_separators_create_empty_elements(self) -> None:
        result = _split_with_escape("a,,b", ",", None)

        assert result == ["a", "", "b"]

    def test_escape_at_end_of_string(self) -> None:
        result = _split_with_escape("a\\", ",", "\\")

        assert result == ["a\\"]

    def test_escape_non_special_char_preserved(self) -> None:
        result = _split_with_escape(r"a\bc", ",", "\\")

        assert result == ["a\\bc"]


class TestApplyItemSeparator:
    def test_applies_to_all_values(self) -> None:
        result = _apply_item_separator(["a,b", "c,d"], ",", None)

        assert result == ["a", "b", "c", "d"]

    def test_with_escape_char(self) -> None:
        result = _apply_item_separator([r"a\,b", "c,d"], ",", "\\")

        assert result == ["a,b", "c", "d"]

    def test_empty_list_returns_empty(self) -> None:
        result = _apply_item_separator([], ",", None)

        assert result == []

    def test_single_value_without_separator(self) -> None:
        result = _apply_item_separator(["abc"], ",", None)

        assert result == ["abc"]


class TestAccumulateListValues:
    def test_append_with_no_current_value(self) -> None:
        result = _accumulate_list_values(NOT_GIVEN, ("a", "b"), "append")

        assert result == (("a", "b"),)

    def test_append_with_existing_value(self) -> None:
        current: tuple[tuple[str, ...], ...] = (("a",),)
        result = _accumulate_list_values(current, ("b", "c"), "append")

        assert result == (("a",), ("b", "c"))

    def test_extend_with_no_current_value(self) -> None:
        result = _accumulate_list_values(NOT_GIVEN, ("a", "b"), "extend")

        assert result == ("a", "b")

    def test_extend_with_existing_value(self) -> None:
        result = _accumulate_list_values(("a",), ("b", "c"), "extend")

        assert result == ("a", "b", "c")

    def test_last_mode_returns_new_values(self) -> None:
        result = _accumulate_list_values(("old",), ("new",), "last")

        assert result == ("new",)

    def test_first_mode_returns_new_values(self) -> None:
        result = _accumulate_list_values(("old",), ("new",), "first")

        assert result == ("new",)

    def test_error_mode_returns_new_values(self) -> None:
        result = _accumulate_list_values(NOT_GIVEN, ("new",), "error")

        assert result == ("new",)


class TestListHandlerArityTypes:
    def test_arity_int_exact_value_count(self) -> None:
        opt = list_option(["values"], arity=3)
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a", "b", "c", "d"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--values", config
        )

        # Integer arity > 1 returns tuple (only arity=1 is scalar)
        assert result == ("a", "b", "c")
        assert state.current == "d"

    def test_arity_int_consumes_exact_count(self) -> None:
        opt = list_option(["values"], arity=3, accumulation_mode="extend")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a", "b", "c", "d"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--values", config
        )

        # With extend mode, returns tuple
        assert result == ("a", "b", "c")
        assert state.current == "d"

    def test_arity_int_one_returns_scalar(self) -> None:
        opt = list_option(["output"], arity=1)
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("file.txt",))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--output", config
        )

        assert result == "file.txt"
        assert isinstance(result, str)

    def test_arity_optional_with_value_returns_scalar(self) -> None:
        opt = list_option(["output"], arity="?")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("file.txt",))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--output", config
        )

        assert result == "file.txt"
        assert isinstance(result, str)

    def test_arity_optional_without_value_returns_none(self) -> None:
        opt = list_option(["flag"], arity="?")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(())
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--flag", config
        )

        assert result is None

    def test_arity_star_consumes_all_until_option(self) -> None:
        opt = list_option(["files"], arity="*")
        verbose = flag_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt, verbose])
        handler = ListOptionHandler()
        state = ParseState(("a.txt", "b.txt", "--verbose"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files", config
        )

        assert result == ("a.txt", "b.txt")
        assert state.current == "--verbose"

    def test_arity_star_allows_zero_values(self) -> None:
        opt = list_option(["files"], arity="*")
        verbose = flag_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt, verbose])
        handler = ListOptionHandler()
        state = ParseState(("--verbose",))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files", config
        )

        assert result == ()

    def test_arity_ellipsis_consumes_including_option_like_strings(self) -> None:
        opt = list_option(["args"], arity="...")
        verbose = flag_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt, verbose])
        handler = ListOptionHandler()
        state = ParseState(("a", "--verbose", "b"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--args", config
        )

        assert result == ("a", "--verbose", "b")

    def test_arity_tuple_range_respects_min(self) -> None:
        opt = list_option(["values"], arity=(2, 4))
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a",))
        resolved = make_resolved_list(opt)

        with pytest.raises(OptionMissingValueError):
            handler.parse(state, ctx, resolver, resolved, NOT_GIVEN, "--values", config)

    def test_arity_tuple_range_respects_max(self) -> None:
        opt = list_option(["values"], arity=(2, 4))
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a", "b", "c", "d", "e", "f"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--values", config
        )

        assert result == ("a", "b", "c", "d")
        assert state.current == "e"

    def test_arity_tuple_with_star_unbounded_max(self) -> None:
        opt = list_option(["values"], arity=(2, "*"))
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a", "b", "c", "d", "e"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--values", config
        )

        assert result == ("a", "b", "c", "d", "e")

    def test_arity_tuple_with_ellipsis_greedy_max(self) -> None:
        opt = list_option(["args"], arity=(1, "..."))
        verbose = flag_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt, verbose])
        handler = ListOptionHandler()
        state = ParseState(("a", "--verbose", "b"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--args", config
        )

        assert result == ("a", "--verbose", "b")


class TestListHandlerAllAccumulationModes:
    def test_last_mode_replaces_previous_value(self) -> None:
        opt = list_option(["files"], arity="*", accumulation_mode="last")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("new1", "new2"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, ("old1", "old2"), "--files", config
        )

        assert result == ("new1", "new2")

    def test_first_mode_skips_when_current_exists(self) -> None:
        opt = list_option(["files"], arity="*", accumulation_mode="first")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("new1", "new2"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, ("old1", "old2"), "--files", config
        )

        assert result == ("old1", "old2")
        assert state.current == "new1"

    def test_first_mode_parses_when_no_current(self) -> None:
        opt = list_option(["files"], arity="*", accumulation_mode="first")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a", "b"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files", config
        )

        assert result == ("a", "b")

    def test_error_mode_raises_when_current_exists(self) -> None:
        opt = list_option(["files"], arity="*", accumulation_mode="error")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("new1", "new2"))
        resolved = make_resolved_list(opt)

        with pytest.raises(OptionNotRepeatableError):
            handler.parse(state, ctx, resolver, resolved, ("old1",), "--files", config)

    def test_error_mode_allows_first_occurrence(self) -> None:
        opt = list_option(["files"], arity="*", accumulation_mode="error")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a", "b"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files", config
        )

        assert result == ("a", "b")

    def test_append_mode_first_occurrence_creates_nested(self) -> None:
        opt = list_option(["files"], accumulation_mode="append")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a", "b"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files", config
        )

        assert result == (("a", "b"),)

    def test_extend_mode_first_occurrence_returns_flat(self) -> None:
        opt = list_option(["files"], accumulation_mode="extend")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a", "b"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files", config
        )

        assert result == ("a", "b")


class TestListHandlerItemSeparator:
    def test_item_separator_splits_values(self) -> None:
        opt = list_option(
            ["tags"],
            arity="*",
            allow_item_separator=True,
            item_separator=",",
        )
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a,b,c",))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--tags", config
        )

        assert result == ("a", "b", "c")

    def test_item_separator_with_escape_char(self) -> None:
        opt = list_option(
            ["tags"],
            arity="*",
            allow_item_separator=True,
            item_separator=",",
            escape_character="\\",
        )
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState((r"a\,b,c",))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--tags", config
        )

        assert result == ("a,b", "c")

    def test_item_separator_disabled_by_default(self) -> None:
        opt = list_option(["tags"], arity="*", item_separator=",")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a,b,c",))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--tags", config
        )

        assert result == ("a,b,c",)

    def test_item_separator_applied_to_inline_value(self) -> None:
        opt = list_option(
            ["tags"],
            arity="*",
            allow_item_separator=True,
            item_separator=",",
        )
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(())
        resolved = make_resolved_list(opt, inline="a,b,c")

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--tags=a,b,c", config
        )

        assert result == ("a", "b", "c")

    def test_item_separator_multiple_args_all_split(self) -> None:
        opt = list_option(
            ["tags"],
            arity="*",
            allow_item_separator=True,
            item_separator=",",
        )
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a,b", "c,d"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--tags", config
        )

        assert result == ("a", "b", "c", "d")


class TestListHandlerResultNormalization:
    def test_scalar_arity_with_last_mode_returns_scalar(self) -> None:
        opt = list_option(["output"], arity=1, accumulation_mode="last")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("file.txt",))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--output", config
        )

        assert result == "file.txt"
        assert isinstance(result, str)

    def test_scalar_arity_with_first_mode_returns_scalar(self) -> None:
        opt = list_option(["output"], arity=1, accumulation_mode="first")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("file.txt",))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--output", config
        )

        assert result == "file.txt"
        assert isinstance(result, str)

    def test_optional_arity_with_value_returns_scalar(self) -> None:
        opt = list_option(["output"], arity="?", accumulation_mode="last")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("file.txt",))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--output", config
        )

        assert result == "file.txt"
        assert isinstance(result, str)

    def test_optional_arity_without_value_returns_none(self) -> None:
        opt = list_option(["flag"], arity="?", accumulation_mode="last")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(())
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--flag", config
        )

        assert result is None

    def test_variadic_arity_returns_tuple(self) -> None:
        opt = list_option(["files"], arity="*")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a", "b"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files", config
        )

        assert result == ("a", "b")
        assert isinstance(result, tuple)

    def test_range_arity_returns_tuple(self) -> None:
        opt = list_option(["files"], arity=(2, 3))
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a", "b", "c"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files", config
        )

        assert result == ("a", "b", "c")
        assert isinstance(result, tuple)

    def test_append_mode_returns_nested_tuple(self) -> None:
        opt = list_option(["files"], arity="*", accumulation_mode="append")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("a", "b"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files", config
        )

        assert result == (("a", "b"),)


class TestListHandlerGreedyVsUnbounded:
    def test_unbounded_stops_at_known_option(self) -> None:
        opt = list_option(["files"], arity="*")
        verbose = flag_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt, verbose])
        handler = ListOptionHandler()
        state = ParseState(("a.txt", "--verbose", "b.txt"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files", config
        )

        assert result == ("a.txt",)
        assert state.current == "--verbose"

    def test_greedy_consumes_through_known_option(self) -> None:
        opt = list_option(["args"], arity="...")
        verbose = flag_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt, verbose])
        handler = ListOptionHandler()
        state = ParseState(("a.txt", "--verbose", "b.txt"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--args", config
        )

        assert result == ("a.txt", "--verbose", "b.txt")

    def test_unbounded_tuple_stops_at_known_option(self) -> None:
        opt = list_option(["files"], arity=(1, "*"))
        verbose = flag_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt, verbose])
        handler = ListOptionHandler()
        state = ParseState(("a.txt", "--verbose"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files", config
        )

        assert result == ("a.txt",)
        assert state.current == "--verbose"

    def test_greedy_tuple_consumes_through_known_option(self) -> None:
        opt = list_option(["args"], arity=(1, "..."))
        verbose = flag_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt, verbose])
        handler = ListOptionHandler()
        state = ParseState(("a.txt", "--verbose"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--args", config
        )

        assert result == ("a.txt", "--verbose")


class TestListHandlerEdgeCases:
    def test_empty_state_with_optional_arity(self) -> None:
        opt = list_option(["opt"], arity="?")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(())
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--opt", config
        )

        assert result is None

    def test_empty_state_with_star_arity(self) -> None:
        opt = list_option(["files"], arity="*")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(())
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files", config
        )

        assert result == ()

    def test_empty_state_with_required_arity_raises(self) -> None:
        opt = list_option(["files"], arity=1)
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(())
        resolved = make_resolved_list(opt)

        with pytest.raises(OptionMissingValueError):
            handler.parse(state, ctx, resolver, resolved, NOT_GIVEN, "--files", config)

    def test_single_value_with_star_arity(self) -> None:
        opt = list_option(["files"], arity="*")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("only.txt",))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files", config
        )

        assert result == ("only.txt",)

    def test_whitespace_value_preserved(self) -> None:
        opt = list_option(["values"], arity=1)
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("   ",))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--values", config
        )

        assert result == "   "

    def test_value_with_equals_sign(self) -> None:
        opt = list_option(["config"], arity=1)
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("key=value",))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        assert result == "key=value"

    def test_value_with_hyphens(self) -> None:
        opt = list_option(["pattern"], arity=1)
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("foo-bar-baz",))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--pattern", config
        )

        assert result == "foo-bar-baz"

    def test_unknown_option_like_string_consumed_as_value(self) -> None:
        opt = list_option(["values"], arity=(2, 2))
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("--unknown", "value"))
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--values", config
        )

        assert result == ("--unknown", "value")

    def test_large_number_of_values(self) -> None:
        opt = list_option(["values"], arity=(50, 50))
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        args = tuple(str(i) for i in range(1, 51))
        state = ParseState(args)
        resolved = make_resolved_list(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--values", config
        )

        assert isinstance(result, tuple)
        assert len(result) == 50
        assert result[0] == "1"
        assert result[49] == "50"


class TestListHandlerMinArityValidation:
    def test_insufficient_values_raises_error(self) -> None:
        opt = list_option(["coords"], arity=(3, 3))
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("10", "20"))
        resolved = make_resolved_list(opt)

        with pytest.raises(OptionMissingValueError) as exc_info:
            handler.parse(state, ctx, resolver, resolved, NOT_GIVEN, "--coords", config)

        assert exc_info.value.option == "coords"

    def test_insufficient_with_inline_raises_error(self) -> None:
        opt = list_option(["coords"], arity=(3, 3))
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("20",))
        resolved = make_resolved_list(opt, inline="10")

        with pytest.raises(OptionMissingValueError):
            handler.parse(
                state, ctx, resolver, resolved, NOT_GIVEN, "--coords=10", config
            )

    def test_known_option_stops_before_min_arity_satisfied(self) -> None:
        opt = list_option(["coords"], arity=(3, 3))
        verbose = flag_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt, verbose])
        handler = ListOptionHandler()
        state = ParseState(("10", "--verbose", "20"))
        resolved = make_resolved_list(opt)

        with pytest.raises(OptionMissingValueError):
            handler.parse(state, ctx, resolver, resolved, NOT_GIVEN, "--coords", config)
