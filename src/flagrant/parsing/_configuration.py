from dataclasses import dataclass

from flagrant.configuration import Configuration


@dataclass(slots=True, frozen=True)
class ParserConfiguration(Configuration):
    """Configuration settings for the [Parser][flagrant.Parser]."""
