import sys
from dataclasses import dataclass, field
from itertools import islice
from typing import TYPE_CHECKING, cast
from typing_extensions import override

from flagrant.configuration import ParserConfiguration
from flagrant.enums import UngroupedPositionalStrategy
from flagrant.specification import (
    DictAccumulationMode,
    DictOptionSpecification,
    FlagAccumulationMode,
    FlagOptionSpecification,
    OptionResult,
    OptionSpecification,
    OptionSpecificationType,
    ValueAccumulationMode,
    ValueOptionSpecification,
    is_flag_option,
    is_value_option,
)

from ._result import ParseResult
from .exceptions import (
    AmbiguousOptionError,
    OptionMissingValueError,
    OptionNotRepeatableError,
    OptionValueNotAllowedError,
    PositionalMissingValueError,
    PositionalUnexpectedValueError,
    UnknownOptionError,
    UnknownSubcommandError,
)

if TYPE_CHECKING:
    from flagrant.specification import (
        CommandSpecification,
    )
    from flagrant.types import (
        Arg,
        ArgPosition,
        Args,
        CommandPath,
        Consumed,
        DictOptionDictValue,
        DictOptionListValue,
        InlineValue,
        OptionName,
        OptionValue,
        PositionalName,
        PositionalValue,
    )


@dataclass(slots=True)  # Mutable for tracking parsing state
class _ParseContext:
    args: "tuple[str, ...]"
    config: "ParserConfiguration"
    path: "CommandPath"
    spec: "CommandSpecification"
    total_args: int
    options: dict["OptionName", "OptionValue"] = field(default_factory=dict)
    position: int = 0
    positionals: dict[str, "ArgPosition"] = field(default_factory=dict)
    positionals_started: bool = False
    subcommand: "ParseResult | None" = None
    trailing: list[str] = field(default_factory=list)
    trailing_started: bool = False

    @override
    def __repr__(self) -> str:
        return (
            f"_ParseContext("
            f" args={self.args},"
            f" config={self.config},"
            f" options={list(self.options.keys())},"
            f" path={self.path},"
            f" position={self.position},"
            f" positionals={list(self.positionals.keys())},"
            f" spec={self.spec.name!r},"
            f" subcommand={self.subcommand},"
            f" total_args={self.total_args},"
            f" trailing={self.trailing},"
            ")"
        )


@dataclass(slots=True, frozen=True)
class _OptionParseContext:
    provided_name: "OptionName"
    matched_name: "OptionName"
    spec: "OptionSpecificationType"
    inline_value: "str | None"

    @override
    def __repr__(self) -> str:
        return (
            f"_OptionParseContext("
            f" inline_value={self.inline_value!r},"
            f" matched_name={self.matched_name!r},"
            f" provided_name={self.provided_name!r},"
            f" spec={self.spec},"
            ")"
        )


def parse_command_line_args(
    spec: "CommandSpecification",
    args: "Args | None" = None,
    config: "ParserConfiguration | None" = None,
) -> ParseResult:
    """Generate structured results from command-line arguments.

    Args:
        spec: The command specification to use for parsing.
        args: The list of command-line arguments to parse. If `None`, uses
            `sys.argv[1:]`.
        config: The parser configuration to use. If `None`, uses the default
            configuration.

    Returns:
        The structured parse result.

    Raises:
        AmbiguousOptionError: If an abbreviated option name matches multiple options.
        OptionMissingValueError: If a required option value is missing.
        OptionValueNotAllowedError: If an inline value is provided for a flag option.
        OptionNotRepeatableError: If a non-repeatable option is provided multiple times.
        PositionalMissingValueError: If a required positional value is missing.
        PositionalUnexpectedValueError: If an unexpected positional value is
            encountered.
        UnknownOptionError: If an unknown option is encountered.
        UnknownSubcommandError: If an unknown subcommand is encountered.
    """
    args = args or sys.argv[1:]
    return _parse_argument_list(
        _ParseContext(
            config=config or ParserConfiguration(),
            spec=spec,
            args=tuple(args),
            total_args=len(args),
            path=(spec.name,),
        ),
    )


