from dataclasses import dataclass, field

from flagrant.configuration import ParserConfiguration
from flagrant.parser.exceptions import (
    AmbiguousOptionError,
    AmbiguousSubcommandError,
    UnknownOptionError,
    UnknownSubcommandError,
)
from flagrant.specification import (
    CommandSpecification,
    DictOptionSpecification,
    FlagOptionSpecification,
    ListOptionSpecification,
    OptionType,
    ScalarOptionSpecification,
)
from flagrant.types import ArgList, CommandName, CommandPath

from ._context import ParseContext
from ._handlers import (
    DictOptionHandler,
    FlagOptionHandler,
    Handler,
    ListOptionHandler,
    ScalarOptionHandler,
)
from ._resolver import CommandResolver, is_ambiguous_names, is_resolved_command
from ._result import ParseResult
from ._state import ParseState


@dataclass(slots=True)
class Parser:
    """Parser for command-line arguments based on a given configuration."""

    spec: "CommandSpecification"
    alias: CommandName | None = None
    path: CommandPath = field(default_factory=tuple)
    config: "ParserConfiguration" = field(default_factory=ParserConfiguration)

    _resolver: "CommandResolver" = field(init=False)
    _handlers: dict[type[OptionType], "Handler"] = field(init=False)

    def __post_init__(self) -> None:
        self.path = self.path or (self.spec.name,)
        self._resolver = CommandResolver(self.spec, self.config)
        self._handlers = Parser._register_handlers()

    def parse(self, args: ArgList) -> "ParseResult":
        state = ParseState(args)
        context = ParseContext(self.spec, self.path, self.config)
        self._parse_args(state, context)
        return ParseResult(
            state.args,
            self.alias or self.spec.name,
            tuple(context.extra_args),
            context.options,
            context.group_positionals(),
            context.subcommand_result,
        )

    def _parse_args(self, state: "ParseState", ctx: "ParseContext") -> None:
        while state.is_not_at_end:
            if state.current == self.config.trailing_arguments_separator:
                state.advance()
                ctx.extra_args.extend(state.consume_remaining())
                break

            if self._try_parse_option(state, ctx):
                continue

            if self._try_parse_subcommand(state, ctx):
                break

            ctx.add_positional_value(state.consume(), state.last_position)

    def _try_parse_option(self, state: "ParseState", ctx: "ParseContext") -> bool:
        arg = state.current
        if arg is None:
            return False

        if arg == "-" or self._is_negative_number_positional(arg):
            ctx.add_positional_value(state.consume(), state.last_position)
            return True

        resolved = self._resolver.resolve_options(arg)
        if is_ambiguous_names(resolved):
            raise AmbiguousOptionError(
                resolved.given_name,
                resolved.matches,
                self.path,
                state.args,
                state.position,
            )
        # Empty list means not an option (no prefix) - let other handlers try
        if resolved == []:
            return False
        # None means looked like an option but couldn't resolve
        if resolved is None:
            raise UnknownOptionError(arg, self.path, state.args, state.position)
        # Non-empty list - process resolved options
        state.advance()
        for option in resolved:
            handler = self._handlers.get(type(option.spec))
            if handler is None:
                msg = f"No handler for option type: {type(option.spec)}"
                raise ValueError(msg)
            current_value = ctx.get_option_value(option.resolved_name)
            new_value = handler.parse(
                state,
                ctx,
                self._resolver,
                option,
                current_value,
                arg,
                self.config,
            )
            ctx.set_option_value(option.resolved_name, new_value)
        return True

    def _is_negative_number_positional(self, arg: str) -> bool:
        if not self.config.allow_negative_numbers:
            return False
        if arg[0] != "-" or len(arg) < 2:
            return False
        return self.config.negative_number_pattern.match(arg) is not None

    def _try_parse_subcommand(
        self, state: "ParseState", context: "ParseContext"
    ) -> bool:
        arg = state.current
        if arg is None:
            return False
        sub = self._resolver.resolve_subcommand(arg)

        if self._should_raise_unknown_subcommand(context) and is_ambiguous_names(sub):
            raise AmbiguousSubcommandError(
                sub.given_name,
                sub.matches,
                self.path,
                state.args,
                state.position,
            )

        if is_resolved_command(sub):
            state.advance()
            sub_path = (*self.path, sub.given_name)
            sub_parser = Parser(sub.spec, sub.resolved_name, sub_path, self.config)
            remaining_args = state.consume_remaining()
            context.subcommand_result = sub_parser.parse(remaining_args)
            return True

        if self._should_raise_unknown_subcommand(context):
            raise UnknownSubcommandError(
                state.current or "", self.path, state.args, state.position
            )

        return False

    def _should_raise_unknown_subcommand(
        self,
        ctx: "ParseContext",
    ) -> bool:
        cmd = self.spec
        return bool(
            cmd.subcommands and not cmd.positionals and not ctx.positionals_started
        )

    @staticmethod
    def _register_handlers() -> dict[type[OptionType], "Handler"]:
        return {
            DictOptionSpecification: DictOptionHandler(),
            FlagOptionSpecification: FlagOptionHandler(),
            ListOptionSpecification: ListOptionHandler(),
            ScalarOptionSpecification: ScalarOptionHandler(),
        }


def parse_command_line_args(
    spec: "CommandSpecification",
    args: ArgList,
    config: "ParserConfiguration | None" = None,
) -> "ParseResult":
    """Parse command-line arguments based on the given specification and configuration.

    Args:
        spec: The command specification to use for parsing.
        args: The list of command-line arguments to parse.
        config: The parser configuration to use (default is a default configuration).

    Returns:
        A ParseResult containing the parsed arguments.
    """
    parser_config = config or ParserConfiguration()
    parser = Parser(spec, config=parser_config)
    return parser.parse(args)
