from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ParseResult:
    """Structured result of parsing command-line arguments."""
