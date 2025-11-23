
from flagrant.configuration import ParserConfiguration
from flagrant.enums import UngroupedPositionalStrategy
from flagrant.parser import parse_command_line_args
from flagrant.specification import (
    Arity,
    CommandSpecification,
)


class TestUngroupedIgnoreWithDelimiter:
    def test_ignore_strategy_drops_delimiter_args(self):
        spec = CommandSpecification(
            "test",
            positionals={"file": Arity.exactly_one()},
        )
        config = ParserConfiguration(
            ungrouped_positional_strategy=UngroupedPositionalStrategy.IGNORE,
        )

        result = parse_command_line_args(
            spec, ["first.txt", "--", "after1.txt", "after2.txt"], config=config
        )

        assert result.positionals["file"] == "first.txt"
        assert len(result.positionals) == 1


class TestUngroupedCollectWithDelimiter:
    def test_collect_strategy_delimiter_args_dropped(self):
        spec = CommandSpecification(
            "test",
            positionals={"file": Arity.exactly_one()},
        )
        config = ParserConfiguration(
            ungrouped_positional_strategy=UngroupedPositionalStrategy.COLLECT,
            ungrouped_positional_name="extras",
        )

        result = parse_command_line_args(
            spec, ["first.txt", "--", "after1.txt", "after2.txt"], config=config
        )

        assert result.positionals["file"] == "first.txt"
        assert len(result.positionals) == 1

    def test_collect_strategy_ungrouped_before_delimiter(self):
        spec = CommandSpecification(
            "test",
            positionals={"file": Arity.exactly_one()},
        )
        config = ParserConfiguration(
            ungrouped_positional_strategy=UngroupedPositionalStrategy.COLLECT,
            ungrouped_positional_name="extras",
        )

        result = parse_command_line_args(
            spec, ["first.txt", "second.txt", "--"], config=config
        )

        assert result.positionals["file"] == "first.txt"
        assert result.positionals["extras"] == ("second.txt",)


class TestUngroupedErrorWithDelimiter:
    def test_error_strategy_delimiter_prevents_error(self):
        spec = CommandSpecification(
            "test",
            positionals={"file": Arity.exactly_one()},
        )
        config = ParserConfiguration(
            ungrouped_positional_strategy=UngroupedPositionalStrategy.ERROR,
        )

        result = parse_command_line_args(
            spec, ["first.txt", "--", "extra.txt"], config=config
        )

        assert result.positionals["file"] == "first.txt"
        assert len(result.positionals) == 1


class TestUngroupedStrategyWithUnboundedSpec:
    def test_ignore_with_unbounded_spec_no_ungrouped(self):
        spec = CommandSpecification(
            "test",
            positionals={"files": Arity.zero_or_more()},
        )
        config = ParserConfiguration(
            ungrouped_positional_strategy=UngroupedPositionalStrategy.IGNORE,
        )

        result = parse_command_line_args(
            spec, ["file1.txt", "file2.txt", "file3.txt"], config=config
        )

        assert result.positionals["files"] == ("file1.txt", "file2.txt", "file3.txt")
        assert len(result.positionals) == 1

    def test_collect_with_unbounded_spec_then_fixed(self):
        spec = CommandSpecification(
            "test",
            positionals={
                "files": Arity.at_least_one(),
                "output": Arity.exactly_one(),
            },
        )
        config = ParserConfiguration(
            ungrouped_positional_strategy=UngroupedPositionalStrategy.COLLECT,
            ungrouped_positional_name="extras",
        )

        result = parse_command_line_args(
            spec,
            ["file1.txt", "file2.txt", "file3.txt", "output.txt", "extra.txt"],
            config=config,
        )

        assert result.positionals["files"] == (
            "file1.txt",
            "file2.txt",
            "file3.txt",
            "output.txt",
        )
        assert result.positionals["output"] == "extra.txt"
        assert "extras" not in result.positionals
