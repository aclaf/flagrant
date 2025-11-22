from flagrant.specification.helpers import (
    find_conflicts,
    find_duplicates,
    flatten_string_iterables,
    long_names,
    prefixed_names,
    short_names,
)


class TestFindDuplicates:
    def test_case_sensitive_finds_duplicates(self) -> None:
        result = find_duplicates(["foo", "bar", "foo"])

        assert result == {"foo"}

    def test_case_sensitive_no_duplicates(self) -> None:
        result = find_duplicates(["foo", "bar", "baz"])

        assert result == set()

    def test_case_sensitive_different_case_not_duplicate(self) -> None:
        result = find_duplicates(["Foo", "foo", "FOO"])

        assert result == set()

    def test_case_insensitive_finds_duplicates(self) -> None:
        result = find_duplicates(["Foo", "foo", "FOO"], case_sensitive=False)

        assert result == {"Foo", "foo", "FOO"}

    def test_case_insensitive_preserves_original_casing(self) -> None:
        result = find_duplicates(["Verbose", "verbose"], case_sensitive=False)

        assert "Verbose" in result
        assert "verbose" in result

    def test_empty_input_returns_empty_set(self) -> None:
        result = find_duplicates([])

        assert result == set()

    def test_single_item_no_duplicate(self) -> None:
        result = find_duplicates(["foo"])

        assert result == set()

    def test_multiple_duplicates(self) -> None:
        result = find_duplicates(["a", "a", "b", "b", "c"])

        assert result == {"a", "b"}

    def test_with_empty_strings(self) -> None:
        result = find_duplicates(["", ""])

        assert result == {""}


class TestFindConflicts:
    def test_case_sensitive_finds_conflicts(self) -> None:
        result = find_conflicts(["a", "b"], ["b", "c"])

        assert result == {"b"}

    def test_case_sensitive_no_conflicts(self) -> None:
        result = find_conflicts(["a", "b"], ["c", "d"])

        assert result == set()

    def test_case_sensitive_different_case_no_conflict(self) -> None:
        result = find_conflicts(["Foo"], ["foo"])

        assert result == set()

    def test_case_insensitive_finds_conflicts(self) -> None:
        result = find_conflicts(["Foo"], ["foo"], case_sensitive=False)

        assert result == {"Foo"}

    def test_case_insensitive_returns_items_a_casing(self) -> None:
        result = find_conflicts(["Verbose"], ["VERBOSE"], case_sensitive=False)

        assert result == {"Verbose"}
        assert "VERBOSE" not in result

    def test_empty_first_iterable(self) -> None:
        result = find_conflicts([], ["a", "b"])

        assert result == set()

    def test_empty_second_iterable(self) -> None:
        result = find_conflicts(["a", "b"], [])

        assert result == set()

    def test_both_empty(self) -> None:
        result = find_conflicts([], [])

        assert result == set()

    def test_multiple_conflicts(self) -> None:
        result = find_conflicts(["a", "b", "c"], ["b", "c", "d"])

        assert result == {"b", "c"}


class TestFlattenStringIterables:
    def test_single_iterable(self) -> None:
        result = flatten_string_iterables(["a", "b"])

        assert result == ("a", "b")

    def test_multiple_iterables(self) -> None:
        result = flatten_string_iterables(["a"], ["b", "c"])

        assert result == ("a", "b", "c")

    def test_with_none_values(self) -> None:
        result = flatten_string_iterables(["a"], None, ["b"])

        assert result == ("a", "b")

    def test_all_none(self) -> None:
        result = flatten_string_iterables(None, None)

        assert result == ()

    def test_empty_iterables(self) -> None:
        result = flatten_string_iterables([], [])

        assert result == ()

    def test_order_preservation(self) -> None:
        result = flatten_string_iterables(["a", "b"], ["c", "d"])

        assert result == ("a", "b", "c", "d")

    def test_mixed_empty_and_populated(self) -> None:
        result = flatten_string_iterables(["a"], None, [], ["b", "c"])

        assert result == ("a", "b", "c")

    def test_returns_tuple(self) -> None:
        result = flatten_string_iterables(["a"])

        assert isinstance(result, tuple)


class TestLongNames:
    def test_filters_single_char_names(self) -> None:
        result = long_names(["v", "verbose", "x", "extra"])

        assert result == ("verbose", "extra")

    def test_returns_multi_char_names(self) -> None:
        result = long_names(["verbose", "quiet", "help"])

        assert result == ("verbose", "quiet", "help")

    def test_empty_input(self) -> None:
        result = long_names([])

        assert result == ()

    def test_with_none_values(self) -> None:
        result = long_names(["verbose"], None, ["quiet"])

        assert result == ("verbose", "quiet")

    def test_all_short_names_returns_empty(self) -> None:
        result = long_names(["a", "b", "c"])

        assert result == ()

    def test_multiple_iterables(self) -> None:
        result = long_names(["verbose"], ["v"], ["quiet"])

        assert result == ("verbose", "quiet")


class TestShortNames:
    def test_filters_multi_char_names(self) -> None:
        result = short_names(["v", "verbose", "x", "extra"])

        assert result == ("v", "x")

    def test_returns_single_char_names(self) -> None:
        result = short_names(["v", "q", "h"])

        assert result == ("v", "q", "h")

    def test_empty_input(self) -> None:
        result = short_names([])

        assert result == ()

    def test_with_none_values(self) -> None:
        result = short_names(["v"], None, ["q"])

        assert result == ("v", "q")

    def test_all_long_names_returns_empty(self) -> None:
        result = short_names(["verbose", "quiet", "help"])

        assert result == ()

    def test_multiple_iterables(self) -> None:
        result = short_names(["v"], ["verbose"], ["q"])

        assert result == ("v", "q")


class TestPrefixedNames:
    def test_single_prefix_single_name(self) -> None:
        result = prefixed_names(["verbose"], ["--"])

        assert result == ("--verbose",)

    def test_multiple_prefixes(self) -> None:
        result = prefixed_names(["v"], ["-", "--"])

        assert result == ("-v", "--v")

    def test_multiple_names(self) -> None:
        result = prefixed_names(["verbose", "quiet"], ["--"])

        assert result == ("--verbose", "--quiet")

    def test_cartesian_product(self) -> None:
        result = prefixed_names(["a", "b"], ["-", "--"])

        assert result == ("-a", "-b", "--a", "--b")

    def test_empty_names(self) -> None:
        result = prefixed_names([], ["--"])

        assert result == ()

    def test_empty_prefixes(self) -> None:
        result = prefixed_names(["verbose"], [])

        assert result == ()

    def test_both_empty(self) -> None:
        result = prefixed_names([], [])

        assert result == ()

    def test_prefix_order(self) -> None:
        result = prefixed_names(["v"], ["--", "-"])

        assert result == ("--v", "-v")

    def test_returns_tuple(self) -> None:
        result = prefixed_names(["a"], ["-"])

        assert isinstance(result, tuple)
