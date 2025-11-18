from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ._result import CompletionResult


class CompletionFormatter(Protocol):
    @staticmethod
    def format(result: "CompletionResult") -> str: ...

    @staticmethod
    def generate_script(command_name: str) -> str: ...