def _parse_argument_list(ctx: _ParseContext) -> ParseResult:
    """Parse a list of command-line arguments.

    Recursively parses subcommands as they are encountered.
    """
    command_spec = ctx.spec
    while ctx.position < ctx.total_args:
        # Subcommand has already been parsed
        if ctx.subcommand is not None:
            break

        arg = ctx.args[ctx.position]

        # Trailing arguments after `--` delimiter
        if ctx.trailing_started:
            ctx.trailing.append(arg)
            ctx.position += 1
        elif arg == ctx.config.trailing_arguments_separator:
            ctx.trailing_started = True
            ctx.position += 1
        # Strict POSIX ordering check
        elif _check_strict_posix_ordering(ctx):
            _collect_positional(ctx, arg)
            ctx.position += 1
        # Long option
        elif arg.startswith(ctx.config.long_name_prefix):
            ctx.position += _parse_long_option(ctx)
        # Short option(s)
        elif arg.startswith(ctx.config.short_name_prefix):
            ctx.position += _parse_short_options(ctx)
        # Subcommand
        elif subcommand_spec := _resolve_subcommand(ctx, arg):
            _parse_subcommand(ctx, subcommand_spec)
        # Command has no positionals defined and argument is not a subcommand
        elif _should_raise_unknown_subcommand(ctx):
            raise _unknown_subcommand_error(ctx, arg)
        # Positional argument
        else:
            _collect_positional(ctx, arg)
            ctx.position += 1

    return ParseResult(
        args=ctx.args,
        command=command_spec.name,
        options=ctx.options,
        positionals=_group_positionals(ctx),
        subcommand=ctx.subcommand,
        extra_args=tuple(ctx.trailing),
    )


def _check_strict_posix_ordering(ctx: _ParseContext) -> bool:
    return ctx.config.strict_posix_options and ctx.positionals_started


def _parse_long_option(ctx: _ParseContext) -> int:
    provided_name, inline_value = _split_option_arg(
        ctx, ctx.args[ctx.position], ctx.config.long_name_prefix
    )
    result = _resolve_option(ctx, provided_name)

    extra_inline_value: InlineValue | None = None
    if result is None and ctx.config.allow_inline_values_without_equals:
        command_spec = ctx.spec
        for name in command_spec.long_option_names:
            if provided_name.startswith(name):
                extra_inline_value = provided_name[len(name) :]
                provided_name = name
                result = OptionResult(name, command_spec.get_option(name))
                break

    if result is None:
        raise _unknown_option_error(ctx, provided_name)

    return _parse_option(
        ctx,
        _OptionParseContext(
            provided_name=provided_name,
            matched_name=result.matched_name,
            spec=result.specification,
            inline_value=_concat_inline_value(ctx, inline_value, extra_inline_value),
        ),
    )


def _parse_short_options(ctx: _ParseContext) -> int:
    chars, inline_value = _split_option_arg(
        ctx, ctx.args[ctx.position], ctx.config.short_name_prefix
    )
    options, updated_inline_value = _resolve_short_option_chars(
        ctx, chars, inline_value
    )
    return _parse_resolved_short_options(ctx, options, updated_inline_value)


def _resolve_short_option_chars(
    ctx: _ParseContext, chars: str, inline_value: str | None
) -> tuple[dict["OptionName", "OptionSpecificationType"], "InlineValue | None"]:
    options: dict[OptionName, OptionSpecificationType] = {}
    for index, char in enumerate(chars):
        result = _resolve_option(ctx, char)
        if result is None and index == 0:
            raise _unknown_option_error(ctx, chars)
        if result is None:
            inline_value = _concat_inline_value(ctx, inline_value, chars[index:])
            break
        matched_name, option_spec = result
        options[matched_name] = option_spec
    return options, inline_value


def _parse_resolved_short_options(
    ctx: _ParseContext,
    options: dict["OptionName", "OptionSpecificationType"],
    inline_value: str | None,
) -> "Consumed":
    last_option_name, last_option = options.popitem()

    for char, inner_option in options.items():
        consumed = _parse_option(
            ctx,
            _OptionParseContext(
                provided_name=char,
                matched_name=inner_option.name,
                spec=inner_option,
                inline_value=None,
            ),
        )
        if consumed != 0:
            msg = "Unexpected consumption of arguments for inner short option."
            raise RuntimeError(msg)

    return _parse_option(
        ctx,
        _OptionParseContext(
            provided_name=last_option_name,
            matched_name=last_option.name,
            spec=last_option,
            inline_value=inline_value,
        ),
    )


