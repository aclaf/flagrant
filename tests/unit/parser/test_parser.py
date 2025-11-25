from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser._parser import Parser
from flagrant.parser.exceptions import (
    AmbiguousOptionError,
    AmbiguousSubcommandError,
    UnknownOptionError,
    UnknownSubcommandError,
)
from flagrant.specification import (
    PositionalSpecification,
    command,
    flag_option,
    scalar_option,
)

if TYPE_CHECKING:
    from flagrant.specification import CommandSpecification


def make_simple_spec(
    name: str = "test",
    *,
    with_flag: bool = False,
    with_scalar: bool = False,
    with_positional: bool = False,
) -> "CommandSpecification":
    options = []
    positionals = []

    if with_flag:
        options.append(flag_option(["verbose", "v"]))
    if with_scalar:
        options.append(scalar_option(["output", "o"]))
    if with_positional:
        positionals.append(PositionalSpecification("file", "*"))

    return command(name, options=options or None, positionals=positionals or None)


def make_subcommand_spec() -> "CommandSpecification":
    sub_commit = command("commit", options=[flag_option(["all", "a"])])
    sub_push = command("push", options=[flag_option(["force", "f"])])
    return command("git", subcommands=[sub_commit, sub_push])


class TestParserInitialization:
    def test_initializes_with_spec_only(self) -> None:
        spec = make_simple_spec()
        parser = Parser(spec)

        assert parser.spec is spec
        assert parser.path == ("test",)
        assert parser.alias is None

    def test_initializes_with_custom_config(self) -> None:
        spec = make_simple_spec()
        config = ParserConfiguration(allow_negative_numbers=False)
        parser = Parser(spec, config=config)

        assert parser.config is config
        assert parser.config.allow_negative_numbers is False

    def test_initializes_with_path(self) -> None:
        spec = make_simple_spec()
        parser = Parser(spec, path=("parent", "child"))

        assert parser.path == ("parent", "child")

    def test_initializes_with_alias(self) -> None:
        spec = make_simple_spec()
        parser = Parser(spec, alias="t")

        assert parser.alias == "t"

    def test_registers_all_handlers(self) -> None:
        spec = make_simple_spec()
        parser = Parser(spec)

        assert len(parser._handlers) == 4


class TestParserOptionResolution:
    def test_long_option_resolves(self) -> None:
        spec = make_simple_spec(with_flag=True)
        result = parse_command_line_args(spec, ["--verbose"])

        assert result.options["verbose"] is True

    def test_short_option_resolves(self) -> None:
        spec = make_simple_spec(with_flag=True)
        result = parse_command_line_args(spec, ["-v"])

        assert result.options["verbose"] is True

    def test_unknown_option_raises_error(self) -> None:
        spec = make_simple_spec(with_flag=True)

        with pytest.raises(UnknownOptionError) as exc_info:
            parse_command_line_args(spec, ["--unknown"])

        assert exc_info.value.option == "--unknown"
        assert exc_info.value.path == ("test",)

    def test_ambiguous_option_raises_error(self) -> None:
        opt1 = scalar_option(["verbose"])
        opt2 = scalar_option(["version"])
        spec = command("test", options=[opt1, opt2])
        config = ParserConfiguration(allow_abbreviated_options=True)

        with pytest.raises(AmbiguousOptionError) as exc_info:
            parse_command_line_args(spec, ["--ver"], config=config)

        assert exc_info.value.option == "ver"
        assert "verbose" in exc_info.value.matched
        assert "version" in exc_info.value.matched

    def test_option_with_value(self) -> None:
        spec = make_simple_spec(with_scalar=True)
        result = parse_command_line_args(spec, ["--output", "file.txt"])

        assert result.options["output"] == "file.txt"

    def test_option_with_inline_value(self) -> None:
        spec = make_simple_spec(with_scalar=True)
        result = parse_command_line_args(spec, ["--output=file.txt"])

        assert result.options["output"] == "file.txt"


class TestParserNegativeNumbers:
    def test_negative_number_not_treated_as_option_when_allowed(self) -> None:
        spec = make_simple_spec(with_flag=True)
        config = ParserConfiguration(allow_negative_numbers=True)
        result = parse_command_line_args(spec, ["-5"], config=config)

        # -5 should not be treated as an option (no error, not in options)
        assert result.options.get("5") is None
        assert result.options.get("verbose") is None

    def test_negative_number_not_treated_as_option_by_default(self) -> None:
        spec = make_simple_spec(with_flag=True)
        result = parse_command_line_args(spec, ["-5"])

        # By default, negative numbers are allowed as positionals
        assert result.options.get("5") is None


