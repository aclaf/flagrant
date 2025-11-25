from typing import TYPE_CHECKING

from flagrant.parser import parse_command_line_args

if TYPE_CHECKING:
    from flagrant.specification import CommandSpecification


class TestGitLikeParser:
    def test_git_commit_with_message(
        self, git_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(git_like_spec, ("commit", "-m", "Fix bug"))

        assert result.subcommand is not None
        assert result.subcommand.command == "commit"
        assert result.subcommand.options["message"] == "Fix bug"

    def test_git_commit_with_all_flag(
        self, git_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(git_like_spec, ("commit", "-a", "-m", "msg"))

        assert result.subcommand is not None
        assert result.subcommand.options["all"] is True
        assert result.subcommand.options["message"] == "msg"

    def test_git_version(self, git_like_spec: "CommandSpecification") -> None:
        result = parse_command_line_args(git_like_spec, ("--version",))

        assert result.options["version"] is True

    def test_git_log_with_options(self, git_like_spec: "CommandSpecification") -> None:
        result = parse_command_line_args(git_like_spec, ("log", "--oneline", "--graph"))

        assert result.subcommand is not None
        assert result.subcommand.command == "log"
        assert result.subcommand.options["oneline"] is True
        assert result.subcommand.options["graph"] is True


class TestDockerLikeParser:
    def test_docker_compose_up(self, docker_like_spec: "CommandSpecification") -> None:
        result = parse_command_line_args(
            docker_like_spec, ("compose", "up", "-d", "--build")
        )

        assert result.subcommand is not None
        assert result.subcommand.command == "compose"
        assert result.subcommand.subcommand is not None
        assert result.subcommand.subcommand.command == "up"
        assert result.subcommand.subcommand.options["detach"] is True
        assert result.subcommand.subcommand.options["build"] is True


class TestTarLikeParser:
    def test_tar_create_compressed(self, tar_like_spec: "CommandSpecification") -> None:
        result = parse_command_line_args(
            tar_like_spec, ("-c", "-z", "-f", "archive.tar.gz")
        )

        assert result.options["create"] is True
        assert result.options["gzip"] is True
        assert result.options["file"] == "archive.tar.gz"

    def test_tar_clustered_flags(self, tar_like_spec: "CommandSpecification") -> None:
        result = parse_command_line_args(tar_like_spec, ("-czvf", "archive.tar.gz"))

        assert result.options["create"] is True
        assert result.options["gzip"] is True
        assert result.options["verbose"] is True
        assert result.options["file"] == "archive.tar.gz"


class TestKubectlLikeParser:
    def test_kubectl_get_pods_with_namespace(
        self, kubectl_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(
            kubectl_like_spec, ("-n", "default", "get", "pods")
        )

        assert result.options["namespace"] == "default"
        assert result.subcommand is not None
        assert result.subcommand.command == "get"

    def test_kubectl_apply_file(
        self, kubectl_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(
            kubectl_like_spec, ("apply", "-f", "deployment.yaml")
        )

        assert result.subcommand is not None
        assert result.subcommand.command == "apply"


class TestMixedOptionsAndSubcommands:
    def test_global_option_before_subcommand(
        self, kubectl_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(
            kubectl_like_spec, ("--context", "prod", "get", "pods")
        )

        assert result.options["context"] == "prod"
        assert result.subcommand is not None
        assert result.subcommand.command == "get"


class TestPositionalArguments:
    def test_positional_after_options(
        self, git_like_spec: "CommandSpecification"
    ) -> None:
        result = parse_command_line_args(git_like_spec, ("add", "-p", "file.txt"))

        assert result.subcommand is not None
        assert result.subcommand.options["patch"] is True
        assert result.subcommand.positionals["paths"] == ("file.txt",)
