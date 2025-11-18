from typing import TYPE_CHECKING

import pytest

from flagrant.parsing import Parser

if TYPE_CHECKING:
    from flagrant.specification import CommandSpecification


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        item.add_marker(pytest.mark.parsing)


@pytest.fixture
def empty_parser(empty_command_spec: "CommandSpecification"):
    return Parser(empty_command_spec)
