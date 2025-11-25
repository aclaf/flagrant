import pytest

from flagrant.parser._parser import (
    _split_escaped,  # pyright: ignore[reportPrivateUsage]
)


@pytest.mark.xfail(reason="Function not yet integrated into parser", strict=False)
class TestBasicSplitting:
    def test_single_delimiter_splits_into_two_segments(self):
        result = _split_escaped("a,b", ",", "\\")

        assert result == ("a", "b")

    def test_no_delimiter_returns_single_segment(self):
        result = _split_escaped("abc", ",", "\\")

        assert result == ("abc",)

    def test_empty_string_returns_empty_tuple(self):
        result = _split_escaped("", ",", "\\")

        assert result == ()

    def test_multiple_delimiters_create_multiple_segments(self):
        result = _split_escaped("a,b,c,d", ",", "\\")

        assert result == ("a", "b", "c", "d")


@pytest.mark.xfail(reason="Function not yet integrated into parser", strict=False)
class TestEscapedDelimiters:
    def test_escaped_delimiter_preserved_in_segment(self):
        result = _split_escaped("a\\,b", ",", "\\")

        assert result == ("a\\,b",)

    def test_escaped_delimiter_does_not_split_segment(self):
        result = _split_escaped("a\\,b,c", ",", "\\")

        assert result == ("a\\,b", "c")

    def test_multiple_escaped_delimiters_in_same_segment(self):
        result = _split_escaped("a\\,b\\,c", ",", "\\")

        assert result == ("a\\,b\\,c",)

    def test_escaped_escape_character_preserved(self):
        result = _split_escaped("a\\\\,b", ",", "\\")

        assert result == ("a\\\\", "b")


@pytest.mark.xfail(reason="Function not yet integrated into parser", strict=False)
class TestEdgeCases:
    def test_delimiter_at_start_creates_empty_first_segment(self):
        result = _split_escaped(",abc", ",", "\\")

        assert result == ("", "abc")

    def test_delimiter_at_end_creates_empty_last_segment(self):
        result = _split_escaped("abc,", ",", "\\")

        assert result == ("abc", "")

    def test_consecutive_delimiters_create_empty_segments(self):
        result = _split_escaped("a,,b", ",", "\\")

        assert result == ("a", "", "b")

    def test_only_delimiter_returns_two_empty_segments(self):
        result = _split_escaped(",", ",", "\\")

        assert result == ("", "")


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
