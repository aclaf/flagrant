from pathlib import Path

import pytest

from flagrant.exceptions import ConfigurationError, ErrorContext, FlagrantError


class TestFlagrantError:
    def test_message_only_initialization(self) -> None:
        error = FlagrantError("test message")

        assert str(error) == "test message"
        assert error.args[0] == "test message"

    def test_message_with_empty_context(self) -> None:
        error = FlagrantError("test message", {})

        assert str(error) == "test message"
        assert error.context == {}

    def test_message_with_populated_context(self) -> None:
        context: ErrorContext = {"key": "value", "count": 42}
        error = FlagrantError("test message", context)

        assert error.context == {"key": "value", "count": 42}

    def test_context_default_is_empty_dict(self) -> None:
        error = FlagrantError("test message")

        assert error.context == {}
        assert isinstance(error.context, dict)

    def test_context_with_nested_structures(self) -> None:
        test_path = Path("/var/log/test")
        context: ErrorContext = {
            "list_value": [1, 2, 3],
            "nested_dict": {"inner": "value"},
            "path": test_path,
            "boolean": True,
            "none_value": None,
            "float_value": 3.14,
        }
        error = FlagrantError("test message", context)

        assert error.context["list_value"] == [1, 2, 3]
        assert error.context["nested_dict"] == {"inner": "value"}
        assert error.context["path"] == test_path
        assert error.context["boolean"] is True
        assert error.context["none_value"] is None
        assert error.context["float_value"] == 3.14

    def test_exception_string_representation(self) -> None:
        error = FlagrantError("detailed error message")

        assert "detailed error message" in str(error)

    def test_inherits_from_exception(self) -> None:
        error = FlagrantError("test")

        assert isinstance(error, Exception)


class TestConfigurationError:
    def test_inherits_from_flagrant_error(self) -> None:
        error = ConfigurationError("config error")

        assert isinstance(error, FlagrantError)
        assert isinstance(error, Exception)

    def test_can_be_caught_as_flagrant_error(self) -> None:
        msg = "test error"
        with pytest.raises(FlagrantError):
            raise ConfigurationError(msg)

    def test_message_and_context_handling(self) -> None:
        context: ErrorContext = {"setting": "invalid_value"}
        error = ConfigurationError("invalid configuration", context)

        assert str(error) == "invalid configuration"
        assert error.context == {"setting": "invalid_value"}

    def test_context_default_is_empty_dict(self) -> None:
        error = ConfigurationError("test")

        assert error.context == {}
