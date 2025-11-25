from typing import TYPE_CHECKING

import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.parser._resolver import (
    AmbiguousNames,
    CommandResolver,
    ResolvedCommand,
    ResolvedOption,
    is_ambiguous_names,
    is_resolved_command,
    is_resolved_option,
)
from flagrant.specification import command, flag_option, scalar_option

if TYPE_CHECKING:
    from flagrant.specification import CommandSpecification


def make_resolver(
    *,
    spec: "CommandSpecification | None" = None,
    config: ParserConfiguration | None = None,
) -> CommandResolver:
    if spec is None:
        spec = command("test")
    if config is None:
        config = ParserConfiguration()
    return CommandResolver(spec, config)


class TestCommandResolverInitialization:
    def test_creates_resolver_with_spec_and_config(self) -> None:
        spec = command("test")
        config = ParserConfiguration()

        resolver = CommandResolver(spec, config)

        assert resolver.spec is spec
        assert resolver.config is config

    def test_creates_option_lookup_maps(self) -> None:
        verbose = flag_option(["verbose", "v"])
        output = scalar_option(["output", "o"])
        spec = command("test", options=[verbose, output])

        resolver = make_resolver(spec=spec)

        assert resolver.get_option("verbose") is not None
        assert resolver.get_option("output") is not None


class TestCommandResolverProperties:
    def test_long_prefix_returns_config_value(self) -> None:
        config = ParserConfiguration(long_name_prefix="--")
        resolver = make_resolver(config=config)

        assert resolver.long_prefix == "--"

    def test_short_prefix_returns_config_value(self) -> None:
        config = ParserConfiguration(short_name_prefix="-")
        resolver = make_resolver(config=config)

        assert resolver.short_prefix == "-"

    def test_inline_value_separator_returns_config_value(self) -> None:
        config = ParserConfiguration(inline_value_separator="=")
        resolver = make_resolver(config=config)

        assert resolver.inline_value_separator == "="

    def test_abbreviated_options_allowed_returns_config_value(self) -> None:
        config = ParserConfiguration(allow_abbreviated_options=True)
        resolver = make_resolver(config=config)

        assert resolver.abbreviated_options_allowed is True

    def test_abbreviated_commands_allowed_returns_config_value(self) -> None:
        config = ParserConfiguration(allow_abbreviated_commands=True)
        resolver = make_resolver(config=config)

        assert resolver.abbreviated_commands_allowed is True


class TestIsLongOption:
    def test_recognizes_long_option(self) -> None:
        resolver = make_resolver()

        assert resolver.is_long_option("--verbose") is True

    def test_rejects_short_option(self) -> None:
        resolver = make_resolver()

        assert resolver.is_long_option("-v") is False

    def test_rejects_positional(self) -> None:
        resolver = make_resolver()

        assert resolver.is_long_option("file.txt") is False

    def test_uses_configured_prefix(self) -> None:
        config = ParserConfiguration(long_name_prefix="++", short_name_prefix="+")
        resolver = make_resolver(config=config)

        assert resolver.is_long_option("++verbose") is True
        assert resolver.is_long_option("--verbose") is False


class TestIsShortOption:
    def test_recognizes_short_option(self) -> None:
        resolver = make_resolver()

        assert resolver.is_short_option("-v") is True

    def test_rejects_long_option(self) -> None:
        resolver = make_resolver()

        assert resolver.is_short_option("--verbose") is False

    def test_rejects_positional(self) -> None:
        resolver = make_resolver()

        assert resolver.is_short_option("file.txt") is False

    def test_uses_configured_prefix(self) -> None:
        config = ParserConfiguration(short_name_prefix="/", long_name_prefix="//")
        resolver = make_resolver(config=config)

        assert resolver.is_short_option("/v") is True
        assert resolver.is_short_option("-v") is False


class TestExtractInlineValue:
    def test_extracts_value_after_equals(self) -> None:
        resolver = make_resolver()

        name, value = resolver.extract_inline_value("output=file.txt")

        assert name == "output"
        assert value == "file.txt"

    def test_returns_none_when_no_equals(self) -> None:
        resolver = make_resolver()

        name, value = resolver.extract_inline_value("verbose")

        assert name == "verbose"
        assert value is None

    def test_splits_on_first_equals_only(self) -> None:
        resolver = make_resolver()

        name, value = resolver.extract_inline_value("config=key=value")

        assert name == "config"
        assert value == "key=value"

    def test_handles_empty_value_after_equals(self) -> None:
        resolver = make_resolver()

        name, value = resolver.extract_inline_value("output=")

        assert name == "output"
        assert value == ""

    def test_uses_configured_separator(self) -> None:
        config = ParserConfiguration(inline_value_separator=":")
        resolver = make_resolver(config=config)

        name, value = resolver.extract_inline_value("output:file.txt")

        assert name == "output"
        assert value == "file.txt"


