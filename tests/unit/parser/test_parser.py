from flagrant.parsing import Parser, ParseResult


class TestParser:
    def test_parse_returns_a_parse_result(self, empty_parser: Parser):
        result = empty_parser.parse()
        assert isinstance(result, ParseResult)
