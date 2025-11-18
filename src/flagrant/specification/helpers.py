"""Helpers for specifications and parsing that can be used by downstream packages."""

import itertools
from collections import Counter, defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


def find_duplicates(items: "Iterable[str]", *, case_sensitive: bool = True) -> set[str]:
    """Find duplicate items in an iterable.

    Args:
        items: An iterable of strings to check for duplicates.
        case_sensitive: Whether the comparison is case sensitive.

    Returns:
        A set of duplicate strings found in the iterable.
    """
    if case_sensitive:
        counts = Counter(items)
        return {item for item, count in counts.items() if count > 1}

    lower_to_originals: dict[str, list[str]] = defaultdict(list)
    for item in items:
        lower_to_originals[item.lower()].append(item)

    return {
        original
        for originals in lower_to_originals.values()
        if len(originals) > 1
        for original in originals
    }


def find_conflicts(
    items_a: "Iterable[str]", items_b: "Iterable[str]", *, case_sensitive: bool = True
) -> set[str]:
    """Find items that appear in both iterables.

    Args:
        items_a: First iterable of strings.
        items_b: Second iterable of strings.
        case_sensitive: Whether the comparison is case sensitive.

    Returns:
        A set of conflicting items in their original casing from items_a.
    """
    if case_sensitive:
        return set(items_a) & set(items_b)
    # Build lowercase mapping from items_a
    lower_to_original: dict[str, str] = {}
    for item in items_a:
        lower = item.lower()
        if lower not in lower_to_original:
            lower_to_original[lower] = item

    # Check items_b against lowercase keys
    conflicts: set[str] = set()
    for item in items_b:
        lower = item.lower()
        if lower in lower_to_original:
            conflicts.add(lower_to_original[lower])

    return conflicts


def flatten_string_iterables(*iterables: "Iterable[str] | None") -> tuple[str, ...]:
    """Flatten multiple iterables of strings into a single tuple.

    Args:
        *iterables: Multiple iterables of strings.

    Returns:
        A tuple containing all strings from the input iterables.
    """
    return tuple(itertools.chain.from_iterable(filter(None, iterables)))


def long_names(*long_names: "Iterable[str] | None") -> tuple[str, ...]:
    """Get all long names from multiple iterables.

    Args:
        *long_names: Multiple iterables of long names.

    Returns:
        A tuple of all long names.
    """
    return tuple(
        name for name in flatten_string_iterables(*long_names) if len(name) > 1
    )


def short_names(*short_names: "Iterable[str] | None") -> tuple[str, ...]:
    """Get all short names from multiple iterables.

    Args:
        *short_names: Multiple iterables of short names.

    Returns:
        A tuple of all short names.
    """
    return tuple(
        name for name in flatten_string_iterables(*short_names) if len(name) == 1
    )


def prefixed_names(
    names: "Iterable[str]",
    prefixes: "Iterable[str]",
) -> tuple[str, ...]:
    """Get all prefixed names.

    Args:
        names: An iterable of the option's names.
        prefixes: An iterable of the option's prefixes.

    Returns:
        A tuple of all prefixed names.
    """
    return tuple(
        f"{prefix}{name}" for prefix, name in itertools.product(prefixes, names)
    )
