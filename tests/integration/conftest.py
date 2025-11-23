from typing import TYPE_CHECKING

import pytest

from flagrant.specification import (
    Arity,
)
from flagrant.specification.enums import ValueAccumulationMode

if TYPE_CHECKING:
    from flagrant.specification import (
        CommandSpecificationFactory,
        FlagOptionSpecificationFactory,
        ValueOptionSpecificationFactory,
    )


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        item.add_marker(pytest.mark.integration)


@pytest.fixture
def git_like_spec(
    make_command: "CommandSpecificationFactory",
    make_flag_opt: "FlagOptionSpecificationFactory",
    make_value_opt: "ValueOptionSpecificationFactory",
):
    """Git-like command specification with accurate options based on actual git CLI."""
    return make_command(
        name="git",
        options={
            "version": make_flag_opt(name="version"),
        },
        subcommands={
            "commit": make_command(
                name="commit",
                options={
                    "message": make_value_opt(name="message", short_names=("m",)),
                    "all": make_flag_opt(name="all", short_names=("a",)),
                    "verbose": make_flag_opt(name="verbose", short_names=("v",)),
                    "amend": make_flag_opt(name="amend"),
                },
            ),
            "push": make_command(
                name="push",
                options={
                    "force": make_flag_opt(name="force", short_names=("f",)),
                    "set-upstream": make_flag_opt(
                        name="set-upstream", short_names=("u",)
                    ),
                },
                positionals={
                    "remote": Arity.at_most_one(),
                    "branch": Arity.at_most_one(),
                },
            ),
            "log": make_command(
                name="log",
                options={
                    "oneline": make_flag_opt(name="oneline"),
                    "graph": make_flag_opt(name="graph"),
                    "max-count": make_value_opt(name="max-count", short_names=("n",)),
                },
            ),
            "add": make_command(
                name="add",
                options={
                    "all": make_flag_opt(name="all", short_names=("A",)),
                    "patch": make_flag_opt(name="patch", short_names=("p",)),
                },
                positionals={
                    "paths": Arity.zero_or_more(),
                },
            ),
        },
    )


@pytest.fixture
def docker_like_spec(
    make_command: "CommandSpecificationFactory",
    make_flag_opt: "FlagOptionSpecificationFactory",
    make_value_opt: "ValueOptionSpecificationFactory",
):
    """Docker-like command specification based on actual docker CLI."""
    return make_command(
        name="docker",
        subcommands={
            "run": make_command(
                name="run",
                options={
                    "interactive": make_flag_opt(
                        name="interactive", short_names=("i",)
                    ),
                    "tty": make_flag_opt(name="tty", short_names=("t",)),
                    "detach": make_flag_opt(name="detach", short_names=("d",)),
                    "name": make_value_opt(name="name"),
                    "env": make_value_opt(
                        name="env",
                        short_names=("e",),
                        accumulation_mode=ValueAccumulationMode.APPEND,
                    ),
                    "volume": make_value_opt(
                        name="volume",
                        short_names=("v",),
                        accumulation_mode=ValueAccumulationMode.APPEND,
                    ),
                },
                positionals={
                    "image": Arity.exactly_one(),
                    "command": Arity.zero_or_more(),
                },
            ),
            "compose": make_command(
                name="compose",
                subcommands={
                    "up": make_command(
                        name="up",
                        options={
                            "detach": make_flag_opt(name="detach", short_names=("d",)),
                            "build": make_flag_opt(name="build"),
                        },
                    ),
                },
            ),
            "image": make_command(
                name="image",
                subcommands={
                    "ls": make_command(
                        name="ls",
                        options={
                            "filter": make_value_opt(name="filter", short_names=("f",)),
                            "all": make_flag_opt(name="all", short_names=("a",)),
                        },
                    ),
                },
            ),
        },
    )


@pytest.fixture
def grep_like_spec(
    make_command: "CommandSpecificationFactory",
    make_flag_opt: "FlagOptionSpecificationFactory",
    make_value_opt: "ValueOptionSpecificationFactory",
):
    """Grep-like command specification based on actual grep CLI."""
    return make_command(
        name="grep",
        options={
            "recursive": make_flag_opt(name="recursive", short_names=("r",)),
            "ignore-case": make_flag_opt(name="ignore-case", short_names=("i",)),
            "line-number": make_flag_opt(name="line-number", short_names=("n",)),
            "count": make_flag_opt(name="count", short_names=("c",)),
            "exclude": make_value_opt(
                name="exclude",
                arity=Arity.at_least_one(),
                accumulation_mode=ValueAccumulationMode.EXTEND,
            ),
            "include": make_value_opt(
                name="include", accumulation_mode=ValueAccumulationMode.APPEND
            ),
        },
        positionals={
            "pattern": Arity.exactly_one(),
            "files": Arity.zero_or_more(),
        },
    )


