import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ._configuration import ParserConfiguration
from ._result import ParseResult

if TYPE_CHECKING:
    from collections.abc import Sequence

    from flagrant.specification import CommandSpecification


@dataclass(slots=True, frozen=True)
class Parser:
    """Extracts structured results from command-line arguments."""

    spec: "CommandSpecification"
    config: "ParserConfiguration" = field(default_factory=ParserConfiguration)

    def parse(self, args: "Sequence[str] | None" = None) -> ParseResult:
        """Generate structured results from command-line arguments."""
        args = args or sys.argv[1:]
        return ParseResult()
