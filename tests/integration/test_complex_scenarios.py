"""Integration tests for complex option and feature combinations."""

from typing import TYPE_CHECKING

from flagrant.parser import parse_command_line_args
from flagrant.specification import (
    Arity,
)
from flagrant.specification.enums import (
    FlagAccumulationMode,
    ValueAccumulationMode,
)

if TYPE_CHECKING:
    from flagrant.specification import (
        CommandSpecificationFactory,
        FlagOptionSpecificationFactory,
        ValueOptionSpecificationFactory,
    )


class TestMultipleOptionInteractions:
    def test_mixed_short_and_long_options_with_values(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        verbose = make_flag_opt(name="verbose", short_names=("v",))
        output = make_value_opt(name="output", short_names=("o",))
        fmt = make_value_opt(name="format", short_names=("f",))
        spec = make_command(
            options={"verbose": verbose, "output": output, "format": fmt}
        )

        result = parse_command_line_args(
            spec, ["-v", "--output", "file.txt", "-f", "json"]
        )

        assert result.options["verbose"] is True
        assert result.options["output"] == "file.txt"
        assert result.options["format"] == "json"

    def test_options_interspersed_with_positionals(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        force = make_flag_opt(name="force", short_names=("f",))
        recursive = make_flag_opt(
            name="recursive", short_names=("r",)
        )
        spec = make_command(
            options={"force": force, "recursive": recursive},
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

    def test_repeated_options_with_different_accumulation_modes(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        verbose = make_flag_opt(
            name="verbose",
            short_names=("v",),
            accumulation_mode=FlagAccumulationMode.COUNT,
        )
        include = make_value_opt(
            name="include",
            arity=Arity.at_least_one(),
            short_names=("I",),
            accumulation_mode=ValueAccumulationMode.EXTEND,
        )
        spec = make_command(options={"verbose": verbose, "include": include})

        result = parse_command_line_args(
            spec, ["-v", "-v", "-v", "-I", "*.py", "-I", "*.txt"]
        )

        assert result.options["verbose"] == 3
        assert result.options["include"] == ("*.py", "*.txt")


class TestSubcommandComplexity:
    def test_subcommand_with_parent_and_child_options(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        config = make_value_opt(name="config", short_names=("c",))
        target = make_value_opt(name="target", short_names=("t",))
        verbose = make_flag_opt(name="verbose", short_names=("v",))

        build_cmd = make_command(
            "build",
            options={"target": target, "verbose": verbose},
            positionals={"files": Arity.zero_or_more()},
        )
        spec = make_command(
            options={"config": config}, subcommands={"build": build_cmd}
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

    def test_three_level_subcommands_with_options_at_each_level(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        global_opt = make_flag_opt(name="global", short_names=("g",))
        level1_opt = make_flag_opt(name="level1-opt")
        level2_opt = make_value_opt(name="level2-opt")

        level2_cmd = make_command("level2", options={"level2-opt": level2_opt})
        level1_cmd = make_command(
            "level1",
            options={"level1-opt": level1_opt},
            subcommands={"level2": level2_cmd},
        )
        spec = make_command(
            "test", options={"global": global_opt}, subcommands={"level1": level1_cmd}
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
    def test_clustered_flags_followed_by_value_option(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        verbose = make_flag_opt(
            name="verbose", long_names=(), short_names=("v",)
        )
        interactive = make_flag_opt(
            name="interactive",
            long_names=(),
            short_names=("i",),
        )
        file_opt = make_value_opt(
            name="file", long_names=(), short_names=("f",)
        )
        spec = make_command(
            options={"verbose": verbose, "interactive": interactive, "file": file_opt}
        )

        result = parse_command_line_args(spec, ["-vif", "output.txt"])

        assert result.options["verbose"] is True
        assert result.options["interactive"] is True
        assert result.options["file"] == "output.txt"

    def test_multiple_value_options_with_different_arities(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        single = make_value_opt(name="single", short_names=("s",))
        multi = make_value_opt(
            name="multi", arity=Arity.at_least_one(), short_names=("m",)
        )
        optional = make_value_opt(
            name="optional", arity=Arity.at_most_one(), short_names=("o",)
        )
        spec = make_command(
            options={"single": single, "multi": multi, "optional": optional}
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
    def test_separator_with_options_and_positionals_before_and_after(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        verbose = make_flag_opt(name="verbose", short_names=("v",))
        spec = make_command(
            options={"verbose": verbose},
            positionals={"files": Arity.zero_or_more()},
        )

        result = parse_command_line_args(
            spec,
            ["-v", "file1.txt", "--", "--not-an-option", "-also-not-an-option"],
        )

        assert result.options["verbose"] is True
        assert result.positionals["files"] == ("file1.txt",)
        assert result.extra_args == ("--not-an-option", "-also-not-an-option")
