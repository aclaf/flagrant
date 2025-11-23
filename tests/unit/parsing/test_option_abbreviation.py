"""Tests for option abbreviation feature."""

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import AmbiguousOptionError, UnknownOptionError
from flagrant.specification import (
    Arity,
    CommandSpecification,
    FlagOptionSpecification,
    ValueOptionSpecification,
)


class TestOptionAbbreviation:
    def test_unambiguous_prefix_matching_for_long_options(self):
        spec = CommandSpecification(
            name="test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=(),
                ),
                "version": FlagOptionSpecification(
                    name="version",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="version",
                    long_names=("version",),
                    short_names=(),
                ),
                "help": FlagOptionSpecification(
                    name="help",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="help",
                    long_names=("help",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_abbreviated_options=True)

        result = parse_command_line_args(spec, ["--verb"], config)

        # Assert
        assert result.options["verbose"] is True
        assert "version" not in result.options
        assert "help" not in result.options

    def test_ambiguous_prefix_raises_error(self):
        # Arrange
        spec = CommandSpecification(
            name="test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=(),
                ),
                "version": FlagOptionSpecification(
                    name="version",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="version",
                    long_names=("version",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_abbreviated_options=True)

        # Act & Assert
        with pytest.raises(AmbiguousOptionError) as exc_info:
            parse_command_line_args(spec, ["--ver"], config)

        # Check that the exception contains the expected option names
        assert exc_info.value.option == "ver"
        assert "verbose" in exc_info.value.matched
        assert "version" in exc_info.value.matched

    def test_exact_match_takes_precedence_over_prefix(self):
        # Arrange
        spec = CommandSpecification(
            name="test",
            options={
                "help": FlagOptionSpecification(
                    name="help",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="help",
                    long_names=("help",),
                    short_names=(),
                ),
                "helpful": FlagOptionSpecification(
                    name="helpful",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="helpful",
                    long_names=("helpful",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_abbreviated_options=True)

        result = parse_command_line_args(spec, ["--help"], config)

        # Assert
        assert result.options["help"] is True
        assert "helpful" not in result.options

    def test_abbreviation_with_values(self):
        # Arrange
        spec = CommandSpecification(
            name="test",
            options={
                "output": ValueOptionSpecification(
                    name="output",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="output",
                    long_names=("output",),
                    short_names=(),
                ),
                "optimize": ValueOptionSpecification(
                    name="optimize",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="optimize",
                    long_names=("optimize",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_abbreviated_options=True)

        result = parse_command_line_args(spec, ["--out=file.txt", "--opt=3"], config)

        # Assert
        assert result.options["output"] == "file.txt"
        assert result.options["optimize"] == "3"

    def test_abbreviation_disabled_in_config(self):
        # Arrange
        spec = CommandSpecification(
            name="test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_abbreviated_options=False)

        # Act & Assert
        with pytest.raises(UnknownOptionError) as exc_info:
            parse_command_line_args(spec, ["--verb"], config)

        assert exc_info.value.option == "verb"

    def test_minimum_abbreviation_length(self):
        # Arrange
        spec = CommandSpecification(
            name="test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=(),
                ),
                "version": FlagOptionSpecification(
                    name="version",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="version",
                    long_names=("version",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(
            allow_abbreviated_options=True, minimum_abbreviation_length=3
        )

        # Act & Assert
        # Too short abbreviation should fail
        with pytest.raises(UnknownOptionError):
            parse_command_line_args(spec, ["--ve"], config)

        # "ver" is 3 chars and ambiguous between verbose and version
        # So this should raise AmbiguousOptionError
        with pytest.raises(AmbiguousOptionError):
            parse_command_line_args(spec, ["--ver"], config)

        # Unambiguous abbreviation of minimum length
        result = parse_command_line_args(spec, ["--vers"], config)
        assert "version" in result.options

    def test_interaction_with_aliases(self):
        # Arrange
        spec = CommandSpecification(
            name="test",
            options={
                "verbose": ValueOptionSpecification(
                    name="verbose",
                    arity=Arity.exactly_one(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose", "verbosity"),
                    short_names=(),
                ),
                "version": FlagOptionSpecification(
                    name="version",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="version",
                    long_names=("version",),
                    short_names=(),
                ),
            },
        )
        config = ParserConfiguration(allow_abbreviated_options=True)

        # Act & Assert
        # "verbos" is ambiguous between "verbose" and "verbosity" (aliases)
        # This should raise AmbiguousOptionError
        with pytest.raises(AmbiguousOptionError) as exc_info:
            parse_command_line_args(spec, ["--verbos=2"], config)

        assert "verbose" in exc_info.value.matched
        assert "verbosity" in exc_info.value.matched

        # But "verbosi" should work as it uniquely matches "verbosity"
        result = parse_command_line_args(spec, ["--verbosi=2"], config)
        assert "verbose" in result.options
        assert result.options["verbose"] == "2"

    def test_case_sensitivity_in_abbreviation(self):
        # Arrange
        spec = CommandSpecification(
            name="test",
            options={
                "verbose": FlagOptionSpecification(
                    name="verbose",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="verbose",
                    long_names=("verbose",),
                    short_names=(),
                ),
                "VERSION": FlagOptionSpecification(
                    name="VERSION",
                    arity=Arity.none(),
                    greedy=False,
                    preferred_name="VERSION",
                    long_names=("VERSION",),
                    short_names=(),
                ),
            },
        )

        # Test case-sensitive abbreviation (default)
        config_sensitive = ParserConfiguration(
            allow_abbreviated_options=True, case_sensitive_options=True
        )

        # Act & Assert - case sensitive
        result = parse_command_line_args(spec, ["--verb"], config_sensitive)
        assert result.options["verbose"] is True

        result = parse_command_line_args(spec, ["--VERS"], config_sensitive)
        assert result.options["VERSION"] is True

        # Test case-insensitive abbreviation
        config_insensitive = ParserConfiguration(
            allow_abbreviated_options=True, case_sensitive_options=False
        )

        # Both should now be ambiguous when case-insensitive
        with pytest.raises(AmbiguousOptionError):
            parse_command_line_args(spec, ["--ver"], config_insensitive)