def _parse_option(ctx: _ParseContext, option: _OptionParseContext) -> int:
    option_spec = option.spec
    if is_flag_option(option_spec):
        value, consumed = _parse_flag_option(ctx, option)
        ctx.options[option_spec.name] = _accumulate_option(ctx, option, value)
        return consumed
    value, consumed = _parse_non_flag_option(ctx, option)
    ctx.options[option_spec.name] = _accumulate_option(ctx, option, value)
    return consumed


def _parse_flag_option(
    ctx: _ParseContext, option: _OptionParseContext
) -> tuple["OptionValue", "Consumed"]:
    inline_value = option.inline_value
    if inline_value is not None:
        raise OptionValueNotAllowedError(
            option.provided_name,
            inline_value,
            path=ctx.path,
            args=ctx.args,
            position=ctx.position,
        )

    return not cast("FlagOptionSpecification", option.spec).is_negative(
        option.provided_name, case_sensitive=ctx.config.case_sensitive_options
    ), 1


def _parse_non_flag_option(
    ctx: _ParseContext, option: _OptionParseContext
) -> tuple["OptionValue", "Consumed"]:
    _check_required_values(ctx, option)
    option_spec = option.spec

    raw, extra_consumed = _collect_values(ctx, option)

    if (
        is_value_option(option_spec)
        and len(raw) == 1
        and option_spec.accepts_at_most_one_value
    ):
        value = cast("OptionValue", raw[0])
    elif is_value_option(option_spec) and option_spec.accepts_multiple_values:
        value = tuple(
            _split_escaped(
                item,
                option_spec.item_separator or ctx.config.value_item_separator,
                option_spec.escape_character or ctx.config.value_escape_character,
            )
            for item in raw
        )
    else:
        value = raw

    # TODO(tbhb): Dict parsing

    return value, extra_consumed + 1


def _check_required_values(ctx: _ParseContext, option: _OptionParseContext) -> None:
    option_spec = option.spec
    inline_value = option.inline_value
    next_args = ctx.args[ctx.position + 1 :]
    satisfies_arity = (
        len(next_args) + (1 if inline_value is not None else 0) >= option_spec.arity.min
    )
    if option_spec.requires_values and not satisfies_arity:
        possible_values = [inline_value] if inline_value is not None else []
        possible_values.extend(
            next_args[: option_spec.arity.min - len(possible_values)]
        )
        raise OptionMissingValueError(
            option.provided_name,
            option_spec.arity,
            tuple(possible_values) if possible_values else None,
            path=ctx.path,
            args=ctx.args,
            position=ctx.position,
        )


def _collect_values(
    ctx: _ParseContext,
    option: _OptionParseContext,
) -> tuple[tuple[str, ...], "Consumed"]:
    option_spec = option.spec
    inline_value = option.inline_value
    next_position = ctx.position + 1
    collected: list[str] = [inline_value] if inline_value is not None else []
    inline_consumed = 1 if inline_value is not None else 0
    consumed = 0

    if option_spec.greedy_accepts_unbounded_values:
        collected.extend(islice(ctx.args, next_position, None))
        consumed = ctx.total_args - next_position
    elif option_spec.accepts_multiple_values:
        if option_spec.arity.max is not None:
            max_position = min(
                next_position + option_spec.arity.max - len(collected),
                ctx.total_args,
            )
        else:
            max_position = ctx.total_args
        for possible_value in islice(ctx.args, next_position, max_position):
            if _is_negative_number(ctx, possible_value, option_spec):
                collected.append(possible_value)
                continue
            if _is_option_or_subcommand(ctx, possible_value):
                break
            collected.append(possible_value)
        consumed = len(collected) - inline_consumed

    return tuple(collected), consumed