class TestResolveOption:
    def test_resolves_exact_long_option_name(self) -> None:
        verbose = flag_option(["verbose"])
        spec = command("test", options=[verbose])
        resolver = make_resolver(spec=spec)

        result = resolver.resolve_option("verbose")

        assert result is not None
        assert result.resolved_name == "verbose"

    def test_resolves_short_option_name(self) -> None:
        verbose = flag_option(["verbose", "v"])
        spec = command("test", options=[verbose])
        resolver = make_resolver(spec=spec)

        result = resolver.resolve_option("v")

        assert result is not None
        assert result.resolved_name == "verbose"

    def test_returns_none_for_unknown_option(self) -> None:
        verbose = flag_option(["verbose"])
        spec = command("test", options=[verbose])
        resolver = make_resolver(spec=spec)

        result = resolver.resolve_option("unknown")

        assert result is None

    def test_case_sensitive_by_default(self) -> None:
        verbose = flag_option(["Verbose"])
        spec = command("test", options=[verbose])
        resolver = make_resolver(spec=spec)

        result = resolver.resolve_option("verbose")

        assert result is None

    def test_case_insensitive_when_configured(self) -> None:
        verbose = flag_option(["Verbose"])
        spec = command("test", options=[verbose])
        config = ParserConfiguration(case_sensitive_options=False)
        resolver = make_resolver(spec=spec, config=config)

        result = resolver.resolve_option("verbose")

        assert result is not None
        assert result.resolved_name == "Verbose"

    def test_converts_underscores_to_hyphens_when_configured(self) -> None:
        dry_run = flag_option(["dry-run"])
        spec = command("test", options=[dry_run])
        config = ParserConfiguration(convert_underscores=True)
        resolver = make_resolver(spec=spec, config=config)

        result = resolver.resolve_option("dry_run")

        assert result is not None
        assert result.resolved_name == "dry-run"


class TestResolveOptionWithAbbreviations:
    def test_returns_none_when_abbreviations_disabled(self) -> None:
        verbose = flag_option(["verbose"])
        spec = command("test", options=[verbose])
        config = ParserConfiguration(allow_abbreviated_options=False)
        resolver = make_resolver(spec=spec, config=config)

        result = resolver.resolve_option_with_abbreviations("verb")

        assert result is None

    def test_resolves_unambiguous_abbreviation(self) -> None:
        verbose = flag_option(["verbose"])
        spec = command("test", options=[verbose])
        config = ParserConfiguration(allow_abbreviated_options=True)
        resolver = make_resolver(spec=spec, config=config)

        result = resolver.resolve_option_with_abbreviations("verb")

        assert is_resolved_option(result)
        assert result.resolved_name == "verbose"

    def test_returns_ambiguous_names_for_multiple_matches(self) -> None:
        verbose = flag_option(["verbose"])
        version = flag_option(["version"])
        spec = command("test", options=[verbose, version])
        config = ParserConfiguration(allow_abbreviated_options=True)
        resolver = make_resolver(spec=spec, config=config)

        result = resolver.resolve_option_with_abbreviations("ver")

        assert is_ambiguous_names(result)
        assert "verbose" in result.matches or "version" in result.matches

    def test_respects_minimum_abbreviation_length(self) -> None:
        verbose = flag_option(["verbose"])
        spec = command("test", options=[verbose])
        config = ParserConfiguration(
            allow_abbreviated_options=True,
            minimum_abbreviation_length=3,
        )
        resolver = make_resolver(spec=spec, config=config)

        result = resolver.resolve_option_with_abbreviations("ve")

        assert result is None


class TestResolveOptions:
    def test_resolves_long_option_with_prefix(self) -> None:
        verbose = flag_option(["verbose"])
        spec = command("test", options=[verbose])
        resolver = make_resolver(spec=spec)

        result = resolver.resolve_options("--verbose")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].resolved_name == "verbose"

    def test_resolves_short_option_with_prefix(self) -> None:
        verbose = flag_option(["verbose", "v"])
        spec = command("test", options=[verbose])
        resolver = make_resolver(spec=spec)

        result = resolver.resolve_options("-v")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].resolved_name == "verbose"

    def test_returns_empty_list_for_positional(self) -> None:
        resolver = make_resolver()

        result = resolver.resolve_options("file.txt")

        assert result == []

    def test_extracts_inline_value_from_long_option(self) -> None:
        output = scalar_option(["output"])
        spec = command("test", options=[output])
        resolver = make_resolver(spec=spec)

        result = resolver.resolve_options("--output=file.txt")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].inline == "file.txt"

    def test_resolves_grouped_short_flags(self) -> None:
        verbose = flag_option(["verbose", "v"])
        force = flag_option(["force", "f"])
        all_opt = flag_option(["all", "a"])
        spec = command("test", options=[verbose, force, all_opt])
        resolver = make_resolver(spec=spec)

        result = resolver.resolve_options("-vfa")

        assert isinstance(result, list)
        assert len(result) == 3
        assert result[0].resolved_name == "verbose"
        assert result[1].resolved_name == "force"
        assert result[2].resolved_name == "all"

    def test_grouped_flags_have_correct_is_inner_and_is_last(self) -> None:
        verbose = flag_option(["verbose", "v"])
        force = flag_option(["force", "f"])
        spec = command("test", options=[verbose, force])
        resolver = make_resolver(spec=spec)

        result = resolver.resolve_options("-vf")

        assert isinstance(result, list)
        assert result[0].is_inner is True
        assert result[0].is_last is False
        assert result[1].is_inner is False
        assert result[1].is_last is True


