"""Unit tests for CommandSpecification and PositionalSpecification."""

from flagrant.specification import command, flag_option, list_option, scalar_option
from flagrant.specification._command import PositionalSpecification


class TestCommandSpecificationDefaults:
    def test_aliases_defaults_to_none(self) -> None:
        cmd = command("git")

        assert cmd.aliases is None

    def test_options_defaults_to_none(self) -> None:
        cmd = command("git")

        assert cmd.options is None

    def test_positionals_defaults_to_none(self) -> None:
        cmd = command("git")

        assert cmd.positionals is None

    def test_subcommands_defaults_to_none(self) -> None:
        cmd = command("git")

        assert cmd.subcommands is None


class TestCommandSpecificationAllAliases:
    def test_all_aliases_includes_name_when_no_aliases(self) -> None:
        cmd = command("git")

        assert cmd.all_aliases == ("git",)

    def test_all_aliases_includes_name_and_aliases(self) -> None:
        cmd = command("commit", aliases=["ci", "c"])

        assert cmd.all_aliases == ("commit", "ci", "c")

    def test_all_aliases_name_is_first(self) -> None:
        cmd = command("status", aliases=["st"])

        assert cmd.all_aliases[0] == "status"


class TestCommandSpecificationAllOptionNames:
    def test_all_option_names_empty_when_no_options(self) -> None:
        cmd = command("git")

        assert cmd.all_option_names == ()

    def test_all_option_names_includes_long_names(self) -> None:
        verbose = flag_option(["verbose"])
        cmd = command("git", options=[verbose])

        assert "verbose" in cmd.all_option_names

    def test_all_option_names_includes_short_names(self) -> None:
        verbose = flag_option(["verbose", "v"])
        cmd = command("git", options=[verbose])

        assert "v" in cmd.all_option_names
        assert "verbose" in cmd.all_option_names

    def test_all_option_names_from_multiple_options(self) -> None:
        verbose = flag_option(["verbose", "v"])
        output = scalar_option(["output", "o"])
        cmd = command("git", options=[verbose, output])

        assert set(cmd.all_option_names) == {"verbose", "v", "output", "o"}

    def test_all_option_names_with_different_option_types(self) -> None:
        flag = flag_option(["verbose", "v"])
        scalar = scalar_option(["output", "o"])
        lst = list_option(["files", "f"])
        cmd = command("tool", options=[flag, scalar, lst])

        expected = {"verbose", "v", "output", "o", "files", "f"}
        assert set(cmd.all_option_names) == expected


class TestCommandSpecificationAllSubcommandNames:
    def test_all_subcommand_names_empty_when_no_subcommands(self) -> None:
        cmd = command("git")

        assert cmd.all_subcommand_names == ()

    def test_all_subcommand_names_includes_subcommand_names(self) -> None:
        commit = command("commit")
        status = command("status")
        cmd = command("git", subcommands=[commit, status])

        assert cmd.all_subcommand_names == ("commit", "status")

    def test_all_subcommand_names_preserves_order(self) -> None:
        add = command("add")
        commit = command("commit")
        push = command("push")
        cmd = command("git", subcommands=[add, commit, push])

        assert cmd.all_subcommand_names == ("add", "commit", "push")


class TestCommandSpecificationNesting:
    def test_nested_subcommands(self) -> None:
        show = command("show")
        remote = command("remote", subcommands=[show])
        cmd = command("git", subcommands=[remote])

        assert cmd.subcommands is not None
        assert cmd.subcommands[0].name == "remote"
        assert cmd.subcommands[0].subcommands is not None
        assert cmd.subcommands[0].subcommands[0].name == "show"

    def test_subcommand_with_options(self) -> None:
        verbose = flag_option(["verbose", "v"])
        commit = command("commit", options=[verbose])
        cmd = command("git", subcommands=[commit])

        assert cmd.subcommands is not None
        assert cmd.subcommands[0].options is not None
        assert cmd.subcommands[0].options[0].name == "verbose"

    def test_subcommand_with_positionals(self) -> None:
        file_pos = PositionalSpecification(name="file", arity="*")
        add = command("add", positionals=[file_pos])
        cmd = command("git", subcommands=[add])

        assert cmd.subcommands is not None
        assert cmd.subcommands[0].positionals is not None
        assert cmd.subcommands[0].positionals[0].name == "file"


class TestCommandSpecificationComplexHierarchy:
    def test_full_hierarchy_with_options_and_positionals(self) -> None:
        # Build a git-like command hierarchy
        verbose = flag_option(["verbose", "v"])
        message = scalar_option(["message", "m"])
        file_pos = PositionalSpecification(name="pathspec", arity="*")

        add = command("add", options=[verbose], positionals=[file_pos])
        commit = command("commit", options=[verbose, message])
        git = command("git", options=[verbose], subcommands=[add, commit])

        # Verify root
        assert git.name == "git"
        assert git.options is not None
        assert len(git.options) == 1

        # Verify subcommands
        assert git.subcommands is not None
        assert len(git.subcommands) == 2

        # Verify add subcommand
        assert git.subcommands[0].name == "add"
        assert git.subcommands[0].positionals is not None
        assert git.subcommands[0].positionals[0].name == "pathspec"

        # Verify commit subcommand
        assert git.subcommands[1].name == "commit"
        assert git.subcommands[1].options is not None
        assert len(git.subcommands[1].options) == 2
