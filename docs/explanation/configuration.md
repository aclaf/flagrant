# Parser configuration

--8<-- "unreleased.md"

This page documents the parser configuration model in Flagrant. It explains the available configuration options, their defaults, and how they influence parsing behavior. It also describes how configuration can be overridden at the command and option level for fine-grained control.

## Table of contents

- [Overview](#overview)
- [Configuration model](#configuration-model)
- [Positional mode configuration](#positional-mode-configuration)
- [Name resolution configuration](#name-resolution-configuration)
- [Flag value handling](#flag-value-handling)
- [Negative number handling](#negative-number-handling)
- [Value flattening](#value-flattening)
- [Configuration interactions](#configuration-interactions)
- [Preset configurations](#preset-configurations)
- [Configuration validation](#configuration-validation)

---

## Overview

Parser configuration controls parsing behavior through a set of boolean flags and value parameters that can be independently enabled or disabled. These configuration options allow the parser to adapt to different CLI conventions and user expectations without changing the parsing algorithm itself.

Configuration is provided when constructing a `Parser` instance and is immutable thereafter. All parser instances share the same configuration throughout their lifetime, enabling safe concurrent reuse and caching of resolution results.

## Configuration model

The `Configuration` class provides all configuration options as properties with sensible defaults. Each option is orthogonal to others unless explicitly documented as interacting.

### Configuration properties

The parser configuration includes the following 26 properties with their default values:

**Positional argument handling:**

- `strict_posix_options: bool = False` - Enforce POSIX-style ordering
- `allow_negative_numbers: bool = True` - Recognize negative numbers as values
- `negative_number_pattern: str = DEFAULT_NEGATIVE_NUMBER_PATTERN` - Custom regex for negative number detection

**Argument file handling:**

- `argument_file_prefix: str | None = "@"` - Character that triggers file expansion
- `argument_file_format: ArgumentFileFormat = LINE` - Format mode (line-based or shell-style)
- `argument_file_comment_char: str | None = "#"` - Character for line comments in files
- `max_argument_file_depth: int = 1` - Maximum recursion depth (if recursive expansion supported)

**Option and command name resolution:**

- `allow_abbreviated_options: bool = False` - Allow unambiguous option name prefixes
- `allow_abbreviated_subcommands: bool = False` - Allow unambiguous subcommand name prefixes
- `minimum_abbreviation_length: int = 3` - Minimum characters required for abbreviations
- `allow_command_aliases: bool = True` - Recognize defined command aliases
- `case_sensitive_commands: bool = True` - Match command names case-sensitively
- `case_sensitive_keys: bool = True` - Match dictionary keys case-sensitively
- `case_sensitive_options: bool = True` - Match option names case-sensitively
- `convert_underscores: bool = True` - Treat underscores and dashes interchangeably

**Dictionary argument handling:**

- `allow_duplicate_list_indices: bool = False` - Allow duplicate list indices in dictionaries
- `allow_sparse_lists: bool = False` - Allow lists with missing indices
- `dict_escape_character: str | None = "\\"` - Character for escaping in dictionary keys/values
- `dict_item_separator: str | None = None` - Character separating multiple key-value pairs
- `key_value_separator: str = "="` - Character separating keys from values
- `merge_strategy: DictMergeStrategy = DEEP` - Strategy for merging dictionaries
- `nesting_separator: str = "."` - Character indicating nested dictionary keys
- `strict_structure: bool = True` - Enforce strict dictionary structure validation

**Option syntax:**

- `long_name_prefix: str = "--"` - Prefix for long option names
- `negation_prefix_separator: str = "-"` - Separator between negation prefix and flag name
- `short_name_prefix: str = "-"` - Prefix for short option names
- `trailing_arguments_separator: str = "--"` - Separator for trailing arguments
- `value_escape_character: str | None = "\\"` - Character for escaping in option values
- `value_item_separator: str = ","` - Character separating multiple values within argument

### Configuration scope

Parser configuration applies at the **command level**. Each `CommandSpecification` is parsed with the same configuration, but different parser instances can use different configurations.

Within a command hierarchy, nested subcommands inherit the parent parser's configuration. The same resolution strategies, flag handling modes, and other settings apply uniformly across all command levels.

### Per-option configuration overrides

Many configuration properties can be overridden at the option level. When an option specification defines its own value for a configuration property, that value takes precedence over the global `Configuration` setting.

#### Override precedence

The parser applies configuration in this order:

1. **Option-specific field** - Value defined directly on the option specification
2. **Global configuration** - Value from the `Configuration` object passed to the parser
3. **System default** - Default value from `constants.py` if neither option nor global config specifies

#### Option-level override table

The following table shows which option specification fields override which global configuration properties:

| Option Specification Field | Global Configuration Property | Applies To Option Type |
|----------------------------|-------------------------------|------------------------|
| `allow_negative_numbers` | `Configuration.allow_negative_numbers` | ValueOptionSpecification |
| `negative_number_pattern` | `Configuration.negative_number_pattern` | ValueOptionSpecification |
| `allow_item_separator` | Implied by `Configuration.value_item_separator` | ValueOptionSpecification |
| `value_item_separator` | `Configuration.value_item_separator` | ValueOptionSpecification |
| `value_escape_character` | `Configuration.value_escape_character` | ValueOptionSpecification |
| `greedy` | No global (always per-option) | ValueOptionSpecification, DictOptionSpecification |
| `arity` | No global (always per-option) | ValueOptionSpecification, DictOptionSpecification |
| `case_sensitive_keys` | `Configuration.case_sensitive_keys` | DictOptionSpecification |
| `item_separator` | `Configuration.dict_item_separator` | DictOptionSpecification |
| `key_value_separator` | `Configuration.key_value_separator` | DictOptionSpecification |
| `nesting_separator` | `Configuration.nesting_separator` | DictOptionSpecification |
| `dict_escape_character` | `Configuration.dict_escape_character` | DictOptionSpecification |
| `allow_nested` | No global (always per-option, default True) | DictOptionSpecification |
| `allow_sparse_lists` | `Configuration.allow_sparse_lists` | DictOptionSpecification |
| `allow_duplicate_list_indices` | `Configuration.allow_duplicate_list_indices` | DictOptionSpecification |
| `strict_structure` | `Configuration.strict_structure` | DictOptionSpecification |
| `merge_strategy` | `Configuration.merge_strategy` | DictOptionSpecification (when accumulation_mode=MERGE) |

#### Override example

```python
from flagrant import Configuration, Parser, CommandSpecification, ValueOptionSpecification
from flagrant.types import Arity

# Global configuration disallows negative numbers
config = ParserConfiguration(
    allow_negative_numbers=False,  # Global setting
    value_item_separator=',',
)

# Specific option overrides to allow negative numbers
spec = CommandSpecification(
    name="analyze",
    options=(
        ValueOptionSpecification(
            name="threshold",
            long_names=("threshold",),
            arity=Arity(1, 1),
            allow_negative_numbers=True,  # Override for this option only
        ),
        ValueOptionSpecification(
            name="count",
            long_names=("count",),
            arity=Arity(1, 1),
            # Uses global allow_negative_numbers=False
        ),
    ),
)


# "threshold" option allows negative numbers despite global setting
result = parse_command_line_args(spec, ["--threshold", "-5"])
# result.options["threshold"].value == "-5"

# "count" option respects global setting
result = parse_command_line_args(spec, ["--count", "-5"])
# Raises error: "-5" classified as short option cluster, not value
```

See the [parser behavior specification](behavior.md) for detailed algorithms showing how per-option overrides affect parsing.

## Positional mode configuration

The `strict_posix_options` flag controls the fundamental parsing style: GNU-style flexible parsing (default) or POSIX-style ordering.

### Flexible positional mode (default)

**Configuration:** `strict_posix_options=False`

In flexible mode, options and positional arguments can appear in any order. The parser recognizes options anywhere in the argument list, regardless of position relative to positionals.

```python# All valid - options can appear anywhere
result = parse_command_line_args(spec, ["--verbose", "file.txt", "--output", "result.txt"])
result = parse_command_line_args(spec, ["file.txt", "--verbose", "--output", "result.txt"])
result = parse_command_line_args(spec, ["file.txt", "result.txt", "--verbose", "--output"])
```

**When to use:**

- Modern CLI tools (git, docker, npm, cargo)
- User convenience is prioritized over strict ordering
- Complex commands with many options and mixed positionals
- Applications targeting users who expect flexible argument ordering

**Advantages:**

- Maximum user flexibility
- Options can logically relate to specific positional arguments
- Supports contemporary CLI conventions

### POSIX-style ordering mode

**Configuration:** `strict_posix_options=True`

When POSIX-style ordering is enabled, all options must precede all positional arguments. Once the parser encounters the first positional argument, it stops recognizing option patterns and treats all subsequent arguments as positionals—even if they structurally look like options.

```python# Valid - options before positionals
result = parse_command_line_args(spec, ["--verbose", "--output", "result.txt", "file.txt"])

# Invalid - option after positional
try:
    result = parse_command_line_args(spec, ["file.txt", "--verbose"])
    # "--verbose" is treated as a positional argument
    # UnexpectedPositionalArgumentError if no positional accepts it
except UnexpectedPositionalArgumentError:
    pass
```

**When to use:**

- Traditional Unix utilities following POSIX.2 conventions
- System tools where strict ordering prevents ambiguity
- Commands that pass unknown arguments to subprocesses
- Applications targeting Unix system administrators

**Advantages:**

- Predictable, conservative parsing behavior
- Option-like values can appear as positionals after the first positional
- Clear separation between option and positional argument regions

**Important:** The single dash `-` (stdin/stdout convention) is always treated as a positional, regardless of positional mode. The double-dash `--` delimiter terminates option parsing in both modes.

## Name resolution configuration

Name resolution determines how user-provided option and subcommand names match against defined specifications. Multiple strategies can be independently enabled, providing rich compositional matching behavior.

### Abbreviation matching

Controls whether users can specify unambiguous prefixes of option and subcommand names instead of full names.

#### `allow_abbreviated_options`

**Default:** `False`

When enabled, users can type a prefix of an option name, provided the prefix uniquely identifies the option among all defined options.

```python
spec = CommandSpecification(
    name="cmd",
    options=(
        OptionSpecification(name="verbose", long_names=("verbose",)),
        OptionSpecification(name="version", long_names=("version",)),
        OptionSpecification(name="verify", long_names=("verify",)),
    ),
)# Unambiguous abbreviations work
result = parse_command_line_args(spec, ["--verb"])    # Matches "verbose"
result = parse_command_line_args(spec, ["--vers"])    # Matches "version"
result = parse_command_line_args(spec, ["--veri"])    # Matches "verify"

# Ambiguous abbreviations raise error
try:
    parse_command_line_args(spec, ["--ver"])  # Ambiguous: verbose, version, verify
except AmbiguousOptionError as e:
    print(e.candidates)  # ["verbose", "version", "verify"]
```

**Trade-offs:**

**Advantages:**

- Significant typing savings for users
- Enables convenient interactive use
- Particularly valuable for developer tools with long option names

**Disadvantages:**

- Risk of abbreviations becoming ambiguous as new options are added
- Scripts using abbreviations become brittle to specification changes
- Can confuse users with typos that partially match multiple options

**When to use:**

- Interactive developer tools where typing convenience matters
- Stable CLIs where new options won't create ambiguities
- Advanced user audiences who understand abbreviation mechanics

**When to avoid:**

- Stable public APIs where backward compatibility is critical
- Simple CLIs with few options where abbreviation provides minimal benefit
- Tools targeting general users who might misunderstand abbreviation behavior

#### `allow_abbreviated_subcommands`

**Default:** `False`

Like option abbreviation, but applies to subcommand names.

```python
spec = CommandSpecification(
    name="git",
    subcommands=(
        CommandSpecification(name="commit"),
        CommandSpecification(name="checkout"),
        CommandSpecification(name="cherry-pick"),
    ),
)result = parse_command_line_args(spec, ["com"])      # Matches "commit"
result = parse_command_line_args(spec, ["chec"])     # Matches "checkout"
result = parse_command_line_args(spec, ["cher"])     # Matches "cherry-pick"
```

**Practical consideration:** Subcommand abbreviation is particularly valuable in interactive contexts but creates risk in scripts. Many users disable this in production CLIs while enabling it in development tools.

#### `minimum_abbreviation_length`

**Default:** `3`

Specifies the minimum number of characters required for an abbreviation to be considered valid. This prevents overly short abbreviations that are likely to become ambiguous or result from typos.

```python# Valid - 5 characters (meets minimum)
result = parse_command_line_args(spec, ["--verbo"])

# Invalid - 4 characters (below minimum)
try:
    parse_command_line_args(spec, ["--verb"])  # Rejected even if unambiguous
except UnknownOptionError:
    pass
```

**Constraints:**

- Must be >= 1
- Values less than 1 raise `ParserConfigurationError` at construction time
- Does not affect exact matches (e.g., `--verbose` works regardless of minimum)

**Practical values:**

- `1` - Maximum convenience, any single character prefix works
- `3` - Balance between convenience and typo safety (default)
- `4-5` - Conservative, reduces accidental matches
- Higher - Very conservative, requires long prefixes

### Alias support

#### `allow_command_aliases`

**Default:** `True`

Controls whether subcommand aliases are recognized during parsing. When disabled, only the canonical subcommand name matches.

```python
spec = CommandSpecification(
    name="cmd",
    subcommands=(
        CommandSpecification(
            name="remove",
            aliases=("rm", "delete"),
        ),
    ),
)

# Aliases enabled (default)result = parse_command_line_args(spec, ["rm"])      # Matches via alias
result = parse_command_line_args(spec, ["delete"])  # Matches via alias
result = parse_command_line_args(spec, ["remove"])  # Matches canonical name

# Aliases disabledresult = parse_command_line_args(spec, ["remove"])  # Canonical name still works
try:
    parse_command_line_args(spec, ["rm"])  # Alias rejected
except UnknownSubcommandError:
    pass
```

**Important:** This configuration affects only subcommand aliases. Option aliases (short and long forms) are always active and cannot be disabled.

**When to disable:**

- Strict parsing modes where only canonical names are accepted
- Testing scenarios that verify correct subcommand usage
- Linting tools that enforce canonical naming
- Environments where alias confusion might cause issues

### Case sensitivity

Three independent flags control case sensitivity for different element types.

#### `case_sensitive_options`

**Default:** `True`

When disabled (`case_sensitive_options=False`), option names match case-insensitively. All case variations are accepted and normalized to the canonical lowercase form.

```python
spec = CommandSpecification(
    name="cmd",
    options=(
        FlagOptionSpecification(name="verbose", long_names=("verbose",)),
    ),
)# All case variations match
result = parse_command_line_args(spec, ["--verbose"])
result = parse_command_line_args(spec, ["--Verbose"])
result = parse_command_line_args(spec, ["--VERBOSE"])
result = parse_command_line_args(spec, ["--VeRbOsE"])

# Canonical name is preserved in result
assert result.options["verbose"].name == "verbose"
```

**When to use:**

- Windows-style CLIs where case is traditionally ignored
- User-friendly applications targeting non-technical users
- CLIs in case-insensitive environments

**When to avoid:**

- Unix tools where case sensitivity is conventional
- Strict parsing where case differences should be errors
- CLIs where option names deliberately differ only in case

#### `case_sensitive_commands`

**Default:** `True`

When disabled (`case_sensitive_commands=False`), subcommand names match case-insensitively.

```pythonresult = parse_command_line_args(spec, ["start"])   # lowercase
result = parse_command_line_args(spec, ["Start"])   # initial capital
result = parse_command_line_args(spec, ["START"])   # uppercase
# All match the same "start" subcommand
```

### Name normalization

#### `convert_underscores`

**Default:** `True`

Enables bidirectional conversion between underscores and dashes in option names. This bridges Python's snake_case naming conventions with CLI's kebab-case conventions.

```python
spec = CommandSpecification(
    name="cmd",
    options=(
        ValueOptionSpecification(name="output_format", long_names=("output-format",), arity=Arity(1, 1)),
    ),
)# Both styles work
result = parse_command_line_args(spec, ["--output-format", "json"])
result = parse_command_line_args(spec, ["--output_format", "json"])

# Canonical name is preserved
assert result.options["output_format"].name == "output_format"
```

**Rationale:** Python developers naturally use underscores in identifiers, but command-line conventions strongly favor dashes. This flag allows both styles without requiring specification changes.

**When to disable:**

- When underscores and dashes have semantic differences (rare)
- When you need strict matching for specific reasons
- When building CLIs that explicitly distinguish `foo_bar` from `foo-bar`

## Flag behavior

Flags are boolean options with `arity=(0, 0)` that represent presence/absence semantics. By default, flags set to `True` when present and `False` when explicitly negated using negation prefixes.

## Argument file handling

### `argument_file_prefix`

**Default:** `"@"`

When set to a single character string, enables argument file expansion where arguments beginning with that character are treated as file paths. The file's contents are read and expanded inline during preprocessing. Setting to `None` or an empty string disables argument file expansion entirely.

See [argument-files.md](argument-files.md#syntax-convention) for complete details on prefix detection, escaping, and error handling.

```python
# Argument files enabled with default @ prefixresult = parse_command_line_args(spec, ["@config.args", "--verbose"])
# Expands contents of config.args inline

# Argument files disabledresult = parse_command_line_args(spec, ["@config.args"])
# Treats @config.args as literal positional argument
```

**When to use:**

- Default `@` prefix matches conventions from javac, Clikt, and picocli
- Custom prefix when `@` conflicts with application-specific syntax
- Disable when application needs to accept literal `@` arguments without escaping

**When to disable:**

- Security-sensitive contexts processing untrusted input
- Applications where `@` is a common argument value
- CLIs that don't need argument file support

### `argument_file_format`

**Default:** `LINE`

Specifies how argument files are parsed. `LINE` mode treats each non-empty, non-comment line as a single argument. `SHELL` mode parses files using shell-style whitespace separation with quoting support.

See [argument-files.md](argument-files.md#file-format-and-syntax) for complete format specifications and parsing rules.

```python
from flagrant.enums import ArgumentFileFormat

# Line-based format (default)# Shell-style format (future)```

**Line-based format characteristics:**

- One argument per line
- Leading/trailing whitespace trimmed
- Empty lines ignored
- Comments start with `#` at line beginning
- Simple and unambiguous

**Shell-style format characteristics (future):**

- Multiple arguments per line separated by whitespace
- Quoting with `'` and `"` for arguments containing spaces
- Escape sequences with backslash
- More flexible but more complex

### `argument_file_comment_char`

**Default:** `"#"`

Specifies the character that introduces line comments in argument files (line-based format only). Lines beginning with this character (optionally preceded by whitespace) are ignored during parsing. Setting to `None` disables comments, allowing values to start with the comment character.

See [argument-files.md](argument-files.md#comment-syntax) for comment syntax rules and edge cases.

```python
# Default: # introduces comments# Custom comment character# Comments disabled```

**When to customize:**

- Application uses `#` as a common argument value
- Match conventions from other configuration formats
- Disable to allow arbitrary argument values

### `max_argument_file_depth`

**Default:** `1`

Specifies the maximum depth of argument file recursion. A depth of 1 means argument files cannot reference other argument files. Higher values allow nested references but increase complexity and risk of circular dependencies.

See [argument-files.md](argument-files.md#recursive-expansion) for recursion semantics, depth limits, and circular reference detection.

```python
# No recursion (argument files cannot reference other files)# Allow one level of recursion```

**Constraints:**

- Must be >= 1 (disallowing all expansion should use `argument_file_prefix=None`)
- Values less than 1 raise `ParserConfigurationError`

**Security consideration:**

Conservative depth limits prevent resource exhaustion from deeply nested or circular file references. Applications processing untrusted input should use `max_argument_file_depth=1`.

## Negative number handling

### `allow_negative_numbers`

**Default:** `True`

When enabled, arguments that look like negative numbers are classified as values or positional arguments rather than short option clusters.

```python
spec = CommandSpecification(
    name="cmd",
    options=(
        OptionSpecification(name="threshold", long_names=("threshold",), arity=Arity(1, 1)),
    ),
    positionals=(
        PositionalSpecification(name="values", arity=Arity(0, None)),
    ),
)

# Enabled (default) - negative numbers recognizedresult = parse_command_line_args(spec, ["--threshold", "-5"])
assert result.options["threshold"].value == "-5"

result = parse_command_line_args(spec, ["-1", "-2", "-3.14"])
assert result.positionals["values"].value == ("-1", "-2", "-3.14")

# Disabled - negative numbers treated as unknown optionstry:
    parse_command_line_args(spec, ["--threshold", "-5"])
except UnknownOptionError:
    # -5 treated as short option cluster
    pass
```

**Pattern matching:**

The default negative number pattern matches:

```regex
^-\d+\.?\d*([eE][+-]?\d+)?$
```

This pattern recognizes:

- **Integers:** `-1`, `-42`, `-999`
- **Decimals:** `-3.14`, `-0.5`, `-100.0`
- **Scientific notation:** `-1e5`, `-2.5E-10`, `-6.022e23`

**When to use:**

- Mathematical or scientific applications handling negative numbers
- Tools that process numerical data
- Any CLI that legitimately accepts negative values
- Options that expect numeric arguments

**When to avoid:**

- CLIs with many short options where `-1`, `-2` might be option names
- Tools where the distinction between options and negative numbers might confuse users
- Simple CLIs where negative numbers aren't needed

### `negative_number_pattern`

**Default:** `None` (uses default pattern shown above)

Customize the regular expression used to detect negative numbers.

```python
config = ParserConfiguration(
    allow_negative_numbers=True,
    # Allow leading decimal: -.5
    negative_number_pattern=r"^-\.?\d+\.?\d*([eE][+-]?\d+)?$",
)

result = parse_command_line_args(spec, ["-.5"], config)  # Valid with custom pattern
assert result.positionals["values"].value == ("-0.5",)
```

**Constraints:**

The custom pattern must:

- Compile successfully as a Python regular expression
- Not match the empty string
- Not contain nested quantifiers like `(a+)+` (ReDoS protection)

If constraints are violated, `ParserConfigurationError` is raised during construction.

**ReDoS protection:**

To prevent Regular Expression Denial of Service attacks, the parser validates that patterns don't contain dangerous nested quantifiers. While not exhaustive, this catches the most common ReDoS patterns.

## Value flattening

### `flatten_option_values`

**Default:** `False`

Global default for value flattening in `ValueAccumulationMode.APPEND` mode. When options appear multiple times with multi-value arity, values from each occurrence can be nested tuples (APPEND) or flattened into a single tuple (EXTEND).

```python
spec = CommandSpecification(
    name="cmd",
    options=(
        ValueOptionSpecification(
            name="input",
            long_names=frozenset({"input"}),
            arity=Arity(2, 2),
            accumulation_mode=ValueAccumulationMode.APPEND,
        ),
    ),
)

# APPEND mode - values remain nested (preserves arity-bounded groups)
result = parse_command_line_args(spec, ["--input", "a", "b", "--input", "c", "d"])
assert result.options["input"].value == (("a", "b"), ("c", "d"))

# EXTEND mode - values flattened into single tuple
spec_extend = CommandSpecification(
    name="cmd",
    options=(
        ValueOptionSpecification(
            name="input",
            long_names=frozenset({"input"}),
            arity=Arity(2, 2),
            accumulation_mode=ValueAccumulationMode.EXTEND,
        ),
    ),
)result = parse_command_line_args(spec, ["--input", "a", "b", "--input", "c", "d"])
assert result.options["input"].value == ("a", "b", "c", "d")
```

**When to use APPEND:**

- When the structure of values (grouped by occurrence) is semantically significant
- When you need to preserve which values came from the same option occurrence
- Building complex data structures where nesting conveys meaning (e.g., key-value pairs)
- Options with arity > 1 where each occurrence represents a logical unit

**When to use EXTEND:**

- Collecting many values where grouping by occurrence is not semantically meaningful
- APIs where flat lists are more convenient than nested structures
- Building simple accumulated value lists
- Collecting file paths, include directories, or other homogeneous collections

**Note:** The `flatten_option_values` configuration flag described here is a legacy concept. Modern implementations should use the explicit APPEND vs EXTEND accumulation modes on value option specifications instead.

## Configuration interactions

Configuration flags are largely independent, but some combinations produce specific behaviors worth understanding.

### Abbreviation with case insensitivity

When both abbreviation and case insensitivity are enabled, abbreviations match case-insensitively:

```pythonresult = parse_command_line_args(spec, ["--VER"])  # Matches "verbose" case-insensitively
```

**How it works:** Names are normalized to lowercase first, then abbreviation matching is applied to the normalized names.

### Aliases with case insensitivity

Aliases also match case-insensitively when enabled:

```python
spec = CommandSpecification(
    name="cmd",
    subcommands=(
        CommandSpecification(name="remove", aliases=("rm",)),
    ),
)result = parse_command_line_args(spec, ["RM"])  # Matches "remove" via alias, case-insensitively
```

### Underscore conversion with abbreviation

Underscore-to-dash conversion applies before abbreviation matching:

```python
spec = CommandSpecification(
    name="cmd",
    options=(
        OptionSpecification(name="my_long_option", long_names=("my-long-option",)),
    ),
)result = parse_command_line_args(spec, ["--my_lon"])  # Underscores normalized, then abbreviated
```

### POSIX-style ordering with abbreviated options

POSIX-style ordering and option abbreviation combine naturally:

```python# Abbreviated option before positional works
result = parse_command_line_args(spec, ["--verb", "file.txt"])

# After positional, even abbreviated option-like args are positionals
result = parse_command_line_args(spec, ["file.txt", "--verb"])
# "--verb" is treated as a positional, not an option
```

### Negative numbers with POSIX-style ordering

Negative number recognition works with POSIX-style ordering in appropriate contexts:

```python# Before positionals started: negative number as option value
result = parse_command_line_args(spec, ["--threshold", "-5"])
assert result.options["threshold"].value == "-5"

# After positionals started: negative number as positional
result = parse_command_line_args(spec, ["file.txt", "-5"])
assert result.positionals["values"].value == ("-5",)
```

## Preset configurations

Common use cases are well-served by preset configurations that combine multiple flags appropriately.

### Modern developer tool

```python```

**Characteristics:**

- Flexible option placement
- User-friendly convenience features
- Supports Python naming conventions
- Suitable for tools like cargo, npm, pip

### Traditional Unix utility

```python    allow_abbreviated_options=False,
    allow_abbreviated_subcommands=False,
    # Conservative settings
    allow_command_aliases=False,
    case_sensitive_options=True,
    case_sensitive_commands=True,
)
```

**Characteristics:**

- POSIX-style argument ordering
- Conservative, strict matching
- Predictable behavior
- Suitable for system utilities

### User-friendly application

```python```

**Characteristics:**

- Flexible argument placement
- Forgiving name matching
- Explicit flag values
- Abbreviations for convenience
- Suitable for user-facing applications

### Scientific/numerical tool

```python```

**Characteristics:**

- Support for negative numeric values
- Otherwise standard behavior
- Suitable for mathematical/scientific applications

### Minimal configuration

```python
# Uses all defaults:
# - Flexible option placement (strict_posix_options=False)
# - No abbreviations (allow_abbreviated_options=False, allow_abbreviated_subcommands=False)
# - Case-sensitive (case_sensitive_options=True, case_sensitive_commands=True, case_sensitive_keys=True)
# - Underscore-dash conversion enabled (convert_underscores=True)
# - Negative numbers recognized (allow_negative_numbers=True)
# - Command aliases enabled (allow_command_aliases=True)
```

This is appropriate for simple CLIs with well-defined option and positional boundaries.

## Configuration validation

The parser validates configuration during construction to catch errors early.

### Validation rules

**Abbreviation configuration:**

- `minimum_abbreviation_length` must be >= 1
- If < 1, raises `ParserConfigurationError`

**Negative number pattern:**

- Custom pattern must compile as valid Python regex
- Pattern must not match empty string
- Pattern must not contain nested quantifiers (ReDoS protection)
- If any constraint is violated, raises `ParserConfigurationError`

All validation occurs at parser construction time, establishing a clear fail-fast boundary. Invalid configurations are caught before any parsing occurs.

### Configuration error handling

Invalid configurations raise `ConfigurationError` with a message identifying the specific constraint violation:

```python
try:
    config = ParserConfiguration(minimum_abbreviation_length=0)  # Invalid
    result = parse_command_line_args(spec, [], config)
except ConfigurationError as e:
    print(e)  # "minimum_abbreviation_length must be >= 1, got 0"
```

## Summary

Parser configuration provides fine-grained control over parsing behavior without changing the fundamental algorithm. Key points:

**Configuration scope:**

- Set at parser construction time
- Immutable throughout the parser's lifetime
- Applies uniformly across all command levels

**Core dimensions:**

- **Positional modes** - POSIX-strict vs GNU-flexible
- **Name resolution** - Abbreviation, case sensitivity, aliases
- **Flag values** - Explicit value assignment for boolean flags
- **Negative numbers** - Recognition of numeric arguments
- **Value flattening** - Nested vs flat tuples with APPEND vs EXTEND accumulation modes

**Design principles:**

- All flags are independent unless explicitly documented as interacting
- Configuration is validated at construction time
- Default configuration is conservative and predictable
- Preset configurations support common use cases

**Related specifications:**

- [Architecture](architecture.md) - System architecture and design principles
- [Grammar specification](grammar.md) - Syntax rules affected by configuration
- [Behavior specification](behavior.md) - Parsing algorithms using configuration
- [Error types](errors.md) - Validation errors
- [Concepts guide](concepts.md) - Arity, accumulation modes, resolution

**Target audience:** Developers configuring parsers, framework builders integrating Flagrant, and anyone designing CLI specifications.

**Maintenance:** Update this specification when configuration options are added, removed, or their behavior changes. Algorithm changes belong in the [behavior specification](behavior.md), syntax changes belong in the [grammar specification](grammar.md).
