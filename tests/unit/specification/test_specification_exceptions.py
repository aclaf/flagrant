import pytest

from flagrant.exceptions import ErrorContext, FlagrantError
from flagrant.specification.exceptions import (
    CommandSpecificationError,
    OptionSpecificationError,
    SpecificationError,
)


class TestSpecificationError:
    def test_inherits_from_flagrant_error(self) -> None:
        error = SpecificationError("spec error")

        assert isinstance(error, FlagrantError)
        assert isinstance(error, Exception)

    def test_message_and_context_handling(self) -> None:
        context: ErrorContext = {"field": "options"}
        error = SpecificationError("invalid specification", context)

        assert str(error) == "invalid specification"
        assert error.context == {"field": "options"}

    def test_can_be_caught_as_flagrant_error(self) -> None:
        msg = "test error"
        with pytest.raises(FlagrantError):
            raise SpecificationError(msg)


class TestOptionSpecificationError:
    def test_message_formatting_includes_option_name(self) -> None:
        error = OptionSpecificationError("verbose", "cannot accept values")

        assert "Option 'verbose' is invalid" in str(error)
        assert "cannot accept values" in str(error)

    def test_inherits_from_specification_error(self) -> None:
        error = OptionSpecificationError("verbose", "test error")

        assert isinstance(error, SpecificationError)
        assert isinstance(error, FlagrantError)

    def test_context_preserved(self) -> None:
        context: ErrorContext = {"expected_type": "flag", "actual_type": "scalar"}
        error = OptionSpecificationError("verbose", "wrong type", context)

        assert error.context == {"expected_type": "flag", "actual_type": "scalar"}

    def test_short_option_name_format(self) -> None:
        error = OptionSpecificationError("v", "invalid short option")

        assert "Option 'v' is invalid" in str(error)
        assert "invalid short option" in str(error)

    def test_long_option_with_prefix(self) -> None:
        error = OptionSpecificationError("--verbose", "duplicate definition")

        assert "Option '--verbose' is invalid" in str(error)

    def test_hyphenated_option_name(self) -> None:
        error = OptionSpecificationError("dry-run", "conflicting names")

        assert "Option 'dry-run' is invalid" in str(error)


class TestCommandSpecificationError:
    def test_message_formatting_includes_command_name(self) -> None:
        error = CommandSpecificationError("deploy", "required but not provided")

        assert "Command 'deploy' is invalid" in str(error)
        assert "required but not provided" in str(error)

    def test_inherits_from_specification_error(self) -> None:
        error = CommandSpecificationError("deploy", "test error")

        assert isinstance(error, SpecificationError)
        assert isinstance(error, FlagrantError)

    def test_context_preserved(self) -> None:
        context: ErrorContext = {"subcommands": ["start", "stop"]}
        error = CommandSpecificationError("service", "missing handler", context)

        assert error.context == {"subcommands": ["start", "stop"]}

    def test_nested_command_name(self) -> None:
        error = CommandSpecificationError("git.commit", "ambiguous")

        assert "Command 'git.commit' is invalid" in str(error)

    def test_hyphenated_command_name(self) -> None:
        error = CommandSpecificationError("dry-run", "conflicting alias")

        assert "Command 'dry-run' is invalid" in str(error)

    def test_can_be_caught_as_specification_error(self) -> None:
        name = "test"
        with pytest.raises(SpecificationError):
            raise CommandSpecificationError(name, "error")
