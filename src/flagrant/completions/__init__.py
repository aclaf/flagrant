"""Completion engine for command-line arguments."""

from ._bash import BashFormatter
from ._completer import Completer
from ._configuration import CompleterConfiguration
from ._fish import FishFormatter
from ._powershell import PowerShellFormatter
from ._protocols import CompletionFormatter
from ._result import CompletionResult
from ._zsh import ZshFormatter

__all__ = [
    "BashFormatter",
    "Completer",
    "CompleterConfiguration",
    "CompletionFormatter",
    "CompletionResult",
    "FishFormatter",
    "PowerShellFormatter",
    "ZshFormatter",
]