class TestResolveSubcommand:
    def test_resolves_exact_subcommand_name(self) -> None:
        commit = command("commit")
        spec = command("git", subcommands=[commit])
        resolver = make_resolver(spec=spec)

        result = resolver.resolve_subcommand("commit")

        assert is_resolved_command(result)
        assert result.resolved_name == "commit"

    def test_returns_none_for_unknown_subcommand(self) -> None:
        commit = command("commit")
        spec = command("git", subcommands=[commit])
        resolver = make_resolver(spec=spec)

        result = resolver.resolve_subcommand("unknown")

        assert result is None

    def test_case_sensitive_by_default(self) -> None:
        commit = command("Commit")
        spec = command("git", subcommands=[commit])
        resolver = make_resolver(spec=spec)

        result = resolver.resolve_subcommand("commit")

        assert result is None

    def test_case_insensitive_when_configured(self) -> None:
        commit = command("Commit")
        spec = command("git", subcommands=[commit])
        config = ParserConfiguration(case_sensitive_commands=False)
        resolver = make_resolver(spec=spec, config=config)

        result = resolver.resolve_subcommand("commit")

        assert is_resolved_command(result)
        assert result.resolved_name == "Commit"

    def test_resolves_unambiguous_abbreviation(self) -> None:
        commit = command("commit")
        spec = command("git", subcommands=[commit])
        config = ParserConfiguration(allow_abbreviated_commands=True)
        resolver = make_resolver(spec=spec, config=config)

        result = resolver.resolve_subcommand("com")

        assert is_resolved_command(result)
        assert result.resolved_name == "commit"

    @pytest.mark.xfail(
        reason="Bug: abbreviated matching uses original names not command_key"
    )
    def test_returns_ambiguous_for_multiple_matches(self) -> None:
        commit = command("commit")
        config_cmd = command("config")
        spec = command("git", subcommands=[commit, config_cmd])
        config = ParserConfiguration(allow_abbreviated_commands=True)
        resolver = make_resolver(spec=spec, config=config)

        result = resolver.resolve_subcommand("co")

        assert is_ambiguous_names(result)


class TestIsOptionOrSubcommand:
    def test_recognizes_long_option(self) -> None:
        verbose = flag_option(["verbose"])
        spec = command("test", options=[verbose])
        resolver = make_resolver(spec=spec)

        assert resolver.is_option_or_subcommand("--verbose") is True

    def test_recognizes_short_option(self) -> None:
        verbose = flag_option(["verbose", "v"])
        spec = command("test", options=[verbose])
        resolver = make_resolver(spec=spec)

        assert resolver.is_option_or_subcommand("-v") is True

    def test_recognizes_subcommand(self) -> None:
        commit = command("commit")
        spec = command("git", subcommands=[commit])
        resolver = make_resolver(spec=spec)

        assert resolver.is_option_or_subcommand("commit") is True

    def test_rejects_unknown_positional(self) -> None:
        verbose = flag_option(["verbose"])
        spec = command("test", options=[verbose])
        resolver = make_resolver(spec=spec)

        assert resolver.is_option_or_subcommand("file.txt") is False

    def test_returns_false_for_none(self) -> None:
        resolver = make_resolver()

        assert resolver.is_option_or_subcommand(None) is False

    def test_returns_false_for_empty_string(self) -> None:
        resolver = make_resolver()

        assert resolver.is_option_or_subcommand("") is False


class TestResolvedOptionDataclass:
    def test_creates_resolved_option(self) -> None:
        verbose = flag_option(["verbose"])
        spec = command("test", options=[verbose])
        resolver = make_resolver(spec=spec)
        opt = resolver.get_option("verbose")

        resolved = ResolvedOption(
            given_name="verbose",
            resolved_name="verbose",
            spec=opt,
        )

        assert resolved.given_name == "verbose"
        assert resolved.resolved_name == "verbose"
        assert resolved.inline is None
        assert resolved.is_inner is False
        assert resolved.is_last is False

    def test_creates_resolved_option_with_inline(self) -> None:
        output = scalar_option(["output"])
        spec = command("test", options=[output])
        resolver = make_resolver(spec=spec)
        opt = resolver.get_option("output")

        resolved = ResolvedOption(
            given_name="output",
            resolved_name="output",
            spec=opt,
            inline="file.txt",
        )

        assert resolved.inline == "file.txt"


