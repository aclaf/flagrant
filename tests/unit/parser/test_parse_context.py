from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser._context import ParseContext
from flagrant.parser._result import ParseResult
from flagrant.parser.exceptions import PositionalMissingValueError
from flagrant.specification import PositionalSpecification, command
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
    def test_group_positionals_uses_implicit_args_spec_when_no_specs_defined(
        self,
    ) -> None:
        spec = command("test")
        ctx = make_context(spec=spec)
        ctx.add_positional_value("file.txt", 0)

        grouped = ctx.group_positionals()

        # When no positional specs are defined, uses implicit "args" spec
        assert "args" in grouped
        assert grouped["args"] == ("file.txt",)

    def test_group_positionals_returns_empty_args_when_no_positionals(self) -> None:
        ctx = make_context()

        grouped = ctx.group_positionals()

        # Implicit "args" spec with arity (0, "*") returns empty tuple
        assert grouped == {"args": ()}


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


# =============================================================================
# Basic grouping tests
# =============================================================================


class TestGroupPositionalsBasicGrouping:
    def test_single_positional_with_exact_arity_one_returns_scalar(self) -> None:
        pos = PositionalSpecification(name="file", arity=1)
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("input.txt", 0)

        grouped = ctx.group_positionals()

        assert grouped["file"] == "input.txt"

    def test_single_positional_with_exact_arity_two_returns_tuple(self) -> None:
        pos = PositionalSpecification(name="files", arity=2)
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("a.txt", 0)
        ctx.add_positional_value("b.txt", 1)

        grouped = ctx.group_positionals()

        assert grouped["files"] == ("a.txt", "b.txt")

    def test_multiple_positionals_with_fixed_arities(self) -> None:
        pos1 = PositionalSpecification(name="src", arity=1)
        pos2 = PositionalSpecification(name="dst", arity=1)
        spec = command("test", positionals=[pos1, pos2])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("source.txt", 0)
        ctx.add_positional_value("dest.txt", 1)

        grouped = ctx.group_positionals()

        assert grouped["src"] == "source.txt"
        assert grouped["dst"] == "dest.txt"

    def test_unbounded_positional_consumes_remainder(self) -> None:
        pos = PositionalSpecification(name="files", arity="*")
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("a.txt", 0)
        ctx.add_positional_value("b.txt", 1)
        ctx.add_positional_value("c.txt", 2)

        grouped = ctx.group_positionals()

        assert grouped["files"] == ("a.txt", "b.txt", "c.txt")

    def test_three_positionals_with_different_arities(self) -> None:
        pos1 = PositionalSpecification(name="cmd", arity=1)
        pos2 = PositionalSpecification(name="args", arity=2)
        pos3 = PositionalSpecification(name="output", arity=1)
        spec = command("test", positionals=[pos1, pos2, pos3])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("build", 0)
        ctx.add_positional_value("file1.c", 1)
        ctx.add_positional_value("file2.c", 2)
        ctx.add_positional_value("output.exe", 3)

        grouped = ctx.group_positionals()

        assert grouped["cmd"] == "build"
        assert grouped["args"] == ("file1.c", "file2.c")
        assert grouped["output"] == "output.exe"


# =============================================================================
# Later needs reservation tests
# =============================================================================


