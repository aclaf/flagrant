import pytest

from flagrant.specification import (
    PositionalSpecification,
    command,
    flag_option,
    list_option,
    scalar_option,
)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        item.add_marker(pytest.mark.integration)


@pytest.fixture
def git_like_spec():
    return command(
        name="git",
        options=[
            flag_option(["version"]),
        ],
        subcommands=[
            command(
                name="commit",
                options=[
                    scalar_option(["message", "m"]),
                    flag_option(["all", "a"]),
                    flag_option(["verbose", "v"]),
                    flag_option(["amend"]),
                ],
            ),
            command(
                name="push",
                options=[
                    flag_option(["force", "f"]),
                    flag_option(["set-upstream", "u"]),
                ],
                positionals=[
                    PositionalSpecification(name="remote", arity="?"),
                    PositionalSpecification(name="branch", arity="?"),
                ],
            ),
            command(
                name="log",
                options=[
                    flag_option(["oneline"]),
                    flag_option(["graph"]),
                    scalar_option(["max-count", "n"]),
                ],
            ),
            command(
                name="add",
                options=[
                    flag_option(["all", "A"]),
                    flag_option(["patch", "p"]),
                ],
                positionals=[
                    PositionalSpecification(name="paths", arity="*"),
                ],
            ),
        ],
    )


@pytest.fixture
def docker_like_spec():
    return command(
        name="docker",
        subcommands=[
            command(
                name="run",
                options=[
                    flag_option(["interactive", "i"]),
                    flag_option(["tty", "t"]),
                    flag_option(["detach", "d"]),
                    scalar_option(["name"]),
                    list_option(["env", "e"], accumulation_mode="append"),
                    list_option(["volume", "v"], accumulation_mode="append"),
                ],
                positionals=[
                    PositionalSpecification(name="image", arity=1),
                    PositionalSpecification(name="command", arity="*"),
                ],
            ),
            command(
                name="compose",
                subcommands=[
                    command(
                        name="up",
                        options=[
                            flag_option(["detach", "d"]),
                            flag_option(["build"]),
                        ],
                    ),
                ],
            ),
            command(
                name="image",
                subcommands=[
                    command(
                        name="ls",
                        options=[
                            scalar_option(["filter", "f"]),
                            flag_option(["all", "a"]),
                        ],
                    ),
                ],
            ),
        ],
    )


@pytest.fixture
def grep_like_spec():
    return command(
        name="grep",
        options=[
            flag_option(["recursive", "r"]),
            flag_option(["ignore-case", "i"]),
            flag_option(["line-number", "n"]),
            flag_option(["count", "c"]),
            list_option(["exclude"], arity=(1, "*"), accumulation_mode="extend"),
            list_option(["include"], accumulation_mode="append"),
        ],
        positionals=[
            PositionalSpecification(name="pattern", arity=1),
            PositionalSpecification(name="files", arity="*"),
        ],
    )


@pytest.fixture
def tar_like_spec():
    return command(
        name="tar",
        options=[
            flag_option(["create", "c"]),
            flag_option(["extract", "x"]),
            flag_option(["gzip", "z"]),
            scalar_option(["file", "f"]),
            flag_option(["verbose", "v"]),
            flag_option(["list", "t"]),
        ],
        positionals=[
            PositionalSpecification(name="files", arity="*"),
        ],
    )


@pytest.fixture
def find_like_spec():
    return command(
        name="find",
        options=[
            scalar_option(["name"]),
            scalar_option(["type"]),
            scalar_option(["maxdepth"]),
            list_option(["exec"], arity=(1, "*"), accumulation_mode="extend"),
        ],
        positionals=[
            PositionalSpecification(name="paths", arity=(1, "*")),
        ],
    )


@pytest.fixture
def kubectl_like_spec():
    return command(
        name="kubectl",
        options=[
            scalar_option(["namespace", "n"]),
            scalar_option(["kubeconfig"]),
            scalar_option(["context"]),
        ],
        subcommands=[
            command(
                name="get",
                options=[
                    scalar_option(["output", "o"]),
                    flag_option(["all-namespaces", "A"]),
                    scalar_option(["selector", "l"]),
                    flag_option(["watch", "w"]),
                ],
                positionals=[
                    PositionalSpecification(name="resource", arity=1),
                    PositionalSpecification(name="name", arity="?"),
                ],
            ),
            command(
                name="apply",
                options=[
                    list_option(["filename", "f"], accumulation_mode="append"),
                    flag_option(["recursive", "R"]),
                    flag_option(["force"]),
                    scalar_option(["dry-run"]),
                ],
            ),
            command(
                name="delete",
                options=[
                    scalar_option(["filename", "f"]),
                    flag_option(["force"]),
                    scalar_option(["grace-period"]),
                    flag_option(["all"]),
                ],
                positionals=[
                    PositionalSpecification(name="resource", arity=1),
                    PositionalSpecification(name="name", arity="*"),
                ],
            ),
            command(
                name="describe",
                options=[
                    scalar_option(["filename", "f"]),
                    scalar_option(["selector", "l"]),
                ],
                positionals=[
                    PositionalSpecification(name="resource", arity=1),
                    PositionalSpecification(name="name", arity="?"),
                ],
            ),
            command(
                name="exec",
                options=[
                    flag_option(["stdin", "i"]),
                    flag_option(["tty", "t"]),
                    scalar_option(["container", "c"]),
                ],
                positionals=[
                    PositionalSpecification(name="pod", arity=1),
                    PositionalSpecification(name="command", arity=(1, "*")),
                ],
            ),
        ],
    )
