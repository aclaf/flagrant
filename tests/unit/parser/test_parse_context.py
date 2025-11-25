from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser._context import ParseContext
from flagrant.parser._result import ParseResult
from flagrant.specification import command
from flagrant.types import NOT_GIVEN

if TYPE_CHECKING:
    from flagrant.specification._command import CommandSpecification


def make_context(
    *,
    spec: "CommandSpecification | None" = None,
    path: tuple[str, ...] | None = None,
    config: ParserConfiguration | None = None,
) -> ParseContext:
    if spec is None:
        spec = command("test")
    if path is None:
        path = (spec.name,)
    if config is None:
        config = ParserConfiguration()
    return ParseContext(spec=spec, path=path, config=config)


class TestParseContextInitialization:
    def test_creates_context_with_spec_and_config(self) -> None:
        spec = command("test")
        config = ParserConfiguration()

        ctx = ParseContext(spec=spec, path=("test",), config=config)

        assert ctx.spec is spec
        assert ctx.config is config
        assert ctx.path == ("test",)

    def test_initializes_with_empty_collections(self) -> None:
        ctx = make_context()

        assert ctx.options == {}
        assert ctx.ungrouped_positionals == []
        assert ctx.extra_args == []
        assert ctx.subcommand_result is None


class TestParseContextOptionValueManagement:
    def test_set_option_value_stores_value(self) -> None:
        ctx = make_context()

        ctx.set_option_value("verbose", True)

        assert ctx.options["verbose"] is True

    def test_get_option_value_returns_stored_value(self) -> None:
        ctx = make_context()
        ctx.set_option_value("output", "file.txt")

        value = ctx.get_option_value("output")

        assert value == "file.txt"

    def test_get_option_value_returns_not_given_for_missing(self) -> None:
        ctx = make_context()

        value = ctx.get_option_value("missing")

        assert value is NOT_GIVEN

    def test_set_option_value_overwrites_existing(self) -> None:
        ctx = make_context()
        ctx.set_option_value("output", "first.txt")
        ctx.set_option_value("output", "second.txt")

        assert ctx.options["output"] == "second.txt"


class TestParseContextPositionalAccumulation:
    def test_add_positional_value_appends_to_list(self) -> None:
        ctx = make_context()

        ctx.add_positional_value("file1.txt", 0)
        ctx.add_positional_value("file2.txt", 1)

        assert len(ctx.ungrouped_positionals) == 2
        assert ctx.ungrouped_positionals[0].value == "file1.txt"
        assert ctx.ungrouped_positionals[1].value == "file2.txt"

    def test_positional_stores_position(self) -> None:
        ctx = make_context()

        ctx.add_positional_value("file.txt", 5)

        assert ctx.ungrouped_positionals[0].position == 5

    def test_positionals_started_is_false_initially(self) -> None:
        ctx = make_context()

        assert ctx.positionals_started is False

    def test_positionals_started_is_true_after_adding(self) -> None:
        ctx = make_context()

        ctx.add_positional_value("file.txt", 0)

        assert ctx.positionals_started is True


class TestParseContextExtraArgs:
    def test_add_extra_arg_appends_to_list(self) -> None:
        ctx = make_context()

        ctx.add_extra_arg("--unknown")
        ctx.add_extra_arg("value")

        assert ctx.extra_args == ["--unknown", "value"]

    def test_extra_args_started_is_false_initially(self) -> None:
        ctx = make_context()

        assert ctx.extra_args_started is False

    def test_extra_args_started_is_true_after_adding(self) -> None:
        ctx = make_context()

        ctx.add_extra_arg("extra")

        assert ctx.extra_args_started is True


class TestParseContextGroupPositionals:
    @pytest.mark.xfail(
        reason="group_positionals() not implemented - returns empty dict"
    )
    def test_group_positionals_assigns_values_to_specs(self) -> None:
        spec = command("test")
        # Would need positional specs here when implemented
        ctx = make_context(spec=spec)
        ctx.add_positional_value("file.txt", 0)

        grouped = ctx.group_positionals()

        assert "file" in grouped

    def test_group_positionals_returns_empty_dict(self) -> None:
        ctx = make_context()
        ctx.add_positional_value("file.txt", 0)

        grouped = ctx.group_positionals()

        # Current implementation returns empty dict
        assert grouped == {}


class TestParseContextSubcommandResult:
    def test_subcommand_result_is_none_initially(self) -> None:
        ctx = make_context()

        assert ctx.subcommand_result is None

    def test_subcommand_result_can_be_assigned(self) -> None:
        ctx = make_context()
        sub_result = ParseResult(args=(), command="commit")

        ctx.subcommand_result = sub_result

        assert ctx.subcommand_result is sub_result


class TestParseContextPath:
    def test_path_is_single_command(self) -> None:
        spec = command("git")
        ctx = make_context(spec=spec, path=("git",))

        assert ctx.path == ("git",)

    def test_path_can_be_nested(self) -> None:
        spec = command("commit")
        ctx = make_context(spec=spec, path=("git", "commit"))

        assert ctx.path == ("git", "commit")
