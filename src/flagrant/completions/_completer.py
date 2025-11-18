import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ._configuration import CompleterConfiguration
from ._result import CompletionResult

if TYPE_CHECKING:
    from collections.abc import Sequence

    from flagrant.specification import CommandSpecification


@dataclass(slots=True, frozen=True)
class Completer:
    """Generates completion suggestions from command-line arguments."""

    spec: "CommandSpecification"
    config: "CompleterConfiguration" = field(default_factory=CompleterConfiguration)

    def complete(self, args: "Sequence[str] | None" = None) -> CompletionResult:
        """Generate completion suggestions from command-line arguments."""
        args = args or sys.argv[1:]
        return CompletionResult()
