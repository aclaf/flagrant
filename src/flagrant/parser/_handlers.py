from typing import TYPE_CHECKING, Protocol, cast
from typing_extensions import override

from flagrant.parser.exceptions import (
    OptionMissingValueError,
    OptionNotRepeatableError,
    OptionValueNotAllowedError,
)
from flagrant.specification import (
    get_arity_min,
    is_counting_flag_option,
    is_dict_option,
    is_flag_option,
    is_greedy_arity,
    is_list_option,
    is_nested_list_option,
    is_scalar_option,
)
from flagrant.specification._arity import get_arity_max
from flagrant.types import DictOptionValue, is_given

if TYPE_CHECKING:
    from flagrant.configuration import ParserConfiguration
    from flagrant.parser._context import ParseContext
    from flagrant.parser._resolver import CommandResolver, ResolvedOption
    from flagrant.parser._state import ParseState
    from flagrant.specification import DictOptionSpecification, ListOptionSpecification
    from flagrant.types import Arg, OptionValue


def _split_with_escape(
    value: str, separator: str, escape_char: str | None
) -> list[str]:
    """Split a value on separator, respecting escape character.

    Args:
        value: The string to split.
        separator: The separator character to split on.
        escape_char: The escape character, or None if escaping is disabled.

    Returns:
        List of split values with escape sequences resolved.
    """
    if escape_char is None:
        return value.split(separator)

    result: list[str] = []
    current: list[str] = []
    i = 0
    while i < len(value):
        char = value[i]
        if char == escape_char and i + 1 < len(value):
            next_char = value[i + 1]
            if next_char in (separator, escape_char):
                current.append(next_char)
                i += 2
                continue
        if char == separator:
            result.append("".join(current))
            current = []
        else:
            current.append(char)
        i += 1
    result.append("".join(current))
    return result


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


def _parse_key_value(
    value: str,
    separator: str,
) -> tuple[str, str]:
    """Parse a key=value string into (key, value) tuple.

    Args:
        value: The raw string to parse.
        separator: The key-value separator (default "=").

    Returns:
        Tuple of (key, value).

    Raises:
        ValueError: If no separator found.
    """
    if separator not in value:
        msg = f"Expected key{separator}value format, got: {value!r}"
        raise ValueError(msg)
    key, _, val = value.partition(separator)
    return (key, val)


def _accumulate_dict_values(
    current: "OptionValue",
    new_dict: "DictOptionValue",
    mode: str,
) -> "OptionValue":
    """Apply accumulation mode to combine current and new dict values."""
    match mode:
        case "append":
            # Build tuple of dicts
            if is_given(current) and isinstance(current, tuple):
                prev = cast("tuple[DictOptionValue, ...]", current)
                return (*prev, new_dict)
            return (new_dict,)
        case "merge":
            # Shallow merge for MVP (deep merge in Stage 4)
            if is_given(current) and isinstance(current, dict):
                return {**current, **new_dict}
            return new_dict
        case "last":
            # Replace entire dict
            return new_dict
        case _:
            # first and error modes - handled before calling this
            return new_dict


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
        if not is_dict_option(option.spec):
            msg = (
                "DictOptionHandler can only parse dict options."
                f" Got option of type: {type(option.spec).__name__}"
            )
            raise TypeError(msg)

        spec = option.spec

        if spec.accumulation_mode == "error" and is_given(current):
            raise OptionNotRepeatableError(
                option.given_name,
                current,
                option.inline or state.peek(1) or None,
                context.path,
                state.args,
                state.position,
            )

        if spec.accumulation_mode == "first" and is_given(current):
            return current

        values = self._collect_values(state, resolver, option, spec)
        self._validate_min_arity(values, option, context, state, spec)

        try:
            new_dict = self._parse_values_to_dict(values, spec)
        except ValueError as e:
            separator = spec.key_value_separator or "="
            msg = (
                f"Option '{option.given_name}' requires key{separator}value format. {e}"
            )
            raise ValueError(msg) from e

        return _accumulate_dict_values(current, new_dict, spec.accumulation_mode)

    def _collect_values(
        self,
        state: "ParseState",
        resolver: "CommandResolver",
        option: "ResolvedOption",
        spec: "DictOptionSpecification",
    ) -> list[str]:
        """Collect values from state according to arity constraints."""
        arity_max = get_arity_max(spec.arity)
        inline_offset = 1 if option.inline is not None else 0
        max_args = arity_max - inline_offset if arity_max is not None else None
        is_greedy = is_greedy_arity(spec.arity)
        values: list[str] = [option.inline] if option.inline is not None else []

        for next_arg in state.peek_n(
            max_args if max_args is not None else state.remaining_count
        ):
            # Short-circuit: greedy mode consumes all args regardless of options
            if not is_greedy and resolver.is_option_or_subcommand(next_arg):
                break
            values.append(state.consume())

        return values

    def _validate_min_arity(
        self,
        values: list[str],
        option: "ResolvedOption",
        context: "ParseContext",
        state: "ParseState",
        spec: "DictOptionSpecification",
    ) -> None:
        """Validate that collected values meet minimum arity requirement."""
        min_args = get_arity_min(spec.arity)

        if len(values) < min_args:
            raise OptionMissingValueError(
                option.given_name,
                spec.arity,
                tuple(values) if values else None,
                context.path,
                state.args,
                state.position,
            )

    def _parse_values_to_dict(
        self,
        values: list[str],
        spec: "DictOptionSpecification",
    ) -> DictOptionValue:
        """Parse list of key=value strings into a dictionary."""
        separator = spec.key_value_separator or "="
        result: DictOptionValue = {}
        for value in values:
            key, val = _parse_key_value(value, separator)
            result[key] = val
        return result


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
            return current_count + 1 if is_positive else current_count

        return is_positive


