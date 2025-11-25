from typing import TYPE_CHECKING, Protocol
from typing_extensions import override

from flagrant.parser.exceptions import (
    OptionMissingValueError,
    OptionNotRepeatableError,
    OptionValueNotAllowedError,
)
from flagrant.specification import (
    is_counting_flag_option,
    is_flag_option,
    is_greedy_arity,
    is_list_option,
    is_nested_list_option,
    is_scalar_option,
)
from flagrant.types import is_given

if TYPE_CHECKING:
    from flagrant.configuration import ParserConfiguration
    from flagrant.parser._context import ParseContext
    from flagrant.parser._resolver import CommandResolver, ResolvedOption
    from flagrant.parser._state import ParseState
    from flagrant.types import Arg, OptionValue


class Handler(Protocol):
    def parse(  # noqa: PLR0913
        self,
        state: "ParseState",
        context: "ParseContext",
        resolver: "CommandResolver",
        option: "ResolvedOption",
        current: "OptionValue",
        arg: "Arg",
        config: "ParserConfiguration",
    ) -> "OptionValue": ...


class DictOptionHandler(Handler):
    @override
    def parse(
        self,
        state: "ParseState",
        context: "ParseContext",
        resolver: "CommandResolver",
        option: "ResolvedOption",
        current: "OptionValue",
        arg: "Arg",
        config: "ParserConfiguration",
    ) -> "OptionValue":
        raise NotImplementedError()


class FlagOptionHandler(Handler):
    @override
    def parse(
        self,
        state: "ParseState",
        context: "ParseContext",
        resolver: "CommandResolver",
        option: "ResolvedOption",
        current: "OptionValue",
        arg: "Arg",
        config: "ParserConfiguration",
    ) -> "OptionValue":
        if not is_flag_option(option.spec):
            msg = (
                "FlagOptionHandler can only parse flag options."
                f" Got option of type: {type(option.spec).__name__}"
            )
            raise TypeError(msg)

        if option.inline is not None:
            raise OptionValueNotAllowedError(
                option.given_name,
                option.inline,
                path=context.path,
                args=state.args,
                position=state.position,
            )

        negative_names = option.spec.negative_names
        name = option.resolved_name
        is_positive = name not in negative_names if negative_names is not None else True

        if is_counting_flag_option(option.spec):
            current_count = current if isinstance(current, int) else 0
            return current_count + (1 if is_positive else -1)

        return is_positive


class ListOptionHandler(Handler):
    @override
    def parse(
        self,
        state: "ParseState",
        context: "ParseContext",
        resolver: "CommandResolver",
        option: "ResolvedOption",
        current: "OptionValue",
        arg: "Arg",
        config: "ParserConfiguration",
    ) -> "OptionValue":
        if not is_list_option(option.spec) and not is_nested_list_option(option.spec):
            msg = (
                "ListOptionHandler can only parse list options."
                f" Got option of type: {type(option.spec).__name__}"
            )
            raise TypeError(msg)

        if option.spec.accumulation_mode == "error" and is_given(current):
            raise OptionNotRepeatableError(
                option.given_name,
                current,
                option.inline or state.peek(1) or None,
                context.path,
                state.args,
                state.position,
            )

        if option.spec.accumulation_mode == "first" and is_given(current):
            return current

        min_args = option.spec.get_min_args(inline=option.inline is not None)
        max_args = option.spec.get_max_args(inline=option.inline is not None)
        values: list[str] = [option.inline] if option.inline is not None else []
        for next_arg in state.peek_n(
            max_args if max_args is not None else state.remaining_count()
        ):
            if resolver.is_option_or_subcommand(next_arg) and not is_greedy_arity(
                option.spec.arity
            ):
                break
            values.append(state.consume())

        raise NotImplementedError()


class ScalarOptionHandler(Handler):
    @override
    def parse(
        self,
        state: "ParseState",
        context: "ParseContext",
        resolver: "CommandResolver",
        option: "ResolvedOption",
        current: "OptionValue",
        arg: "Arg",
        config: "ParserConfiguration",
    ) -> "OptionValue":
        if not is_scalar_option(option.spec):
            msg = (
                "ScalarOptionHandler can only parse scalar options."
                f" Got option of type: {type(option.spec).__name__}"
            )
            raise TypeError(msg)

        if is_given(current) and option.spec.accumulation_mode == "error":
            raise OptionNotRepeatableError(
                option.given_name,
                current,
                option.inline or state.peek(1) or None,
                context.path,
                state.args,
                state.position,
            )

        if is_given(current) and option.spec.accumulation_mode == "first":
            return current

        if (
            option.spec.requires_value
            and option.inline is None
            and (state.is_at_end or resolver.is_option_or_subcommand(state.current))
        ):
            raise OptionMissingValueError(
                option.given_name,
                option.spec.arity,
                state.current,
                context.path,
                state.args,
                state.position,
            )

        if option.inline is not None:
            value = option.inline
        elif not state.is_at_end and not resolver.is_option_or_subcommand(
            state.current
        ):
            value = state.consume()
        else:
            value = None

        return value