def _accumulate_option(
    ctx: _ParseContext,
    option: _OptionParseContext,
    value: "OptionValue",
) -> "OptionValue":
    options = ctx.options
    option_spec = option.spec
    accumulated_value: OptionValue
    match option_spec, option_spec.accumulation_mode:
        # --option value1 --option value2
        # -> value1
        case _, (
            DictAccumulationMode.FIRST
            | ValueAccumulationMode.FIRST
            | FlagAccumulationMode.FIRST
        ) if option_spec.name in options:
            accumulated_value = options[option_spec.name]
        # --option value1 --option value2
        # -> value2
        case _, (
            DictAccumulationMode.LAST
            | ValueAccumulationMode.LAST
            | FlagAccumulationMode.LAST
        ):
            accumulated_value = value
        # --option value1 --option value2
        # -> Error
        case _, (
            DictAccumulationMode.ERROR
            | ValueAccumulationMode.ERROR
            | FlagAccumulationMode.ERROR
        ) if option_spec.name in options:
            raise _option_not_repeatable_error(ctx, option, value)

        # --flag --flag --flag
        # -> 3
        case FlagOptionSpecification(), FlagAccumulationMode.COUNT:
            previous = cast("int", options.get(option_spec.name, 0))
            accumulated_value = previous + cast("int", value)

        # --option value1 --option value2
        # -> (value1, value2)
        case ValueOptionSpecification(), ValueAccumulationMode.APPEND if (
            option_spec.accepts_at_most_one_value
        ):
            previous = cast("tuple[str, ...]", options.get(option_spec.name, ()))
            accumulated_value = cast("OptionValue", (*previous, cast("str", value)))
        # --option value1 value2 --option value3 value4
        # -> ((value1, value2), (value3, value4))
        case ValueOptionSpecification(), ValueAccumulationMode.APPEND:
            previous = cast(
                "tuple[tuple[str, ...], ...]", options.get(option_spec.name, ())
            )
            accumulated_value = cast(
                "OptionValue", (*previous, *(cast("tuple[str, ...]", value)))
            )
        # --option value1 value2 --option value3 value4
        # -> (value1, value2, value3, value4)
        case ValueOptionSpecification(), ValueAccumulationMode.EXTEND:
            previous = cast("tuple[str, ...]", options.get(option_spec.name, ()))
            accumulated_value = cast(
                "OptionValue", (*previous, *(cast("tuple[str, ...]", value)))
            )

        # --dict-option key1=val1 --dict-option key2=val2
        # -> {'key1': 'val1', 'key2': 'val2'}
        case DictOptionSpecification(), DictAccumulationMode.MERGE:
            previous = cast("DictOptionDictValue", options.get(option_spec.name, {}))
            # TODO(tbhb): Support deep merge
            accumulated_value = cast(
                "OptionValue", previous | cast("DictOptionDictValue", value)
            )
        # --dict-option key1=val1 --dict-option key2=val2
        # -> ({'key1': 'val1'}, {'key2': 'val2'})
        case DictOptionSpecification(), DictAccumulationMode.APPEND:
            previous = cast(
                "DictOptionListValue",
                options.get(option_spec.name, ()),
            )
            accumulated_value = cast(
                "OptionValue",
                (*previous, cast("DictOptionDictValue", value)),
            )

        case _:
            msg = "Unhandled accumulation mode"
            raise RuntimeError(msg)

    return accumulated_value


def _split_option_arg(
    ctx: _ParseContext, arg: "Arg", prefix: str
) -> tuple["OptionName", "InlineValue | None"]:
    unprefixed = arg[len(prefix) :]
    if ctx.config.option_value_separator not in unprefixed:
        return unprefixed, None

    # Inline value will be an empty string if separator is at end
    parts = unprefixed.split(ctx.config.option_value_separator, 1)
    return parts[0], parts[1]


def _parse_subcommand(
    ctx: _ParseContext,
    subcommand_spec: "CommandSpecification",
) -> None:
    subcommand_name = subcommand_spec.name
    subcommand_result = _parse_argument_list(
        _ParseContext(
            config=ctx.config,
            spec=subcommand_spec,
            args=ctx.args,  # Preserve full args for accurate positions in errors
            total_args=len(ctx.args),
            path=(*ctx.path, subcommand_name),
            position=ctx.position + 1,
            subcommand=None,
        ),
    )
    ctx.subcommand = subcommand_result


