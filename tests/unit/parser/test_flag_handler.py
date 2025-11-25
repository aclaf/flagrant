from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser._context import ParseContext
from flagrant.parser._handlers import FlagOptionHandler
from flagrant.parser._resolver import CommandResolver, ResolvedOption
from flagrant.parser._state import ParseState
from flagrant.parser.exceptions import OptionValueNotAllowedError
from flagrant.specification import command, flag_option, scalar_option
from flagrant.types import NOT_GIVEN

if TYPE_CHECKING:
    from flagrant.specification._options import FlagOptionSpecification, OptionType


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


def make_resolved_flag(
    opt: "FlagOptionSpecification",
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


class TestFlagHandlerBasicParsing:
    def test_returns_true_for_flag(self) -> None:
        opt = flag_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = FlagOptionHandler()
        state = ParseState(("--verbose",))
        resolved = make_resolved_flag(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--verbose", config
        )

        assert result is True

    def test_returns_true_regardless_of_current_value(self) -> None:
        opt = flag_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = FlagOptionHandler()
        state = ParseState(("--verbose",))
        resolved = make_resolved_flag(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, False, "--verbose", config
        )

        assert result is True


class TestFlagHandlerNegativeFlags:
    def test_returns_false_for_negative_flag(self) -> None:
        opt = flag_option(["verbose"], negative_names=("no-verbose",))
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = FlagOptionHandler()
        state = ParseState(("--no-verbose",))
        resolved = ResolvedOption(
            given_name="no-verbose",
            resolved_name="no-verbose",
            spec=opt,
        )

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--no-verbose", config
        )

        assert result is False

    def test_returns_true_for_positive_with_negative_defined(self) -> None:
        opt = flag_option(["verbose"], negative_names=("no-verbose",))
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = FlagOptionHandler()
        state = ParseState(("--verbose",))
        resolved = make_resolved_flag(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--verbose", config
        )

        assert result is True


class TestFlagHandlerInlineValueRejection:
    def test_raises_error_for_inline_value(self) -> None:
        opt = flag_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = FlagOptionHandler()
        state = ParseState(("--verbose=true",))
        resolved = make_resolved_flag(opt, inline="true")

        with pytest.raises(OptionValueNotAllowedError) as exc_info:
            handler.parse(
                state, ctx, resolver, resolved, NOT_GIVEN, "--verbose=true", config
            )

        assert exc_info.value.option == "verbose"
        assert exc_info.value.received == "true"

    def test_raises_error_for_empty_inline_value(self) -> None:
        opt = flag_option(["verbose"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = FlagOptionHandler()
        state = ParseState(("--verbose=",))
        resolved = make_resolved_flag(opt, inline="")

        with pytest.raises(OptionValueNotAllowedError):
            handler.parse(
                state, ctx, resolver, resolved, NOT_GIVEN, "--verbose=", config
            )


class TestFlagHandlerTypeEnforcement:
    def test_raises_type_error_for_non_flag_option(self) -> None:
        opt = scalar_option(["output"])
        ctx, resolver, config = make_handler_context(options=[opt])  # type: ignore[list-item]
        handler = FlagOptionHandler()
        state = ParseState(("--output", "file.txt"))
        resolved = ResolvedOption(
            given_name="output",
            resolved_name="output",
            spec=opt,
        )

        with pytest.raises(
            TypeError, match="FlagOptionHandler can only parse flag options"
        ):
            handler.parse(state, ctx, resolver, resolved, NOT_GIVEN, "--output", config)


class TestCountingFlagHandler:
    def test_increments_count_from_not_given(self) -> None:
        opt = flag_option(["verbose", "v"], accumulation_mode="count")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = FlagOptionHandler()
        state = ParseState(("-v",))
        resolved = make_resolved_flag(opt, given_name="v")

        result = handler.parse(state, ctx, resolver, resolved, NOT_GIVEN, "-v", config)

        assert result == 1

    def test_increments_count_from_zero(self) -> None:
        opt = flag_option(["verbose", "v"], accumulation_mode="count")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = FlagOptionHandler()
        state = ParseState(("-v",))
        resolved = make_resolved_flag(opt, given_name="v")

        result = handler.parse(state, ctx, resolver, resolved, 0, "-v", config)

        assert result == 1

    def test_increments_existing_count(self) -> None:
        opt = flag_option(["verbose", "v"], accumulation_mode="count")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = FlagOptionHandler()
        state = ParseState(("-v",))
        resolved = make_resolved_flag(opt, given_name="v")

        result = handler.parse(state, ctx, resolver, resolved, 2, "-v", config)

        assert result == 3

    def test_negative_counting_flag_is_noop(self) -> None:
        opt = flag_option(
            ["verbose", "v"],
            accumulation_mode="count",
            negative_names=("quiet", "q"),
        )
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = FlagOptionHandler()
        state = ParseState(("-q",))
        resolved = ResolvedOption(
            given_name="q",
            resolved_name="q",
            spec=opt,
        )

        result = handler.parse(state, ctx, resolver, resolved, 2, "-q", config)

        assert result == 2

    def test_counting_flag_handles_non_int_current(self) -> None:
        opt = flag_option(["verbose", "v"], accumulation_mode="count")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = FlagOptionHandler()
        state = ParseState(("-v",))
        resolved = make_resolved_flag(opt, given_name="v")

        result = handler.parse(
            state, ctx, resolver, resolved, "not an int", "-v", config
        )

        assert result == 1


class TestCountingFlagNegativeNoOp:
    def test_negative_flag_does_not_decrement_from_not_given(self) -> None:
        opt = flag_option(
            ["verbose", "v"],
            accumulation_mode="count",
            negative_names=("quiet", "q"),
        )
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = FlagOptionHandler()
        state = ParseState(("-q",))
        resolved = ResolvedOption(
            given_name="q",
            resolved_name="q",
            spec=opt,
        )

        result = handler.parse(state, ctx, resolver, resolved, NOT_GIVEN, "-q", config)

        assert result == 0

    def test_negative_flag_does_not_decrement_from_zero(self) -> None:
        opt = flag_option(
            ["verbose", "v"],
            accumulation_mode="count",
            negative_names=("quiet", "q"),
        )
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = FlagOptionHandler()
        state = ParseState(("-q",))
        resolved = ResolvedOption(
            given_name="q",
            resolved_name="q",
            spec=opt,
        )

        result = handler.parse(state, ctx, resolver, resolved, 0, "-q", config)

        assert result == 0

    def test_negative_flag_does_not_go_below_zero(self) -> None:
        opt = flag_option(
            ["verbose", "v"],
            accumulation_mode="count",
            negative_names=("quiet", "q"),
        )
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = FlagOptionHandler()
        state = ParseState(("--quiet",))
        resolved = ResolvedOption(
            given_name="quiet",
            resolved_name="quiet",
            spec=opt,
        )

        result = handler.parse(state, ctx, resolver, resolved, 1, "--quiet", config)

        assert result == 1

    def test_negative_flag_preserves_positive_count(self) -> None:
        opt = flag_option(
            ["verbose", "v"],
            accumulation_mode="count",
            negative_names=("quiet", "q"),
        )
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = FlagOptionHandler()
        state = ParseState(("-q",))
        resolved = ResolvedOption(
            given_name="q",
            resolved_name="q",
            spec=opt,
        )

        result = handler.parse(state, ctx, resolver, resolved, 5, "-q", config)

        assert result == 5
