import pytest

from flagrant.configuration import ParserConfiguration
from flagrant.exceptions import ConfigurationError


class TestParserConfigurationDefaults:
    def test_default_initialization(self) -> None:
        config = ParserConfiguration()

        assert config.allow_abbreviated_options is False
        assert config.allow_abbreviated_commands is False
        assert config.allow_command_aliases is True
        assert config.allow_negative_numbers is True
        assert config.case_sensitive_commands is True
        assert config.case_sensitive_options is True
        assert config.long_name_prefix == "--"
        assert config.short_name_prefix == "-"
        assert config.trailing_arguments_separator == "--"
        assert config.key_value_separator == "="
        assert config.nesting_separator == "."
        assert config.max_argument_file_depth == 5
        assert config.minimum_abbreviation_length == 3

    def test_frozen_prevents_modification(self) -> None:
        config = ParserConfiguration()

        with pytest.raises(AttributeError):
            config.allow_negative_numbers = False  # type: ignore[misc]


class TestParserConfigurationValidation:
    def test_key_value_separator_equals_dict_item_separator_raises(self) -> None:
        with pytest.raises(ConfigurationError) as exc_info:
            ParserConfiguration(key_value_separator="=", dict_item_separator="=")

        assert "key_value_separator" in str(exc_info.value)
        assert "dict_item_separator" in str(exc_info.value)

    def test_key_value_separator_equals_nesting_separator_raises(self) -> None:
        with pytest.raises(ConfigurationError) as exc_info:
            ParserConfiguration(key_value_separator=".", nesting_separator=".")

        assert "key_value_separator" in str(exc_info.value)
        assert "nesting_separator" in str(exc_info.value)

    def test_long_name_prefix_equals_short_name_prefix_raises(self) -> None:
        with pytest.raises(ConfigurationError) as exc_info:
            ParserConfiguration(long_name_prefix="-", short_name_prefix="-")

        assert "long_name_prefix" in str(exc_info.value)
        assert "short_name_prefix" in str(exc_info.value)

    def test_short_name_prefix_equals_trailing_separator_raises(self) -> None:
        with pytest.raises(ConfigurationError) as exc_info:
            ParserConfiguration(
                short_name_prefix="++",
                long_name_prefix="+++",
                trailing_arguments_separator="++",
            )

        assert "short_name_prefix" in str(exc_info.value)
        assert "trailing_arguments_separator" in str(exc_info.value)

    def test_max_argument_file_depth_less_than_one_raises(self) -> None:
        with pytest.raises(ConfigurationError) as exc_info:
            ParserConfiguration(max_argument_file_depth=0)

        assert "max_argument_file_depth" in str(exc_info.value)
        assert "at least 1" in str(exc_info.value)

        with pytest.raises(ConfigurationError):
            ParserConfiguration(max_argument_file_depth=-1)

    def test_minimum_abbreviation_length_less_than_one_raises(self) -> None:
        with pytest.raises(ConfigurationError) as exc_info:
            ParserConfiguration(minimum_abbreviation_length=0)

        assert "minimum_abbreviation_length" in str(exc_info.value)
        assert "at least 1" in str(exc_info.value)

        with pytest.raises(ConfigurationError):
            ParserConfiguration(minimum_abbreviation_length=-1)

    def test_valid_separator_combinations_pass(self) -> None:
        config = ParserConfiguration(
            key_value_separator="=",
            dict_item_separator=",",
            nesting_separator=".",
            long_name_prefix="--",
            short_name_prefix="-",
            trailing_arguments_separator="--",
        )

        assert config.key_value_separator == "="
        assert config.dict_item_separator == ","
        assert config.nesting_separator == "."


class TestParserConfigurationNullable:
    def test_dict_item_separator_none_skips_validation(self) -> None:
        config = ParserConfiguration(
            key_value_separator="=",
            dict_item_separator=None,
        )

        assert config.dict_item_separator is None
        assert config.key_value_separator == "="

    def test_dict_item_separator_none_is_default(self) -> None:
        config = ParserConfiguration()

        assert config.dict_item_separator is None


class TestParserConfigurationCustomValues:
    def test_custom_prefixes(self) -> None:
        config = ParserConfiguration(
            long_name_prefix="++",
            short_name_prefix="+",
        )

        assert config.long_name_prefix == "++"
        assert config.short_name_prefix == "+"

    def test_custom_separators(self) -> None:
        config = ParserConfiguration(
            key_value_separator=":",
            nesting_separator="/",
            trailing_arguments_separator="---",
        )

        assert config.key_value_separator == ":"
        assert config.nesting_separator == "/"
        assert config.trailing_arguments_separator == "---"

    def test_custom_depth_limits(self) -> None:
        config = ParserConfiguration(
            max_argument_file_depth=10,
            minimum_abbreviation_length=5,
        )

        assert config.max_argument_file_depth == 10
        assert config.minimum_abbreviation_length == 5
