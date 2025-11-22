# Parser types specification

This page provides a comprehensive reference for all type definitions used in the Flagrant parser component. It describes the specification types that define command structure, the result types that represent parsed output, the configuration types that control parsing behavior, and the supporting types that enable type-safe parsing operations.

The parser type system is designed around three architectural principles: immutability for thread safety and predictable behavior, type safety through comprehensive Python type hints leveraging modern typing features, and compositional design where simple types combine to express complex CLI semantics. Understanding these types is essential for creating command specifications, processing parse results, and reasoning about parser behavior.

## Table of contents

- [Parser types specification](#parser-types-specification)
  - [Table of contents](#table-of-contents)
  - [Type system overview](#type-system-overview)
  - [Specification types](#specification-types)
    - [Specification hierarchy](#specification-hierarchy)
    - [ParameterSpecification](#parameterspecification)
    - [OptionSpecification](#optionspecification)
    - [FlagOptionSpecification](#flagoptionspecification)
    - [ValueOptionSpecification](#valueoptionspecification)
    - [DictOptionSpecification](#dictoptionspecification)
    - [PositionalSpecification](#positionalspecification)
    - [CommandSpecification](#commandspecification)
    - [Arity](#arity)
  - [Parse result types](#parse-result-types)
    - [ParseResult](#parseresult)
    - [ParsedOption](#parsedoption)
    - [ParsedPositional](#parsedpositional)
  - [Configuration types](#configuration-types)
    - [Configuration](#configuration)
    - [ArgumentFileFormat](#argumentfileformat)
    - [Accumulation mode enums](#accumulation-mode-enums)
    - [FlagAccumulationMode](#flagaccumulationmode)
    - [ValueAccumulationMode](#valueaccumulationmode)
    - [DictAccumulationMode](#dictaccumulationmode)
    - [DictMergeStrategy](#dictmergestrategy)
  - [Supporting types](#supporting-types)
    - [Value types](#value-types)
    - [Type aliases](#type-aliases)
    - [Type guards](#type-guards)
  - [Type relationships and patterns](#type-relationships-and-patterns)
    - [Specification hierarchy](#specification-hierarchy-1)
    - [Result type consistency](#result-type-consistency)
    - [Immutable collection usage](#immutable-collection-usage)
    - [Generic patterns with arity](#generic-patterns-with-arity)
    - [Recursive result structures](#recursive-result-structures)
  - [Usage examples](#usage-examples)
    - [Basic command with options and positionals](#basic-command-with-options-and-positionals)
    - [Nested subcommands with recursive results](#nested-subcommands-with-recursive-results)
    - [Flag options with counting and negation](#flag-options-with-counting-and-negation)
    - [Variadic positionals with arity constraints](#variadic-positionals-with-arity-constraints)
    - [Custom parser configuration](#custom-parser-configuration)
    - [Type-safe value access with type guards](#type-safe-value-access-with-type-guards)

---

## Type system overview

The parser type system consists of four primary categories, each serving a distinct role in the parsing lifecycle. Specification types are immutable data structures that define what to parse, containing command metadata, option definitions, and positional argument specifications. Parse result types are immutable data structures representing parsed output, capturing the structured interpretation of command-line arguments. Configuration types control how parsing behaves, defining flags and settings that modify parser algorithms. Supporting types provide the foundational primitives like arity constraints, accumulation modes, and value representations.

These categories form a clear conceptual model. Specifications are the input blueprints created by developers to describe CLI interfaces. Configuration customizes parser behavior through optional flags and settings. The parser consumes specifications and configuration to process arguments. Parse results are the output produced by the parser, representing the structured data extracted from raw argument strings.

All types throughout the parser are immutable after construction. Specification types use `@dataclass(frozen=True, slots=True)` to prevent modification while minimizing memory overhead. Parse result types use `@dataclass(frozen=True)` for the same immutability guarantee with automatic `__eq__`, `__hash__`, and `__repr__` implementations. This pervasive immutability enables aggressive caching, safe concurrent usage, and predictable behavior without defensive copying.

The type system leverages modern Python typing features through `typing` and `typing-extensions`. Type parameter syntax from Python 3.12+ provides clean generic definitions. Pattern matching from Python 3.10+ enables exhaustive type-based dispatch. The `ReadOnly` type from `typing-extensions` documents fields that should not be modified even in mutable contexts. `TypeIs` provides improved type narrowing over `TypeGuard` for validation predicates. These features combine to create a type system that is both expressive and enforceable through static analysis with basedpyright.

---

## Specification types

Specification types define the structure and behavior of command-line interfaces. They are immutable, validated at construction, and shared across parser and completer components to ensure consistent behavior.

### Specification hierarchy

The specification type system uses a three-tier inheritance hierarchy for options, separating flag options, value options, and dictionary options into distinct types. This design provides type safety and clarity about what capabilities each option type supports.

```
ParameterSpecification (base)
    ├── OptionSpecification (base for all named parameters)
    │   ├── FlagOptionSpecification (boolean flags)
    │   ├── ValueOptionSpecification (single or multiple values)
    │   └── DictOptionSpecification (key-value dictionaries)
    └── PositionalSpecification (positional parameters)

CommandSpecification (standalone, not inheriting from ParameterSpecification)
```

All specification types use `@dataclass(slots=True, frozen=True)` for immutability and memory efficiency. The three option types inherit from `OptionSpecification`, which inherits from `ParameterSpecification`. `PositionalSpecification` also inherits from `ParameterSpecification`. `CommandSpecification` is independent and contains collections of other specification types.

### ParameterSpecification

`ParameterSpecification` is the base class for all parameter specifications, providing the common `name` attribute shared by all parameters.

**Conceptual structure:**

`ParameterSpecification` serves as the base type for all parameter specifications, providing a common `name` attribute that all parameters share. The canonical parameter name identifies the parameter in parse results and error messages. Naming constraints vary by parameter type, with option specifications having stricter format rules than positional specifications.

This base type provides structural commonality across different parameter types. Implementations use concrete subclasses rather than polymorphic references to the base type.

### OptionSpecification

`OptionSpecification` is the base class for all named parameter types (flags, values, dictionaries), providing common attributes for long and short names.

**Module:** `flagrant.specification`

**Type definition:**

```python
class OptionSpecification(ParameterSpecification):
    """Base class for named parameters.

    Attributes:
        long_names: Set of long names (e.g., "verbose") for the option.
        short_names: Set of short names (e.g., "v") for the option.
    """

    long_names: frozenset[str] = field(default_factory=lambda: frozenset[str]())
    short_names: frozenset[str] = field(default_factory=lambda: frozenset[str]())
```

**Field descriptions:**

The `long_names` field contains long-form option names stored as a `frozenset`. Each long name must be at least 2 characters. **Important:** Names are stored WITHOUT any prefix characters. The prefix (`--` by default, configurable via `Configuration.long_name_prefix`) is added dynamically during parsing. For example, the name `"verbose"` is stored in `long_names`, and users type `--verbose` on the command line.

The `short_names` field contains short-form option names stored as a `frozenset`. Each short name must be exactly 1 character. **Important:** Names are stored WITHOUT the prefix character. The prefix (`-` by default, configurable via `Configuration.short_name_prefix`) is added dynamically during parsing. For example, the name `"v"` is stored in `short_names`, and users type `-v` on the command line.

This base class is not instantiated directly; use one of the three concrete option types.

### FlagOptionSpecification

`FlagOptionSpecification` defines a boolean flag parameter that appears with or without a value and can be negated.

**Module:** `flagrant.specification`

**Type definition:**

```python
class FlagOptionSpecification(OptionSpecification):
    """Describes a boolean parameter.

    Attributes:
        accumulation_mode: Strategy for combining multiple occurrences of the
            same flag option.
        negation_prefixes: Words that negate the flag option when used as a prefix
            to long names of the flag.
        negation_short_names: Characters that negate the flag option when used as a
            short name of the flag.
    """

    accumulation_mode: FlagAccumulationMode = FlagAccumulationMode.LAST
    negation_prefixes: frozenset[str] = field(default_factory=lambda: frozenset[str]())
    negation_short_names: frozenset[str] = field(default_factory=lambda: frozenset[str]())
```

**Field descriptions:**

The `accumulation_mode` field determines behavior when the flag appears multiple times. See [FlagAccumulationMode](#flagaccumulationmode) for detailed mode descriptions. Default is `LAST`.

The `negation_prefixes` field contains prefix words that create negated flag forms. For a flag with long name `"verbose"` (stored without prefix) and negation prefix `"no"`, the parser accepts both `--verbose` (sets to true) and `--no-verbose` (sets to false) on the command line. The parser generates the negated form by joining the negation prefix word with the long name using the negation separator (configurable via `Configuration.negation_prefix_separator`, default `"-"`), then prepending the configured long name prefix.

The `negation_short_names` field contains short names that explicitly negate the flag. Unlike `negation_prefixes` which work with long names, negation short names are standalone single-character options that set the flag to false. This allows different short names for positive and negative forms of the same flag.

Example with `negation_short_names`:

```python
# Specification for a color flag
color_flag = FlagOptionSpecification(
    name="color",
    long_names=frozenset({"color"}),
    short_names=frozenset({"c"}),  # -c enables color
    negation_prefixes=frozenset({"no"}),  # --no-color disables color
    negation_short_names=frozenset({"C"}),  # -C disables color (uppercase)
)

# Usage examples:
# --color or -c     → color=True
# --no-color or -C  → color=False
```

Common patterns include using uppercase for negation when lowercase is positive (e.g., `-v` for verbose, `-V` for non-verbose), or using different letters entirely (e.g., `-c` for color, `-m` for monochrome).

**Common flag specification patterns:**

A simple boolean flag specification defines a name and short name, using default LAST accumulation mode. When the flag appears, its value is true; when absent, false.

A flag with negation support defines a name, long names, and negation prefixes. The negation prefixes generate negated forms like `--no-color` that set the flag to false. For short-form negation, add `negation_short_names` to provide explicit short names that negate the flag.

A counter flag uses COUNT accumulation mode to track the number of times the flag appears, useful for verbosity levels where `-vvv` produces a count of 3.

### ValueOptionSpecification

`ValueOptionSpecification` defines a parameter that accepts one or more string values.

**Module:** `flagrant.specification`

**Type definition:**

```python
class ValueOptionSpecification(OptionSpecification):
    """Describes a single or multiple value parameter.

    Attributes:
        accumulation_mode: Strategy for combining multiple occurrences of the
            same value option.
        allow_item_separator: If True, allows shorthand syntax for list values.
            If False, only separate arguments are treated as multiple values.
        allow_negative_numbers: If True, allows negative numbers as values
            for this option. If False, negative numbers are treated as separate
            options or arguments.
        arity: Number of values expected for each occurrence.
        greedy: If True, consumes all remaining arguments as part of this option.
            If False, stops at the next recognized parameter or subcommand.
        escape_character: Character used to escape special characters in values.
            If None, Configuration.value_escape_character is used.
        item_separator: Character that separates multiple values within a single
            argument. If None, Configuration.value_item_separator is used.
        negative_number_pattern: Regular expression pattern used to identify negative
            numbers. If None, Configuration.negative_number_pattern is used.
    """

    accumulation_mode: ValueAccumulationMode = ValueAccumulationMode.LAST
    allow_item_separator: bool = False
    allow_negative_numbers: bool = False
    arity: Arity = EXACTLY_ONE_ARITY
    greedy: bool = False
    escape_character: str | None = None
    item_separator: str | None = None
    negative_number_pattern: str | None = None
```

**Field descriptions:**

The `accumulation_mode` field determines behavior when the option appears multiple times. See [ValueAccumulationMode](#valueaccumulationmode) for detailed mode descriptions. Default is `LAST`.

The `arity` field defines how many values the option accepts as an `Arity` named tuple with `(min, max)` bounds. Default is `EXACTLY_ONE_ARITY` (Arity(1, 1)) for exactly one value.

The `allow_item_separator` field enables shorthand syntax where multiple values can be provided in a single argument separated by a delimiter. For example, with `item_separator=","`, `--values a,b,c` is equivalent to `--values a b c`.

The `greedy` field causes the option to consume all remaining arguments, ignoring normal stopping conditions. When `greedy=True`, the option consumes arguments until one of two absolute stopping conditions is met: (1) the end of the argument list is reached, or (2) the trailing arguments separator `--` is encountered. Unlike non-greedy options, greedy options do not stop at option-like arguments (those starting with `-`) or subcommand names—they consume everything as values. This is useful for options that pass arbitrary arguments to subprocesses or tools where argument structure is unknown. When `greedy=False` (default), the option respects normal stopping conditions: it stops consuming when it encounters an argument starting with `-` (except bare `-`), a recognized subcommand name, or reaches the maximum arity.

The `allow_negative_numbers` field controls whether arguments that look like negative numbers (e.g., `-5`, `-3.14`) are treated as values for this option or as separate options/flags. When `True`, negative numbers are consumed as values.

The escape and separator fields control value parsing behavior. When set to `None`, they inherit from the global `Configuration` object. When set explicitly, they override global defaults for this specific option.

**Common value option patterns:**

A single-value option defines a name, short name, and arity (1, 1) for exactly one value.

A multi-value option uses arity (1, None) for at least one value with EXTEND accumulation mode to collect all values into a flat tuple across multiple occurrences.

An option with item separator enables shorthand syntax where multiple values appear in a single argument separated by a delimiter like comma.

A greedy option sets the greedy flag to consume all remaining arguments regardless of whether they look like options or subcommands. Example with `greedy=True`:

```python
# Specification with greedy option
exec_spec = ValueOptionSpecification(
    name="exec",
    long_names=frozenset({"exec"}),
    arity=Arity(1, None),
    greedy=True,
)

# Parsing: program --exec command --flag arg -- trailing
# Result: exec.value = ("command", "--flag", "arg")
# The greedy option consumed everything up to "--", including option-like "--flag"
```

Contrast with non-greedy (default):

```python
# Specification with non-greedy option
files_spec = ValueOptionSpecification(
    name="files",
    long_names=frozenset({"files"}),
    arity=Arity(1, None),
    greedy=False,  # Default
)

# Parsing: program --files file1.txt file2.txt --output result.txt
# Result: files.value = ("file1.txt", "file2.txt")
# The non-greedy option stopped at "--output" (recognized option)
```

### DictOptionSpecification

`DictOptionSpecification` defines a parameter that parses key-value pairs into dictionary structures with support for nesting and list indexing.

**Module:** `flagrant.specification`

**Type definition:**

```python
class DictOptionSpecification(OptionSpecification):
    """Describes a dictionary parameter.

    Attributes:
        accumulation_mode: Strategy for combining multiple occurrences of the
            same dictionary option.
        allow_duplicate_list_indices: If True, allows multiple entries for the
            same list index when parsing list values. If False, raises an error
            on duplicates.
        allow_item_separator: If True, allows shorthand syntax for dictionary values.
            If False, only separate arguments are treated as multiple values.
        allow_nested: If True, allows nested dictionaries when parsing values. If
            False, only flat dictionaries are permitted.
        allow_sparse_lists: If True, allows lists with missing indices when
            parsing list values. If False, raises an error for sparse lists.
        arity: Number of arguments expected for each occurrence.
        case_sensitive_keys: If True, dictionary keys are case-sensitive.
            If False, keys are treated as case-insensitive.
        escape_character: Character used to escape special characters in keys
            and values. If None, Configuration.dict_escape_character is used.
        greedy: If True, consumes all remaining arguments as part of the
            dictionary. If False, stops at the next recognized parameter or subcommand.
        item_separator: Character that separates individual key-value pairs. If None,
            Configuration.dict_item_separator is used.
        key_value_separator: Character that separates keys from values within
            a key-value pair. If None, Configuration.key_value_separator is used.
        merge_strategy: Strategy for merging dictionaries when accumulation_mode
            is MERGE.
        nesting_separator: Character that indicates nested dictionary keys. If None,
            Configuration.nesting_separator is used.
        strict_structure: If True, enforces strict adherence to expected
            dictionary structure during parsing. If False, allows leniency
            in structure. If None, Configuration.strict_structure is used.
    """

    accumulation_mode: DictAccumulationMode = DictAccumulationMode.MERGE
    allow_duplicate_list_indices: bool = False
    allow_item_separator: bool = True
    allow_nested: bool = True
    allow_sparse_lists: bool = False
    arity: Arity = AT_LEAST_ONE_ARITY
    case_sensitive_keys: bool = True
    escape_character: str | None = None
    greedy: bool = False
    item_separator: str | None = None
    key_value_separator: str | None = None
    merge_strategy: DictMergeStrategy = DictMergeStrategy.DEEP
    nesting_separator: str | None = None
    strict_structure: bool | None = None
```

**Field descriptions:**

The `accumulation_mode` field determines behavior when the option appears multiple times. See [DictAccumulationMode](#dictaccumulationmode) for detailed mode descriptions. Default is `MERGE`, which merges dictionaries together.

The `arity` field defines how many key-value arguments the option accepts. Default is `AT_LEAST_ONE_ARITY` (Arity(1, None)) for one or more key-value pairs.

The `allow_nested` field enables nested dictionary syntax using a nesting separator. For example, with `nesting_separator="."`, `--config database.host=localhost` creates `{"database": {"host": "localhost"}}`.

The `allow_item_separator` field enables providing multiple key-value pairs in a single argument. For example, with `item_separator=","`, `--config a=1,b=2` is equivalent to `--config a=1 b=2`.

The `merge_strategy` field controls how dictionaries are merged when `accumulation_mode=MERGE`. `DEEP` performs recursive merging of nested dictionaries. `SHALLOW` only merges top-level keys.

The `allow_duplicate_list_indices` field controls whether duplicate list indices are permitted when parsing list values. When `False` (default), specifying the same index twice raises an error. When `True`, duplicate indices are allowed.

Example with `allow_duplicate_list_indices=False` (default):

```python
# Input: --items items.0=a items.0=b
# Error: DuplicateListIndexError - index 0 specified multiple times
```

Example with `allow_duplicate_list_indices=True`:

```python
# Input: --items items.0=a items.0=b
# Result: {"items": ["b"]}  # Last value wins for index 0
```

The `allow_sparse_lists` field controls whether lists can have missing indices (gaps). When `False` (default), lists must have consecutive indices starting from 0. When `True`, gaps are allowed and filled with placeholder values or skipped.

Example with `allow_sparse_lists=False` (default):

```python
# Input: --items items.0=a items.2=c
# Error: SparseListError - missing index 1
```

Example with `allow_sparse_lists=True`:

```python
# Input: --items items.0=a items.2=c
# Result: {"items": ["a", null, "c"]}  # Gap filled with null/None
```

The `case_sensitive_keys` field controls whether dictionary keys are matched case-sensitively. When `True` (default), keys are case-sensitive. When `False`, keys are normalized to a consistent case before comparison.

Example with `case_sensitive_keys=True` (default):

```python
# Input: --config Host=localhost host=127.0.0.1
# Result: {"Host": "localhost", "host": "127.0.0.1"}  # Two separate keys
```

Example with `case_sensitive_keys=False`:

```python
# Input: --config Host=localhost host=127.0.0.1
# Result: {"host": "127.0.0.1"}  # Keys normalized, last value wins
```

All separator and escape character fields default to `None`, inheriting from global `Configuration`. When set explicitly, they override global defaults for this specific option.

**Common dictionary option patterns:**

A simple dictionary option defines a name and short name, using default MERGE accumulation mode with DEEP merge strategy.

A dictionary with nested support enables dot-notation syntax for nested keys, with MERGE accumulation and DEEP merge strategy to recursively combine nested dictionaries.

A dictionary with case-insensitive keys sets the case_sensitive_keys flag to false and optionally enables item separator for convenient multiple key-value specification.

### PositionalSpecification

`PositionalSpecification` defines a positional parameter identified by position in the argument sequence rather than by a name or prefix.

**Module:** `flagrant.specification`

**Type definition:**

```python
class PositionalSpecification(ParameterSpecification):
    """Describes a positional parameter.

    Attributes:
        arity: Number of values expected for the positional parameter.
        greedy: If True, consumes all remaining arguments as part of this
            positional parameter. If False, stops at the next recognized
            parameter or subcommand.
    """

    arity: Arity = EXACTLY_ONE_ARITY
    greedy: bool = False
```

**Field descriptions:**

The `arity` field defines how many values this positional consumes from the argument sequence. Default is `EXACTLY_ONE_ARITY` (Arity(1, 1)) for exactly one value. Unbounded positionals use `AT_LEAST_ONE_ARITY` (Arity(1, None)) or `ZERO_OR_MORE_ARITY` (Arity(0, None)) to consume as many values as available while respecting later positionals' minimum requirements.

The `greedy` field causes the positional to consume all remaining arguments. This is useful for variadic positionals that should capture everything not consumed by prior parameters.

**Positional ordering semantics:**

Positionals are matched in the order they appear in `CommandSpecification.positionals`. The parser assigns arguments to positionals sequentially based on arity constraints, ensuring later positionals with minimum requirements receive sufficient values before earlier unbounded positionals consume remaining arguments.

**Common positional specification patterns:**

A required single value positional uses arity (1, 1) for exactly one required value.

An optional single value positional uses arity (0, 1) for zero or one value.

A variadic positional requiring at least one value uses arity (1, None) to consume one or more values.

An optional variadic positional uses arity (0, None) to consume zero or more values.

A greedy positional sets the greedy flag to consume all remaining arguments.

### CommandSpecification

`CommandSpecification` defines the complete structure of a command or subcommand, containing tuples of options, positionals, and nested subcommands.

**Conceptual structure:**

`CommandSpecification` defines the complete structure of a command or subcommand through five primary attributes:

- `name`: The canonical command name serving as the primary identifier
- `aliases`: Alternative names for the command as an immutable tuple
- `options`: Tuple of option specifications (flags, values, dictionaries) for this command
- `positionals`: Tuple of positional specifications matched sequentially
- `subcommands`: Tuple of nested command specifications creating command hierarchies

**Field descriptions:**

The `name` field contains the canonical command name, serving as the primary identifier in parse results and error messages.

The `aliases` field contains alternative names for the command as a tuple. Each alias must follow the same validation rules as the canonical name. Aliases enable convenient shortcuts like `ls` for `list` or `rm` for `remove`. Whether aliases are recognized depends on the `Configuration.allow_command_aliases` setting.

The `options` field contains a tuple of option specifications for this command. The tuple is immutable and preserves insertion order. All three option specification types (`FlagOptionSpecification`, `ValueOptionSpecification`, `DictOptionSpecification`) can be included.

The `positionals` field contains a tuple of positional specifications for this command. Positionals are matched sequentially in the order they appear in this tuple.

The `subcommands` field contains a tuple of nested command specifications, creating recursive command hierarchies. Subcommand names must be unique within a command level.

**Immutability pattern:**

```python
# Create command spec
spec = CommandSpecification(
    name="docker",
    options=(
        FlagOptionSpecification(name="help", short_names=frozenset({"h"})),
        ValueOptionSpecification(name="host", short_names=frozenset({"H"})),
    ),
    subcommands=(
        CommandSpecification(name="run"),
        CommandSpecification(name="build"),
    ),
)

# Fields are immutable
spec.name = "podman"  # ❌ Raises FrozenInstanceError

# Collections are immutable tuples
spec.aliases += ("dk",)  # ❌ Cannot assign to frozen dataclass
new_options = spec.options + (ValueOptionSpecification(name="new"),)  # ✅ Creates new tuple, doesn't modify spec

# Safe to share across threads and cache aggressively
parser1 = Parser(spec)
parser2 = Parser(spec)  # Shares the same spec instance safely
```

**Example command specifications:**

```python
# Simple command with options and positionals
build_spec = CommandSpecification(
    name="build",
    options=(
        FlagOptionSpecification(name="verbose", short_names=frozenset({"v"})),
        ValueOptionSpecification(name="output", short_names=frozenset({"o"})),
    ),
    positionals=(
        PositionalSpecification(name="source", arity=EXACTLY_ONE_ARITY),
    ),
)

# Nested command hierarchy
git_spec = CommandSpecification(
    name="git",
    subcommands=(
        CommandSpecification(
            name="remote",
            subcommands=(
                CommandSpecification(name="add"),
                CommandSpecification(name="remove"),
            ),
        ),
        CommandSpecification(name="commit"),
    ),
)

# Command with aliases
list_spec = CommandSpecification(
    name="list",
    aliases=("ls", "dir"),
    options=(
        FlagOptionSpecification(name="all", short_names=frozenset({"a"})),
    ),
)
```

### Arity

`Arity` defines the number of values a parameter (option or positional) accepts through minimum and maximum bounds.

**Conceptual structure:**

`Arity` defines value count constraints for parameters through two components:

- `min`: Minimum number of values required (must be non-negative)
- `max`: Maximum number of values allowed (must be non-negative or None for unbounded)

**Field descriptions:**

The `min` field specifies the minimum number of values required. The parser raises an error if fewer values are consumed. Must be non-negative.

The `max` field specifies the maximum number of values the parameter will consume. When `None`, the parameter is unbounded and consumes as many values as possible (subject to stopping conditions). When an integer, the parameter stops consuming after reaching this limit. Must be non-negative or `None`.

**Validation:**

Arity validation occurs during parameter spec construction. Constraints checked include minimum greater than or equal to zero, maximum greater than or equal to zero (or None for unbounded), and minimum less than or equal to maximum when maximum is bounded.

**Common arity patterns:**

- (0, 0): Flags accepting no values
- (1, 1): Exactly one value (most common for options)
- (0, 1): Optional single value
- (1, None): One or more values (required variadic)
- (0, None): Zero or more values (optional variadic)
- (2, 2): Exactly two values (e.g., coordinates x y)
- (2, 5): Between 2 and 5 values (bounded range)

**Usage patterns:**

A value option requiring exactly 2 values uses arity (2, 2), consumed as `--coord 10 20`.

A positional accepting 1 or more files uses arity (1, None), consumed as `file1.txt file2.txt file3.txt`.

A flag with counting uses arity (0, 0) with COUNT accumulation mode to track occurrence count. For example, `-vvv` produces a count of 3.

---

## Parse result types

Parse result types represent the structured output produced by the parser when successfully processing command-line arguments. All result types are immutable, enabling safe sharing and caching.

### ParseResult

`ParseResult` is the primary output of parsing, containing all parsed options, positionals, and metadata about the invoked command.

**Module:** `flagrant.parsing._result`

**Type definition:**

```python
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

@dataclass(frozen=True)
class ParseResult:
    """Immutable result of parsing command-line arguments.

    Attributes:
        command: Canonical name of the command that was invoked.
        alias: Specific alias used by the user (if any), otherwise None.
        options: Parsed options keyed by canonical option name.
        positionals: Parsed positionals keyed by positional spec name.
        extra_args: Arguments appearing after '--' separator.
        subcommand: Nested parse result for invoked subcommand (if any).
    """

    command: str
    alias: str | None = None
    options: Mapping[str, ParsedOption] = field(default_factory=lambda: MappingProxyType({}))
    positionals: Mapping[str, ParsedPositional] = field(default_factory=lambda: MappingProxyType({}))
    extra_args: tuple[str, ...] = ()
    subcommand: 'ParseResult | None' = None
```

**Field descriptions:**

The `command` field contains the canonical command name from the `CommandSpecification`, serving as the primary identifier for which command was invoked. This is always the canonical name, never an alias.

The `alias` field contains the specific alias the user provided, if the command was invoked via an alias. When the canonical name was used, this field is `None`. This enables tracking user preferences and providing context in error messages.

The `options` field maps canonical option names to `ParsedOption` instances using `Mapping[str, ParsedOption]` for immutability. Keys are the canonical names from option specs, not the long or short forms used by the user. Each `ParsedOption` preserves the specific name variant the user provided while keying by canonical name ensures consistent access. Implementations must use `MappingProxyType`.

The `positionals` field maps positional spec names to `ParsedPositional` instances using `Mapping[str, ParsedPositional]`. Keys are the names from positional specs, reflecting the semantic grouping defined in the command specification. Implementations must use `MappingProxyType`.

The `extra_args` field contains all arguments appearing after the `--` separator as an immutable tuple. These arguments bypass normal parsing and are preserved exactly as provided. Applications often pass these to subprocess invocations.

The `subcommand` field contains a nested `ParseResult` for the invoked subcommand, creating recursive result structures that mirror command hierarchies. When no subcommand was invoked, this field is `None`.

**Immutability implementation:**

```python
from types import MappingProxyType

# Internal construction
result = ParseResult(
    command="git",
    options=MappingProxyType({"verbose": ParsedOption("verbose", True)}),
    positionals=MappingProxyType({"file": ParsedPositional("file", "main.py")}),
)

# Attempting mutation fails
result.options["new"] = ParsedOption("new", "value")
# ❌ TypeError: 'mappingproxy' object does not support item assignment
```

**Recursive structure:**

```python
# Parsing: git remote add origin https://github.com/user/repo.git
result = parser.parse(["git", "remote", "add", "origin", "https://..."])

# Access command hierarchy
result.command                          # "git"
result.subcommand.command               # "remote"
result.subcommand.subcommand.command    # "add"

# Access positionals at leaf level
result.subcommand.subcommand.positionals["name"].value      # "origin"
result.subcommand.subcommand.positionals["url"].value       # "https://..."
```

**Accessing parsed values:**

```python
# Check if option was provided
if "verbose" in result.options:
    verbose_value = result.options["verbose"].value

# Get option with default
output_value = result.options.get("output", ParsedOption("output", "default.txt")).value

# Access positionals
input_file = result.positionals["input"].value

# Iterate all options
for option_name, parsed_option in result.options.items():
    print(f"{option_name}: {parsed_option.value}")
```

### ParsedOption

`ParsedOption` represents a single parsed option with its value and metadata about how it was specified.

**Module:** `flagrant.parsing._result`

**Type definition:**

```python
@dataclass(frozen=True)
class ParsedOption:
    """Immutable representation of a parsed option.

    Attributes:
        name: Canonical option name from the option spec.
        value: Parsed value(s) with type depending on arity and accumulation.
        alias: Specific name variant the user provided (may be long, short, or abbreviated).
    """

    name: str
    value: OptionValue  # Type alias defined in Value Types section
    alias: str | None = None
```

**Field descriptions:**

The `name` field contains the canonical option name from the option specification, providing a consistent identifier regardless of how the user specified the option.

The `value` field contains the parsed value(s) with type determined by the option's arity, accumulation mode, and flag status. The type is `OptionValue`, a union type that encompasses all possible option value types. See [Value types](#value-types) for detailed type mappings and when each variant applies.

The `alias` field contains the specific name variant the user provided, such as the long form "verbose", short form "v", or an abbreviation "verb". This preserves user intent for error messages and analytics while maintaining canonical access via the `name` field.

**Value type patterns:**

```python
# Flag option (is_flag=True, arity=(0,0))
ParsedOption(name="verbose", value=True)         # type: bool

# Counter flag (is_flag=True, accumulation_mode=COUNT)
ParsedOption(name="verbose", value=3)            # type: int

# Single-value option (arity=(1,1), accumulation_mode=LAST_WINS)
ParsedOption(name="output", value="result.txt")  # type: str

# Multi-value option (arity=(2,2))
ParsedOption(name="coord", value=("10", "20"))   # type: tuple[str, ...]

# Collected values (accumulation_mode=APPEND or EXTEND)
ParsedOption(
    name="define",
    value=("KEY1=VAL1", "KEY2=VAL2")             # type: tuple[str, ...]
)

# Nested collection (rare, specific arity patterns)
ParsedOption(
    name="pairs",
    value=(("a", "1"), ("b", "2"))               # type: tuple[tuple[str, ...], ...]
)
```

### ParsedPositional

`ParsedPositional` represents grouped positional arguments matched to a positional spec.

**Module:** `flagrant.parsing._result`

**Type definition:**

```python
@dataclass(frozen=True)
class ParsedPositional:
    """Immutable representation of parsed positional arguments.

    Attributes:
        name: Positional parameter name from the positional spec.
        value: Parsed value(s) as string or tuple of strings.
    """

    name: str
    value: PositionalValue  # Type alias defined in Value Types section
```

**Field descriptions:**

The `name` field contains the positional parameter name from the `PositionalSpecification`, serving as the identifier for accessing this positional in parse results.

The `value` field contains the parsed value(s) as either a single string (when arity min == max == 1) or a tuple of strings (for all other arity patterns). Unlike options which support boolean and integer values, positionals always contain string values. The type is `PositionalValue`, a union of `str` and `tuple[str, ...]`.

**Value type patterns:**

```python
# Single-value positional (arity=(1,1))
ParsedPositional(name="input", value="file.txt")  # type: str

# Multi-value positional (arity=(3,3))
ParsedPositional(
    name="coords",
    value=("10", "20", "30")                      # type: tuple[str, ...]
)

# Variadic positional (arity=(1,None))
ParsedPositional(
    name="files",
    value=("file1.txt", "file2.txt", "file3.txt") # type: tuple[str, ...]
)

# Optional positional (arity=(0,1)) - when provided
ParsedPositional(name="output", value="result.txt")  # type: str

# Optional positional (arity=(0,1)) - when not provided
# Positional not present in result.positionals dictionary
```

---

## Configuration types

Configuration types control parser behavior through flags and settings that modify parsing algorithms without changing command specifications.

### Configuration

`Configuration` encapsulates all behavioral settings for the parser and completers, controlling features like abbreviation matching, case sensitivity, strict mode, and dictionary parsing behavior.

**Module:** `flagrant.configuration`

**Type definition:**

```python
@dataclass(slots=True, frozen=True)
class Configuration:
    """Common configuration settings.

    Attributes:
        allow_abbreviated_options: Enable matching option name prefixes.
        allow_abbreviated_subcommands: Enable matching subcommand name prefixes.
        allow_command_aliases: Enable matching command aliases.
        allow_duplicate_list_indices: Allow duplicate list indices in dictionary values.
        allow_negative_numbers: Treat negative numbers as values rather than options.
        allow_sparse_lists: Allow lists with missing indices in dictionary values.
        argument_file_comment_char: Character for line comments in argument files.
        argument_file_format: Format mode for parsing argument files.
        argument_file_prefix: Character that triggers argument file expansion.
        case_sensitive_commands: Match command names case-sensitively.
        case_sensitive_keys: Match dictionary keys case-sensitively.
        case_sensitive_options: Match option names case-sensitively.
        convert_underscores: Treat underscores and dashes interchangeably.
        dict_escape_character: Character for escaping special chars in dict keys/values.
        dict_item_separator: Character separating multiple dict key-value pairs.
        key_value_separator: Character separating keys from values in dicts.
        long_name_prefix: Prefix for long option names (default "--").
        max_argument_file_depth: Maximum recursion depth for argument file expansion.
        merge_strategy: Strategy for merging dictionaries.
        minimum_abbreviation_length: Minimum characters for abbreviation matching.
        negation_prefix_separator: Separator between negation prefix and flag name.
        negative_number_pattern: Regex pattern identifying negative numbers.
        nesting_separator: Character indicating nested dictionary keys.
        short_name_prefix: Prefix for short option names (default "-").
        strict_structure: Enforce strict dictionary structure validation.
        strict_options_before_positionals: Enforce POSIX-style option ordering.
        trailing_arguments_separator: Separator for trailing arguments (default "--").
        value_escape_character: Character for escaping special chars in values.
        value_item_separator: Character separating multiple values within argument.
    """

    allow_abbreviated_options: bool = False
    allow_abbreviated_subcommands: bool = False
    allow_command_aliases: bool = True
    allow_duplicate_list_indices: bool = False
    allow_negative_numbers: bool = True
    allow_sparse_lists: bool = False
    argument_file_comment_char: str | None = "#"
    argument_file_format: ArgumentFileFormat = ArgumentFileFormat.LINE
    argument_file_prefix: str | None = "@"
    case_sensitive_commands: bool = True
    case_sensitive_keys: bool = True
    case_sensitive_options: bool = True
    convert_underscores: bool = True
    dict_escape_character: str | None = DEFAULT_DICT_ESCAPE_CHARACTER
    dict_item_separator: str | None = None
    key_value_separator: str = DEFAULT_KEY_VALUE_SEPARATOR
    long_name_prefix: str = DEFAULT_LONG_NAME_PREFIX
    max_argument_file_depth: int = 1
    merge_strategy: DictMergeStrategy = DEFAULT_MERGE_STRATEGY
    minimum_abbreviation_length: int = DEFAULT_MINIMUM_ABBREVIATION_LENGTH
    negation_prefix_separator: str = DEFAULT_NEGATION_PREFIX_SEPARATOR
    negative_number_pattern: str = DEFAULT_NEGATIVE_NUMBER_PATTERN
    nesting_separator: str = DEFAULT_NESTING_SEPARATOR
    short_name_prefix: str = DEFAULT_SHORT_NAME_PREFIX
    strict_structure: bool = True
    strict_options_before_positionals: bool = False
    trailing_arguments_separator: str = DEFAULT_TRAILING_ARGUMENTS_SEPARATOR
    value_escape_character: str | None = DEFAULT_VALUE_ESCAPE_CHARACTER
    value_item_separator: str = DEFAULT_VALUE_ITEM_SEPARATOR
```

**Field descriptions:**

The `allow_abbreviated_options` field controls whether the parser accepts unambiguous prefixes of option names. When true, users can type `--verb` instead of `--verbose` if no other option starts with "verb". The `minimum_abbreviation_length` sets the minimum prefix length to prevent accidentally matching very short prefixes.

The `allow_abbreviated_subcommands` field enables prefix matching for subcommand names using the same logic as option abbreviations.

The `allow_command_aliases` field controls whether command aliases are recognized. When true, a command defined with aliases accepts both the canonical name and all aliases. When false, only the canonical name matches.

The `allow_negative_numbers` field controls whether arguments matching the `negative_number_pattern` are treated as values or options. When true, `-5` or `-3.14` are consumed as values rather than interpreted as short options.

The `case_sensitive_commands`, `case_sensitive_options`, and `case_sensitive_keys` fields control case-sensitive matching for commands, options, and dictionary keys respectively. When false, names are normalized before comparison, allowing `--VERBOSE`, `--Verbose`, and `--verbose` to match the same option.

The `convert_underscores` field enables treating underscores and dashes interchangeably in option names, bridging Python snake_case conventions with CLI kebab-case conventions. When enabled, an option defined as "output-file" matches `--output_file` and vice versa.

The `strict_options_before_positionals` field enforces POSIX-style ordering where all options must precede all positional arguments. Once the first positional is encountered, subsequent option-like arguments are treated as positional values.

The separator and prefix fields control parsing syntax. `long_name_prefix` and `short_name_prefix` define how options are specified (default `--` and `-`). `key_value_separator` splits dictionary entries (default `=`). `nesting_separator` creates nested dictionary paths (default `.`). `value_item_separator` splits multiple values in a single argument. `negation_prefix_separator` joins negation prefixes to flag names (default `-`). `trailing_arguments_separator` marks the start of trailing arguments (default `--`).

The escape character fields control special character handling. `dict_escape_character` escapes special characters in dictionary keys and values. `value_escape_character` escapes special characters in option and positional values. When `None`, escaping is disabled.

The dictionary parsing fields control behavior specific to dictionary options. `allow_duplicate_list_indices` and `allow_sparse_lists` control list handling within dictionaries. `strict_structure` enforces strict validation of dictionary structure. `merge_strategy` determines how dictionaries are merged when `accumulation_mode=MERGE`.

The `negative_number_pattern` field is a regex pattern used to identify negative numbers (default matches standard numeric literals like `-5`, `-3.14`, `-.5`).

**Configuration presets:**

```python
# GNU-style flexible parsing (default)
gnu_config = Configuration(
    allow_command_aliases=True,
    strict_options_before_positionals=False,
)

# POSIX-style strict parsing
posix_config = Configuration(
    allow_abbreviated_options=False,
    allow_command_aliases=False,
    strict_options_before_positionals=True,
)

# User-friendly modern CLI
modern_config = Configuration(
    allow_abbreviated_options=True,
    allow_abbreviated_subcommands=True,
    convert_underscores=True,
    minimum_abbreviation_length=2,
)

# Windows-style case-insensitive
windows_config = Configuration(
    case_sensitive_commands=False,
    case_sensitive_options=False,
    case_sensitive_keys=False,
)
```

### ArgumentFileFormat

`ArgumentFileFormat` defines the format used for parsing argument file contents.

**Module:** `flagrant.enums`

**Type definition:**

```python
class ArgumentFileFormat(Enum):
    """Format for parsing argument files.

    Attributes:
        LINE: Each line is a single argument. Simple and unambiguous.
        SHELL: Whitespace-separated with quoting support (future).
    """

    LINE = "line"
    SHELL = "shell"  # Future enhancement
```

**Member descriptions:**

`LINE` - Each non-empty, non-comment line in the argument file becomes a single argument. Leading and trailing whitespace is trimmed. Lines beginning with `#` (configurable) are treated as comments. This format is simple, unambiguous, and matches argparse defaults.

`SHELL` - (Future enhancement) Arguments are separated by whitespace (spaces, tabs, newlines) with quoting and escaping support. Single and double quotes allow arguments to contain whitespace. This format is more flexible but requires a proper shell-style tokenizer.

**Example usage:**

```python
from flagrant.enums import ArgumentFileFormat

# Default line-based format
config = Configuration(argument_file_format=ArgumentFileFormat.LINE)

# Shell-style format (future)
config = Configuration(argument_file_format=ArgumentFileFormat.SHELL)
```

### Accumulation mode enums

Accumulation mode enums define strategies for handling repeated option occurrences. Flagrant provides three separate enums for the three option types: `FlagAccumulationMode` for flag options, `ValueAccumulationMode` for value options, and `DictAccumulationMode` for dictionary options. This type-specific approach ensures each option type only exposes accumulation modes that make sense for its semantics.

### FlagAccumulationMode

`FlagAccumulationMode` defines accumulation strategies for flag options that produce boolean or counted values.

**Module:** `flagrant.enums`

**Type definition:**

```python
from enum import Enum

class FlagAccumulationMode(str, Enum):
    """Accumulation modes for flag option parameters.

    Members:
        FIRST: Keep only the first flag occurrence, ignore subsequent flags.
        LAST: Keep only the last flag occurrence, overwrite previous flags.
        COUNT: Count the number of flag occurrences.
        ERROR: Raise an error if flag appears more than once.
    """

    FIRST = "first"
    LAST = "last"
    COUNT = "count"
    ERROR = "error"
```

**Mode descriptions:**

`FIRST` keeps only the first flag value when the flag appears multiple times, silently ignoring all later occurrences. This provides "sticky" semantics where the initial specification locks in the value.

`LAST` keeps only the most recent flag value when the flag appears multiple times. Each new occurrence completely replaces the previous value. This is the default mode for flag options.

`COUNT` counts the number of times the flag appears, storing the count as an integer. This implements incrementing levels (e.g., `-vvv` produces 3 for verbosity).

`ERROR` raises an exception if the flag appears more than once. This enforces single-specification semantics with fail-fast behavior.

**Usage examples:**

```python
# Last wins (default for flags)
color = FlagOptionSpecification(
    name="color",
    long_names=frozenset({"color"}),
    accumulation_mode=FlagAccumulationMode.LAST,
)
# Input: --color --no-color --color
# Result: True (last occurrence wins)

# Counter flag for verbosity levels
verbose = FlagOptionSpecification(
    name="verbose",
    short_names=frozenset({"v"}),
    accumulation_mode=FlagAccumulationMode.COUNT,
)
# Input: -vvv
# Result: 3

# Error on duplicate
force = FlagOptionSpecification(
    name="force",
    accumulation_mode=FlagAccumulationMode.ERROR,
)
# Input: --force --force
# Raises: DuplicateOptionError
```

### ValueAccumulationMode

`ValueAccumulationMode` defines accumulation strategies for value options that accept string arguments.

**Module:** `flagrant.enums`

**Type definition:**

```python
class ValueAccumulationMode(str, Enum):
    """Accumulation modes for value option parameters.

    Members:
        FIRST: Keep only the first value, ignore subsequent values.
        LAST: Keep only the last value, overwrite previous values.
        APPEND: Append each arity-bounded set of values as a tuple.
        EXTEND: Extend all values into a single flat tuple.
        ERROR: Raise an error if option appears more than once.
    """

    FIRST = "first"
    LAST = "last"
    APPEND = "append"
    EXTEND = "extend"
    ERROR = "error"
```

**Mode descriptions:**

`FIRST` keeps only the first value(s) when the option appears multiple times, silently ignoring all later occurrences.

`LAST` keeps only the most recent value(s) when the option appears multiple times. Each new occurrence completely replaces the previous value. This is the default mode for value options and enables patterns where command-line arguments override configuration file settings.

`APPEND` appends each occurrence's arity-bounded values as a separate tuple element. For an option with `arity=Arity(2,2)`, each occurrence contributes a tuple of 2 values, creating a nested tuple structure.

`EXTEND` extends all values into a single flat tuple. All values from all occurrences are combined into one tuple, regardless of arity boundaries.

`ERROR` raises an exception if the option appears more than once. This enforces single-specification semantics.

**Usage examples:**

```python
# Last wins: command-line overrides config (default)
output = ValueOptionSpecification(
    name="output",
    short_names=frozenset({"o"}),
    accumulation_mode=ValueAccumulationMode.LAST,
)
# Input: --output a.txt --output b.txt
# Result: "b.txt"

# Extend: collect all values into flat tuple
include = ValueOptionSpecification(
    name="include",
    short_names=frozenset({"I"}),
    arity=AT_LEAST_ONE_ARITY,
    accumulation_mode=ValueAccumulationMode.EXTEND,
)
# Input: --include /usr/include --include /opt/include
# Result: ("/usr/include", "/opt/include")

# Append: preserve arity-bounded groups
define = ValueOptionSpecification(
    name="define",
    short_names=frozenset({"D"}),
    arity=Arity(2, 2),
    accumulation_mode=ValueAccumulationMode.APPEND,
)
# Input: --define KEY1 VAL1 --define KEY2 VAL2
# Result: (("KEY1", "VAL1"), ("KEY2", "VAL2"))
```

### DictAccumulationMode

`DictAccumulationMode` defines accumulation strategies for dictionary options that parse key-value pairs.

**Module:** `flagrant.enums`

**Type definition:**

```python
class DictAccumulationMode(str, Enum):
    """Accumulation modes for dictionary option parameters.

    Members:
        MERGE: Merge dictionaries together, combining keys and values.
        FIRST: Keep only the first dictionary, ignore subsequent ones.
        LAST: Keep only the last dictionary, overwrite previous ones.
        APPEND: Append each dictionary as a separate tuple element.
        ERROR: Raise an error if option appears more than once.
    """

    MERGE = "merge"
    FIRST = "first"
    LAST = "last"
    APPEND = "append"
    ERROR = "error"
```

**Mode descriptions:**

`MERGE` merges dictionaries together, combining keys and values. The merge behavior is controlled by the `merge_strategy` field (see `DictMergeStrategy`). This is the default mode for dictionary options.

`FIRST` keeps only the first dictionary when the option appears multiple times, silently ignoring all later occurrences.

`LAST` keeps only the most recent dictionary when the option appears multiple times. Each new occurrence completely replaces the previous dictionary.

`APPEND` appends each occurrence's dictionary as a separate element in a tuple of dictionaries.

`ERROR` raises an exception if the option appears more than once.

**Usage examples:**

```python
# Merge: combine dictionaries (default)
config = DictOptionSpecification(
    name="config",
    short_names=frozenset({"c"}),
    accumulation_mode=DictAccumulationMode.MERGE,
    merge_strategy=DictMergeStrategy.DEEP,
)
# Input: --config a=1 b=2 --config c=3
# Result: {"a": "1", "b": "2", "c": "3"}

# Append: preserve separate dictionaries
env = DictOptionSpecification(
    name="env",
    accumulation_mode=DictAccumulationMode.APPEND,
)
# Input: --env A=1 B=2 --env C=3 D=4
# Result: ({"A": "1", "B": "2"}, {"C": "3", "D": "4"})
```

### DictMergeStrategy

`DictMergeStrategy` controls how dictionaries are merged when `DictAccumulationMode.MERGE` is used.

**Module:** `flagrant.enums`

**Type definition:**

```python
class DictMergeStrategy(str, Enum):
    """Strategies for merging dictionaries in dictionary option parameters.

    Members:
        SHALLOW: Perform a shallow merge of dictionaries.
        DEEP: Perform a deep merge, recursively merging nested dictionaries.
    """

    SHALLOW = "shallow"
    DEEP = "deep"
```

**Strategy descriptions:**

`SHALLOW` performs a shallow merge where top-level keys from later dictionaries overwrite keys from earlier dictionaries. Nested dictionaries are not merged recursively; they replace entirely.

`DEEP` performs a deep merge that recursively merges nested dictionary structures. When a key exists in multiple dictionaries and all values are dictionaries, they are merged recursively. Non-dictionary values are overwritten.

**Usage examples:**

```python
# Shallow merge: nested dicts replace entirely
config = DictOptionSpecification(
    name="config",
    accumulation_mode=DictAccumulationMode.MERGE,
    merge_strategy=DictMergeStrategy.SHALLOW,
)
# Input: --config db.host=localhost --config db.port=5432
# Result: {"db": {"port": "5432"}}  # Second overwrites first

# Deep merge: nested dicts merge recursively (default)
settings = DictOptionSpecification(
    name="setting",
    accumulation_mode=DictAccumulationMode.MERGE,
    merge_strategy=DictMergeStrategy.DEEP,
)
# Input: --setting db.host=localhost --setting db.port=5432
# Result: {"db": {"host": "localhost", "port": "5432"}}  # Merged
```

---

## Supporting types

Supporting types provide foundational primitives and type aliases used throughout the parser.

### Value types

Parsed values in `ParsedOption` and `ParsedPositional` use specific Python types determined by arity, accumulation mode, and option type. The parser uses a simplified type structure that covers all parsing scenarios.

**Module:** `flagrant.types`

**Complete type definitions:**

```python
# Flag option values
FlagOptionValue = bool | int

# Value option values
ValueOptionValue = str | tuple[str, ...] | tuple[tuple[str, ...], ...]

# Dictionary option values (recursive type for nested structures)
DictValue = str | dict[str, "DictValue"] | list["DictValue"]
DictOptionValue = dict[str, DictValue] | tuple[dict[str, DictValue], ...]

# Union of all option values
OptionValue = FlagOptionValue | ValueOptionValue | DictOptionValue

# Positional values
PositionalValue = str | tuple[str, ...]
```

**Type breakdown by option kind:**

**Flag options** (`FlagOptionSpecification`) produce `FlagOptionValue`:

- `bool`: Standard flags with FIRST, LAST, or ERROR accumulation modes. True when flag appears, False when negated form appears
- `int`: Flags with COUNT accumulation mode. The integer represents how many times the flag appeared

Examples:

```python
# Boolean flag
ParsedOption(name="verbose", value=True)    # type: bool

# Count flag
ParsedOption(name="verbose", value=3)       # type: int (appeared 3 times)
```

**Value options** (`ValueOptionSpecification`) produce `ValueOptionValue`:

- `str`: Single-value options with arity `(1, 1)` and FIRST or LAST accumulation
- `tuple[str, ...]`: Multi-value options or options with EXTEND accumulation
- `tuple[tuple[str, ...], ...]`: Options with APPEND accumulation that preserve arity-bounded groups

Examples:

```python
# Single value (arity=1,1, accumulation=LAST)
ParsedOption(name="output", value="result.txt")  # type: str

# Multiple values (arity=2,2)
ParsedOption(name="coord", value=("10", "20"))   # type: tuple[str, ...]

# Collected values (accumulation=EXTEND)
ParsedOption(name="include", value=("/usr/include", "/opt/include"))  # tuple[str, ...]

# Nested groups (accumulation=APPEND with arity > 1)
ParsedOption(name="pairs", value=(("a", "1"), ("b", "2")))  # tuple[tuple[str, ...], ...]
```

**Dictionary options** (`DictOptionSpecification`) produce `DictOptionValue`:

The `DictValue` recursive type supports:

- String values: `"value"`
- Nested dictionaries: `{"nested": {"key": "value"}}`
- String lists: `["item1", "item2", "item3"]`
- Nested structure lists: `[{"a": "1"}, {"b": "2"}]`

`DictOptionValue` can be either:

- Single dictionary: `dict[str, DictValue]` (for MERGE, FIRST, LAST accumulation)
- Tuple of dictionaries: `tuple[dict[str, DictValue], ...]` (for APPEND accumulation)

Examples:

```python
# Single dictionary (accumulation=MERGE)
ParsedOption(
    name="config",
    value={"host": "localhost", "port": "5432"}  # type: dict[str, DictValue]
)

# Nested dictionary
ParsedOption(
    name="config",
    value={
        "database": {
            "host": "localhost",
            "port": "5432"
        }
    }
)

# Dictionary with list
ParsedOption(
    name="servers",
    value={"hosts": ["web1", "web2", "web3"]}
)

# Multiple dictionaries (accumulation=APPEND)
ParsedOption(
    name="env",
    value=(
        {"A": "1", "B": "2"},
        {"C": "3", "D": "4"}
    )  # type: tuple[dict[str, DictValue], ...]
)
```

**Positionals** (`PositionalSpecification`) produce `PositionalValue`:

- `str`: Single-value positionals with arity `(1, 1)`
- `tuple[str, ...]`: All other arity patterns

Examples:

```python
# Single value (arity=1,1)
ParsedPositional(name="input", value="file.txt")  # type: str

# Multiple values (arity=1,None)
ParsedPositional(
    name="files",
    value=("file1.txt", "file2.txt", "file3.txt")  # type: tuple[str, ...]
)
```

**When each value type applies:**

For **flag options** (FlagOptionSpecification):

- `accumulation_mode=COUNT` → `int` (count of occurrences)
- All other modes → `bool` (True when present, False when negated)

For **value options** (ValueOptionSpecification):

- `arity=Arity(1,1)` and `accumulation_mode` in (LAST, FIRST) → `str` (single value)
- `accumulation_mode=EXTEND` → `tuple[str, ...]` (flat tuple of all values)
- `accumulation_mode=APPEND` with `arity.max > 1` → `tuple[tuple[str, ...], ...]` (nested tuples preserving groups)
- `accumulation_mode=APPEND` with `arity.max == 1` → `tuple[str, ...]` (tuple of individual strings)
- `arity.max > 1` or `arity.max is None` → `tuple[str, ...]` (multiple values)

For **dictionary options** (DictOptionSpecification):

- `accumulation_mode=APPEND` → `tuple[dict[str, DictValue], ...]` (tuple of dictionaries)
- All other modes (MERGE, FIRST, LAST) → `dict[str, DictValue]` (single merged dictionary)

For **positionals** (PositionalSpecification):

- `arity=Arity(1,1)` → `str` (single value)
- All other arity patterns → `tuple[str, ...]`

### Type aliases

The parser defines type aliases matching the simplified type structure shown above.

**Module:** `flagrant.types`

**Complete type alias definitions:**

```python
# Flag option values
FlagOptionValue = bool | int

# Value option values
ValueOptionValue = str | tuple[str, ...] | tuple[tuple[str, ...], ...]

# Dictionary option values
DictValue = str | dict[str, "DictValue"] | list["DictValue"]
DictOptionValue = dict[str, DictValue] | tuple[dict[str, DictValue], ...]

# All option values
OptionValue = FlagOptionValue | ValueOptionValue | DictOptionValue

# Positional values
PositionalValue = str | tuple[str, ...]
```

These type aliases provide semantic documentation while maintaining the simplified type structure used throughout the implementation.

### Type guards

Type guards enable runtime type narrowing, allowing code to determine which variant of a union type is present and gain type-safe access.

**Module:** `flagrant.types`

**Type guard definitions:**

```python
from typing_extensions import TypeIs

def is_flag_boolean_value(value: OptionValue) -> TypeIs[bool]:
    """Type guard for boolean flag values.

    Returns True if value is a boolean from a standard flag.
    """
    return isinstance(value, bool)

def is_flag_count_value(value: OptionValue) -> TypeIs[int]:
    """Type guard for flag counter values.

    Returns True if value is an integer count from a COUNT accumulation flag.
    """
    return isinstance(value, int)

def is_single_value(value: OptionValue | PositionalValue) -> TypeIs[str]:
    """Type guard for single string values.

    Returns True if value is a single string (not a tuple or dict).
    """
    return isinstance(value, str)

def is_multiple_values(value: OptionValue | PositionalValue) -> TypeIs[tuple[str, ...]]:
    """Type guard for multiple string values.

    Returns True if value is a tuple of strings.
    """
    return isinstance(value, tuple) and all(isinstance(v, str) for v in value)

def is_dictionary_value(value: OptionValue) -> TypeIs[dict[str, DictValue]]:
    """Type guard for dictionary values from dict parsing.

    Returns True if value is a parsed dictionary structure.
    """
    return isinstance(value, dict)

def is_multiple_dictionary_values(value: OptionValue) -> TypeIs[tuple[dict[str, DictValue], ...]]:
    """Type guard for multiple dictionary values.

    Returns True if value is a tuple of dictionaries.
    """
    return isinstance(value, tuple) and all(isinstance(v, dict) for v in value)
```

**Usage example:**

```python
from flagrant.types import (
    is_flag_count_value,
    is_single_value,
    is_multiple_values,
    is_dictionary_value,
)

def process_option(option: ParsedOption) -> None:
    """Process parsed option with type-safe value access."""

    if is_flag_count_value(option.value):
        # Type checker knows option.value is int
        print(f"Flag appeared {option.value} times")
        count: int = option.value  # Type-safe

    elif is_dictionary_value(option.value):
        # Type checker knows option.value is dict
        print(f"Dictionary: {option.value}")
        for key, value in option.value.items():  # Type-safe dict iteration
            process_config(key, value)

    elif is_single_value(option.value):
        # Type checker knows option.value is str
        print(f"Single value: {option.value}")
        path = Path(option.value)  # Type-safe string usage

    elif is_multiple_values(option.value):
        # Type checker knows option.value is tuple[str, ...]
        print(f"Multiple values: {', '.join(option.value)}")
        for value in option.value:  # Type-safe iteration
            process_string(value)
```

**Validation predicate types:**

```python
from typing_extensions import TypeIs

# Argument syntax predicates
def is_option_like(arg: str) -> TypeIs[str]:
    """Type guard for option-like arguments (start with -)."""
    return arg.startswith("-") and arg != "-"

def is_long_option(arg: str) -> TypeIs[str]:
    """Type guard for long options (start with --)."""
    return arg.startswith("--") and len(arg) > 2

def is_short_option(arg: str) -> TypeIs[str]:
    """Type guard for short options (start with single -)."""
    return arg.startswith("-") and not arg.startswith("--") and len(arg) > 1

def is_negative_number(arg: str) -> TypeIs[str]:
    """Type guard for negative number literals.

    Distinguishes negative numbers from short options.
    Returns True for strings like '-5', '-3.14', '-.5'.
    """
    if not arg.startswith("-"):
        return False
    try:
        float(arg)
        return True
    except ValueError:
        return False
```

These type aliases and guards improve readability in function signatures, enable better IDE autocomplete, and provide type-safe runtime narrowing of union types.

---

## Type relationships and patterns

Understanding how types relate to each other reveals important architectural patterns and usage idioms.

### Specification hierarchy

Specification types do not inherit from a common base class. Each spec type is independently defined because they have fundamentally different concerns and data requirements. Shared behavior is extracted into module-level utility functions rather than inherited methods.

```python
# No common base class
CommandSpecification  # Orchestrates command structure
FlagOptionSpecification, ValueOptionSpecification, DictOptionSpecification  # Define option behavior
PositionalSpecification  # Defines positional behavior

# Shared behavior through utilities (not inheritance)
def validate_arity(arity: Arity) -> None: ...
def validate_name(name: str, name_type: str) -> None: ...
```

While specification types don't inherit from a common base, they follow the structural contract documented in `SpecificationProtocol`. This composition-over-inheritance design keeps each spec type focused on its specific responsibilities while avoiding the complexity of multi-level inheritance hierarchies.

### Result type consistency

All result types use `@dataclass(frozen=True)` for consistent immutability guarantees. This uniform pattern provides automatic `__eq__`, `__hash__`, and `__repr__` implementations while enforcing immutability at the type level.

```python
@dataclass(frozen=True)
class ParseResult: ...

@dataclass(frozen=True)
class ParsedOption: ...

@dataclass(frozen=True)
class ParsedPositional: ...

# Immutability enforced
result = ParseResult(command="build")
result.command = "test"  # ❌ FrozenInstanceError

# Automatic equality
opt1 = ParsedOption(name="verbose", value=True)
opt2 = ParsedOption(name="verbose", value=True)
assert opt1 == opt2  # ✅ Automatic structural equality

# Automatic hashing (enables use in sets and dicts)
options_set = {opt1, opt2}  # ✅ Works because ParsedOption is hashable
```

### Immutable collection usage

Specification types use `frozenset` for name collections and `Mapping` (backed by `MappingProxyType`) for structured data, ensuring that specs cannot be modified after construction.

```python
from types import MappingProxyType
from typing import Mapping

# Frozenset for name collections
class OptionSpecification:
    long_names: frozenset[str]        # Cannot add/remove long names
    short_names: frozenset[str]       # Cannot add/remove short names

class FlagOptionSpecification(OptionSpecification):
    negation_prefixes: frozenset[str]  # Cannot modify negation prefixes
    negation_short_names: frozenset[str]  # Cannot modify negation short names

# CommandSpecification uses tuples for immutable collections
class CommandSpecification:
    options: tuple[OptionSpecification, ...]  # Immutable tuple of options
    positionals: tuple[PositionalSpecification, ...]  # Immutable tuple of positionals
    subcommands: tuple[CommandSpecification, ...]  # Immutable tuple of subcommands

# Create immutable spec
spec = CommandSpecification(
    name="build",
    options=(
        FlagOptionSpecification(name="verbose", short_names=frozenset({"v"})),
        ValueOptionSpecification(name="output", short_names=frozenset({"o"})),
    ),
)

# Mutation attempts fail
spec.options = spec.options + (FlagOptionSpecification(name="new"),)
# ❌ FrozenInstanceError: cannot assign to field 'options'
```

The use of `Mapping` type annotations combined with `MappingProxyType` implementations provides true immutability, preventing both field reassignment (via `frozen=True`) and dictionary content modification (via `MappingProxyType`).

### Generic patterns with arity

Arity constraints create generic patterns that apply uniformly to both options and positionals, enabling shared validation and consumption logic.

```python
# Generic arity validation (works for options and positionals)
def validate_arity(arity: Arity) -> None:
    if arity.min < 0:
        raise InvalidArityError("Minimum arity cannot be negative")
    if arity.max is not None and arity.max < 0:
        raise InvalidArityError("Maximum arity cannot be negative")
    if arity.max is not None and arity.min > arity.max:
        raise InvalidArityError("Minimum arity cannot exceed maximum")

# Generic value consumption (works for options and positionals)
def consume_values(
    available_args: Sequence[str],
    arity: Arity,
    stop_at_option: bool = True,
) -> tuple[str, ...]:
    """Consume values according to arity constraints."""
    # Shared logic for both option and positional value consumption
    ...
```

This generic design reduces code duplication and ensures consistent behavior across parameter types.

### Recursive result structures

Parse results mirror the recursive structure of command specifications through the `subcommand` field, creating tree structures that represent command hierarchies.

```python
# Specification hierarchy
git_spec = CommandSpecification(
    name="git",
    subcommands=(
        CommandSpecification(
            name="remote",
            subcommands=(
                CommandSpecification(name="add"),
                CommandSpecification(name="remove"),
            ),
        ),
    ),
)

# Result hierarchy (mirrors spec structure)
result = ParseResult(
    command="git",
    subcommand=ParseResult(
        command="remote",
        subcommand=ParseResult(
            command="add",
            positionals=MappingProxyType({...}),
        ),
    ),
)

# Recursive traversal
def get_command_path(result: ParseResult) -> list[str]:
    """Extract full command path from result."""
    path = [result.command]
    current = result.subcommand
    while current is not None:
        path.append(current.command)
        current = current.subcommand
    return path

# Usage
path = get_command_path(result)  # ["git", "remote", "add"]
```

---

## Usage examples

Practical examples demonstrate how types compose to create complete parsing workflows.

### Basic command with options and positionals

```python
from flagrant.specification import (
    CommandSpecification,
    FlagOptionSpecification,
    ValueOptionSpecification,
    PositionalSpecification,
)
from flagrant.types import Arity, EXACTLY_ONE_ARITY
from flagrant.enums import ValueAccumulationMode
from flagrant.parsing import Parser

# Define specification
build_spec = CommandSpecification(
    name="build",
    options=(
        FlagOptionSpecification(name="verbose", short_names=frozenset({"v"})),
        ValueOptionSpecification(name="output", short_names=frozenset({"o"})),
        ValueOptionSpecification(
            name="define",
            short_names=frozenset({"D"}),
            accumulation_mode=ValueAccumulationMode.EXTEND,
        ),
    ),
    positionals=(
        PositionalSpecification(name="source", arity=EXACTLY_ONE_ARITY),
    ),
)

# Create parser
parser = Parser(build_spec)

# Parse arguments
result = parser.parse(["build", "-v", "-D", "DEBUG=1", "-D", "TRACE=1", "-o", "app.exe", "main.c"])

# Access parsed values
assert result.command == "build"
assert result.options["verbose"].value is True
assert result.options["output"].value == "app.exe"
assert result.options["define"].value == ("DEBUG=1", "TRACE=1")
assert result.positionals["source"].value == "main.c"
```

### Nested subcommands with recursive results

```python
# Define nested command hierarchy
docker_spec = CommandSpecification(
    name="docker",
    options=(
        ValueOptionSpecification(name="host", short_names=frozenset({"H"})),
    ),
    subcommands=(
        CommandSpecification(
            name="container",
            subcommands=(
                CommandSpecification(
                    name="run",
                    options=(
                        FlagOptionSpecification(name="detach", short_names=frozenset({"d"})),
                        ValueOptionSpecification(
                            name="publish",
                            short_names=frozenset({"p"}),
                            accumulation_mode=ValueAccumulationMode.EXTEND,
                        ),
                    ),
                    positionals=(
                        PositionalSpecification(name="image", arity=Arity(1, 1)),
                        PositionalSpecification(name="command", arity=Arity(0, None)),
                    ),
                ),
            ),
        ),
    ),
)

# Parse nested command
parser = Parser(docker_spec)
result = parser.parse([
    "docker", "--host", "tcp://localhost:2375",
    "container", "run", "-d", "-p", "8080:80", "-p", "8443:443",
    "nginx:latest", "nginx", "-g", "daemon off;"
])

# Access nested results
assert result.command == "docker"
assert result.options["host"].value == "tcp://localhost:2375"

container_result = result.subcommand
assert container_result.command == "container"

run_result = container_result.subcommand
assert run_result.command == "run"
assert run_result.options["detach"].value is True
assert run_result.options["publish"].value == ("8080:80", "8443:443")
assert run_result.positionals["image"].value == "nginx:latest"
assert run_result.positionals["command"].value == ("nginx", "-g", "daemon off;")
```

### Flag options with counting and negation

```python
# Define flag options
log_spec = CommandSpecification(
    name="log",
    options=(
        # Counter flag for verbosity levels
        FlagOptionSpecification(
            name="verbose",
            short_names=frozenset({"v"}),
            accumulation_mode=FlagAccumulationMode.COUNT,
        ),
        # Flag with negation support
        FlagOptionSpecification(
            name="color",
            negation_prefixes=frozenset({"no"}),
        ),
    ),
)

parser = Parser(log_spec)

# Parse with counted flags
result1 = parser.parse(["log", "-vvv"])
assert result1.options["verbose"].value == 3  # Count of 3

# Parse with negation
result2 = parser.parse(["log", "--no-color"])
assert result2.options["color"].value is False  # Negated flag
```

### Variadic positionals with arity constraints

```python
# Copy command: multiple sources, one destination
copy_spec = CommandSpecification(
    name="copy",
    positionals=(
        PositionalSpecification(name="sources", arity=Arity(1, None)),  # One or more
        PositionalSpecification(name="destination", arity=Arity(1, 1)),  # Exactly one
    ),
)

parser = Parser(copy_spec)
result = parser.parse(["copy", "file1.txt", "file2.txt", "file3.txt", "dest/"])

# Sources consume all but last argument
assert result.positionals["sources"].value == ("file1.txt", "file2.txt", "file3.txt")

# Destination consumes final argument
assert result.positionals["destination"].value == "dest/"
```

### Custom parser configuration

```python
from flagrant.parsing import ParserConfiguration

# Create custom configuration
config = ParserConfiguration(
    allow_abbreviated_options=True,
    convert_underscores=True,
    minimum_abbreviation_length=2,
)

# Create parser with custom config
parser = Parser(build_spec, config=config)

# Abbreviations work
result1 = parser.parse(["build", "--verb", "main.c"])
assert result1.options["verbose"].value is True  # Matched via abbreviation

# Underscore/dash conversion works
result2 = parser.parse(["build", "--output_file", "app.exe", "main.c"])
assert result2.options["output"].value == "app.exe"  # Matched despite underscore
```

### Type-safe value access with type guards

```python
from flagrant.types import is_flag_count_value, is_single_value, is_multiple_values
from pathlib import Path

def process_parsed_option(option: ParsedOption) -> None:
    """Process option with type-safe value access."""

    if is_flag_count_value(option.value):
        # Type checker knows value is int
        verbosity_level = option.value
        configure_logging(level=verbosity_level)

    elif is_single_value(option.value):
        # Type checker knows value is str
        output_path = Path(option.value)
        write_output(output_path)

    elif is_multiple_values(option.value):
        # Type checker knows value is tuple[str, ...]
        for include_path in option.value:
            add_include_directory(include_path)

# Usage
for opt_name, parsed_opt in result.options.items():
    process_parsed_option(parsed_opt)
```

---

**Summary:** This specification comprehensively documents the parser type system including specification types that define CLI structure, result types that represent parsed output, configuration types that control behavior, and supporting types that provide foundational primitives. All types are designed for immutability through `Mapping` types backed by `MappingProxyType`, type safety through comprehensive annotations, and compositional usage enabling robust CLI parsing implementations.

**Implementation notes:** Implementations must use `@dataclass(frozen=True, slots=True)` for specification types to enforce immutability and minimize memory overhead. Result types must use `@dataclass(frozen=True)` for automatic equality and hashing support. All dictionary fields in specifications and results must use `Mapping` type annotations and be constructed with `MappingProxyType` to prevent mutation. All type annotations should leverage `typing` and `typing-extensions` for maximum type safety with basedpyright.

**Related pages:** See [Behavior](behavior.md) for parsing algorithms that consume these types, [Errors](errors.md) for exception types raised during validation and parsing, [Configuration](configuration.md) for detailed configuration option descriptions, and [Dictionary Parsing](dictionary-parsing.md) for dictionary value parsing specification.