class TestParserTrailingSeparator:
    def test_double_dash_stops_option_parsing(self) -> None:
        spec = make_simple_spec(with_flag=True)
        result = parse_command_line_args(spec, ["--", "--verbose"])

        assert result.options.get("verbose") is None
        assert "--verbose" in result.extra_args

    def test_args_after_separator_become_extra_args(self) -> None:
        spec = make_simple_spec()
        result = parse_command_line_args(spec, ["--", "a", "b", "c"])

        assert result.extra_args == ("a", "b", "c")

    def test_separator_with_no_following_args(self) -> None:
        spec = make_simple_spec()
        result = parse_command_line_args(spec, ["--"])

        assert result.extra_args == ()

    def test_options_before_separator_parsed(self) -> None:
        spec = make_simple_spec(with_flag=True)
        result = parse_command_line_args(spec, ["--verbose", "--", "--other"])

        assert result.options["verbose"] is True
        assert result.extra_args == ("--other",)


class TestParserSubcommandRouting:
    def test_valid_subcommand_routes_correctly(self) -> None:
        spec = make_subcommand_spec()
        result = parse_command_line_args(spec, ["commit", "--all"])

        assert result.subcommand is not None
        assert result.subcommand.command == "commit"
        assert result.subcommand.options["all"] is True

    def test_subcommand_path_propagation(self) -> None:
        spec = make_subcommand_spec()
        result = parse_command_line_args(spec, ["commit"])

        assert result.subcommand is not None
        assert result.path == ("git", "commit")

    def test_unknown_subcommand_raises_error(self) -> None:
        spec = make_subcommand_spec()

        with pytest.raises(UnknownSubcommandError) as exc_info:
            parse_command_line_args(spec, ["unknown"])

        assert exc_info.value.subcommand == "unknown"

    def test_ambiguous_subcommand_raises_error(self) -> None:
        sub_commit = command("commit")
        sub_compare = command("compare")
        spec = command("git", subcommands=[sub_commit, sub_compare])
        config = ParserConfiguration(allow_abbreviated_commands=True)

        with pytest.raises(AmbiguousSubcommandError) as exc_info:
            parse_command_line_args(spec, ["com"], config=config)

        assert "commit" in exc_info.value.matched
        assert "compare" in exc_info.value.matched

    def test_subcommand_receives_remaining_args(self) -> None:
        spec = make_subcommand_spec()
        result = parse_command_line_args(spec, ["push", "--force"])

        assert result.subcommand is not None
        assert result.subcommand.options["force"] is True


class TestParserArgumentLoop:
    def test_empty_args_returns_empty_result(self) -> None:
        spec = make_simple_spec()
        result = parse_command_line_args(spec, [])

        assert result.options == {}
        assert result.positionals == {}
        assert result.extra_args == ()

    def test_mixed_options_and_positionals(self) -> None:
        spec = make_simple_spec(with_flag=True, with_positional=True)
        result = parse_command_line_args(spec, ["--verbose", "file.txt"])

        assert result.options["verbose"] is True
        # Positional grouping is not yet implemented, but parsing succeeds
        assert result.extra_args == ()

    def test_single_dash_not_treated_as_option(self) -> None:
        spec = make_simple_spec(with_flag=True)
        result = parse_command_line_args(spec, ["-"])

        # Single dash is treated as positional, not an option
        assert result.options.get("verbose") is None

    def test_multiple_options(self) -> None:
        opt1 = flag_option(["verbose", "v"])
        opt2 = flag_option(["quiet", "q"])
        spec = command("test", options=[opt1, opt2])
        result = parse_command_line_args(spec, ["-v", "-q"])

        assert result.options["verbose"] is True
        assert result.options["quiet"] is True


class TestParseCommandLineArgs:
    def test_convenience_function_with_default_config(self) -> None:
        spec = make_simple_spec(with_flag=True)
        result = parse_command_line_args(spec, ["--verbose"])

        assert result.options["verbose"] is True

    def test_convenience_function_with_custom_config(self) -> None:
        spec = make_simple_spec()
        config = ParserConfiguration(trailing_arguments_separator="---")
        result = parse_command_line_args(spec, ["---", "extra"], config=config)

        assert result.extra_args == ("extra",)

    def test_returns_parse_result(self) -> None:
        spec = make_simple_spec()
        result = parse_command_line_args(spec, [])

        assert result.command == "test"
        assert hasattr(result, "options")
        assert hasattr(result, "positionals")
        assert hasattr(result, "extra_args")