class TestGroupPositionalsLaterNeedsReservation:
    def test_unbounded_positional_reserves_for_later_required(self) -> None:
        pos1 = PositionalSpecification(name="files", arity="*")
        pos2 = PositionalSpecification(name="output", arity=1)
        spec = command("test", positionals=[pos1, pos2])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("a.txt", 0)
        ctx.add_positional_value("b.txt", 1)
        ctx.add_positional_value("out.txt", 2)

        grouped = ctx.group_positionals()

        assert grouped["files"] == ("a.txt", "b.txt")
        assert grouped["output"] == "out.txt"

    def test_middle_positional_limited_by_later_minimums(self) -> None:
        pos1 = PositionalSpecification(name="first", arity=1)
        pos2 = PositionalSpecification(name="middle", arity="*")
        pos3 = PositionalSpecification(name="last", arity=2)
        spec = command("test", positionals=[pos1, pos2, pos3])
        ctx = make_context(spec=spec)
        for i, val in enumerate(["a", "b", "c", "d", "e"]):
            ctx.add_positional_value(val, i)

        grouped = ctx.group_positionals()

        assert grouped["first"] == "a"
        assert grouped["middle"] == ("b", "c")
        assert grouped["last"] == ("d", "e")

    def test_worked_example_command_files_output(self) -> None:
        pos1 = PositionalSpecification(name="command", arity=1)
        pos2 = PositionalSpecification(name="files", arity=(1, "*"))
        pos3 = PositionalSpecification(name="output", arity=1)
        spec = command("test", positionals=[pos1, pos2, pos3])
        ctx = make_context(spec=spec)
        for i, val in enumerate(
            ["build", "file1.txt", "file2.txt", "file3.txt", "result.out"]
        ):
            ctx.add_positional_value(val, i)

        grouped = ctx.group_positionals()

        assert grouped["command"] == "build"
        assert grouped["files"] == ("file1.txt", "file2.txt", "file3.txt")
        assert grouped["output"] == "result.out"

    def test_unbounded_with_multiple_later_required(self) -> None:
        pos1 = PositionalSpecification(name="files", arity="*")
        pos2 = PositionalSpecification(name="dst", arity=1)
        pos3 = PositionalSpecification(name="mode", arity=1)
        spec = command("test", positionals=[pos1, pos2, pos3])
        ctx = make_context(spec=spec)
        for i, val in enumerate(["a.txt", "b.txt", "/dst", "copy"]):
            ctx.add_positional_value(val, i)

        grouped = ctx.group_positionals()

        assert grouped["files"] == ("a.txt", "b.txt")
        assert grouped["dst"] == "/dst"
        assert grouped["mode"] == "copy"

    def test_range_arity_middle_limited_by_later(self) -> None:
        pos1 = PositionalSpecification(name="first", arity=1)
        pos2 = PositionalSpecification(name="middle", arity=(1, 5))
        pos3 = PositionalSpecification(name="last", arity=1)
        spec = command("test", positionals=[pos1, pos2, pos3])
        ctx = make_context(spec=spec)
        for i, val in enumerate(["a", "b", "c"]):
            ctx.add_positional_value(val, i)

        grouped = ctx.group_positionals()

        assert grouped["first"] == "a"
        assert grouped["middle"] == ("b",)
        assert grouped["last"] == "c"


# =============================================================================
# Result shape tests
# =============================================================================


class TestGroupPositionalsResultShapes:
    def test_arity_int_one_returns_scalar_string(self) -> None:
        pos = PositionalSpecification(name="file", arity=1)
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("test.txt", 0)

        grouped = ctx.group_positionals()

        assert grouped["file"] == "test.txt"
        assert isinstance(grouped["file"], str)

    def test_arity_tuple_one_one_returns_scalar_string(self) -> None:
        pos = PositionalSpecification(name="file", arity=(1, 1))
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("test.txt", 0)

        grouped = ctx.group_positionals()

        assert grouped["file"] == "test.txt"
        assert isinstance(grouped["file"], str)

    def test_arity_int_two_returns_tuple(self) -> None:
        pos = PositionalSpecification(name="files", arity=2)
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("a.txt", 0)
        ctx.add_positional_value("b.txt", 1)

        grouped = ctx.group_positionals()

        assert grouped["files"] == ("a.txt", "b.txt")
        assert isinstance(grouped["files"], tuple)

    def test_arity_star_returns_tuple(self) -> None:
        pos = PositionalSpecification(name="files", arity="*")
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("a.txt", 0)
        ctx.add_positional_value("b.txt", 1)

        grouped = ctx.group_positionals()

        assert grouped["files"] == ("a.txt", "b.txt")
        assert isinstance(grouped["files"], tuple)

    def test_arity_star_with_no_values_returns_empty_tuple(self) -> None:
        pos = PositionalSpecification(name="files", arity="*")
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)

        grouped = ctx.group_positionals()

        assert grouped["files"] == ()
        assert isinstance(grouped["files"], tuple)

    def test_arity_range_returns_tuple(self) -> None:
        pos = PositionalSpecification(name="files", arity=(2, 4))
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("a.txt", 0)
        ctx.add_positional_value("b.txt", 1)
        ctx.add_positional_value("c.txt", 2)

        grouped = ctx.group_positionals()

        assert grouped["files"] == ("a.txt", "b.txt", "c.txt")
        assert isinstance(grouped["files"], tuple)

    def test_arity_optional_with_value_returns_tuple(self) -> None:
        pos = PositionalSpecification(name="file", arity="?")
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("test.txt", 0)

        grouped = ctx.group_positionals()

        assert grouped["file"] == ("test.txt",)
        assert isinstance(grouped["file"], tuple)

    def test_arity_optional_without_value_returns_empty_tuple(self) -> None:
        pos = PositionalSpecification(name="file", arity="?")
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)

        grouped = ctx.group_positionals()

        assert grouped["file"] == ()


