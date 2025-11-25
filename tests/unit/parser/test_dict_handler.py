from typing import TYPE_CHECKING, Any

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser._context import ParseContext
from flagrant.parser._handlers import DictOptionHandler
from flagrant.parser._resolver import CommandResolver, ResolvedOption
from flagrant.parser._state import ParseState
from flagrant.specification import command, dict_option
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


@pytest.mark.xfail(reason="DictOptionHandler.parse() raises NotImplementedError")
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

        result: Any = handler.parse(
            state, ctx, resolver, resolved, NOT_GIVEN, "--config", config
        )

        assert isinstance(result, dict)
        assert result["server"]["db"]["connection"]["host"] == "localhost"


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


@pytest.mark.xfail(reason="DictOptionHandler.parse() raises NotImplementedError")
class TestDictHandlerAccumulationModes:
    def test_merge_mode_merges_dictionaries(self) -> None:
        opt = dict_option(["config"], accumulation_mode="merge")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("b=2",))
        resolved = make_resolved_dict(opt)
        current: Any = {"a": 1}

        result = handler.parse(
            state, ctx, resolver, resolved, current, "--config", config
        )

        assert result == {"a": 1, "b": 2}

    def test_replace_mode_replaces_dictionary(self) -> None:
        opt = dict_option(["config"], accumulation_mode="last")
        ctx, resolver, config = make_handler_context(options=[opt])
        handler = DictOptionHandler()
        state = ParseState(("b=2",))
        resolved = make_resolved_dict(opt)
        current: Any = {"a": 1}

        result = handler.parse(
            state, ctx, resolver, resolved, current, "--config", config
        )

        assert result == {"b": 2}


@pytest.mark.xfail(reason="DictOptionHandler.parse() raises NotImplementedError")
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