@pytest.fixture
def tar_like_spec(
    make_command: "CommandSpecificationFactory",
    make_flag_opt: "FlagOptionSpecificationFactory",
    make_value_opt: "ValueOptionSpecificationFactory",
):
    """Tar-like command specification with accurate options based on actual tar CLI."""
    return make_command(
        name="tar",
        options={
            "create": make_flag_opt(name="create", short_names=("c",)),
            "extract": make_flag_opt(name="extract", short_names=("x",)),
            "gzip": make_flag_opt(name="gzip", short_names=("z",)),
            "file": make_value_opt(name="file", short_names=("f",)),
            "verbose": make_flag_opt(name="verbose", short_names=("v",)),
            "list": make_flag_opt(name="list", short_names=("t",)),
        },
        positionals={
            "files": Arity.zero_or_more(),
        },
    )


@pytest.fixture
def find_like_spec(
    make_command: "CommandSpecificationFactory",
    make_value_opt: "ValueOptionSpecificationFactory",
):
    """Find-like command specification based on actual find CLI."""
    return make_command(
        name="find",
        options={
            "name": make_value_opt(name="name"),
            "type": make_value_opt(name="type"),
            "maxdepth": make_value_opt(name="maxdepth"),
            "exec": make_value_opt(
                name="exec",
                arity=Arity.at_least_one(),
                accumulation_mode=ValueAccumulationMode.EXTEND,
            ),
        },
        positionals={
            "paths": Arity.at_least_one(),
        },
    )


@pytest.fixture
def kubectl_like_spec(
    make_command: "CommandSpecificationFactory",
    make_flag_opt: "FlagOptionSpecificationFactory",
    make_value_opt: "ValueOptionSpecificationFactory",
):
    """Kubectl-like command specification based on actual kubectl CLI."""
    return make_command(
        name="kubectl",
        options={
            "namespace": make_value_opt(name="namespace", short_names=("n",)),
            "kubeconfig": make_value_opt(name="kubeconfig"),
            "context": make_value_opt(name="context"),
        },
        subcommands={
            "get": make_command(
                name="get",
                options={
                    "output": make_value_opt(name="output", short_names=("o",)),
                    "all-namespaces": make_flag_opt(
                        name="all-namespaces", short_names=("A",)
                    ),
                    "selector": make_value_opt(name="selector", short_names=("l",)),
                    "watch": make_flag_opt(name="watch", short_names=("w",)),
                },
                positionals={
                    "resource": Arity.exactly_one(),
                    "name": Arity.at_most_one(),
                },
            ),
            "apply": make_command(
                name="apply",
                options={
                    "filename": make_value_opt(
                        name="filename",
                        short_names=("f",),
                        accumulation_mode=ValueAccumulationMode.APPEND,
                    ),
                    "recursive": make_flag_opt(name="recursive", short_names=("R",)),
                    "force": make_flag_opt(name="force"),
                    "dry-run": make_value_opt(name="dry-run"),
                },
            ),
            "delete": make_command(
                name="delete",
                options={
                    "filename": make_value_opt(name="filename", short_names=("f",)),
                    "force": make_flag_opt(name="force"),
                    "grace-period": make_value_opt(name="grace-period"),
                    "all": make_flag_opt(name="all"),
                },
                positionals={
                    "resource": Arity.exactly_one(),
                    "name": Arity.zero_or_more(),
                },
            ),
            "describe": make_command(
                name="describe",
                options={
                    "filename": make_value_opt(name="filename", short_names=("f",)),
                    "selector": make_value_opt(name="selector", short_names=("l",)),
                },
                positionals={
                    "resource": Arity.exactly_one(),
                    "name": Arity.at_most_one(),
                },
            ),
            "exec": make_command(
                name="exec",
                options={
                    "stdin": make_flag_opt(name="stdin", short_names=("i",)),
                    "tty": make_flag_opt(name="tty", short_names=("t",)),
                    "container": make_value_opt(name="container", short_names=("c",)),
                },
                positionals={
                    "pod": Arity.exactly_one(),
                    "command": Arity.at_least_one(),
                },
            ),
        },
    )