# =============================================================================
# Edge cases tests
# =============================================================================


class TestGroupPositionalsEdgeCases:
    def test_no_positional_specs_uses_implicit_args_spec(self) -> None:
        spec = command("test")
        ctx = make_context(spec=spec)
        ctx.add_positional_value("a", 0)
        ctx.add_positional_value("b", 1)

        grouped = ctx.group_positionals()

        assert "args" in grouped
        assert grouped["args"] == ("a", "b")

    def test_empty_positionals_tuple_uses_implicit_args_spec(self) -> None:
        spec = command("test", positionals=[])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("a", 0)

        grouped = ctx.group_positionals()

        assert "args" in grouped
        assert grouped["args"] == ("a",)

    def test_zero_positionals_when_all_optional_returns_empty(self) -> None:
        pos1 = PositionalSpecification(name="opt1", arity="?")
        pos2 = PositionalSpecification(name="opt2", arity="*")
        spec = command("test", positionals=[pos1, pos2])
        ctx = make_context(spec=spec)

        grouped = ctx.group_positionals()

        assert grouped["opt1"] == ()
        assert grouped["opt2"] == ()

    def test_insufficient_positionals_raises_error(self) -> None:
        pos = PositionalSpecification(name="files", arity=3)
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("a.txt", 0)
        ctx.add_positional_value("b.txt", 1)

        with pytest.raises(PositionalMissingValueError) as exc_info:
            ctx.group_positionals()

        assert "3" in str(exc_info.value) or exc_info.value.required == 3

    def test_insufficient_positionals_for_later_spec_raises_error(self) -> None:
        pos1 = PositionalSpecification(name="first", arity=1)
        pos2 = PositionalSpecification(name="second", arity=2)
        spec = command("test", positionals=[pos1, pos2])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("only_one", 0)

        with pytest.raises(PositionalMissingValueError):
            ctx.group_positionals()

    def test_single_positional_consuming_all(self) -> None:
        pos = PositionalSpecification(name="all", arity=(1, "*"))
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        for i in range(10):
            ctx.add_positional_value(f"arg{i}", i)

        grouped = ctx.group_positionals()

        assert len(grouped["all"]) == 10
        assert grouped["all"][0] == "arg0"
        assert grouped["all"][9] == "arg9"

    def test_multiple_required_then_unbounded_at_end(self) -> None:
        pos1 = PositionalSpecification(name="first", arity=1)
        pos2 = PositionalSpecification(name="second", arity=1)
        pos3 = PositionalSpecification(name="rest", arity="*")
        spec = command("test", positionals=[pos1, pos2, pos3])
        ctx = make_context(spec=spec)
        for i, val in enumerate(["a", "b", "c", "d", "e"]):
            ctx.add_positional_value(val, i)

        grouped = ctx.group_positionals()

        assert grouped["first"] == "a"
        assert grouped["second"] == "b"
        assert grouped["rest"] == ("c", "d", "e")


# =============================================================================
# Arity types tests
# =============================================================================


