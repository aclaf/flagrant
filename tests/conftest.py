import pytest

from flagrant.specification import CommandSpecification


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        item.add_marker(pytest.mark.unit)


@pytest.fixture
def empty_command_spec():
    return CommandSpecification("test")
