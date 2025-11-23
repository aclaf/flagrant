import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Auto-apply 'parsing' marker to all tests in this directory."""
    for item in items:
        item.add_marker(pytest.mark.parsing)