def _apply_item_separator(
    values: list[str],
    separator: str,
    escape_char: str | None,
) -> list[str]:
    """Apply item separator splitting to a list of values."""
    result: list[str] = []
    for v in values:
        result.extend(_split_with_escape(v, separator, escape_char))
    return result


def _accumulate_list_values(
    current: "OptionValue",
    new_values: tuple[str, ...],
    mode: str,
) -> "OptionValue":
    """Apply accumulation mode to combine current and new list values."""
    match mode:
        case "append":
            # Nest as tuple of tuples: (*current, new_values)
            if is_given(current) and isinstance(current, tuple):
                prev = cast("tuple[tuple[str, ...], ...]", current)
                return (*prev, new_values)
            return (new_values,)
        case "extend":
            # Flatten: (*current, *new_values)
            if is_given(current) and isinstance(current, tuple):
                prev_flat = cast("tuple[str, ...]", current)
                return (*prev_flat, *new_values)
            return new_values
        case _:
            # last, first, error all return new_values directly
            return new_values


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

        values = self._collect_values(state, resolver, option)
        values = self._apply_separator_if_enabled(values, option)
        self._validate_min_arity(values, option, context, state)

        return self._normalize_result(values, option, current)

    def _collect_values(
        self,
        state: "ParseState",
        resolver: "CommandResolver",
        option: "ResolvedOption",
    ) -> list[str]:
        """Collect values from state according to arity constraints."""
        spec = cast("ListOptionSpecification", option.spec)
        max_args = spec.get_max_args(inline=option.inline is not None)
        is_greedy = is_greedy_arity(spec.arity)
        values: list[str] = [option.inline] if option.inline is not None else []

        for next_arg in state.peek_n(
            max_args if max_args is not None else state.remaining_count
        ):
            # Short-circuit: greedy mode consumes all args regardless of options
            if not is_greedy and resolver.is_option_or_subcommand(next_arg):
                break
            values.append(state.consume())

        return values

    def _apply_separator_if_enabled(
        self,
        values: list[str],
        option: "ResolvedOption",
    ) -> list[str]:
        """Apply item separator splitting if configured."""
        spec = cast("ListOptionSpecification", option.spec)
        if spec.allow_item_separator and spec.item_separator is not None:
            return _apply_item_separator(
                values, spec.item_separator, spec.escape_character
            )
        return values

    def _validate_min_arity(
        self,
        values: list[str],
        option: "ResolvedOption",
        context: "ParseContext",
        state: "ParseState",
    ) -> None:
        """Validate that collected values meet minimum arity requirement."""
        spec = cast("ListOptionSpecification", option.spec)
        min_args = spec.get_min_args(inline=option.inline is not None)

        if len(values) < min_args:
            raise OptionMissingValueError(
                option.given_name,
                spec.arity,
                tuple(values) if values else None,
                context.path,
                state.args,
                state.position,
            )

    def _normalize_result(
        self,
        values: list[str],
        option: "ResolvedOption",
        current: "OptionValue",
    ) -> "OptionValue":
        """Normalize result shape based on arity and accumulation mode."""
        spec = cast("ListOptionSpecification", option.spec)

        # Only arity=1 or "?" with last/first returns scalar string
        # (integers > 1 return tuple per spec)
        if spec.arity in (1, "?") and spec.accumulation_mode in ("last", "first"):
            if spec.arity == "?" and not values:
                return None
            return values[0] if values else None

        # All other cases return tuple
        new_values: tuple[str, ...] = tuple(values)
        return _accumulate_list_values(current, new_values, spec.accumulation_mode)


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
