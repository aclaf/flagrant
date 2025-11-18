from typing import TYPE_CHECKING
from typing_extensions import override

from ._protocols import CompletionFormatter

if TYPE_CHECKING:
    from ._result import CompletionResult


class PowerShellFormatter(CompletionFormatter):
    @staticmethod
    @override
    def format(result: "CompletionResult") -> str:
        raise NotImplementedError

    @staticmethod
    @override
    def generate_script(command_name: str) -> str:
        raise NotImplementedError
