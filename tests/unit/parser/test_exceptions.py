from typing import TYPE_CHECKING

from flagrant.parser.exceptions import (
    AmbiguousOptionError,
    AmbiguousSubcommandError,
    OptionMissingValueError,
    OptionNotRepeatableError,
    OptionParseError,
    OptionValueNotAllowedError,
    ParseError,
    PositionalMissingValueError,
    PositionalParseError,
    PositionalUnexpectedValueError,
    SubcommandParseError,
    UnknownOptionError,
    UnknownSubcommandError,
)

if TYPE_CHECKING:
    from flagrant.exceptions import ErrorContext


class TestParseErrorHierarchy:
    def test_parse_error_is_base_class(self):
        err = ParseError(
            message="test error",
            path=("git",),
            args=("--unknown",),
            position=0,
        )

        assert isinstance(err, Exception)
        # Note: self.args shadows Exception.args, so str(err) returns first CLI arg
        # The message is passed to FlagrantError but then shadowed
        assert err.args == ("--unknown",)

    def test_parse_error_stores_path_and_derives_command(self):
        err = ParseError(message="test", path=("git", "commit"), args=(), position=0)

        assert err.path == ("git", "commit")
        assert err.command == "commit"


class TestUnknownOptionError:
    def test_inherits_from_option_parse_error(self):
        err = UnknownOptionError(
            option="foo", path=("test",), args=("--foo",), position=0
        )

        assert isinstance(err, OptionParseError)
        assert isinstance(err, ParseError)


class TestAmbiguousOptionError:
    def test_inherits_from_option_parse_error(self) -> None:
        err = AmbiguousOptionError(
            option="v",
            matched=("verbose",),
            path=("test",),
            args=("-v",),
            position=0,
        )

        assert isinstance(err, OptionParseError)


class TestOptionMissingValueError:
    def test_inherits_from_option_parse_error(self):
        err = OptionMissingValueError(
            option="file",
            required=1,
            received=None,
            path=("test",),
            args=("--file",),
            position=0,
        )

        assert isinstance(err, OptionParseError)


class TestOptionValueNotAllowedError:
    def test_inherits_from_option_parse_error(self):
        err = OptionValueNotAllowedError(
            option="flag",
            received="val",
            path=("test",),
            args=("--flag=val",),
            position=0,
        )

        assert isinstance(err, OptionParseError)


class TestOptionNotRepeatableError:
    def test_inherits_from_option_parse_error(self):
        err = OptionNotRepeatableError(
            option="file",
            current="a",
            received="b",
            path=("test",),
            args=(),
            position=0,
        )

        assert isinstance(err, OptionParseError)


class TestPositionalMissingValueError:
    def test_inherits_from_positional_parse_error(self):
        err = PositionalMissingValueError(
            message="test",
            positional="arg",
            required=1,
            received=None,
            path=("test",),
            args=(),
            position=0,
        )

        assert isinstance(err, PositionalParseError)


class TestPositionalUnexpectedValueError:
    def test_inherits_from_positional_parse_error(self):
        err = PositionalUnexpectedValueError(
            positional="pos",
            received="val",
            path=("test",),
            args=(),
            position=0,
        )

        assert isinstance(err, PositionalParseError)


class TestUnknownSubcommandError:
    def test_inherits_from_subcommand_parse_error(self):
        err = UnknownSubcommandError(
            subcommand="bad", path=("test",), args=("bad",), position=0
        )

        assert isinstance(err, SubcommandParseError)
        assert isinstance(err, ParseError)


class TestAmbiguousSubcommandError:
    def test_inherits_from_subcommand_parse_error(self):
        err = AmbiguousSubcommandError(
            subcommand="c",
            matched=("cmd1",),
            path=("test",),
            args=("c",),
            position=0,
        )

        assert isinstance(err, SubcommandParseError)


class TestExceptionContext:
    def test_parse_error_accepts_context(self) -> None:
        context: ErrorContext = {"hint": "Did you mean --verbose?"}
        err = ParseError(
            message="test",
            path=("git",),
            args=(),
            position=0,
            context=context,
        )

        assert err.context == context

    def test_option_parse_error_accepts_context(self) -> None:
        context: ErrorContext = {"suggestion": "verbose"}
        err = UnknownOptionError(
            option="verb",
            path=("git",),
            args=("--verb",),
            position=0,
            context=context,
        )

        assert err.context == context
