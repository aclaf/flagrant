"""Integration tests for real-world CLI command patterns."""

from typing import TYPE_CHECKING

import pytest

from flagrant.parser import parse_command_line_args

if TYPE_CHECKING:
    from flagrant.specification import CommandSpecification


class TestGitStylePatterns:
    def test_git_commit_with_clustered_short_options_and_value(
        self, git_like_spec: "CommandSpecification"
    ):
        spec = git_like_spec

        result = parse_command_line_args(spec, ["commit", "-am", "Initial commit"])

        assert result.subcommand is not None
        assert result.subcommand.command == "commit"
        assert result.subcommand.options["all"] is True
        assert result.subcommand.options["message"] == "Initial commit"
        assert not result.subcommand.positionals

    def test_git_push_with_positionals_and_flag(
        self, git_like_spec: "CommandSpecification"
    ):
        spec = git_like_spec

        result = parse_command_line_args(spec, ["push", "origin", "main", "--force"])

        assert result.subcommand is not None
        assert result.subcommand.command == "push"
        assert result.subcommand.options["force"] is True
        assert result.subcommand.positionals["remote"] == "origin"
        assert result.subcommand.positionals["branch"] == "main"

    def test_git_log_with_long_and_short_options(
        self, git_like_spec: "CommandSpecification"
    ):
        spec = git_like_spec

        result = parse_command_line_args(spec, ["log", "--oneline", "-n", "10"])

        assert result.subcommand is not None
        assert result.subcommand.command == "log"
        assert result.subcommand.options["oneline"] is True
        assert result.subcommand.options["max-count"] == "10"


class TestDockerStylePatterns:
    def test_docker_run_with_clustered_flags_and_positionals(
        self, docker_like_spec: "CommandSpecification"
    ):
        spec = docker_like_spec

        result = parse_command_line_args(spec, ["run", "-it", "ubuntu", "bash"])

        assert result.subcommand is not None
        assert result.subcommand.command == "run"
        assert result.subcommand.options["interactive"] is True
        assert result.subcommand.options["tty"] is True
        assert result.subcommand.positionals["image"] == "ubuntu"
        assert result.subcommand.positionals["command"] == ("bash",)

    def test_docker_compose_nested_subcommands_with_flags(
        self, docker_like_spec: "CommandSpecification"
    ):
        spec = docker_like_spec

        result = parse_command_line_args(spec, ["compose", "up", "-d", "--build"])

        assert result.subcommand is not None
        assert result.subcommand.command == "compose"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "up"
        assert result.subcommand.subcommand.options["detach"] is True
        assert result.subcommand.subcommand.options["build"] is True

    def test_docker_image_ls_with_long_option_value(
        self, docker_like_spec: "CommandSpecification"
    ):
        spec = docker_like_spec

        result = parse_command_line_args(
            spec, ["image", "ls", "--filter", "dangling=true"]
        )

        assert result.subcommand is not None
        assert result.subcommand.command == "image"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "ls"
        assert result.subcommand.subcommand.options["filter"] == "dangling=true"


class TestUnixToolPatterns:
    def test_grep_recursive_with_pattern_and_path(
        self, grep_like_spec: "CommandSpecification"
    ):
        spec = grep_like_spec

        result = parse_command_line_args(spec, ["-r", "pattern", "."])

        assert result.options["recursive"] is True
        assert result.positionals["pattern"] == "pattern"
        assert result.positionals["files"] == (".",)

    def test_grep_with_multiple_exclude_patterns(
        self, grep_like_spec: "CommandSpecification"
    ):
        spec = grep_like_spec

        result = parse_command_line_args(
            spec,
            [
                "-r",
                "TODO",
                ".",
                "--exclude",
                "*.pyc",
                "--exclude",
                "*.pyo",
            ],
        )

        assert result.options["recursive"] is True
        assert result.positionals["pattern"] == "TODO"
        assert result.positionals["files"] == (".",)
        assert result.options["exclude"] == ("*.pyc", "*.pyo")

    def test_tar_create_with_clustered_options_and_files(
        self, tar_like_spec: "CommandSpecification"
    ):
        spec = tar_like_spec

        result = parse_command_line_args(spec, ["-czf", "archive.tar.gz", "files/"])

        assert result.options["create"] is True
        assert result.options["gzip"] is True
        assert result.options["file"] == "archive.tar.gz"
        assert result.positionals["files"] == ("files/",)

    def test_find_with_multiple_predicates(
        self, find_like_spec: "CommandSpecification"
    ):
        spec = find_like_spec

        result = parse_command_line_args(spec, [".", "--name", "*.py", "--type", "f"])

        assert result.positionals["paths"] == (".",)
        assert result.options["name"] == "*.py"
        assert result.options["type"] == "f"


class TestKubectlPatterns:
    @pytest.mark.xfail(reason="Issue #020: StopIteration with optional positionals")
    def test_kubectl_get_pods_with_namespace_and_output(
        self, kubectl_like_spec: "CommandSpecification"
    ):
        spec = kubectl_like_spec

        result = parse_command_line_args(
            spec, ["-n", "default", "get", "pods", "-o", "yaml"]
        )

        assert result.subcommand is not None
        assert result.subcommand.command == "get"
        assert result.options["namespace"] == "default"
        assert result.subcommand.options["output"] == "yaml"
        assert result.subcommand.positionals["resource"] == "pods"
        # Name positional should not be present as it wasn't provided

    def test_kubectl_apply_with_multiple_files(
        self, kubectl_like_spec: "CommandSpecification"
    ):
        spec = kubectl_like_spec

        result = parse_command_line_args(
            spec, ["apply", "-f", "deploy.yaml", "-f", "service.yaml"]
        )

        assert result.subcommand is not None
        assert result.subcommand.command == "apply"
        assert result.subcommand.options["filename"] == ("deploy.yaml", "service.yaml")

    def test_kubectl_exec_with_interactive_tty(
        self, kubectl_like_spec: "CommandSpecification"
    ):
        spec = kubectl_like_spec

        result = parse_command_line_args(spec, ["exec", "-it", "my-pod", "bash"])

        assert result.subcommand is not None
        assert result.subcommand.command == "exec"
        assert result.subcommand.options["stdin"] is True
        assert result.subcommand.options["tty"] is True
        assert result.subcommand.positionals["pod"] == "my-pod"
        assert result.subcommand.positionals["command"] == ("bash",)

    def test_kubectl_delete_with_selector(
        self, kubectl_like_spec: "CommandSpecification"
    ):
        spec = kubectl_like_spec

        result = parse_command_line_args(
            spec, ["-n", "production", "delete", "pods", "pod1", "pod2"]
        )

        assert result.subcommand is not None
        assert result.subcommand.command == "delete"
        assert result.options["namespace"] == "production"
        assert result.subcommand.positionals["resource"] == "pods"
        assert result.subcommand.positionals["name"] == ("pod1", "pod2")
