from dataclasses import dataclass

from flagrant.configuration import Configuration


@dataclass(slots=True, frozen=True)
class CompleterConfiguration(Configuration):
    """Configuration settings for the [Completer][flagrant.Completer]."""
