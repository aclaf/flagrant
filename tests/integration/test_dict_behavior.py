import pytest

from flagrant.parser import parse_command_line_args
from flagrant.parser.exceptions import OptionNotRepeatableError
from flagrant.specification import (
    command,
    dict_option,
)


class TestBasicDictParsing:
    def test_long_option_captures_key_value(self):
        opt = dict_option(["config"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--config", "key=value"))

        assert result.options["config"] == {"key": "value"}

    def test_short_option_captures_key_value(self):
        opt = dict_option(["c"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("-c", "key=value"))

        assert result.options["c"] == {"key": "value"}

    def test_option_absent_creates_no_entry_in_result(self):
        opt = dict_option(["config"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ())

        assert "config" not in result.options


class TestDictMultipleKeyValues:
    def test_multiple_key_values_in_single_occurrence(self):
        opt = dict_option(["config"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--config", "host=localhost", "port=8080")
        )

        assert result.options["config"] == {"host": "localhost", "port": "8080"}

    def test_multiple_occurrences_merge_by_default(self):
        opt = dict_option(["config"], accumulation_mode="merge")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--config", "a=1", "--config", "b=2"))

        assert result.options["config"] == {"a": "1", "b": "2"}


class TestDictAccumulationModes:
    def test_last_mode_keeps_last_occurrence(self):
        opt = dict_option(["config"], accumulation_mode="last")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--config", "a=1", "--config", "b=2"))

        assert result.options["config"] == {"b": "2"}

    def test_first_mode_keeps_first_occurrence(self):
        opt = dict_option(["config"], accumulation_mode="first")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--config", "a=1", "--config", "b=2"))

        assert result.options["config"] == {"a": "1"}

    def test_merge_mode_combines_dictionaries(self):
        opt = dict_option(["config"], accumulation_mode="merge")
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--config", "a=1", "--config", "b=2", "--config", "a=3")
        )

        # Last value for key 'a' wins
        assert result.options["config"] == {"a": "3", "b": "2"}

    def test_error_mode_raises_on_second_occurrence(self):
        opt = dict_option(["config"], accumulation_mode="error")
        spec = command("test", options=[opt])

        with pytest.raises(OptionNotRepeatableError):
            parse_command_line_args(spec, ("--config", "a=1", "--config", "b=2"))


@pytest.mark.xfail(reason="Nested keys not implemented in MVP")
class TestDictNestedKeys:
    def test_nested_key_creates_nested_dict(self):
        opt = dict_option(["config"], allow_nested=True)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--config", "db.host=localhost"))

        assert result.options["config"] == {"db": {"host": "localhost"}}

    def test_multiple_nested_keys(self):
        opt = dict_option(["config"], allow_nested=True)
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--config", "db.host=localhost", "db.port=5432")
        )

        assert result.options["config"] == {"db": {"host": "localhost", "port": "5432"}}

    def test_deeply_nested_keys(self):
        opt = dict_option(["config"], allow_nested=True)
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--config", "server.db.connection.host=localhost")
        )

        assert result.options["config"] == {
            "server": {"db": {"connection": {"host": "localhost"}}}
        }


class TestDictNestedDisabled:
    def test_nested_disabled_uses_literal_key(self):
        # When allow_nested=False (default), dots are literal key characters
        opt = dict_option(["config"], allow_nested=False)
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--config", "db.host=localhost"))

        assert result.options["config"] == {"db.host": "localhost"}


@pytest.mark.xfail(reason="Nested keys not implemented in MVP")
class TestDictMergeStrategies:
    def test_deep_merge_combines_nested_dicts(self):
        opt = dict_option(["config"], merge_strategy="deep")
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--config", "db.host=localhost", "--config", "db.port=5432")
        )

        assert result.options["config"] == {"db": {"host": "localhost", "port": "5432"}}

    def test_shallow_merge_replaces_nested_dicts(self):
        opt = dict_option(["config"], merge_strategy="shallow")
        spec = command("test", options=[opt])

        result = parse_command_line_args(
            spec, ("--config", "db.host=localhost", "--config", "db.port=5432")
        )

        # Shallow merge replaces the entire 'db' key
        assert result.options["config"] == {"db": {"port": "5432"}}


class TestDictInlineValues:
    def test_inline_value_with_equals(self):
        opt = dict_option(["config"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--config=key=value",))

        assert result.options["config"] == {"key": "value"}

    def test_inline_value_short_option(self):
        opt = dict_option(["c"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("-c=key=value",))

        assert result.options["c"] == {"key": "value"}


class TestDictCustomSeparators:
    def test_custom_key_value_separator(self):
        opt = dict_option(["config"], key_value_separator=":")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--config", "key:value"))

        assert result.options["config"] == {"key": "value"}

    @pytest.mark.xfail(reason="Nested keys not implemented in MVP")
    def test_custom_nesting_separator(self):
        opt = dict_option(["config"], nesting_separator="/")
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--config", "db/host=localhost"))

        assert result.options["config"] == {"db": {"host": "localhost"}}


class TestDictEdgeCases:
    def test_empty_value(self):
        opt = dict_option(["config"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--config", "key="))

        assert result.options["config"] == {"key": ""}

    def test_value_containing_equals(self):
        opt = dict_option(["config"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--config", "expr=a=b"))

        assert result.options["config"] == {"expr": "a=b"}

    def test_value_containing_spaces(self):
        opt = dict_option(["config"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--config", "message=hello world"))

        assert result.options["config"] == {"message": "hello world"}

    def test_numeric_key(self):
        opt = dict_option(["config"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--config", "0=first", "1=second"))

        assert result.options["config"] == {"0": "first", "1": "second"}


class TestDictResultTypes:
    def test_result_is_dict(self):
        opt = dict_option(["config"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--config", "key=value"))

        assert isinstance(result.options["config"], dict)

    def test_values_are_strings(self):
        opt = dict_option(["config"])
        spec = command("test", options=[opt])

        result = parse_command_line_args(spec, ("--config", "count=42"))

        config = result.options["config"]
        assert isinstance(config, dict)
        assert config["count"] == "42"
        assert isinstance(config["count"], str)
