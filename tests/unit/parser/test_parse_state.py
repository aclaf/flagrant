import pytest

from flagrant.parser._state import ParseState


class TestParseStateInitialization:
    def test_initializes_with_empty_tuple(self):
        state = ParseState(())

        assert state.args == ()
        assert state.position == 0
        assert state.remaining_count == 0

    def test_initializes_with_args_tuple(self):
        state = ParseState(("--verbose", "-o", "file.txt"))

        assert state.args == ("--verbose", "-o", "file.txt")
        assert state.position == 0
        assert state.remaining_count == 3

    def test_initializes_with_list_sequence(self):
        state = ParseState(["--verbose", "-o", "file.txt"])

        assert state.args == ("--verbose", "-o", "file.txt")
        assert state.position == 0


class TestParseStateBoundaryConditions:
    def test_is_at_end_for_empty_args(self):
        state = ParseState(())

        assert state.is_at_end is True
        assert state.is_not_at_end is False

    def test_is_not_at_end_for_non_empty_args(self):
        state = ParseState(("--verbose",))

        assert state.is_at_end is False
        assert state.is_not_at_end is True

    def test_remaining_count_at_start(self):
        state = ParseState(("a", "b", "c"))

        assert state.remaining_count == 3

    def test_remaining_count_after_advance(self):
        state = ParseState(("a", "b", "c"))
        state.advance(2)

        assert state.remaining_count == 1

    def test_remaining_count_at_end(self):
        state = ParseState(("a", "b", "c"))
        state.advance(3)

        assert state.remaining_count == 0


class TestParseStateCurrentProperty:
    def test_current_returns_first_arg_at_start(self):
        state = ParseState(("--verbose", "-o"))

        assert state.current == "--verbose"

    def test_current_returns_none_when_at_end(self):
        state = ParseState(())

        assert state.current is None

    def test_current_updates_after_advance(self):
        state = ParseState(("a", "b", "c"))
        state.advance()

        assert state.current == "b"


class TestParseStateNextProperty:
    def test_next_returns_next_arg(self):
        state = ParseState(("a", "b", "c"))

        assert state.next == "b"  # next is peek(1), returns arg after current

    def test_next_returns_none_when_at_end(self):
        state = ParseState(())

        assert state.next is None


class TestParseStatePeek:
    def test_peek_returns_current_by_default(self):
        state = ParseState(("a", "b", "c"))

        assert state.peek() == "a"

    def test_peek_with_positive_offset(self):
        state = ParseState(("a", "b", "c"))

        assert state.peek(1) == "b"
        assert state.peek(2) == "c"

    def test_peek_returns_none_for_out_of_bounds_offset(self):
        state = ParseState(("a", "b"))

        assert state.peek(5) is None

    def test_peek_returns_none_for_negative_out_of_bounds(self):
        state = ParseState(("a", "b"))

        assert state.peek(-5) is None


class TestParseStatePeekN:
    def test_peek_n_returns_tuple_of_args(self):
        state = ParseState(("a", "b", "c", "d"))

        assert state.peek_n(2) == ("a", "b")

    def test_peek_n_with_offset(self):
        state = ParseState(("a", "b", "c", "d"))

        assert state.peek_n(2, offset=1) == ("b", "c")

    def test_peek_n_returns_empty_when_exceeds_remaining(self):
        state = ParseState(("a", "b"))

        assert state.peek_n(5) == ()

    def test_peek_n_returns_empty_for_invalid_offset(self):
        state = ParseState(("a", "b", "c"))

        assert state.peek_n(2, offset=5) == ()


class TestParseStateAdvance:
    def test_advance_increments_position_by_one(self):
        state = ParseState(("a", "b", "c"))
        state.advance()

        assert state.position == 1

    def test_advance_increments_position_by_count(self):
        state = ParseState(("a", "b", "c", "d"))
        state.advance(3)

        assert state.position == 3

    def test_advance_does_not_exceed_total(self):
        state = ParseState(("a", "b"))
        state.advance(10)

        assert state.position == 2
        assert state.is_at_end is True


class TestParseStateConsume:
    def test_consume_returns_current_and_advances(self):
        state = ParseState(("--verbose", "-o"))

        result = state.consume()

        assert result == "--verbose"
        assert state.position == 1
        assert state.current == "-o"

    def test_consume_raises_when_at_end(self):
        state = ParseState(())

        with pytest.raises(IndexError, match="No more arguments to consume"):
            state.consume()

    def test_consume_multiple_times(self):
        state = ParseState(("a", "b", "c"))

        assert state.consume() == "a"
        assert state.consume() == "b"
        assert state.consume() == "c"
        assert state.is_at_end is True


class TestParseStateConsumeN:
    def test_consume_n_returns_tuple_of_n_args(self):
        state = ParseState(("a", "b", "c", "d"))

        result = state.consume_n(2)

        assert result == ("a", "b")
        assert state.position == 2

    def test_consume_n_raises_when_not_enough_args(self):
        state = ParseState(("a", "b"))

        with pytest.raises(IndexError, match="Cannot consume 5 arguments"):
            state.consume_n(5)

    def test_consume_n_with_exact_remaining(self):
        state = ParseState(("a", "b", "c"))

        result = state.consume_n(3)

        assert result == ("a", "b", "c")
        assert state.is_at_end is True


class TestParseStateConsumeRemaining:
    def test_consume_remaining_returns_all_args(self):
        state = ParseState(("a", "b", "c"))

        result = state.consume_remaining()

        assert result == ("a", "b", "c")
        assert state.is_at_end is True

    def test_consume_remaining_after_partial_consumption(self):
        state = ParseState(("a", "b", "c", "d"))
        state.advance(2)

        result = state.consume_remaining()

        assert result == ("c", "d")
        assert state.is_at_end is True

    def test_consume_remaining_returns_empty_when_at_end(self):
        state = ParseState(())

        result = state.consume_remaining()

        assert result == ()


class TestParseStateConsumeIfMatch:
    def test_consume_if_match_consumes_matching_value(self):
        state = ParseState(("--", "extra"))

        result = state.consume_if_match("--")

        assert result is True
        assert state.current == "extra"

    def test_consume_if_match_does_not_consume_non_matching(self):
        state = ParseState(("--verbose", "extra"))

        result = state.consume_if_match("--")

        assert result is False
        assert state.current == "--verbose"

    def test_consume_if_match_returns_false_at_end(self):
        state = ParseState(())

        result = state.consume_if_match("--")

        assert result is False


class TestParseStateConsumeIfPrefix:
    def test_consume_if_prefix_consumes_matching_prefix(self):
        state = ParseState(("--verbose", "extra"))

        result = state.consume_if_prefix("--")

        assert result == "--verbose"
        assert state.current == "extra"

    def test_consume_if_prefix_returns_none_for_non_matching(self):
        state = ParseState(("-v", "extra"))

        result = state.consume_if_prefix("--")

        assert result is None
        assert state.current == "-v"

    def test_consume_if_prefix_returns_none_at_end(self):
        state = ParseState(())

        result = state.consume_if_prefix("--")

        assert result is None


class TestParseStateLastPosition:
    def test_last_position_at_start_is_zero(self):
        state = ParseState(("a", "b"))

        assert state.last_position == 0

    def test_last_position_after_advance(self):
        state = ParseState(("a", "b", "c"))
        state.advance(2)

        assert state.last_position == 1

    def test_last_position_never_negative(self):
        state = ParseState(())

        assert state.last_position == 0
