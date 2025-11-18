from flagrant.completions import Completer, CompletionResult


class TestCompleter:
    def test_complete_returns_a_completion_result(self, empty_completer: Completer):
        result = empty_completer.complete()
        assert isinstance(result, CompletionResult)
