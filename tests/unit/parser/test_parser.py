from flagrant.parser import ParseResult


class TestParser:
    def test_parse_returns_a_parse_result(self, empty_parser):
        # TODO(refactor): Update this test for the new parser API
        result = empty_parser.parse()
        assert isinstance(result, ParseResult)
