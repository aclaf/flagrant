"""Type and utilities for defines the arity (number of accepted values) for options and positional parameters."""  # noqa: E501

from typing import NamedTuple
from typing_extensions import override


class Arity(NamedTuple):
    """Defines the number of values an option or positional parameter accepts.

    Arity specifies both a minimum and maximum number of values. A maximum
    of None indicates unbounded arity (accepts unlimited values).

    Attributes:
        min: The minimum number of values required.
        max: The maximum number of values allowed, or None for unbounded.

    Examples:
        Common arity patterns:

            Arity(1, 1)     # Exactly one value (the most common case)
            Arity(2, 2)     # Exactly two values
            Arity(0, 0)     # No values (flag options)
            Arity(0, None)  # Zero or more values (optional variadic)
            Arity(1, None)  # One or more values (required variadic)
            Arity(2, 5)     # Between 2 and 5 values (specific range)
    """

    min: int
    max: int | None

    @classmethod
    def exact(cls, count: int) -> "Arity":
        """Create an Arity that requires exactly `count` values.

        Args:
            count: The exact number of values required.

        Returns:
            An Arity instance with both min and max set to `count`.
        """
        return cls(count, count)

    @classmethod
    def exactly_one(cls) -> "Arity":
        """Create an Arity that requires exactly one value.

        Returns:
            An Arity instance with both min and max set to 1.
        """
        return cls(1, 1)

    @classmethod
    def at_least_one(cls) -> "Arity":
        """Create an Arity that requires at least one value.

        Returns:
            An Arity instance with min set to 1 and max set to None (unbounded).
        """
        return cls(1, None)

    @classmethod
    def at_most_one(cls) -> "Arity":
        """Create an Arity that allows at most one value.

        Returns:
            An Arity instance with min set to 0 and max set to 1.
        """
        return cls(0, 1)

    @classmethod
    def none(cls) -> "Arity":
        """Create an Arity that accepts no values.

        Returns:
            An Arity instance with both min and max set to 0.
        """
        return cls(0, 0)

    @classmethod
    def zero_or_more(cls) -> "Arity":
        """Create an Arity that allows zero or more values.

        Returns:
            An Arity instance with min set to 0 and max set to None (unbounded).
        """
        return cls(0, None)

    @override
    def __repr__(self) -> str:
        return f"Arity(min={self.min!r}, max={self.max!r})"

    @property
    def accepts_at_least_one_value(self) -> bool:
        """Check if this arity accepts at least one value.

        Returns:
            True if the arity's maximum is None (unbounded) or greater than 0,
            False otherwise.
        """
        return self.max is None or self.max > 0

    @property
    def accepts_at_most_one_value(self) -> bool:
        """Check if this arity accepts at most one value.

        Returns:
            True if the arity allows zero or one value, False otherwise.
        """
        return self.max == 1

    @property
    def accepts_multiple_values(self) -> bool:
        """Check if this arity accepts multiple values.

        Returns:
            True if the arity allows more than one value, False otherwise.
        """
        return self.max is None or self.max > 1

    @property
    def accepts_unbounded_values(self) -> bool:
        """Check if this arity accepts any number of values.

        Returns:
            True if the arity's minimum is 0 and maximum is None (unbounded),
            False otherwise.
        """
        return self.min == 0 and self.max is None

    @property
    def accepts_values(self) -> bool:
        """Check if this arity accepts one or more values.

        Returns:
            True if the arity requires or allows values, False if it accepts none.
        """
        return self.max is None or self.max > 0

    @property
    def rejects_values(self) -> bool:
        """Check if this arity rejects all values.

        Returns:
            True if the arity accepts no values (min and max are both 0),
            False otherwise.
        """
        return self.min == 0 and self.max == 0

    @property
    def requires_multiple_values(self) -> bool:
        """Check if this arity requires multiple values.

        Returns:
            True if the arity's minimum is greater than 1, False otherwise.
        """
        return self.min > 1

    @property
    def requires_values(self) -> bool:
        """Check if this arity requires one or more values.

        Returns:
            True if the arity requires at least one value, False otherwise.
        """
        return self.min > 0
