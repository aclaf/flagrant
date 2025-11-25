from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from typing_extensions import override

from flagrant.types import ParseResultDict, PositionalName

if TYPE_CHECKING:
    from collections.abc import Iterator

    from flagrant.types import OptionValue, PositionalValue


@dataclass(slots=True, frozen=True)
class ParseResult:
    """Structured result of parsing command-line arguments."""

    args: tuple[str, ...]
    command: str
    extra_args: tuple[str, ...] = field(default_factory=tuple)
    options: dict[str, "OptionValue"] = field(default_factory=dict)
    positionals: dict["PositionalName", tuple["PositionalValue", ...]] = field(
        default_factory=dict
    )
    subcommand: "ParseResult | None" = None

    def __iter__(self) -> "Iterator[ParseResult]":
        """Iterate over this result and all nested subcommand results."""
        current: ParseResult | None = self
        while current is not None:
            yield current
            current = current.subcommand

    def __len__(self) -> int:
        """Get the number of commands in the parse result chain."""
        return sum(1 for _ in self)

    @override
    def __repr__(self) -> str:
        parts = [f"ParseResult(command={self.command!r}"]

        if self.options:
            parts.append(f"options={list(self.options.keys())}")
        if self.positionals:
            parts.append(f"positionals={list(self.positionals.keys())}")
        if self.subcommand:
            parts.append(f"subcommand={self.subcommand.command!r}")

        return ", ".join(parts) + ")"

    @override
    def __str__(self) -> str:
        return " ".join(self.path)

    @property
    def path(self) -> tuple[str, ...]:
        """Get the full command path."""
        return tuple(result.command for result in self)

    @property
    def is_leaf(self) -> bool:
        """Check if this is the final command (has no subcommand)."""
        return self.subcommand is None

    @property
    def has_subcommand(self) -> bool:
        """Check if this command has a subcommand."""
        return self.subcommand is not None

    def get_all_options(self) -> dict[str, "OptionValue"]:
        """Get all options from the entire hierarchy.

        Returns a merged dictionary with leaf values taking precedence
        over parent values when names conflict.
        """
        merged: dict[str, OptionValue] = {}
        for result in self:
            merged.update(result.options)
        return merged

    def get_all_positionals(
        self,
    ) -> dict[PositionalName, tuple["PositionalValue", ...]]:
        """Get all positionals from the entire hierarchy.

        Returns a merged dictionary with leaf values taking precedence
        over parent values when names conflict.
        """
        merged: dict[PositionalName, tuple[PositionalValue, ...]] = {}
        for result in self:
            merged.update(result.positionals)
        return merged

    def get_depth(self) -> int:
        """Get the depth of this command in the hierarchy."""
        depth = 0
        current = self.subcommand
        while current is not None:
            depth += 1
            current = current.subcommand
        return depth

    def get_deepest_subcommand(self) -> "ParseResult":
        """Get the most deeply nested subcommand parse result."""
        *_, last = self
        return last

    def get_option(
        self, name: str, default: "OptionValue | None" = None
    ) -> "OptionValue | None":
        """Get an option value with a fallback default."""
        return self.options.get(name, default)

    def get_positional(
        self, name: str, default: "tuple[PositionalValue, ...] | None" = None
    ) -> "tuple[PositionalValue, ...] | None":
        """Get a positional value with a fallback default."""
        return self.positionals.get(name, default)

    def has_option(self, name: str) -> bool:
        """Check if an option was provided."""
        return name in self.options

    def has_positional(self, name: str) -> bool:
        """Check if a positional was provided."""
        return name in self.positionals

    def find_option(self, name: str) -> "OptionValue | None":
        """Find an option in this result or any parent command.

        Searches from leaf to root, returning the first match found.
        Useful for global flags that can appear at any command level.
        """
        for result in self.reversed():
            if name in result.options:
                return result.options[name]
        return None

    def find_positional(self, name: str) -> "tuple[PositionalValue, ...] | None":
        """Find a positional in this result or any parent command.

        Searches from leaf to root, returning the first match found.
        """
        for result in self.reversed():
            if name in result.positionals:
                return result.positionals[name]
        return None

    def reversed(self) -> "Iterator[ParseResult]":
        """Iterate over this result and all nested subcommand results in reverse."""
        if self.subcommand is not None:
            yield from self.subcommand.reversed()
        yield self

    def to_dict(self) -> ParseResultDict:
        """Convert to a dictionary for serialization or debugging."""
        return ParseResultDict(
            command=self.command,
            args=self.args,
            options=self.options,
            positionals=self.positionals,
            subcommand=(self.subcommand.to_dict() if self.subcommand else None),
        )
