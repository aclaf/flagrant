from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser._context import ParseContext
from flagrant.parser._handlers import DictOptionHandler
from flagrant.parser._resolver import CommandResolver, ResolvedOption
from flagrant.parser._state import ParseState
from flagrant.parser.exceptions import OptionMissingValueError, OptionNotRepeatableError
from flagrant.specification import command, dict_option, scalar_option
from flagrant.types import NOT_GIVEN

if TYPE_CHECKING:
    from flagrant.specification._command import CommandSpecification
    from flagrant.specification._options import DictOptionSpecification, OptionType


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


def make_resolved_dict(
    option_spec: "DictOptionSpecification",
    given_name: str | None = None,
    inline: str | None = None,
) -> ResolvedOption:
    return ResolvedOption(
        given_name=given_name or option_spec.name,
        resolved_name=option_spec.name,
        spec=option_spec,
        inline=inline,
    )


class TestDictHandlerBasicParsing:
    def test_parses_key_value_pair(self) -> None:
        opt = dict_option(["config"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("key=value",))
        resolved = make_resolved_dict(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        assert result == {"key": "value"}

    def test_parses_multiple_key_value_pairs(self) -> None:
        opt = dict_option(["config"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("key1=value1", "key2=value2"))
        resolved = make_resolved_dict(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        assert result == {"key1": "value1", "key2": "value2"}


@pytest.mark.xfail(reason="DictOptionHandler.parse() raises NotImplementedError")
class TestDictHandlerNestedKeys:
    def test_parses_nested_key(self) -> None:
        opt = dict_option(["config"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("db.host=localhost",))
        resolved = make_resolved_dict(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        assert result == {"db": {"host": "localhost"}}

    def test_parses_deeply_nested_key(self) -> None:
        opt = dict_option(["config"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("server.db.connection.host=localhost",))
        resolved = make_resolved_dict(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        assert isinstance(result, dict)
        assert result["server"]["db"]["connection"]["host"] == "localhost"  # pyright: ignore[reportArgumentType,reportCallIssue]


@pytest.mark.xfail(reason="DictOptionHandler.parse() raises NotImplementedError")
class TestDictHandlerListIndices:
    def test_parses_list_index(self) -> None:
        opt = dict_option(["config"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("items[0]=first",))
        resolved = make_resolved_dict(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        assert result == {"items": ["first"]}

    def test_parses_multiple_list_indices(self) -> None:
        opt = dict_option(["config"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("items[0]=first", "items[1]=second"))
        resolved = make_resolved_dict(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        assert result == {"items": ["first", "second"]}


class TestDictHandlerAccumulationModes:
    def test_merge_mode_merges_dictionaries(self) -> None:
        opt = dict_option(["config"], accumulation_mode="merge")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("b=2",))
        resolved = make_resolved_dict(opt)
        current = {"a": "1"}

        result = handler.parse(
            state,
            ctx,
            resolver,
            resolved,
            current,  # pyright: ignore[reportArgumentType]
            "--config",
            config,
        )

        assert result == {"a": "1", "b": "2"}

    def test_merge_mode_overwrites_existing_keys(self) -> None:
        opt = dict_option(["config"], accumulation_mode="merge")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("a=new",))
        resolved = make_resolved_dict(opt)
        current = {"a": "old"}

        result = handler.parse(
            state,
            ctx,
            resolver,
            resolved,
            current,  # pyright: ignore[reportArgumentType]
            "--config",
            config,
        )

        assert result == {"a": "new"}

    def test_last_mode_replaces_dictionary(self) -> None:
        opt = dict_option(["config"], accumulation_mode="last")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("b=2",))
        resolved = make_resolved_dict(opt)
        current = {"a": "1"}

        result = handler.parse(
            state,
            ctx,
            resolver,
            resolved,
            current,  # pyright: ignore[reportArgumentType]
            "--config",
            config,
        )

        assert result == {"b": "2"}

    def test_first_mode_keeps_existing_dictionary(self) -> None:
        opt = dict_option(["config"], accumulation_mode="first")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("b=2",))
        resolved = make_resolved_dict(opt)
        current = {"a": "1"}

        result = handler.parse(
            state,
            ctx,
            resolver,
            resolved,
            current,  # pyright: ignore[reportArgumentType]
            "--config",
            config,
        )

        assert result == {"a": "1"}

    def test_first_mode_accepts_when_no_current(self) -> None:
        opt = dict_option(["config"], accumulation_mode="first")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("b=2",))
        resolved = make_resolved_dict(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        assert result == {"b": "2"}

    def test_append_mode_builds_tuple_of_dicts(self) -> None:
        opt = dict_option(["config"], accumulation_mode="append")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("b=2",))
        resolved = make_resolved_dict(opt)
        current = ({"a": "1"},)

        result = handler.parse(
            state,
            ctx,
            resolver,
            resolved,
            current,  # pyright: ignore[reportArgumentType]
            "--config",
            config,
        )

        assert result == ({"a": "1"}, {"b": "2"})

    def test_append_mode_creates_tuple_when_no_current(self) -> None:
        opt = dict_option(["config"], accumulation_mode="append")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("a=1",))
        resolved = make_resolved_dict(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        assert result == ({"a": "1"},)

    def test_error_mode_raises_when_repeated(self) -> None:
        opt = dict_option(["config"], accumulation_mode="error")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("b=2",))
        resolved = make_resolved_dict(opt)
        current = {"a": "1"}

        with pytest.raises(OptionNotRepeatableError):
            handler.parse(
                state,
                ctx,
                resolver,
                resolved,
                current,  # pyright: ignore[reportArgumentType]
                "--config",
                config,
            )

    def test_error_mode_accepts_first_value(self) -> None:
        opt = dict_option(["config"], accumulation_mode="error")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("a=1",))
        resolved = make_resolved_dict(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        assert result == {"a": "1"}


class TestDictHandlerInlineValues:
    def test_uses_inline_value(self) -> None:
        opt = dict_option(["config"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(())
        resolved = make_resolved_dict(opt, inline="key=value")

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config=key=value", config
        )

        assert result == {"key": "value"}

    def test_inline_with_additional_args(self) -> None:
        opt = dict_option(["config"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("key2=value2",))
        resolved = make_resolved_dict(opt, inline="key1=value1")

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config=key1=value1", config
        )

        assert result == {"key1": "value1", "key2": "value2"}


class TestDictHandlerCustomSeparator:
    def test_uses_custom_key_value_separator(self) -> None:
        opt = dict_option(["config"], key_value_separator=":")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("key:value",))
        resolved = make_resolved_dict(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        assert result == {"key": "value"}

    def test_custom_separator_with_default_in_value(self) -> None:
        opt = dict_option(["config"], key_value_separator=":")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("key:val=xyz",))
        resolved = make_resolved_dict(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        assert result == {"key": "val=xyz"}


class TestDictHandlerEdgeCases:
    def test_value_with_equals_in_it(self) -> None:
        opt = dict_option(["config"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("key=a=b=c",))
        resolved = make_resolved_dict(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        assert result == {"key": "a=b=c"}

    def test_empty_value(self) -> None:
        opt = dict_option(["config"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("key=",))
        resolved = make_resolved_dict(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        assert result == {"key": ""}

    def test_missing_separator_raises_error(self) -> None:
        opt = dict_option(["config"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("keyvalue",))
        resolved = make_resolved_dict(opt)

        with pytest.raises(ValueError, match="requires key=value format"):
            handler.parse(state, ctx, resolver, resolved, NOT_GIVEN, "--config", config)

    def test_duplicate_keys_last_wins(self) -> None:
        opt = dict_option(["config"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("key=first", "key=second"))
        resolved = make_resolved_dict(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        assert result == {"key": "second"}


class TestDictHandlerArity:
    def test_respects_fixed_arity(self) -> None:
        opt = dict_option(["config"], arity=2)
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("key1=value1", "key2=value2", "key3=value3"))
        resolved = make_resolved_dict(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        # Should only consume 2 values
        assert result == {"key1": "value1", "key2": "value2"}
        assert state.remaining_count == 1

    def test_minimum_arity_raises_when_not_met(self) -> None:
        opt = dict_option(["config"], arity=(2, 4))
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("key1=value1",))
        resolved = make_resolved_dict(opt)

        with pytest.raises(OptionMissingValueError):
            handler.parse(state, ctx, resolver, resolved, NOT_GIVEN, "--config", config)

    def test_stops_at_option_for_star_arity(self) -> None:
        opt = dict_option(["config"], arity="*")
        other_opt = dict_option(["other"])
        ctx, resolver, config = make_handler_context(options=[opt, other_opt])
        handler = DictOptionHandler()
        state = ParseState(("key1=value1", "--other", "key2=value2"))
        resolved = make_resolved_dict(opt)

        result = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        # Should stop at --other
        assert result == {"key1": "value1"}
        assert state.current == "--other"


class TestDictHandlerTypeGuard:
    def test_raises_for_non_dict_option(self) -> None:
        opt = scalar_option(["config"])
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("value",))
        resolved = ResolvedOption(
            given_name="--config",
            resolved_name="config",
            spec=opt,
            inline=None,
        )

        with pytest.raises(TypeError, match="DictOptionHandler can only parse dict"):
            handler.parse(state, ctx, resolver, resolved, NOT_GIVEN, "--config", config)
