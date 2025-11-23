from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import OptionMissingValueError
from flagrant.specification import (
    Arity,
)

if TYPE_CHECKING:
    from flagrant.specification import (
        CommandSpecificationFactory,
        FlagOptionSpecificationFactory,
        ValueOptionSpecificationFactory,
    )


class TestGreedyModeBasic:
    def test_greedy_option_consumes_all_remaining_arguments(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="files", arity=Arity.at_least_one(), greedy=True)
        spec = make_command(options={"files": opt})

        result = parse_command_line_args(
            spec, ["--files", "file1.txt", "--output", "file2.txt", "-v"]
        )

        assert result.options["files"] == ("file1.txt", "--output", "file2.txt", "-v")

    def test_greedy_option_at_end_of_arguments(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="files", arity=Arity.at_least_one(), greedy=True)
        spec = make_command(options={"files": opt})

        result = parse_command_line_args(spec, ["--files", "single.txt"])

        assert result.options["files"] == ("single.txt",)


class TestGreedyModeWithDelimiter:
    def test_greedy_option_consumes_delimiter_and_trailing_args(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="args", arity=Arity.at_least_one(), greedy=True)
        spec = make_command(options={"args": opt})

        result = parse_command_line_args(
            spec, ["--args", "a", "b", "c", "--", "positional"]
        )

        assert result.options["args"] == ("a", "b", "c", "--", "positional")


class TestGreedyModeWithSubcommands:
    def test_greedy_option_stops_at_subcommand(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="files", arity=Arity.at_least_one(), greedy=True)
        build_cmd = make_command("build")
        spec = make_command(options={"files": opt}, subcommands={"build": build_cmd})

        result = parse_command_line_args(
            spec, ["--files", "file.txt", "build", "other.txt"]
        )

        assert result.options["files"] == ("file.txt",)
        assert result.subcommand is not None
        assert result.subcommand.command == "build"


class TestGreedyModeArityEnforcement:
    def test_greedy_option_enforces_minimum_arity(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(
            name="coords", arity=Arity(2, None), greedy=True, short_names=()
        )
        spec = make_command(options={"coords": opt})

        with pytest.raises(OptionMissingValueError) as exc_info:
            _ = parse_command_line_args(spec, ["--coords", "10"])

        assert exc_info.value.option == "coords"


class TestGreedyModeInlineValues:
    def test_greedy_option_with_inline_value_consumes_remaining_args(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="files", arity=Arity.at_least_one(), greedy=True)
        spec = make_command(options={"files": opt})

        result = parse_command_line_args(
            spec, ["--files=first.txt", "second.txt", "third.txt"]
        )

        assert result.options["files"] == ("first.txt", "second.txt", "third.txt")

    def test_greedy_option_inline_value_satisfies_minimum_arity(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="files", arity=Arity(2, None), greedy=True)
        spec = make_command(options={"files": opt})

        result = parse_command_line_args(spec, ["--files=first.txt", "second.txt"])

        assert result.options["files"] == ("first.txt", "second.txt")

    def test_greedy_option_inline_value_insufficient_arity_raises_error(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="files", arity=Arity(3, None), greedy=True)
        spec = make_command(options={"files": opt})

        with pytest.raises(OptionMissingValueError) as exc_info:
            _ = parse_command_line_args(spec, ["--files=first.txt", "second.txt"])

        assert exc_info.value.option == "files"


class TestGreedyModeNegativeNumbers:
    def test_greedy_option_consumes_negative_numbers(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="values", arity=Arity.at_least_one(), greedy=True)
        spec = make_command(options={"values": opt})
        config = ParserConfiguration(allow_negative_numbers=True)

        result = parse_command_line_args(
            spec, ["--values", "10", "-5", "3.14", "-99.9"], config=config
        )

        assert result.options["values"] == ("10", "-5", "3.14", "-99.9")

    def test_greedy_option_stops_at_option_not_negative_number(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        opt_values = make_value_opt(
            name="values", arity=Arity.at_least_one(), greedy=True
        )
        opt_verbose = make_flag_opt(name="verbose")
        spec = make_command(options={"values": opt_values, "verbose": opt_verbose})
        config = ParserConfiguration(allow_negative_numbers=True)

        result = parse_command_line_args(
            spec, ["--values", "10", "-5", "--verbose"], config=config
        )

        assert result.options["values"] == ("10", "-5")
        assert result.options["verbose"] is True

    def test_greedy_option_with_negative_number_config_disabled(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        opt = make_value_opt(name="values", arity=Arity.at_least_one(), greedy=True)
        spec = make_command(options={"values": opt})
        config = ParserConfiguration(allow_negative_numbers=False)

        result = parse_command_line_args(
            spec, ["--values", "10", "-5", "3"], config=config
        )

        assert result.options["values"] == ("10", "-5", "3")
