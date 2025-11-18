from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class CompletionResult:
    """Structured result of generating completion suggestions."""
