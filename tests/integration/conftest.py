import pytest

from flagrant.specification import (
    Arity,
    CommandSpecification,
    FlagOptionSpecification,
    ValueOptionSpecification,
)
from flagrant.specification.enums import ValueAccumulationMode


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        item.add_marker(pytest.mark.integration)


@pytest.fixture
def git_like_spec():
    """Git-like command specification with accurate options based on actual git CLI."""
    return CommandSpecification(
        name="git",
        options={
            "version": FlagOptionSpecification(
                name="version",
                arity=Arity.none(),
                greedy=False,
                preferred_name="version",
                long_names=("version",),
                short_names=(),
            ),
        },
        subcommands={
            "commit": CommandSpecification(
                name="commit",
                options={
                    "message": ValueOptionSpecification(
                        name="message",
                        arity=Arity.exactly_one(),
                        greedy=False,
                        preferred_name="message",
                        long_names=("message",),
                        short_names=("m",),
                    ),
                    "all": FlagOptionSpecification(
                        name="all",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="all",
                        long_names=("all",),
                        short_names=("a",),
                    ),
                    "verbose": FlagOptionSpecification(
                        name="verbose",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="verbose",
                        long_names=("verbose",),
                        short_names=("v",),
                    ),
                    "amend": FlagOptionSpecification(
                        name="amend",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="amend",
                        long_names=("amend",),
                        short_names=(),
                    ),
                },
            ),
            "push": CommandSpecification(
                name="push",
                options={
                    "force": FlagOptionSpecification(
                        name="force",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="force",
                        long_names=("force",),
                        short_names=("f",),
                    ),
                    "set-upstream": FlagOptionSpecification(
                        name="set-upstream",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="set-upstream",
                        long_names=("set-upstream",),
                        short_names=("u",),
                    ),
                },
                positionals={
                    "remote": Arity.at_most_one(),
                    "branch": Arity.at_most_one(),
                },
            ),
            "log": CommandSpecification(
                name="log",
                options={
                    "oneline": FlagOptionSpecification(
                        name="oneline",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="oneline",
                        long_names=("oneline",),
                        short_names=(),
                    ),
                    "graph": FlagOptionSpecification(
                        name="graph",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="graph",
                        long_names=("graph",),
                        short_names=(),
                    ),
                    "max-count": ValueOptionSpecification(
                        name="max-count",
                        arity=Arity.exactly_one(),
                        greedy=False,
                        preferred_name="max-count",
                        long_names=("max-count",),
                        short_names=("n",),
                    ),
                },
            ),
            "add": CommandSpecification(
                name="add",
                options={
                    "all": FlagOptionSpecification(
                        name="all",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="all",
                        long_names=("all",),
                        short_names=("A",),
                    ),
                    "patch": FlagOptionSpecification(
                        name="patch",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="patch",
                        long_names=("patch",),
                        short_names=("p",),
                    ),
                },
                positionals={
                    "paths": Arity.zero_or_more(),
                },
            ),
        },
    )


@pytest.fixture
def docker_like_spec():
    """Docker-like command specification based on actual docker CLI."""
    return CommandSpecification(
        name="docker",
        subcommands={
            "run": CommandSpecification(
                name="run",
                options={
                    "interactive": FlagOptionSpecification(
                        name="interactive",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="interactive",
                        long_names=("interactive",),
                        short_names=("i",),
                    ),
                    "tty": FlagOptionSpecification(
                        name="tty",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="tty",
                        long_names=("tty",),
                        short_names=("t",),
                    ),
                    "detach": FlagOptionSpecification(
                        name="detach",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="detach",
                        long_names=("detach",),
                        short_names=("d",),
                    ),
                    "name": ValueOptionSpecification(
                        name="name",
                        arity=Arity.exactly_one(),
                        greedy=False,
                        preferred_name="name",
                        long_names=("name",),
                        short_names=(),
                    ),
                    "env": ValueOptionSpecification(
                        name="env",
                        arity=Arity.exactly_one(),
                        greedy=False,
                        preferred_name="env",
                        long_names=("env",),
                        short_names=("e",),
                        accumulation_mode=ValueAccumulationMode.APPEND,
                    ),
                    "volume": ValueOptionSpecification(
                        name="volume",
                        arity=Arity.exactly_one(),
                        greedy=False,
                        preferred_name="volume",
                        long_names=("volume",),
                        short_names=("v",),
                        accumulation_mode=ValueAccumulationMode.APPEND,
                    ),
                },
                positionals={
                    "image": Arity.exactly_one(),
                    "command": Arity.zero_or_more(),
                },
            ),
            "compose": CommandSpecification(
                name="compose",
                subcommands={
                    "up": CommandSpecification(
                        name="up",
                        options={
                            "detach": FlagOptionSpecification(
                                name="detach",
                                arity=Arity.none(),
                                greedy=False,
                                preferred_name="detach",
                                long_names=("detach",),
                                short_names=("d",),
                            ),
                            "build": FlagOptionSpecification(
                                name="build",
                                arity=Arity.none(),
                                greedy=False,
                                preferred_name="build",
                                long_names=("build",),
                                short_names=(),
                            ),
                        },
                    ),
                },
            ),
            "image": CommandSpecification(
                name="image",
                subcommands={
                    "ls": CommandSpecification(
                        name="ls",
                        options={
                            "filter": ValueOptionSpecification(
                                name="filter",
                                arity=Arity.exactly_one(),
                                greedy=False,
                                preferred_name="filter",
                                long_names=("filter",),
                                short_names=("f",),
                            ),
                            "all": FlagOptionSpecification(
                                name="all",
                                arity=Arity.none(),
                                greedy=False,
                                preferred_name="all",
                                long_names=("all",),
                                short_names=("a",),
                            ),
                        },
                    ),
                },
            ),
        },
    )