def _should_raise_unknown_subcommand(
    ctx: _ParseContext,
) -> bool:
    command_spec = ctx.spec
    return bool(
        command_spec.subcommands
        and not command_spec.positionals
        and not ctx.positionals_started
    )


def _collect_positional(
    ctx: _ParseContext,
    arg: str,
) -> None:
    ctx.positionals[arg] = ctx.position
    ctx.positionals_started = True


def _group_positionals(
    ctx: _ParseContext,
) -> dict["PositionalName", "PositionalValue"]:
    ungrouped_positionals = ctx.positionals
    if not ungrouped_positionals:
        return {}

    command_spec = ctx.spec
    if not command_spec.positionals:
        return _handle_ungrouped_positionals(ctx, ungrouped_positionals)

    groups = command_spec.positionals
    grouped_positionals: dict[PositionalName, PositionalValue] = {}
    remaining_positionals = len(ungrouped_positionals)
    ungrouped_index = 0
    for group_index, (group, arity) in enumerate(groups.items()):
        if remaining_positionals < arity.min:
            raise PositionalMissingValueError(
                group,
                arity,
                tuple(islice(ungrouped_positionals.keys(), ungrouped_index)),
                path=ctx.path,
                args=ctx.args,
                position=ungrouped_index,
            )

        subsequent_min = sum(
            arity.min for arity in islice(groups.values(), group_index + 1, len(groups))
        )

        to_consume = 0
        if arity.accepts_unbounded_values:
            to_consume = max(0, remaining_positionals - subsequent_min)
        elif arity.max is not None:
            # Bounded arity
            available = max(0, len(ungrouped_positionals) - subsequent_min)
            to_consume = min(arity.max, available)

        consumed_values = islice(
            ungrouped_positionals.keys(),
            ungrouped_index,
            ungrouped_index + to_consume,
        )
        remaining_positionals -= to_consume
        ungrouped_index += to_consume
        grouped_positionals[group] = (
            next(consumed_values)
            if arity.accepts_at_most_one_value
            else tuple(consumed_values)
        )

    if (
        remaining_positionals
        and ctx.config.strict_posix_options
        and ungrouped_index < len(ungrouped_positionals)
    ):
        grouped_positionals.update(
            _handle_ungrouped_positionals(
                ctx,
                dict(islice(ungrouped_positionals.items(), ungrouped_index, None)),
            )
        )

    return grouped_positionals


def _handle_ungrouped_positionals(
    ctx: _ParseContext,
    positionals: dict[str, int],
) -> dict["PositionalName", "PositionalValue"]:
    if not positionals:
        return {}
    strategy = ctx.config.ungrouped_positional_strategy
    match strategy:
        case UngroupedPositionalStrategy.IGNORE:
            return {}
        case UngroupedPositionalStrategy.COLLECT:
            return {ctx.config.ungrouped_positional_name: tuple(positionals.keys())}
        case UngroupedPositionalStrategy.ERROR:
            first_positional = next(iter(positionals))
            raise PositionalUnexpectedValueError(
                ctx.spec.name,
                tuple(positionals.keys()),
                path=ctx.path,
                args=ctx.args,
                position=positionals[first_positional],
            )


def _concat_inline_value(
    ctx: _ParseContext, value: "InlineValue | None", extra: "InlineValue | None"
) -> "InlineValue | None":
    if value is None and extra is None:
        return None
    return ctx.config.option_value_separator.join(
        v for v in (value, extra) if v is not None
    )


def _is_negative_number(
    ctx: _ParseContext, value: str, option_spec: OptionSpecification
) -> bool:
    if not is_value_option(option_spec):
        return False

    if not (option_spec.allow_negative_numbers or ctx.config.allow_negative_numbers):
        return False

    pattern = option_spec.negative_number_pattern or ctx.config.negative_number_pattern
    return pattern.match(value) is not None


