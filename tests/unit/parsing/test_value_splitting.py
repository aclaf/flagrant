import pytest

from flagrant.parser._parser import (
    _split_escaped,  # pyright: ignore[reportPrivateUsage]
)


@pytest.mark.xfail(reason="Function not yet integrated into parser", strict=False)
class TestValueSplitting:
    @pytest.mark.parametrize(
        ("input_str", "delimiter", "escape_char", "expected"),
        [
            ("a,b", ",", "\\", ("a", "b")),
            ("abc", ",", "\\", ("abc",)),
            ("", ",", "\\", ()),
            ("a,b,c,d", ",", "\\", ("a", "b", "c", "d")),
            ("a\\,b", ",", "\\", ("a\\,b",)),
            ("a\\,b,c", ",", "\\", ("a\\,b", "c")),
            ("a\\,b\\,c", ",", "\\", ("a\\,b\\,c",)),
            ("a\\\\,b", ",", "\\", ("a\\\\", "b")),
            (",abc", ",", "\\", ("", "abc")),
            ("abc,", ",", "\\", ("abc", "")),
            ("a,,b", ",", "\\", ("a", "", "b")),
            (",", ",", "\\", ("", "")),
        ],
    )
    def test_split_escaped(
        self,
        input_str: str,
        delimiter: str,
        escape_char: str,
        expected: tuple[str, ...],
    ):
        result = _split_escaped(input_str, delimiter, escape_char)
        assert result == expected


@pytest.mark.xfail(reason="Function not yet integrated into parser", strict=False)
class TestValidation:
    def test_multichar_delimiter_raises_value_error(self):
        with pytest.raises(ValueError, match="Delimiter must be a single character"):
            _split_escaped("a::b", "::", "\\")

    def test_multichar_escape_raises_value_error(self):
        with pytest.raises(
            ValueError, match="Escape character must be a single character"
        ):
            _split_escaped("a,b", ",", "\\\\")

    def test_same_delimiter_and_escape_raises_value_error(self):
        with pytest.raises(
            ValueError, match="Escape character and delimiter cannot be the same"
        ):
            _split_escaped("a,b", ",", ",")
