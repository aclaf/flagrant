from typing import TYPE_CHECKING

import pytest

from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import PositionalMissingValueError
from flagrant.specification import PositionalSpecification, command, flag_option

if TYPE_CHECKING:
    from flagrant.specification import CommandSpecification


# =============================================================================
# End-to-end parsing with positionals
# =============================================================================


class TestBasicPositionalParsing:
    def test_single_required_positional(self) -> None:
        pos = PositionalSpecification(name="file", arity=1)
        spec = command("test", positionals=[pos])

        result = parse_command_line_args(spec, ("input.txt",))

        assert result.positionals["file"] == "input.txt"

    def test_multiple_required_positionals(self) -> None:
        src = PositionalSpecification(name="source", arity=1)
        dst = PositionalSpecification(name="destination", arity=1)
        spec = command("cp", positionals=[src, dst])

        result = parse_command_line_args(spec, ("file.txt", "backup.txt"))

        assert result.positionals["source"] == "file.txt"
        assert result.positionals["destination"] == "backup.txt"

    def test_unbounded_positional_collects_all(self) -> None:
        files = PositionalSpecification(name="files", arity="*")
        spec = command("test", positionals=[files])

        result = parse_command_line_args(spec, ("a.txt", "b.txt", "c.txt"))

        assert result.positionals["files"] == ("a.txt", "b.txt", "c.txt")

    def test_unbounded_positional_with_no_args_returns_empty(self) -> None:
        files = PositionalSpecification(name="files", arity="*")
        spec = command("test", positionals=[files])

        result = parse_command_line_args(spec, ())

        assert result.positionals["files"] == ()


class TestPositionalWithOptions:
    def test_positionals_after_options(self) -> None:
        verbose = flag_option(["verbose", "v"])
        files = PositionalSpecification(name="files", arity="*")
        spec = command("test", options=[verbose], positionals=[files])

        result = parse_command_line_args(spec, ("--verbose", "a.txt", "b.txt"))

        assert result.options["verbose"] is True
        assert result.positionals["files"] == ("a.txt", "b.txt")

    def test_options_and_positionals_mixed_via_double_dash(self) -> None:
        verbose = flag_option(["verbose", "v"])
        files = PositionalSpecification(name="files", arity="*")
        spec = command("test", options=[verbose], positionals=[files])

        result = parse_command_line_args(
            spec, ("--verbose", "--", "--not-an-option", "file.txt")
        )

        assert result.options["verbose"] is True
        assert result.extra_args == ("--not-an-option", "file.txt")

    def test_short_option_cluster_before_positionals(self) -> None:
        flag_a = flag_option(["a"])
        flag_b = flag_option(["b"])
        files = PositionalSpecification(name="files", arity="*")
        spec = command("test", options=[flag_a, flag_b], positionals=[files])

        result = parse_command_line_args(spec, ("-ab", "input.txt"))

        assert result.options["a"] is True
        assert result.options["b"] is True
        assert result.positionals["files"] == ("input.txt",)


class TestLaterNeedsReservation:
    def test_unbounded_middle_reserves_for_required_last(self) -> None:
        first = PositionalSpecification(name="first", arity=1)
        middle = PositionalSpecification(name="middle", arity="*")
        last = PositionalSpecification(name="last", arity=1)
        spec = command("test", positionals=[first, middle, last])

        result = parse_command_line_args(spec, ("a", "b", "c", "d"))

        assert result.positionals["first"] == "a"
        assert result.positionals["middle"] == ("b", "c")
        assert result.positionals["last"] == "d"

    def test_behavior_md_worked_example(self) -> None:
        cmd = PositionalSpecification(name="command", arity=1)
        files = PositionalSpecification(name="files", arity=(1, "*"))
        output = PositionalSpecification(name="output", arity=1)
        spec = command("build", positionals=[cmd, files, output])

        result = parse_command_line_args(
            spec, ("build", "file1.txt", "file2.txt", "file3.txt", "result.out")
        )

        assert result.positionals["command"] == "build"
        assert result.positionals["files"] == ("file1.txt", "file2.txt", "file3.txt")
        assert result.positionals["output"] == "result.out"

    def test_multiple_unbounded_specs_reserve_correctly(self) -> None:
        first = PositionalSpecification(name="first", arity=(1, "*"))
        second = PositionalSpecification(name="second", arity=1)
        third = PositionalSpecification(name="third", arity=1)
        spec = command("test", positionals=[first, second, third])

        result = parse_command_line_args(spec, ("a", "b", "c", "d", "e"))

        assert result.positionals["first"] == ("a", "b", "c")
        assert result.positionals["second"] == "d"
        assert result.positionals["third"] == "e"