class TestGroupPositionalsArityTypes:
    def test_fixed_int_arity(self) -> None:
        pos = PositionalSpecification(name="fixed", arity=3)
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        for i, val in enumerate(["a", "b", "c"]):
            ctx.add_positional_value(val, i)

        grouped = ctx.group_positionals()

        assert grouped["fixed"] == ("a", "b", "c")

    def test_optional_question_mark_arity_with_value(self) -> None:
        pos = PositionalSpecification(name="opt", arity="?")
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("value", 0)

        grouped = ctx.group_positionals()

        assert grouped["opt"] == ("value",)

    def test_optional_question_mark_arity_without_value(self) -> None:
        pos = PositionalSpecification(name="opt", arity="?")
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)

        grouped = ctx.group_positionals()

        assert grouped["opt"] == ()

    def test_unbounded_star_arity_with_values(self) -> None:
        pos = PositionalSpecification(name="files", arity="*")
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        for i in range(5):
            ctx.add_positional_value(f"file{i}", i)

        grouped = ctx.group_positionals()

        assert grouped["files"] == ("file0", "file1", "file2", "file3", "file4")

    def test_unbounded_star_arity_without_values(self) -> None:
        pos = PositionalSpecification(name="files", arity="*")
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)

        grouped = ctx.group_positionals()

        assert grouped["files"] == ()

    def test_greedy_ellipsis_arity(self) -> None:
        pos = PositionalSpecification(name="args", arity="...")
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        for i in range(3):
            ctx.add_positional_value(f"arg{i}", i)

        grouped = ctx.group_positionals()

        assert grouped["args"] == ("arg0", "arg1", "arg2")

    def test_greedy_ellipsis_arity_empty(self) -> None:
        pos = PositionalSpecification(name="args", arity="...")
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)

        grouped = ctx.group_positionals()

        assert grouped["args"] == ()

    def test_range_tuple_arity_min_equals_max(self) -> None:
        pos = PositionalSpecification(name="pair", arity=(2, 2))
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("a", 0)
        ctx.add_positional_value("b", 1)

        grouped = ctx.group_positionals()

        assert grouped["pair"] == ("a", "b")

    def test_range_tuple_arity_variable(self) -> None:
        pos = PositionalSpecification(name="items", arity=(1, 3))
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("a", 0)
        ctx.add_positional_value("b", 1)

        grouped = ctx.group_positionals()

        assert grouped["items"] == ("a", "b")

    def test_range_with_unbounded_max(self) -> None:
        pos = PositionalSpecification(name="files", arity=(2, "*"))
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        for i in range(5):
            ctx.add_positional_value(f"f{i}", i)

        grouped = ctx.group_positionals()

        assert grouped["files"] == ("f0", "f1", "f2", "f3", "f4")

    def test_range_with_greedy_max(self) -> None:
        pos = PositionalSpecification(name="args", arity=(1, "..."))
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        for i in range(4):
            ctx.add_positional_value(f"a{i}", i)

        grouped = ctx.group_positionals()

        assert grouped["args"] == ("a0", "a1", "a2", "a3")


class TestGroupPositionalsComplexScenarios:
    def test_optional_followed_by_required(self) -> None:
        pos1 = PositionalSpecification(name="opt", arity="?")
        pos2 = PositionalSpecification(name="req", arity=1)
        spec = command("test", positionals=[pos1, pos2])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("only", 0)

        grouped = ctx.group_positionals()

        assert grouped["opt"] == ()
        assert grouped["req"] == "only"

    def test_optional_followed_by_required_with_both_values(self) -> None:
        pos1 = PositionalSpecification(name="opt", arity="?")
        pos2 = PositionalSpecification(name="req", arity=1)
        spec = command("test", positionals=[pos1, pos2])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("first", 0)
        ctx.add_positional_value("second", 1)

        grouped = ctx.group_positionals()

        assert grouped["opt"] == ("first",)
        assert grouped["req"] == "second"

    def test_range_with_exact_minimum(self) -> None:
        pos = PositionalSpecification(name="files", arity=(2, 5))
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        ctx.add_positional_value("a", 0)
        ctx.add_positional_value("b", 1)

        grouped = ctx.group_positionals()

        assert grouped["files"] == ("a", "b")

    def test_range_with_exact_maximum(self) -> None:
        pos = PositionalSpecification(name="files", arity=(2, 5))
        spec = command("test", positionals=[pos])
        ctx = make_context(spec=spec)
        for i in range(5):
            ctx.add_positional_value(f"f{i}", i)

        grouped = ctx.group_positionals()

        assert grouped["files"] == ("f0", "f1", "f2", "f3", "f4")

    def test_range_consumes_up_to_max_but_not_beyond(self) -> None:
        pos1 = PositionalSpecification(name="limited", arity=(1, 3))
        pos2 = PositionalSpecification(name="rest", arity="*")
        spec = command("test", positionals=[pos1, pos2])
        ctx = make_context(spec=spec)
        for i in range(6):
            ctx.add_positional_value(f"v{i}", i)

        grouped = ctx.group_positionals()

        assert grouped["limited"] == ("v0", "v1", "v2")
        assert grouped["rest"] == ("v3", "v4", "v5")