def _is_option_or_subcommand(ctx: _ParseContext, value: str) -> bool:
    if not value:
        return False
    if value.startswith(ctx.config.long_name_prefix):
        name = value[len(ctx.config.long_name_prefix) :]
        return _resolve_option(ctx, name) is not None
    if value.startswith(ctx.config.short_name_prefix):
        name = value[len(ctx.config.short_name_prefix) :]
        return _resolve_option(ctx, name) is not None
    return _resolve_subcommand(ctx, value) is not None


def _resolve_option(
    ctx: _ParseContext,
    name: str,
) -> "OptionResult | None":
    command_spec = ctx.spec
    if not command_spec.options:
        return None

    if ctx.config.convert_underscores:
        name = name.replace("_", "-")

    mapping = (
        command_spec.option_name_mapping
        if ctx.config.case_sensitive_options
        else command_spec.option_name_mapping_ci
    )
    search_key = name if ctx.config.case_sensitive_options else name.lower()
    canonical_name = mapping.get(search_key)
    if canonical_name:
        return OptionResult(search_key, command_spec.options[canonical_name])

    if not ctx.config.allow_abbreviated_options:
        return None

    if len(search_key) < ctx.config.minimum_abbreviation_length:
        return None

    matches_iter = (m for m in mapping if m.startswith(search_key))
    matches = list(islice(matches_iter, 3))
    if len(matches) == 1:
        matched_name = matches[0]
        return OptionResult(matched_name, command_spec.options[mapping[matched_name]])
    if len(matches) > 1:
        raise AmbiguousOptionError(
            search_key,
            tuple(matches),
            path=ctx.path,
            args=ctx.args,
            position=ctx.position,
        )

    return None


def _resolve_subcommand(
    ctx: _ParseContext,
    name: str,
) -> "CommandSpecification | None":
    command_spec = ctx.spec
    if not command_spec.subcommands:
        return None

    if ctx.config.convert_underscores:
        name = name.replace("_", "-")

    mapping = (
        command_spec.subcommand_name_mapping
        if ctx.config.case_sensitive_commands
        else command_spec.subcommand_name_mapping_ci
    )
    search_key = name if ctx.config.case_sensitive_commands else name.lower()
    canonical_name = mapping.get(search_key)
    if canonical_name:
        return command_spec.subcommands[canonical_name]
    if not ctx.config.allow_abbreviated_subcommands:
        return None

    if len(search_key) < ctx.config.minimum_abbreviation_length:
        return None

    matches = [m for m in mapping if m.startswith(search_key)]
    if len(matches) == 1:
        return command_spec.subcommands[mapping[matches[0]]]

    # Does not raise error because arg may be a positional
    return None


def _option_not_repeatable_error(
    ctx: _ParseContext,
    option: _OptionParseContext,
    value: "OptionValue",
) -> OptionNotRepeatableError:
    return OptionNotRepeatableError(
        option.provided_name,
        value,
        path=ctx.path,
        args=ctx.args,
        position=ctx.position,
    )


def _unknown_option_error(ctx: _ParseContext, provided_name: str) -> UnknownOptionError:
    return UnknownOptionError(
        provided_name, path=ctx.path, args=ctx.args, position=ctx.position
    )


def _unknown_subcommand_error(ctx: _ParseContext, arg: str) -> UnknownSubcommandError:
    return UnknownSubcommandError(
        arg, args=ctx.args, path=ctx.path, position=ctx.position
    )


def _split_escaped(value: str, delimiter: str, escape: str) -> tuple[str, ...]:
    if len(delimiter) != 1:
        msg = "Delimiter must be a single character."
        raise ValueError(msg)
    if len(escape) != 1:
        msg = "Escape character must be a single character."
        raise ValueError(msg)
    if escape == delimiter:
        msg = "Escape character and delimiter cannot be the same."
        raise ValueError(msg)

    if not value:
        return ()

    segments: list[str] = []
    current: list[str] = []
    index = 0

    while index < len(value):
        char = value[index]
        if char == escape and index + 1 < len(value):
            next_char = value[index + 1]
            if next_char in (delimiter, escape):
                current.append(char)
                current.append(next_char)
                index += 2
                continue
        if char == delimiter:
            segments.append("".join(current))
            current = []
            index += 1
            continue

        current.append(char)
        index += 1

    segments.append("".join(current))
    return tuple(segments)
