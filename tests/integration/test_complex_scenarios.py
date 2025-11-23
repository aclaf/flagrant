"""Integration tests for complex option and feature combinations."""

from flagrant.parser import parse_command_line_args
from flagrant.specification import (
    Arity,
    CommandSpecification,
    FlagOptionSpecification,
    ValueOptionSpecification,
)
from flagrant.specification.enums import (
    FlagAccumulationMode,
    ValueAccumulationMode,
)


class TestMultipleOptionInteractions:
    def test_mixed_short_and_long_options_with_values(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=("v",),
                ),
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=("output",),
                    short_names=("o",),
                ),
                "format": ValueOptionSpecification(
                    name="format",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="format",
                    long_names=("format",),
                    short_names=("f",),
                ),
            },
        )

        result = parse_command_line_args(
            spec, ["-v", "--output", "file.txt", "-f", "json"]
        )

        assert result.options["verbose"] is True
        assert result.options["output"] == "file.txt"
        assert result.options["format"] == "json"

    def test_options_interspersed_with_positionals(self):
        spec = CommandSpecification(
            "test",
            options={
                "force": FlagOptionSpecification(
                    name="force",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="force",
                    long_names=("force",),
                    short_names=("f",),
                ),
                "recursive": FlagOptionSpecification(
                    name="recursive",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="recursive",
                    long_names=("recursive",),
                    short_names=("r",),
                ),
            },
            positionals={
                "source": Arity.exactly_one(),
                "dest": Arity.exactly_one(),
            },
        )

        result = parse_command_line_args(
            spec, ["--force", "src.txt", "--recursive", "dest.txt"]
        )

        assert result.options["force"] is True
        assert result.options["recursive"] is True
        assert result.positionals["source"] == "src.txt"
        assert result.positionals["dest"] == "dest.txt"

    def test_repeated_options_with_different_accumulation_modes(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=("v",),
                    accumulation_mode=FlagAccumulationMode.COUNT,
                ),
                "include": ValueOptionSpecification(
                    name="include",
                    arity=Arity.at_least_one(),
                    greedy=False,
                    preferred_name="include",
                    long_names=("include",),
                    short_names=("I",),
                    accumulation_mode=ValueAccumulationMode.EXTEND,
                ),
            },
        )

        result = parse_command_line_args(
            spec, ["-v", "-v", "-v", "-I", "*.py", "-I", "*.txt"]
        )

        assert result.options["verbose"] == 3
        assert result.options["include"] == ("*.py", "*.txt")


class TestSubcommandComplexity:
    def test_subcommand_with_parent_and_child_options(self):
        spec = CommandSpecification(
            "test",
            options={
                "config": ValueOptionSpecification(
                    name="config",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="config",
                    long_names=("config",),
                    short_names=("c",),
                ),
            },
            subcommands={
                "build": CommandSpecification(
                    "build",
                    options={
                        "target": ValueOptionSpecification(
                            name="target",
                            arity=Arity.exactly_one(),
                            greedy=False,
                            preferred_name="target",
                            long_names=("target",),
                            short_names=("t",),
                        ),
                        "verbose": FlagOptionSpecification(
                            name="verbose",
                            arity=Arity.none(),
                            greedy=False,
                            preferred_name="verbose",
                            long_names=("verbose",),
                            short_names=("v",),
                        ),
                    },
                    positionals={
                        "files": Arity.zero_or_more(),
                    },
                ),
            },
        )

        result = parse_command_line_args(
            spec,
            [
                "--config",
                "prod.yaml",
                "build",
                "-v",
                "--target",
                "release",
                "main.c",
                "utils.c",
            ],
        )

        assert result.options["config"] == "prod.yaml"
        assert result.subcommand is not None
        assert result.subcommand.command == "build"
        assert result.subcommand.options["verbose"] is True
        assert result.subcommand.options["target"] == "release"
        assert result.subcommand.positionals["files"] == ("main.c", "utils.c")

    def test_three_level_subcommands_with_options_at_each_level(self):
        spec = CommandSpecification(
            "test",
            options={
                "global": FlagOptionSpecification(
                    name="global",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="global",
                    long_names=("global",),
                    short_names=("g",),
                ),
            },
            subcommands={
                "level1": CommandSpecification(
                    "level1",
                    options={
                        "level1-opt": FlagOptionSpecification(
                            name="level1-opt",
                            arity=Arity.none(),
                            greedy=False,
                            preferred_name="level1-opt",
                            long_names=("level1-opt",),
                            short_names=(),
                        ),
                    },
                    subcommands={
                        "level2": CommandSpecification(
                            "level2",
                            options={
                                "level2-opt": ValueOptionSpecification(
                                    name="level2-opt",
                                    arity=Arity.exactly_one(),
                                    greedy=False,
                                    preferred_name="level2-opt",
                                    long_names=("level2-opt",),
                                    short_names=(),
                                ),
                            },
                        ),
                    },
                ),
            },
        )

        result = parse_command_line_args(
            spec,
            ["--global", "level1", "--level1-opt", "level2", "--level2-opt", "value"],
        )

        assert result.options["global"] is True
        assert result.subcommand is not None
        assert result.subcommand.command == "level1"
        assert result.subcommand.options["level1-opt"] is True
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "level2"
        assert result.subcommand.subcommand.options["level2-opt"] == "value"


class TestClusteredOptionsWithValues:
    def test_clustered_flags_followed_by_value_option(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=(),
                    short_names=("v",),
                ),
                "interactive": FlagOptionSpecification(
                    name="interactive",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="interactive",
                    long_names=(),
                    short_names=("i",),
                ),
                "file": ValueOptionSpecification(
                    name="file",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="file",
                    long_names=(),
                    short_names=("f",),
                ),
            },
        )

        result = parse_command_line_args(spec, ["-vif", "output.txt"])

        assert result.options["verbose"] is True
        assert result.options["interactive"] is True
        assert result.options["file"] == "output.txt"

    def test_multiple_value_options_with_different_arities(self):
        spec = CommandSpecification(
            "test",
            options={
                "single": ValueOptionSpecification(
                    name="single",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="single",
                    long_names=("single",),
                    short_names=("s",),
                ),
                "multi": ValueOptionSpecification(
                    name="multi",
                    arity=Arity.at_least_one(),
                    greedy=False,
                    preferred_name="multi",
                    long_names=("multi",),
                    short_names=("m",),
                ),
                "optional": ValueOptionSpecification(
                    name="optional",
                    arity=Arity.at_most_one(),
                    greedy=False,
                    preferred_name="optional",
                    long_names=("optional",),
                    short_names=("o",),
                ),
            },
        )

        result = parse_command_line_args(
            spec,
            [
                "--single",
                "one",
                "--multi",
                "a",
                "b",
                "c",
                "--optional",
            ],
        )

        assert result.options["single"] == "one"
        assert result.options["multi"] == ("a", "b", "c")
        assert result.options["optional"] == ()


class TestSeparatorWithComplexCommands:
    def test_separator_with_options_and_positionals_before_and_after(self):
        spec = CommandSpecification(
            "test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=("v",),
                ),
            },
            positionals={
                "files": Arity.zero_or_more(),
            },
        )

        result = parse_command_line_args(
            spec,
            ["-v", "file1.txt", "--", "--not-an-option", "-also-not-an-option"],
        )

        assert result.options["verbose"] is True
        assert result.positionals["files"] == ("file1.txt",)
        assert result.extra_args == ("--not-an-option", "-also-not-an-option")
