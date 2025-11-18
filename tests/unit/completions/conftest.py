from typing import TYPE_CHECKING

import pytest

from flagrant.completions import Completer

if TYPE_CHECKING:
    from flagrant.specification import CommandSpecification


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        item.add_marker(pytest.mark.completions)


@pytest.fixture
def empty_completer(empty_command_spec: "CommandSpecification"):
    return Completer(empty_command_spec)
