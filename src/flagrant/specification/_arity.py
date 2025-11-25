"""Type and utilities for defines the arity (number of accepted values) for options and positional parameters."""  # noqa: E501

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from typing_extensions import TypeIs

Arity = (
    int
    | Literal["?", "*", "..."]
    | tuple[int, int]
    | tuple[int, Literal["*"]]
    | tuple[int, Literal["..."]]
)
"""The number of arguments an option or positional parameter can accept."""


def get_arity_min(arity: Arity) -> int:
    """Get the minimum number of arguments for the given arity."""
    match arity:
        case int():
            return arity
        case "?":
            return 0
        case "*":
            return 0
        case "...":
            return 0
        case (min_args, _):
            return min_args


def get_arity_max(arity: Arity) -> int | None:
    """Get the maximum number of arguments for the given arity, or None if unbounded."""
    match arity:
        case int():
            return arity
        case "?":
            return 1
        case "*":
            return None
        case "...":
            return None
        case (_, max_args):
            match max_args:
                case int():
                    return max_args
                case "*" | "...":
                    return None


def is_greedy_arity(
    arity: Arity,
) -> "TypeIs[Literal['...'] | tuple[int, Literal['...']]]":
    """True if the arity consumes all remaining arguments."""
    return arity == "..." or (isinstance(arity, tuple) and arity[1] == "...")


def is_fixed_range_arity(arity: Arity) -> "TypeIs[tuple[int, int]]":
    """True if the arity is a fixed range (min and max are integers)."""
    return isinstance(arity, tuple) and isinstance(arity[1], int)


def is_optional_arity(arity: Arity) -> bool:
    """True if the arity accepts zero values."""
    return get_arity_min(arity) == 0


def is_optional_scalar_arity(arity: Arity) -> "TypeIs[Literal['?']]":
    """True if the arity accepts zero or one value."""
    return arity == "?"


def is_scalar_arity(arity: Arity) -> "TypeIs[int | Literal['?']]":
    """True if the arity accepts a single value or zero/one value (`?`)."""
    return isinstance(arity, int) or arity == "?"


def is_unbounded_arity(
    arity: Arity,
) -> "TypeIs[Literal['*'] | tuple[int, Literal['*']]]":
    """True if the arity has unbounded maximum but stops at options and subcommands."""
    return arity == "*" or (isinstance(arity, tuple) and arity[1] == "*")


def is_variadic_arity(
    arity: Arity,
) -> "TypeIs[Literal['*', '...'] | tuple[int, int] | tuple[int, Literal['*']] | tuple[int, Literal['...']]]":  # noqa: E501
    """True is the arity accepts multiple values."""
    return not is_scalar_arity(arity)


def is_zero_arity(arity: Arity) -> "TypeIs[Literal[0]]":
    """True if the arity is accepts no values."""
    return arity == 0


def validate_arity(arity: Arity) -> None:
    """Validate that the given arity is well-formed.

    Args:
        arity: The arity to validate.

    Raises:
        ValueError: If the arity is not well-formed.
    """
    match arity:
        case int() as n:
            if n < 0:
                msg = f"Arity integer must be non-negative, got: {arity}"
                raise ValueError(msg)
        case (min_args, max_args):
            if min_args < 0:
                msg = f"Arity minimum must be non-negative, got: {arity}"
                raise ValueError(msg)
            match max_args:
                case int(n):
                    if n < min_args:
                        msg = f"Arity max must be >= min, got: {arity}"
                        raise ValueError(msg)
                case "*" | "...":
                    pass
        case "?" | "*" | "...":
            pass