@pytest.fixture
def grep_like_spec():
    """Grep-like command specification based on actual grep CLI."""
    return CommandSpecification(
        name="grep",
        options={
            "recursive": FlagOptionSpecification(
                name="recursive",
                arity=Arity.none(),
                greedy=False,
                preferred_name="recursive",
                long_names=("recursive",),
                short_names=("r",),
            ),
            "ignore-case": FlagOptionSpecification(
                name="ignore-case",
                arity=Arity.none(),
                greedy=False,
                preferred_name="ignore-case",
                long_names=("ignore-case",),
                short_names=("i",),
            ),
            "line-number": FlagOptionSpecification(
                name="line-number",
                arity=Arity.none(),
                greedy=False,
                preferred_name="line-number",
                long_names=("line-number",),
                short_names=("n",),
            ),
            "count": FlagOptionSpecification(
                name="count",
                arity=Arity.none(),
                greedy=False,
                preferred_name="count",
                long_names=("count",),
                short_names=("c",),
            ),
            "exclude": ValueOptionSpecification(
                name="exclude",
                arity=Arity.at_least_one(),
                greedy=False,
                preferred_name="exclude",
                long_names=("exclude",),
                short_names=(),
                accumulation_mode=ValueAccumulationMode.EXTEND,
            ),
            "include": ValueOptionSpecification(
                name="include",
                arity=Arity.exactly_one(),
                greedy=False,
                preferred_name="include",
                long_names=("include",),
                short_names=(),
                accumulation_mode=ValueAccumulationMode.APPEND,
            ),
        },
        positionals={
            "pattern": Arity.exactly_one(),
            "files": Arity.zero_or_more(),
        },
    )


@pytest.fixture
def tar_like_spec():
    """Tar-like command specification with accurate options based on actual tar CLI."""
    return CommandSpecification(
        name="tar",
        options={
            "create": FlagOptionSpecification(
                name="create",
                arity=Arity.none(),
                greedy=False,
                preferred_name="create",
                long_names=("create",),
                short_names=("c",),
            ),
            "extract": FlagOptionSpecification(
                name="extract",
                arity=Arity.none(),
                greedy=False,
                preferred_name="extract",
                long_names=("extract",),
                short_names=("x",),
            ),
            "gzip": FlagOptionSpecification(
                name="gzip",
                arity=Arity.none(),
                greedy=False,
                preferred_name="gzip",
                long_names=("gzip",),
                short_names=("z",),
            ),
            "file": ValueOptionSpecification(
                name="file",
                arity=Arity.exactly_one(),
                greedy=False,
                preferred_name="file",
                long_names=("file",),
                short_names=("f",),
            ),
            "verbose": FlagOptionSpecification(
                name="verbose",
                arity=Arity.none(),
                greedy=False,
                preferred_name="verbose",
                long_names=("verbose",),
                short_names=("v",),
            ),
            "list": FlagOptionSpecification(
                name="list",
                arity=Arity.none(),
                greedy=False,
                preferred_name="list",
                long_names=("list",),
                short_names=("t",),
            ),
        },
        positionals={
            "files": Arity.zero_or_more(),
        },
    )


@pytest.fixture
def find_like_spec():
    """Find-like command specification based on actual find CLI."""
    return CommandSpecification(
        name="find",
        options={
            "name": ValueOptionSpecification(
                name="name",
                arity=Arity.exactly_one(),
                greedy=False,
                preferred_name="name",
                long_names=("name",),
                short_names=(),
            ),
            "type": ValueOptionSpecification(
                name="type",
                arity=Arity.exactly_one(),
                greedy=False,
                preferred_name="type",
                long_names=("type",),
                short_names=(),
            ),
            "maxdepth": ValueOptionSpecification(
                name="maxdepth",
                arity=Arity.exactly_one(),
                greedy=False,
                preferred_name="maxdepth",
                long_names=("maxdepth",),
                short_names=(),
            ),
            "exec": ValueOptionSpecification(
                name="exec",
                arity=Arity.at_least_one(),
                greedy=False,
                preferred_name="exec",
                long_names=("exec",),
                short_names=(),
                accumulation_mode=ValueAccumulationMode.EXTEND,
            ),
        },
        positionals={
            "paths": Arity.at_least_one(),
        },
    )