class TestResultShapes:
    def test_arity_one_returns_scalar(self) -> None:
        file = PositionalSpecification(name="file", arity=1)
        spec = command("test", positionals=[file])

        result = parse_command_line_args(spec, ("test.txt",))

        assert result.positionals["file"] == "test.txt"
        assert isinstance(result.positionals["file"], str)

    def test_arity_tuple_one_one_returns_scalar(self) -> None:
        file = PositionalSpecification(name="file", arity=(1, 1))
        spec = command("test", positionals=[file])

        result = parse_command_line_args(spec, ("test.txt",))

        assert result.positionals["file"] == "test.txt"
        assert isinstance(result.positionals["file"], str)

    def test_arity_two_returns_tuple(self) -> None:
        coords = PositionalSpecification(name="coords", arity=2)
        spec = command("test", positionals=[coords])

        result = parse_command_line_args(spec, ("10", "20"))

        assert result.positionals["coords"] == ("10", "20")
        assert isinstance(result.positionals["coords"], tuple)

    def test_arity_star_returns_tuple(self) -> None:
        files = PositionalSpecification(name="files", arity="*")
        spec = command("test", positionals=[files])

        result = parse_command_line_args(spec, ("a.txt", "b.txt"))

        assert isinstance(result.positionals["files"], tuple)


class TestInsufficientPositionals:
    def test_insufficient_for_required_raises_error(self) -> None:
        src = PositionalSpecification(name="source", arity=1)
        dst = PositionalSpecification(name="destination", arity=1)
        spec = command("cp", positionals=[src, dst])

        with pytest.raises(PositionalMissingValueError):
            parse_command_line_args(spec, ("only_one.txt",))

    def test_insufficient_for_range_minimum_raises_error(self) -> None:
        files = PositionalSpecification(name="files", arity=(3, 5))
        spec = command("test", positionals=[files])

        with pytest.raises(PositionalMissingValueError):
            parse_command_line_args(spec, ("a.txt", "b.txt"))

    def test_no_args_for_required_raises_error(self) -> None:
        required = PositionalSpecification(name="required", arity=1)
        spec = command("test", positionals=[required])

        with pytest.raises(PositionalMissingValueError):
            parse_command_line_args(spec, ())


# =============================================================================
# Commands with subcommands and their own positionals
# =============================================================================


