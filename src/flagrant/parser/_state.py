from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from flagrant.types import Arg, ArgList


@dataclass(slots=True)
class ParseState:
    _args: "Sequence[str]"
    _total: int = field(init=False)
    _position: int = field(default=0)

    def __post_init__(self) -> None:
        self._total = len(self._args)

    @property
    def args(self) -> "ArgList":
        return tuple(self._args)

    @property
    def is_at_end(self) -> bool:
        return self.position >= self._total

    @property
    def is_not_at_end(self) -> bool:
        return self._position < self._total

    @property
    def current(self) -> "Arg | None":
        if self._position >= self._total:
            return None
        return self._args[self._position]

    @property
    def next(self) -> "Arg | None":
        return self.peek(1)

    @property
    def position(self) -> int:
        return self._position

    @property
    def last_position(self) -> int:
        return max(0, self._position - 1)

    @property
    def remaining_count(self) -> int:
        return max(0, self._total - self._position)

    def peek(self, offset: int = 0) -> "Arg | None":
        index = self._position + offset
        if 0 <= index < self._total:
            return self._args[index]
        return None

    def peek_n(self, count: int, offset: int = 0) -> tuple["Arg", ...]:
        start = self._position + offset
        end = start + count
        if 0 <= start < self._total and end <= self._total:
            return tuple(self._args[start:end])
        return ()

    def advance(self, count: int = 1) -> None:
        self._position = min(self._position + count, self._total)

    def consume(self) -> "Arg":
        if self.is_at_end:
            msg = "No more arguments to consume"
            raise IndexError(msg)

        arg = self._args[self._position]
        self._position += 1
        return arg

    def consume_n(self, count: int) -> tuple["Arg", ...]:
        if self._position + count > self._total:
            msg = (
                f"Cannot consume {count} arguments."
                f" Only {self.remaining_count} remaining"
            )
            raise IndexError(msg)

        start = self._position
        end = start + count
        args = self._args[start:end]
        self.advance(count)
        return tuple(args)

    def consume_if_match(self, value: "Arg") -> bool:
        if self._position < self._total and self._args[self._position] == value:
            self._position += 1
            return True
        return False

    def consume_if_prefix(self, prefix: str) -> "Arg | None":
        if self._position < self._total and self._args[self._position].startswith(
            prefix
        ):
            return self.consume()
        return None

    def consume_remaining(self) -> tuple["Arg", ...]:
        if self.is_at_end:
            return ()
        args = self._args[self._position :]
        self._position = self._total
        return tuple(args)
