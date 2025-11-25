from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser._context import ParseContext
from flagrant.parser._handlers import ScalarOptionHandler
from flagrant.parser._resolver import CommandResolver, ResolvedOption
from flagrant.parser._state import ParseState
from flagrant.parser.exceptions import OptionMissingValueError, OptionNotRepeatableError
from flagrant.specification import command, flag_option, scalar_option
from flagrant.types import NOT_GIVEN

if TYPE_CHECKING:
    from flagrant.specification._options import OptionType, ScalarOptionSpecification


def make_handler_context(
    options: "list[OptionType] | None" = None,
) -> tuple[ParseContext, CommandResolver, ParserConfiguration]:
    spec = command("test", options=options or [])
    config = ParserConfiguration()
    return (
        ParseContext(spec=spec, path=(spec.name,), config=config),
        CommandResolver(spec, config),
        config,
    )


def make_resolved_scalar(
    opt: "ScalarOptionSpecification",
    *,
    given_name: str | None = None,
    inline: str | None = None,
) -> ResolvedOption:
    return ResolvedOption(
        given_name=given_name or opt.name,
        resolved_name=opt.name,
        spec=opt,
        inline=inline,
    )


class TestScalarHandlerBasicParsing:
    def test_consumes_next_arg_as_value(self) -> None:
        opt = scalar_option(["output"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ScalarOptionHandler()
        state = ParseState(("file.txt",))
        resolved = make_resolved_scalar(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--output", config
        )

        assert result == "file.txt"
        assert state.is_at_end is True

    def test_returns_inline_value(self) -> None:
        opt = scalar_option(["output"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ScalarOptionHandler()
        state = ParseState(())
        resolved = make_resolved_scalar(opt, inline="file.txt")

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--output=file.txt", config
        )

        assert result == "file.txt"

    def test_inline_value_takes_precedence_over_args(self) -> None:
        opt = scalar_option(["output"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ScalarOptionHandler()
        state = ParseState(("other.txt",))
        resolved = make_resolved_scalar(opt, inline="inline.txt")

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--output=inline.txt", config
        )

        assert result == "inline.txt"
        assert state.remaining_count == 1


class TestScalarHandlerMissingValue:
    def test_raises_error_when_at_end(self) -> None:
        opt = scalar_option(["output"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ScalarOptionHandler()
        state = ParseState(())
        resolved = make_resolved_scalar(opt)

        with pytest.raises(OptionMissingValueError) as exc_info:
            handler.parse(
                state, ctx, resolver, resolved, NOT_GIVEN, "--output", config
            )

        assert exc_info.value.option == "output"

    def test_raises_error_when_next_arg_is_option(self) -> None:
        opt = scalar_option(["output"])
        verbose = scalar_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt, verbose])
        handler = ScalarOptionHandler()
        state = ParseState(("--verbose",))
        resolved = make_resolved_scalar(opt)

        with pytest.raises(OptionMissingValueError):
            handler.parse(
                state, ctx, resolver, resolved, NOT_GIVEN, "--output", config
            )


class TestScalarHandlerOptionalArity:
    def test_optional_arity_returns_none_when_at_end(self) -> None:
        opt = scalar_option(["level"], arity="?")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ScalarOptionHandler()
        state = ParseState(())
        resolved = make_resolved_scalar(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--level", config
        )

        assert result is None

    def test_optional_arity_returns_none_when_next_is_option(self) -> None:
        opt = scalar_option(["level"], arity="?")
        verbose = scalar_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt, verbose])
        handler = ScalarOptionHandler()
        state = ParseState(("--verbose",))
        resolved = make_resolved_scalar(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--level", config
        )

        assert result is None
        assert state.remaining_count == 1

    def test_optional_arity_returns_value_when_present(self) -> None:
        opt = scalar_option(["level"], arity="?")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ScalarOptionHandler()
        state = ParseState(("debug",))
        resolved = make_resolved_scalar(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--level", config
        )

        assert result == "debug"


class TestScalarHandlerAccumulationModes:
    def test_last_mode_overwrites_value(self) -> None:
        opt = scalar_option(["output"], accumulation_mode="last")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ScalarOptionHandler()
        state = ParseState(("second.txt",))
        resolved = make_resolved_scalar(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, "first.txt", "--output", config
        )

        assert result == "second.txt"

    def test_first_mode_keeps_first_value(self) -> None:
        opt = scalar_option(["output"], accumulation_mode="first")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ScalarOptionHandler()
        state = ParseState(("second.txt",))
        resolved = make_resolved_scalar(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, "first.txt", "--output", config
        )

        assert result == "first.txt"

    def test_error_mode_raises_on_second_occurrence(self) -> None:
        opt = scalar_option(["output"], accumulation_mode="error")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ScalarOptionHandler()
        state = ParseState(("second.txt",))
        resolved = make_resolved_scalar(opt)

        with pytest.raises(OptionNotRepeatableError) as exc_info:
            handler.parse(
                state, ctx, resolver, resolved, "first.txt", "--output", config
            )

        assert exc_info.value.current == "first.txt"

    def test_error_mode_allows_first_occurrence(self) -> None:
        opt = scalar_option(["output"], accumulation_mode="error")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ScalarOptionHandler()
        state = ParseState(("file.txt",))
        resolved = make_resolved_scalar(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--output", config
        )

        assert result == "file.txt"


class TestScalarHandlerTypeEnforcement:
    def test_raises_type_error_for_non_scalar_option(self) -> None:
        opt = flag_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ScalarOptionHandler()
        state = ParseState(())
        resolved = ResolvedOption(
            given_name="verbose",
            resolved_name="verbose",
            spec=opt,
        )

        with pytest.raises(
            TypeError, match="ScalarOptionHandler can only parse scalar options"
        ):
            handler.parse(
                state, ctx, resolver, resolved, NOT_GIVEN, "--verbose", config
            )


class TestScalarHandlerEdgeCases:
    def test_empty_string_via_inline(self) -> None:
        opt = scalar_option(["output"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ScalarOptionHandler()
        state = ParseState(())
        resolved = make_resolved_scalar(opt, inline="")

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--output=", config
        )

        assert result == ""

    def test_value_looks_like_option_via_inline(self) -> None:
        opt = scalar_option(["output"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ScalarOptionHandler()
        state = ParseState(())
        resolved = make_resolved_scalar(opt, inline="--file.txt")

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--output=--file.txt", config
        )

        assert result == "--file.txt"

    def test_whitespace_value(self) -> None:
        opt = scalar_option(["output"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = ScalarOptionHandler()
        state = ParseState(("   ",))
        resolved = make_resolved_scalar(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--output", config
        )

        assert result == "   "
