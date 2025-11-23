from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import AmbiguousOptionError, UnknownOptionError

if TYPE_CHECKING:
    from flagrant.specification import (
        CommandSpecificationFactory,
        FlagOptionSpecificationFactory,
        ValueOptionSpecificationFactory,
    )


class TestOptionAbbreviation:
    def test_unambiguous_prefix_matching_for_long_options(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            options={
                "verbose": make_flag_opt(name="verbose"),
                "version": make_flag_opt(name="version"),
                "help": make_flag_opt(name="help"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_options=True)

        result = parse_command_line_args(spec, ["--verb"], config)

        assert result.options["verbose"] is True
        assert "version" not in result.options
        assert "help" not in result.options

    def test_ambiguous_prefix_raises_error(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            options={
                "verbose": make_flag_opt(name="verbose"),
                "version": make_flag_opt(name="version"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_options=True)

        with pytest.raises(AmbiguousOptionError) as exc_info:
            parse_command_line_args(spec, ["--ver"], config)

        assert exc_info.value.option == "ver"
        assert "verbose" in exc_info.value.matched
        assert "version" in exc_info.value.matched

    def test_exact_match_takes_precedence_over_prefix(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            options={
                "help": make_flag_opt(name="help"),
                "helpful": make_flag_opt(name="helpful"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_options=True)

        result = parse_command_line_args(spec, ["--help"], config)

        assert result.options["help"] is True
        assert "helpful" not in result.options

    def test_abbreviation_with_values(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            options={
                "output": make_value_opt(name="output"),
                "optimize": make_value_opt(name="optimize"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_options=True)

        result = parse_command_line_args(spec, ["--out=file.txt", "--opt=3"], config)

        assert result.options["output"] == "file.txt"
        assert result.options["optimize"] == "3"

    def test_abbreviation_disabled_in_config(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            options={"verbose": make_flag_opt(name="verbose")},
        )
        config = ParserConfiguration(allow_abbreviated_options=False)

        with pytest.raises(UnknownOptionError) as exc_info:
            parse_command_line_args(spec, ["--verb"], config)

        assert exc_info.value.option == "verb"

    def test_minimum_abbreviation_length(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            options={
                "verbose": make_flag_opt(name="verbose"),
                "version": make_flag_opt(name="version"),
            },
        )
        config = ParserConfiguration(
            allow_abbreviated_options=True, minimum_abbreviation_length=3
        )

        with pytest.raises(UnknownOptionError):
            parse_command_line_args(spec, ["--ve"], config)

        with pytest.raises(AmbiguousOptionError):
            parse_command_line_args(spec, ["--ver"], config)

        result = parse_command_line_args(spec, ["--vers"], config)
        assert "version" in result.options

    def test_interaction_with_aliases(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            options={
                "verbose": make_value_opt(
                    name="verbose", long_names=("verbose", "verbosity")
                ),
                "version": make_flag_opt(name="version"),
            },
        )
        config = ParserConfiguration(allow_abbreviated_options=True)

        with pytest.raises(AmbiguousOptionError) as exc_info:
            parse_command_line_args(spec, ["--verbos=2"], config)

        assert "verbose" in exc_info.value.matched
        assert "verbosity" in exc_info.value.matched

        result = parse_command_line_args(spec, ["--verbosi=2"], config)
        assert "verbose" in result.options
        assert result.options["verbose"] == "2"

    def test_case_sensitivity_in_abbreviation(
        self,
        make_command: "CommandSpecificationFactory",
        make_flag_opt: "FlagOptionSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            options={
                "verbose": make_flag_opt(name="verbose"),
                "VERSION": make_flag_opt(name="VERSION"),
            },
        )

        config_sensitive = ParserConfiguration(
            allow_abbreviated_options=True, case_sensitive_options=True
        )

        result = parse_command_line_args(spec, ["--verb"], config_sensitive)
        assert result.options["verbose"] is True

        result = parse_command_line_args(spec, ["--VERS"], config_sensitive)
        assert result.options["VERSION"] is True

        config_insensitive = ParserConfiguration(
            allow_abbreviated_options=True, case_sensitive_options=False
        )

        with pytest.raises(AmbiguousOptionError):
            parse_command_line_args(spec, ["--ver"], config_insensitive)


class TestInteractionWithAbbreviation:
    def test_inline_value_without_equals_with_abbreviation_enabled(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            options={
                "output": make_value_opt(name="output"),
                "optimize": make_value_opt(name="optimize"),
            },
        )
        config = ParserConfiguration(
            allow_inline_values_without_equals=True,
            allow_abbreviated_options=True,
        )

        result = parse_command_line_args(spec, ["--outputfile.txt"], config)

        assert result.options["output"] == "file.txt"

    def test_abbreviation_takes_precedence_over_inline_prefix_match(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            options={
                "out": make_value_opt(name="out"),
                "output": make_value_opt(name="output"),
            },
        )
        config = ParserConfiguration(
            allow_inline_values_without_equals=True,
            allow_abbreviated_options=True,
        )

        result = parse_command_line_args(spec, ["--out", "value"], config)

        assert result.options["out"] == "value"
        assert "output" not in result.options

    def test_ambiguous_abbreviation_with_inline_values(
        self,
        make_command: "CommandSpecificationFactory",
        make_value_opt: "ValueOptionSpecificationFactory",
    ):
        spec = make_command(
            name="test",
            options={
                "verbose": make_value_opt(name="verbose"),
                "version": make_value_opt(name="version"),
            },
        )
        config = ParserConfiguration(
            allow_inline_values_without_equals=True,
            allow_abbreviated_options=True,
        )

        with pytest.raises(AmbiguousOptionError) as exc_info:
            parse_command_line_args(spec, ["--ver", "value"], config)

        assert exc_info.value.option == "ver"
        assert "verbose" in exc_info.value.matched
        assert "version" in exc_info.value.matched
