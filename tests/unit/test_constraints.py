from flagrant.constraints import (
    COMMAND_NAME_PATTERN,
    LONG_NAME_PATTERN,
    MINIMUM_LONG_OPTION_NAME_LENGTH,
    NEGATIVE_PREFIX_PATTERN,
    NEGATIVE_PREFIX_SEPARATOR,
    PARAMETER_NAME_PATTERN,
    SHORT_NAME_PATTERN,
)


class TestCommandNamePattern:
    def test_valid_command_names(self) -> None:
        assert COMMAND_NAME_PATTERN.match("git") is not None
        assert COMMAND_NAME_PATTERN.match("my-command") is not None
        assert COMMAND_NAME_PATTERN.match("cmd_123") is not None

    def test_invalid_command_names(self) -> None:
        assert COMMAND_NAME_PATTERN.match("-invalid") is None
        assert COMMAND_NAME_PATTERN.match("_invalid") is None
        assert COMMAND_NAME_PATTERN.match("") is None


class TestLongNamePattern:
    def test_valid_long_names(self) -> None:
        assert LONG_NAME_PATTERN.match("verbose") is not None
        assert LONG_NAME_PATTERN.match("dry-run") is not None
        assert LONG_NAME_PATTERN.match("output_file") is not None

    def test_invalid_long_names(self) -> None:
        assert LONG_NAME_PATTERN.match("-v") is None
        assert LONG_NAME_PATTERN.match("") is None


class TestShortNamePattern:
    def test_valid_short_names(self) -> None:
        assert SHORT_NAME_PATTERN.match("v") is not None
        assert SHORT_NAME_PATTERN.match("1") is not None

    def test_invalid_short_names(self) -> None:
        assert SHORT_NAME_PATTERN.match("vv") is None
        assert SHORT_NAME_PATTERN.match("-") is None
        assert SHORT_NAME_PATTERN.match("") is None


class TestNegativePrefixPattern:
    def test_valid_negative_prefixes(self) -> None:
        assert NEGATIVE_PREFIX_PATTERN.match("no") is not None
        assert NEGATIVE_PREFIX_PATTERN.match("without") is not None

    def test_invalid_negative_prefixes(self) -> None:
        assert NEGATIVE_PREFIX_PATTERN.match("-no") is None


class TestParameterNamePattern:
    def test_valid_parameter_names(self) -> None:
        assert PARAMETER_NAME_PATTERN.match("file") is not None
        assert PARAMETER_NAME_PATTERN.match("_private") is not None
        assert PARAMETER_NAME_PATTERN.match("arg_1") is not None

    def test_invalid_parameter_names(self) -> None:
        assert PARAMETER_NAME_PATTERN.match("1arg") is None
        assert PARAMETER_NAME_PATTERN.match("-arg") is None


class TestConstants:
    def test_minimum_long_option_length(self) -> None:
        assert MINIMUM_LONG_OPTION_NAME_LENGTH == 2

    def test_negative_prefix_separator(self) -> None:
        assert NEGATIVE_PREFIX_SEPARATOR == "-"