class TestSubcommandsWithPositionals:
    def test_subcommand_with_positionals(
        self, git_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(
            git_like_spec, ("add", "file1.txt", "file2.txt")
        )

        assert result.subcommand is not None
        assert result.subcommand.command == "add"
        assert result.subcommand.positionals["paths"] == ("file1.txt", "file2.txt")

    def test_subcommand_with_options_and_positionals(
        self, git_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(git_like_spec, ("add", "-A", "src/", "tests/"))

        assert result.subcommand is not None
        assert result.subcommand.options["all"] is True
        assert result.subcommand.positionals["paths"] == ("src/", "tests/")

    def test_subcommand_optional_positionals(
        self, git_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(git_like_spec, ("push",))

        assert result.subcommand is not None
        assert result.subcommand.command == "push"
        assert result.subcommand.positionals["remote"] == ()
        assert result.subcommand.positionals["branch"] == ()

    def test_subcommand_with_some_optional_positionals(
        self, git_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(git_like_spec, ("push", "origin"))

        assert result.subcommand is not None
        assert result.subcommand.positionals["remote"] == ("origin",)
        assert result.subcommand.positionals["branch"] == ()

    def test_subcommand_with_all_optional_positionals(
        self, git_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(git_like_spec, ("push", "origin", "main"))

        assert result.subcommand is not None
        assert result.subcommand.positionals["remote"] == ("origin",)
        assert result.subcommand.positionals["branch"] == ("main",)


class TestDockerRunPositionals:
    def test_docker_run_image_only(
        self, docker_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(docker_like_spec, ("run", "nginx"))

        assert result.subcommand is not None
        assert result.subcommand.command == "run"
        assert result.subcommand.positionals["image"] == "nginx"
        assert result.subcommand.positionals["command"] == ()

    def test_docker_run_image_with_command(
        self, docker_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(
            docker_like_spec, ("run", "ubuntu", "bash", "-c", "echo hello")
        )

        assert result.subcommand is not None
        assert result.subcommand.positionals["image"] == "ubuntu"
        assert result.subcommand.positionals["command"] == ("bash", "-c", "echo hello")

    def test_docker_run_with_options_and_positionals(
        self, docker_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(
            docker_like_spec,
            ("run", "-it", "--name", "mycontainer", "alpine", "/bin/sh"),
        )

        assert result.subcommand is not None
        assert result.subcommand.options["interactive"] is True
        assert result.subcommand.options["tty"] is True
        assert result.subcommand.options["name"] == "mycontainer"
        assert result.subcommand.positionals["image"] == "alpine"
        assert result.subcommand.positionals["command"] == ("/bin/sh",)


class TestGrepPositionals:
    def test_grep_pattern_only(self, grep_like_spec: "CommandSpecification") -> None:
        result = parse_command_line_args(grep_like_spec, ("error",))

        assert result.positionals["pattern"] == "error"
        assert result.positionals["files"] == ()

    def test_grep_pattern_with_files(
        self, grep_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(
            grep_like_spec, ("pattern", "file1.txt", "file2.txt")
        )

        assert result.positionals["pattern"] == "pattern"
        assert result.positionals["files"] == ("file1.txt", "file2.txt")

    def test_grep_with_options_and_positionals(
        self, grep_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(
            grep_like_spec, ("-rni", "TODO", "src/", "tests/")
        )

        assert result.options["recursive"] is True
        assert result.options["line-number"] is True
        assert result.options["ignore-case"] is True
        assert result.positionals["pattern"] == "TODO"
        assert result.positionals["files"] == ("src/", "tests/")


class TestKubectlPositionals:
    def test_kubectl_get_pods(self, kubectl_like_spec: "CommandSpecification") -> None:
        result = parse_command_line_args(kubectl_like_spec, ("get", "pods"))

        assert result.subcommand is not None
        assert result.subcommand.positionals["resource"] == "pods"
        assert result.subcommand.positionals["name"] == ()

    def test_kubectl_get_pod_by_name(
        self, kubectl_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(kubectl_like_spec, ("get", "pod", "nginx-123"))

        assert result.subcommand is not None
        assert result.subcommand.positionals["resource"] == "pod"
        assert result.subcommand.positionals["name"] == ("nginx-123",)

    def test_kubectl_delete_multiple_resources(
        self, kubectl_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(
            kubectl_like_spec, ("delete", "pod", "pod1", "pod2", "pod3")
        )

        assert result.subcommand is not None
        assert result.subcommand.positionals["resource"] == "pod"
        assert result.subcommand.positionals["name"] == ("pod1", "pod2", "pod3")

    def test_kubectl_exec_with_command(
        self, kubectl_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(
            kubectl_like_spec, ("exec", "-it", "mypod", "/bin/bash")
        )

        assert result.subcommand is not None
        assert result.subcommand.options["stdin"] is True
        assert result.subcommand.options["tty"] is True
        assert result.subcommand.positionals["pod"] == "mypod"
        assert result.subcommand.positionals["command"] == ("/bin/bash",)

    def test_kubectl_exec_with_extra_args_after_double_dash(
        self, kubectl_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(
            kubectl_like_spec, ("exec", "-it", "mypod", "bash", "--", "-c", "echo hi")
        )

        assert result.subcommand is not None
        assert result.subcommand.positionals["pod"] == "mypod"
        assert result.subcommand.positionals["command"] == ("bash",)
        assert result.subcommand.extra_args == ("-c", "echo hi")


class TestFindPositionals:
    def test_find_single_path(self, find_like_spec: "CommandSpecification") -> None:
        result = parse_command_line_args(find_like_spec, (".",))

        assert result.positionals["paths"] == (".",)

    def test_find_multiple_paths(self, find_like_spec: "CommandSpecification") -> None:
        result = parse_command_line_args(find_like_spec, ("src", "tests", "docs"))

        assert result.positionals["paths"] == ("src", "tests", "docs")

    def test_find_path_with_options(
        self, find_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(
            find_like_spec, (".", "--name", "*.py", "--type", "f")
        )

        assert result.positionals["paths"] == (".",)
        assert result.options["name"] == "*.py"
        assert result.options["type"] == "f"


# =============================================================================
# Arity variations
# =============================================================================


class TestArityVariations:
    def test_optional_positional_with_value(self) -> None:
        opt = PositionalSpecification(name="config", arity="?")
        spec = command("test", positionals=[opt])

        result = parse_command_line_args(spec, ("config.yaml",))

        assert result.positionals["config"] == ("config.yaml",)

    def test_optional_positional_without_value(self) -> None:
        opt = PositionalSpecification(name="config", arity="?")
        spec = command("test", positionals=[opt])

        result = parse_command_line_args(spec, ())

        assert result.positionals["config"] == ()

    def test_greedy_positional_with_regular_values(self) -> None:
        args = PositionalSpecification(name="args", arity="...")
        spec = command("test", positionals=[args])

        result = parse_command_line_args(spec, ("arg1", "arg2", "arg3"))

        assert result.positionals["args"] == ("arg1", "arg2", "arg3")

    def test_greedy_positional_via_double_dash(self) -> None:
        args = PositionalSpecification(name="args", arity="...")
        spec = command("test", positionals=[args])

        result = parse_command_line_args(spec, ("--", "--flag", "value", "-x"))

        # After --, all args become extra_args, not positionals
        assert result.positionals["args"] == ()
        assert result.extra_args == ("--flag", "value", "-x")

    def test_range_positional_at_minimum(self) -> None:
        files = PositionalSpecification(name="files", arity=(2, 5))
        spec = command("test", positionals=[files])

        result = parse_command_line_args(spec, ("a.txt", "b.txt"))

        assert result.positionals["files"] == ("a.txt", "b.txt")

    def test_range_positional_at_maximum(self) -> None:
        files = PositionalSpecification(name="files", arity=(2, 5))
        spec = command("test", positionals=[files])

        result = parse_command_line_args(
            spec, ("a.txt", "b.txt", "c.txt", "d.txt", "e.txt")
        )

        assert result.positionals["files"] == (
            "a.txt",
            "b.txt",
            "c.txt",
            "d.txt",
            "e.txt",
        )

    def test_range_with_unbounded_max(self) -> None:
        files = PositionalSpecification(name="files", arity=(1, "*"))
        spec = command("test", positionals=[files])

        result = parse_command_line_args(
            spec, ("a.txt", "b.txt", "c.txt", "d.txt", "e.txt")
        )

        assert len(result.positionals["files"]) == 5


class TestImplicitArgsSpec:
    def test_no_positional_spec_uses_implicit_args(self) -> None:
        spec = command("test")

        result = parse_command_line_args(spec, ("arg1", "arg2", "arg3"))

        assert result.positionals["args"] == ("arg1", "arg2", "arg3")

    def test_no_positional_spec_empty_args(self) -> None:
        spec = command("test")

        result = parse_command_line_args(spec, ())

        assert result.positionals["args"] == ()

    def test_command_with_options_and_implicit_positionals(self) -> None:
        verbose = flag_option(["verbose", "v"])
        spec = command("test", options=[verbose])

        result = parse_command_line_args(spec, ("--verbose", "file.txt"))

        assert result.options["verbose"] is True
        assert result.positionals["args"] == ("file.txt",)
