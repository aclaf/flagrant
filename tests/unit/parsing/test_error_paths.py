import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.enums import UngroupedPositionalStrategy
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import (
    PositionalUnexpectedValueError,
    UnknownSubcommandError,
)
from flagrant.specification import (
    Arity,
    CommandSpecification,
    FlagOptionSpecification,
)


class TestUnknownSubcommandError:
    def test_unknown_subcommand_raises_error_when_no_positionals(self):
        spec = CommandSpecification(
            "test",
            subcommands={
                "build": CommandSpecification("build"),
                "clean": CommandSpecification("clean"),
            },
        )

        with pytest.raises(UnknownSubcommandError) as exc_info:
            _ = parse_command_line_args(spec, ["unknown"])

        assert exc_info.value.subcommand == "unknown"

    def test_unknown_arg_becomes_positional_when_positionals_defined(self):
        spec = CommandSpecification(
            "test",
            subcommands={
                "build": CommandSpecification("build"),
            },
            positionals={"files": Arity.at_least_one()},
        )

        result = parse_command_line_args(spec, ["unknown.txt"])

        assert result.positionals["files"] == ("unknown.txt",)
        assert result.subcommand is None

    def test_unknown_subcommand_after_options(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=(),
                )
            },
            subcommands={
                "build": CommandSpecification("build"),
            },
        )

        with pytest.raises(UnknownSubcommandError) as exc_info:
            _ = parse_command_line_args(spec, ["--verbose", "unknown"])

        assert exc_info.value.subcommand == "unknown"

    def test_unknown_subcommand_after_delimiter(self):
        spec = CommandSpecification(
            "test",
            subcommands={
                "build": CommandSpecification("build"),
            },
        )

        result = parse_command_line_args(spec, ["--", "unknown"])

        assert result.subcommand is None


class TestUngroupedPositionalStrategyIgnore:
    def test_ignore_strategy_drops_extra_positionals(self):
        spec = CommandSpecification(
            "test",
            positionals={"file": Arity.exactly_one()},
        )

        config = ParserConfiguration(
            ungrouped_positional_strategy=UngroupedPositionalStrategy.IGNORE
        )

        result = parse_command_line_args(
            spec,
            ["first.txt", "extra1.txt", "extra2.txt"],
            config=config,
        )

        assert result.positionals["file"] == "first.txt"
        assert len(result.positionals) == 1

    def test_ignore_strategy_with_no_positional_specs(self):
        spec = CommandSpecification("test")

        config = ParserConfiguration(
            ungrouped_positional_strategy=UngroupedPositionalStrategy.IGNORE
        )

        result = parse_command_line_args(
            spec,
            ["pos1", "pos2", "pos3"],
            config=config,
        )

        assert result.positionals == {}

    def test_ignore_strategy_after_satisfied_specs(self):
        spec = CommandSpecification(
            "test",
            positionals={
                "input": Arity.exactly_one(),
                "output": Arity.exactly_one(),
            },
        )

        config = ParserConfiguration(
            ungrouped_positional_strategy=UngroupedPositionalStrategy.IGNORE
        )

        result = parse_command_line_args(
            spec,
            ["in.txt", "out.txt", "extra1.txt", "extra2.txt"],
            config=config,
        )

        assert result.positionals["input"] == "in.txt"
        assert result.positionals["output"] == "out.txt"
        assert len(result.positionals) == 2


class TestUngroupedPositionalStrategyCollect:
    def test_collect_strategy_gathers_extras(self):
        spec = CommandSpecification(
            "test",
            positionals={"file": Arity.exactly_one()},
        )

        config = ParserConfiguration(
            ungrouped_positional_strategy=UngroupedPositionalStrategy.COLLECT,
            ungrouped_positional_name="extras",
        )

        result = parse_command_line_args(
            spec,
            ["first.txt", "extra1.txt", "extra2.txt"],
            config=config,
        )

        assert result.positionals["file"] == "first.txt"
        assert result.positionals["extras"] == ("extra1.txt", "extra2.txt")

    def test_collect_strategy_with_no_specs(self):
        spec = CommandSpecification("test")

        config = ParserConfiguration(
            ungrouped_positional_strategy=UngroupedPositionalStrategy.COLLECT,
            ungrouped_positional_name="args",
        )

        result = parse_command_line_args(
            spec,
            ["pos1", "pos2", "pos3"],
            config=config,
        )

        assert result.positionals["args"] == ("pos1", "pos2", "pos3")

    def test_collect_strategy_custom_name(self):
        spec = CommandSpecification("test")

        config = ParserConfiguration(
            ungrouped_positional_strategy=UngroupedPositionalStrategy.COLLECT,
            ungrouped_positional_name="remaining_args",
        )

        result = parse_command_line_args(
            spec,
            ["arg1", "arg2"],
            config=config,
        )

        assert result.positionals["remaining_args"] == ("arg1", "arg2")


class TestUngroupedPositionalStrategyError:
    def test_error_strategy_raises_on_extras(self):
        spec = CommandSpecification(
            "test",
            positionals={"file": Arity.exactly_one()},
        )

        config = ParserConfiguration(
            ungrouped_positional_strategy=UngroupedPositionalStrategy.ERROR
        )

        with pytest.raises(PositionalUnexpectedValueError) as exc_info:
            _ = parse_command_line_args(
                spec,
                ["first.txt", "extra.txt"],
                config=config,
            )

        assert "extra.txt" in str(exc_info.value)

    def test_error_strategy_with_no_specs(self):
        spec = CommandSpecification("test")

        config = ParserConfiguration(
            ungrouped_positional_strategy=UngroupedPositionalStrategy.ERROR
        )

        with pytest.raises(PositionalUnexpectedValueError):
            _ = parse_command_line_args(
                spec,
                ["unexpected.txt"],
                config=config,
            )

    def test_error_strategy_message_includes_value(self):
        spec = CommandSpecification("test")

        config = ParserConfiguration(
            ungrouped_positional_strategy=UngroupedPositionalStrategy.ERROR
        )

        with pytest.raises(PositionalUnexpectedValueError) as exc_info:
            _ = parse_command_line_args(
                spec,
                ["unexpected.txt"],
                config=config,
            )

        error = exc_info.value
        assert hasattr(error, "value") or "unexpected.txt" in str(error)
