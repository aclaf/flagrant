"""Helpers for specifications and parsing that can be used by downstream packages."""

from collections import Counter, defaultdict
from typing import TYPE_CHECKING

from flagrant.constraints import (
    NEGATIVE_PREFIX_SEPARATOR,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from flagrant.types import FrozenOptionNames, OptionName


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


def all_long_option_names(
    long_names: "Iterable[str]",
    negative_long_names: "Iterable[str] | None" = None,
    negative_prefixes: "Iterable[str] | None" = None,
) -> "FrozenOptionNames":
    """Get all long option names, including negative names.

    Args:
        long_names: An iterable of the option's long names.
        negative_long_names: An iterable of the option's negative long names.
        negative_prefixes: An iterable of the option's negative prefixes.

    Returns:
        A tuple of all long option names.
    """
    names: list[str] = list(long_names or [])

    if negative_long_names is not None:
        names.extend(negative_long_names)

    if negative_prefixes is not None:
        names.extend(negative_prefix_names(long_names, negative_prefixes))

    return tuple(names)


def all_negative_long_option_names(
    long_names: "Iterable[str]",
    negative_long_names: "Iterable[str]",
    negative_prefixes: "Iterable[str]",
) -> "FrozenOptionNames":
    """Get all negative long option names.

    Args:
        long_names: An iterable of the option's long names.
        negative_long_names: An iterable of the option's negative long names.
        negative_prefixes: An iterable of the option's negative prefixes.

    Returns:
        A tuple of all negative long option names.
    """
    names: list[str] = list(negative_long_names)
    prefix_names = negative_prefix_names(
        long_names,
        negative_prefixes,
    )

    return (*names, *prefix_names)


def all_negative_names(
    long_names: "Iterable[str]",
    negative_long_names: "Iterable[str]",
    negative_prefixes: "Iterable[str]",
    negative_short_names: "Iterable[str]",
) -> "FrozenOptionNames":
    """Get all negative option names.

    Args:
        long_names: An iterable of the option's long names.
        negative_long_names: An iterable of the option's negative long names.
        negative_prefixes: An iterable of the option's negative prefixes.
        negative_short_names: An iterable of the option's negative short names.

    Returns:
        A tuple of all negative option names.
    """
    names: list[str] = list(negative_short_names or [])
    names.extend(
        all_negative_long_option_names(
            long_names,
            negative_long_names,
            negative_prefixes,
        )
    )

    return tuple(names)


def all_option_names(
    long_names: "FrozenOptionNames | None" = None,
    short_names: "FrozenOptionNames | None" = None,
    negative_long_names: "FrozenOptionNames | None" = None,
    negative_prefixes: "FrozenOptionNames | None" = None,
    negative_short_names: "FrozenOptionNames | None" = None,
) -> "FrozenOptionNames":
    """Get all option names, including negative names.

    Args:
        long_names: An iterable of the option's long names.
        short_names: An iterable of the option's short names.
        negative_long_names: An iterable of the option's negative long names.
        negative_prefixes: An iterable of the option's negative prefixes.
        negative_short_names: An iterable of the option's negative short names.

    Returns:
        A tuple of all option names.
    """
    names: list[OptionName] = []
    if long_names:
        names.extend(long_names)
    if short_names:
        names.extend(short_names)
    if negative_long_names:
        names.extend(negative_long_names)
    if negative_prefixes and long_names:
        names.extend(negative_prefix_names(long_names, negative_prefixes))
    if negative_short_names:
        names.extend(negative_short_names)
    return tuple(names)


def all_short_names(
    short_names: "Iterable[str]",
    negative_short_names: "Iterable[str] | None" = None,
) -> "FrozenOptionNames":
    """Get all short option names, optionally including negative short names.

    Args:
        short_names: An iterable of the option's short names.
        negative_short_names: An iterable of the option's negative short names.

    Returns:
        A tuple of all short option names.
    """
    names: list[str] = list(short_names)

    if negative_short_names is not None:
        names.extend(negative_short_names)

    return tuple(names)


def negative_prefix_names(
    long_names: "Iterable[str]",
    negative_prefixes: "Iterable[str]",
) -> "FrozenOptionNames":
    """Get all negative prefix names.

    Args:
        long_names: An iterable of the option's long names.
        negative_prefixes: An iterable of the option's negative prefixes.
        negative_prefix_separator: The separator between the negative prefix and
            the option name.

    Returns:
        A tuple of all negative prefix names.
    """
    return tuple(
        {
            f"{prefix}{NEGATIVE_PREFIX_SEPARATOR}{name}"
            for prefix in negative_prefixes
            for name in long_names
        }
    )
