from typing import TYPE_CHECKING, Any

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser._context import ParseContext
from flagrant.parser._handlers import ListOptionHandler
from flagrant.parser._resolver import CommandResolver, ResolvedOption
from flagrant.parser._state import ParseState
from flagrant.parser.exceptions import OptionMissingValueError
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


@pytest.mark.xfail(reason="ListOptionHandler.parse() raises NotImplementedError")
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


@pytest.mark.xfail(reason="ListOptionHandler.parse() raises NotImplementedError")
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


@pytest.mark.xfail(reason="ListOptionHandler.parse() raises NotImplementedError")
class TestListHandlerAccumulationModes:
    def test_append_mode_creates_nested_list(self) -> None:
        opt = list_option(["files"], accumulation_mode="append")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("b.txt", "c.txt"))
        resolved = make_resolved_list(opt)
        current: Any = (("a.txt",),)

        result: Any = handler.parse(
            state, ctx, resolver, resolved, current, "--files", config
        )

        # append mode should create nested list
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


@pytest.mark.xfail(reason="ListOptionHandler.parse() raises NotImplementedError")
class TestListHandlerInlineValues:
    def test_uses_inline_value(self) -> None:
        opt = list_option(["files"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ListOptionHandler()
        state = ParseState(("b.txt",))
        resolved = make_resolved_list(opt, inline="a.txt")

        result: Any = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--files=a.txt", config
        )

        # Should include inline value plus additional args
        assert "a.txt" in result