@pytest.fixture
def kubectl_like_spec():
    """Kubectl-like command specification based on actual kubectl CLI."""
    return CommandSpecification(
        name="kubectl",
        options={
            "namespace": ValueOptionSpecification(
                name="namespace",
                arity=Arity.exactly_one(),
                greedy=False,
                preferred_name="namespace",
                long_names=("namespace",),
                short_names=("n",),
            ),
            "kubeconfig": ValueOptionSpecification(
                name="kubeconfig",
                arity=Arity.exactly_one(),
                greedy=False,
                preferred_name="kubeconfig",
                long_names=("kubeconfig",),
                short_names=(),
            ),
            "context": ValueOptionSpecification(
                name="context",
                arity=Arity.exactly_one(),
                greedy=False,
                preferred_name="context",
                long_names=("context",),
                short_names=(),
            ),
        },
        subcommands={
            "get": CommandSpecification(
                name="get",
                options={
                    "output": ValueOptionSpecification(
                        name="output",
                        arity=Arity.exactly_one(),
                        greedy=False,
                        preferred_name="output",
                        long_names=("output",),
                        short_names=("o",),
                    ),
                    "all-namespaces": FlagOptionSpecification(
                        name="all-namespaces",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="all-namespaces",
                        long_names=("all-namespaces",),
                        short_names=("A",),
                    ),
                    "selector": ValueOptionSpecification(
                        name="selector",
                        arity=Arity.exactly_one(),
                        greedy=False,
                        preferred_name="selector",
                        long_names=("selector",),
                        short_names=("l",),
                    ),
                    "watch": FlagOptionSpecification(
                        name="watch",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="watch",
                        long_names=("watch",),
                        short_names=("w",),
                    ),
                },
                positionals={
                    "resource": Arity.exactly_one(),
                    "name": Arity.at_most_one(),
                },
            ),
            "apply": CommandSpecification(
                name="apply",
                options={
                    "filename": ValueOptionSpecification(
                        name="filename",
                        arity=Arity.exactly_one(),
                        greedy=False,
                        preferred_name="filename",
                        long_names=("filename",),
                        short_names=("f",),
                        accumulation_mode=ValueAccumulationMode.APPEND,
                    ),
                    "recursive": FlagOptionSpecification(
                        name="recursive",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="recursive",
                        long_names=("recursive",),
                        short_names=("R",),
                    ),
                    "force": FlagOptionSpecification(
                        name="force",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="force",
                        long_names=("force",),
                        short_names=(),
                    ),
                    "dry-run": ValueOptionSpecification(
                        name="dry-run",
                        arity=Arity.exactly_one(),
                        greedy=False,
                        preferred_name="dry-run",
                        long_names=("dry-run",),
                        short_names=(),
                    ),
                },
            ),
            "delete": CommandSpecification(
                name="delete",
                options={
                    "filename": ValueOptionSpecification(
                        name="filename",
                        arity=Arity.exactly_one(),
                        greedy=False,
                        preferred_name="filename",
                        long_names=("filename",),
                        short_names=("f",),
                    ),
                    "force": FlagOptionSpecification(
                        name="force",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="force",
                        long_names=("force",),
                        short_names=(),
                    ),
                    "grace-period": ValueOptionSpecification(
                        name="grace-period",
                        arity=Arity.exactly_one(),
                        greedy=False,
                        preferred_name="grace-period",
                        long_names=("grace-period",),
                        short_names=(),
                    ),
                    "all": FlagOptionSpecification(
                        name="all",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="all",
                        long_names=("all",),
                        short_names=(),
                    ),
                },
                positionals={
                    "resource": Arity.exactly_one(),
                    "name": Arity.zero_or_more(),
                },
            ),
            "describe": CommandSpecification(
                name="describe",
                options={
                    "filename": ValueOptionSpecification(
                        name="filename",
                        arity=Arity.exactly_one(),
                        greedy=False,
                        preferred_name="filename",
                        long_names=("filename",),
                        short_names=("f",),
                    ),
                    "selector": ValueOptionSpecification(
                        name="selector",
                        arity=Arity.exactly_one(),
                        greedy=False,
                        preferred_name="selector",
                        long_names=("selector",),
                        short_names=("l",),
                    ),
                },
                positionals={
                    "resource": Arity.exactly_one(),
                    "name": Arity.at_most_one(),
                },
            ),
            "exec": CommandSpecification(
                name="exec",
                options={
                    "stdin": FlagOptionSpecification(
                        name="stdin",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="stdin",
                        long_names=("stdin",),
                        short_names=("i",),
                    ),
                    "tty": FlagOptionSpecification(
                        name="tty",
                        arity=Arity.none(),
                        greedy=False,
                        preferred_name="tty",
                        long_names=("tty",),
                        short_names=("t",),
                    ),
                    "container": ValueOptionSpecification(
                        name="container",
                        arity=Arity.exactly_one(),
                        greedy=False,
                        preferred_name="container",
                        long_names=("container",),
                        short_names=("c",),
                    ),
                },
                positionals={
                    "pod": Arity.exactly_one(),
                    "command": Arity.at_least_one(),
                },
            ),
        },
    )