class TestResolvedCommandNamedTuple:
    def test_creates_resolved_command(self) -> None:
        spec = command("commit")

        resolved = ResolvedCommand(
            given_name="commit",
            resolved_name="commit",
            spec=spec,
        )

        assert resolved.given_name == "commit"
        assert resolved.resolved_name == "commit"
        assert resolved.spec is spec


class TestAmbiguousNamesDataclass:
    def test_creates_ambiguous_names(self) -> None:
        ambiguous = AmbiguousNames(
            given_name="ver",
            matches=("verbose", "version"),
        )

        assert ambiguous.given_name == "ver"
        assert ambiguous.matches == ("verbose", "version")


class TestSubcommandAliasNormalization:
    def test_resolves_alias_exactly(self) -> None:
        commit = command("commit", aliases=["ci"])
        spec = command("git", subcommands=[commit])
        resolver = make_resolver(spec=spec)

        result = resolver.resolve_subcommand("ci")

        assert is_resolved_command(result)
        assert result.resolved_name == "commit"

    def test_resolves_alias_case_insensitive(self) -> None:
        commit = command("commit", aliases=["CI"])
        spec = command("git", subcommands=[commit])
        config = ParserConfiguration(case_sensitive_commands=False)
        resolver = make_resolver(spec=spec, config=config)

        result = resolver.resolve_subcommand("ci")

        assert is_resolved_command(result)
        assert result.resolved_name == "commit"

    def test_resolves_alias_with_underscore_conversion(self) -> None:
        run_tests = command("run-tests", aliases=["test-all"])
        spec = command("app", subcommands=[run_tests])
        config = ParserConfiguration(convert_underscores=True)
        resolver = make_resolver(spec=spec, config=config)

        result = resolver.resolve_subcommand("test_all")

        assert is_resolved_command(result)
        assert result.resolved_name == "run-tests"

    def test_resolves_primary_name_with_underscore_conversion(self) -> None:
        run_tests = command("run-tests")
        spec = command("app", subcommands=[run_tests])
        config = ParserConfiguration(convert_underscores=True)
        resolver = make_resolver(spec=spec, config=config)

        result = resolver.resolve_subcommand("run_tests")

        assert is_resolved_command(result)
        assert result.resolved_name == "run-tests"

    def test_resolves_alias_with_combined_normalization(self) -> None:
        my_cmd = command("my-command", aliases=["My-Alias"])
        spec = command("app", subcommands=[my_cmd])
        config = ParserConfiguration(
            case_sensitive_commands=False,
            convert_underscores=True,
        )
        resolver = make_resolver(spec=spec, config=config)

        result = resolver.resolve_subcommand("my_alias")

        assert is_resolved_command(result)
        assert result.resolved_name == "my-command"

    def test_multiple_aliases_all_resolve_correctly(self) -> None:
        deploy = command("deploy", aliases=["release", "ship"])
        spec = command("app", subcommands=[deploy])
        resolver = make_resolver(spec=spec)

        result_deploy = resolver.resolve_subcommand("deploy")
        result_release = resolver.resolve_subcommand("release")
        result_ship = resolver.resolve_subcommand("ship")

        assert is_resolved_command(result_deploy)
        assert result_deploy.resolved_name == "deploy"
        assert is_resolved_command(result_release)
        assert result_release.resolved_name == "deploy"
        assert is_resolved_command(result_ship)
        assert result_ship.resolved_name == "deploy"


class TestTypeGuards:
    def test_is_resolved_option(self) -> None:
        verbose = flag_option(["verbose"])
        spec = command("test", options=[verbose])
        resolver = make_resolver(spec=spec)
        opt = resolver.get_option("verbose")
        resolved = ResolvedOption("verbose", "verbose", opt)

        assert is_resolved_option(resolved) is True
        assert is_resolved_option("not a resolved option") is False

    def test_is_resolved_command(self) -> None:
        spec = command("commit")
        resolved = ResolvedCommand("commit", "commit", spec)

        assert is_resolved_command(resolved) is True
        assert is_resolved_command("not a resolved command") is False

    def test_is_ambiguous_names(self) -> None:
        ambiguous = AmbiguousNames("ver", ("verbose", "version"))

        assert is_ambiguous_names(ambiguous) is True
        assert is_ambiguous_names("not ambiguous") is False
