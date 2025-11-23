import pytest

from flagrant.specification import CommandSpecification


@pytest.fixture
def empty_command_spec():
    return CommandSpecification("test")
