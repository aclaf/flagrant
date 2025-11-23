import pytest

from flagrant.specification import (
    Arity,
    CommandSpecification,
    DictOptionSpecification,
    FlagOptionSpecification,
    OptionSpecificationType,
    ValueOptionSpecification,
)
from flagrant.specification.enums import (
    DictAccumulationMode,
    DictMergeStrategy,
    FlagAccumulationMode,
    ValueAccumulationMode,
)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        item.add_marker(pytest.mark.unit)


@pytest.fixture
def make_flag_opt():
    """Factory for FlagOptionSpecification."""

    def _make(  # noqa: PLR0913
        name: str = "flag",
        *,
        long_names: tuple[str, ...] | None = None,
        short_names: tuple[str, ...] | None = None,
        negative_prefixes: tuple[str, ...] | None = None,
        negative_short_names: tuple[str, ...] | None = None,
        accumulation_mode: FlagAccumulationMode = FlagAccumulationMode.LAST,
        case_sensitive: bool = True,
    ) -> FlagOptionSpecification:
        _long_names = (name,) if long_names is None else long_names
        _short_names = () if short_names is None else short_names
        _negative_prefixes = () if negative_prefixes is None else negative_prefixes
        _negative_short_names = (
            () if negative_short_names is None else negative_short_names
        )

        return FlagOptionSpecification(
            name=name,
            arity=Arity.none(),
            greedy=False,
            preferred_name=name,
            long_names=_long_names,
            short_names=_short_names,
            negative_prefixes=_negative_prefixes,
            negative_short_names=_negative_short_names,
            accumulation_mode=accumulation_mode,
            case_sensitive=case_sensitive,
        )

    return _make


@pytest.fixture
def make_value_opt():
    """Factory for ValueOptionSpecification."""

    def _make(  # noqa: PLR0913
        name: str = "option",
        *,
        arity: Arity | None = None,
        long_names: tuple[str, ...] | None = None,
        short_names: tuple[str, ...] | None = None,
        greedy: bool = False,
        accumulation_mode: ValueAccumulationMode = ValueAccumulationMode.LAST,
        allow_negative_numbers: bool = False,
        case_sensitive: bool = True,
    ) -> ValueOptionSpecification:
        _long_names = (name,) if long_names is None else long_names
        _short_names = () if short_names is None else short_names
        _arity = arity or Arity.exactly_one()

        return ValueOptionSpecification(
            name=name,
            arity=_arity,
            greedy=greedy,
            preferred_name=name,
            long_names=_long_names,
            short_names=_short_names,
            accumulation_mode=accumulation_mode,
            allow_negative_numbers=allow_negative_numbers,
            case_sensitive=case_sensitive,
        )

    return _make


@pytest.fixture
def make_dict_opt():
    def _make(  # noqa: PLR0913
        name: str = "dict",
        *,
        arity: Arity | None = None,
        long_names: tuple[str, ...] | None = None,
        short_names: tuple[str, ...] | None = None,
        greedy: bool = False,
        accumulation_mode: DictAccumulationMode = DictAccumulationMode.MERGE,
        merge_strategy: DictMergeStrategy = DictMergeStrategy.DEEP,
        case_sensitive: bool = True,
        allow_nested: bool = True,
        key_value_separator: str | None = None,
        nesting_separator: str | None = None,
    ) -> DictOptionSpecification:
        _arity = arity or Arity.exactly_one()
        _long_names = (name,) if long_names is None else long_names
        _short_names = () if short_names is None else short_names
        _arity = arity or Arity.exactly_one()

        return DictOptionSpecification(
            name=name,
            arity=_arity,
            greedy=greedy,
            preferred_name=name,
            long_names=_long_names,
            short_names=_short_names,
            accumulation_mode=accumulation_mode,
            merge_strategy=merge_strategy,
            case_sensitive=case_sensitive,
            allow_nested=allow_nested,
            key_value_separator=key_value_separator,
            nesting_separator=nesting_separator,
        )

    return _make


@pytest.fixture
def make_command():
    """Factory for CommandSpecification."""

    def _make(
        name: str = "test_command",
        *,
        aliases: tuple[str, ...] | None = None,
        options: dict[str, OptionSpecificationType] | None = None,
        positionals: dict[str, Arity] | None = None,
        subcommands: dict[str, CommandSpecification] | None = None,
    ) -> CommandSpecification:
        return CommandSpecification(
            name=name,
            aliases=aliases,
            options=options,
            positionals=positionals,
            subcommands=subcommands,
        )

    return _make


@pytest.fixture
def empty_command_spec():
    return CommandSpecification("test")
