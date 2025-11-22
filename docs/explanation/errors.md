# Parser error specification

This page provides a comprehensive reference for all error conditions, error types, and error context in the Flagrant parser. It specifies when errors are raised, what information each error captures, and how error context is structured.

The parser uses a two-phase error strategy. Construction-time errors prevent invalid specifications from reaching the parser, catching configuration mistakes early. Parse-time errors represent user input violations during argument processing, providing structured information that higher-level components format for display.

## Table of contents

- [Error hierarchy](#error-hierarchy)
- [Construction-time errors](#construction-time-errors)
  - [SpecificationError](#specificationerror)
  - [DuplicateNameError](#duplicatenameerror)
  - [InvalidNameFormatError](#invalidnameformaterror)
  - [InvalidArityError](#invalidarityerror)
  - [InvalidFlagConfigError](#invalidflagconfigerror)
- [Parse-time errors](#parse-time-errors)
  - [UnknownOptionError](#unknownoptionerror)
  - [AmbiguousOptionError](#ambiguousoptionerror)
  - [InsufficientValuesError](#insufficientvalueserror)
  - [ValueNotAllowedError](#valuenotallowederror)
  - [DuplicateOptionError](#duplicateoptionerror)
  - [UnexpectedArgumentError](#unexpectedargumenterror)
  - [AmbiguousSubcommandError](#ambiguoussubcommanderror)
  - [UnknownSubcommandError](#unknownsubcommanderror)
- [Error context](#error-context)
  - [Common context fields](#common-context-fields)
  - [Error message format](#error-message-format)
- [Examples catalog](#examples-catalog)

---

## Error hierarchy

The parser uses a three-tier exception hierarchy that separates concerns and enables targeted error handling.

### Base exception

**`FlagrantError`** is the base exception for all Flagrant-related errors. This is the top-level catch point for any system error.

```python
class FlagrantError(Exception):
    """Base class for all Flagrant-related errors."""
```

### Configuration errors

**`ConfigurationError`** is the base for all configuration-related errors that occur outside the parser. This includes completion configuration and parser configuration.

```python
class ConfigurationError(FlagrantError):
    """Raised when there is an error in configuration settings."""
```

**`ParserConfigurationError`** (extends `ConfigurationError`) is raised when parser configuration is invalid. This occurs at parser construction time when configuration values violate constraints.

```python
class ParserConfigurationError(ConfigurationError):
    """Raised when parser configuration is invalid."""
```

Example: Invalid abbreviation length configuration.

```python
# ❌ Raises ParserConfigurationError
parser = Parser(spec, minimum_abbreviation_length=0)  # Must be >= 1
```

### Specification errors

**`SpecificationError`** is the base for all specification validation errors. These occur when a command specification violates structural constraints.

```python
class SpecificationError(FlagrantError):
    """Raised when there is an error in a command or parameter specification."""
```

Specification errors are raised at construction time and are further subdivided into specific error types based on the constraint violated.

### Parse errors

**`ParseError`** is the base for all parsing errors. These occur during argument processing when user input violates specification constraints.

```python
class ParseError(FlagrantError):
    """Base class for all parsing-related errors."""
```

Parse errors represent user input mistakes, not configuration problems. They provide structured information about what was wrong with the input.

### Error hierarchy diagram

```
FlagrantError (base for all Flagrant errors)
├── ConfigurationError (configuration problems)
│   ├── CompletionConfigurationError
│   └── ParserConfigurationError
├── SpecificationError (specification validation)
│   ├── DuplicateNameError
│   ├── InvalidNameFormatError
│   ├── InvalidArityError
│   └── InvalidFlagConfigError
└── ParseError (parsing/user input errors)
    ├── UnknownOptionError
    ├── AmbiguousOptionError
    ├── InsufficientValuesError
    ├── ValueNotAllowedError
    ├── DuplicateOptionError
    ├── UnexpectedArgumentError
    ├── UnknownSubcommandError
    ├── AmbiguousSubcommandError
    ├── ArgumentFileNotFoundError
    ├── ArgumentFileReadError
    ├── ArgumentFileFormatError
    └── ArgumentFileRecursionError
```

---

## Construction-time errors

Construction-time errors occur when creating specification objects or parser instances. These errors prevent invalid configurations from reaching the parser by failing fast during initialization.

### SpecificationError

**When raised:** A command specification violates a structural constraint during validation.

**Timing:** During `CommandSpec`, `OptionSpec`, or `PositionalSpec` construction.

**Severity:** Fatal - invalid specification prevents parsing.

**Context provided:**

- **`specification`** - The specification object that failed validation
- **`constraint_type`** - The kind of constraint violated (e.g., "name_format", "arity_bounds", "name_uniqueness")
- **`message`** - Human-readable description of the violation

**Base exception:** All specification validation errors extend `SpecificationError`.

**Example:**

```python
# ❌ Raises SpecificationError (or subclass)
try:
    spec = CommandSpecification(name="")
except SpecificationError as e:
    # Command names must not be empty
    print(f"Specification error: {e}")
```

### DuplicateNameError

**When raised:** A specification contains duplicate names that must be unique.

**Timing:** During spec construction when validating option names, positional names, or subcommand names.

**Severity:** Fatal - prevents construction.

**Context provided:**

- **`name_type`** - Kind of name that duplicates ("option", "positional", "subcommand")
- **`duplicates`** - Set or list of duplicate names found
- **`conflicting_specs`** - The spec objects that share the duplicate names
- **`specification`** - The parent specification where duplication occurred

**Uniqueness requirements:**

Within a command:

- All option long names must be unique
- All option short names must be unique
- All positional names must be unique
- All subcommand names and aliases must be unique

**Examples:**

```python
# ❌ Duplicate long option names
try:
    spec = CommandSpecification(
        name="cmd",
        options=(
            FlagOptionSpecification(name="verbose", long_names=frozenset({"verbose"})),
            FlagOptionSpecification(name="verbosity", long_names=frozenset({"verbose"})),  # Duplicate!
        )
    )
except DuplicateNameError as e:
    # Error: Duplicate option long name 'verbose' in command 'cmd'
    print(f"Duplication: {e.duplicates}")  # {'verbose'}
    print(f"Type: {e.name_type}")          # 'option'
```

```python
# ❌ Duplicate short option names
try:
    spec = CommandSpecification(
        name="cmd",
        options=(
            FlagOptionSpecification(name="verbose", short_names=frozenset({"v"})),
            FlagOptionSpecification(name="version", short_names=frozenset({"v"})),  # Duplicate!
        )
    )
except DuplicateNameError as e:
    # Error: Duplicate option short name 'v' in command 'cmd'
    print(f"Duplication: {e.duplicates}")  # {'v'}
```

```python
# ❌ Duplicate positional names
try:
    spec = CommandSpecification(
        name="cmd",
        positionals=(
            PositionalSpecification(name="file", arity=Arity(1, 1)),
            PositionalSpecification(name="file", arity=Arity(1, 1)),  # Duplicate!
        )
    )
except DuplicateNameError as e:
    # Error: Duplicate positional name 'file' in command 'cmd'
    print(f"Duplication: {e.duplicates}")  # {'file'}
```

```python
# ❌ Duplicate subcommand names
try:
    spec = CommandSpecification(
        name="git",
        subcommands=(
            CommandSpecification(name="commit"),
            CommandSpecification(name="commit"),  # Duplicate!
        )
    )
except DuplicateNameError as e:
    # Error: Duplicate subcommand name 'commit' in command 'git'
    print(f"Duplication: {e.duplicates}")  # {'commit'}
```

### InvalidNameFormatError

**When raised:** A name violates format rules during spec construction.

**Timing:** During spec construction when validating names.

**Severity:** Fatal - prevents construction.

**Context provided:**

- **`name`** - The invalid name
- **`name_type`** - Kind of name ("command", "long_option", "short_option", "positional")
- **`rule_violated`** - The specific format rule that was violated
- **`details`** - Additional information about the rule

**Format rules:**

Command names:

- Must be non-empty
- Must start with an alphabetic character (A-Z, a-z)
- May contain alphanumeric characters, dashes, and underscores
- Must not contain whitespace or special characters

Long option names:

- Must be at least two characters
- Must not start with dashes
- May contain alphanumeric characters and dashes
- Must not contain whitespace

Short option names:

- Must be exactly one character
- Must be alphanumeric
- Must not be a dash

Positional names:

- Must be non-empty
- Should follow the same conventions as command names (but less strictly enforced)

**Examples:**

```python
# ❌ Command name with invalid starting character
try:
    spec = CommandSpecification(name="123app")
except InvalidNameFormatError as e:
    # Error: Command name '123app' must start with alphabetic character
    print(f"Rule: {e.rule_violated}")      # 'starts_with_alpha'
    print(f"Name: {e.name}")               # '123app'
    print(f"Type: {e.name_type}")          # 'command'
```

```python
# ❌ Long option name too short
try:
    opt = FlagOptionSpecification(name="v", long_names=frozenset({"v"}))
except InvalidNameFormatError as e:
    # Error: Long option name 'v' must be at least 2 characters
    print(f"Rule: {e.rule_violated}")      # 'min_length'
    print(f"Details: {e.details}")         # {'min_length': 2, 'actual': 1}
```

```python
# ❌ Short option name too long
try:
    opt = FlagOptionSpecification(name="verbose", short_names=frozenset({"vb"}))
except InvalidNameFormatError as e:
    # Error: Short option name 'vb' must be exactly 1 character
    print(f"Rule: {e.rule_violated}")      # 'exact_length'
    print(f"Details: {e.details}")         # {'required': 1, 'actual': 2}
```

```python
# ❌ Long option name with dashes at start
try:
    opt = FlagOptionSpecification(name="verbose", long_names=frozenset({"--verbose"}))
except InvalidNameFormatError as e:
    # Error: Long option name '--verbose' must not start with dashes
    print(f"Rule: {e.rule_violated}")      # 'no_leading_dashes'
```

### InvalidArityError

**When raised:** An arity specification violates constraints during spec construction.

**Timing:** During `OptionSpec` or `PositionalSpec` construction when arity is validated.

**Severity:** Fatal - prevents construction.

**Context provided:**

- **`specification`** - The spec with invalid arity
- **`arity`** - The `Arity` object that is invalid
- **`constraint_violated`** - Description of what went wrong ("min_negative", "max_negative", "min_exceeds_max")
- **`actual_values`** - The (min, max) values provided

**Arity constraints:**

- **Minimum arity:** Must be non-negative (>= 0)
- **Maximum arity:** Must be non-negative or None (unbounded)
- **Relationship:** Minimum must not exceed maximum

**Examples:**

```python
# ❌ Negative minimum arity
try:
    pos = PositionalSpecification(name="file", arity=Arity(-1, 1))
except InvalidArityError as e:
    # Error: Minimum arity cannot be negative, got -1
    print(f"Constraint: {e.constraint_violated}")  # 'min_negative'
    print(f"Arity: {e.arity}")                      # Arity(min=-1, max=1)
```

```python
# ❌ Minimum exceeds maximum
try:
    opt = ValueOptionSpecification(name="coords", arity=Arity(5, 2))
except InvalidArityError as e:
    # Error: Minimum arity (5) cannot exceed maximum arity (2)
    print(f"Constraint: {e.constraint_violated}")  # 'min_exceeds_max'
    print(f"Arity: {e.arity}")                      # Arity(min=5, max=2)
```

```python
# ❌ Negative maximum arity (when not unbounded)
try:
    opt = ValueOptionSpecification(name="files", arity=Arity(0, -1))
except InvalidArityError as e:
    # Error: Maximum arity cannot be negative, got -1
    print(f"Constraint: {e.constraint_violated}")  # 'max_negative'
```

### InvalidFlagConfigError

**When raised:** A flag configuration contains inconsistencies or invalid values during spec construction.

**Timing:** During `OptionSpec` construction when flag settings are validated.

**Severity:** Fatal - prevents construction.

**Context provided:**

- **`specification`** - The option spec with invalid flag config
- **`config_error_type`** - Type of config error ("overlapping_flag_values", "empty_negation_word", "invalid_negation_word")
- **`conflicting_values`** - Values or configurations that conflict
- **`details`** - Additional context about the error

**Flag configuration constraints:**

- Negation words must be non-empty
- Negation words must not contain whitespace or special characters

**Examples:**

```python
# ❌ Empty negation word
try:
    opt = FlagOptionSpecification(
        name="verbose",
        negation_prefixes=frozenset({""}),  # Empty string!
    )
except InvalidFlagConfigError as e:
    # Error: Negation words must not be empty
    print(f"Error type: {e.config_error_type}")    # 'empty_negation_word'
```

```python
# ❌ Negation word with whitespace
try:
    opt = FlagOptionSpecification(
        name="verbose",
        negation_prefixes=frozenset({"no longer"}),  # Contains space!
    )
except InvalidFlagConfigError as e:
    # Error: Negation words must not contain whitespace
    print(f"Error type: {e.config_error_type}")    # 'invalid_negation_word'
    print(f"Details: {e.details}")                  # {'invalid_word': 'no longer'}
```

---

## Parse-time errors

Parse-time errors occur during argument processing when user input violates specification constraints. Unlike construction-time errors, these represent user input mistakes rather than configuration problems.

### UnknownOptionError

**When raised:** User specifies an option that is not in the specification.

**Timing:** During parsing when an option name cannot be matched.

**Severity:** Non-fatal in isolation - the error is raised but parse result may still be available.

**Context provided:**

- **`option_name`** - The unknown option as provided by the user
- **`option_form`** - Form of the option ("long" or "short")
- **`valid_options`** - List of valid option names for this command (raw candidate data for Aclaf's suggestion engine)
- **`command_name`** - Name of the command where error occurred
- **`argv`** - Complete command-line arguments being parsed
- **`argument_index`** - Index in argv where error occurred
- **`subcommand_path`** - Chain of parent→child subcommands

**When does this occur:**

- User specifies a long option like `--unknown` that doesn't exist
- User specifies a short option like `-x` that doesn't exist
- User abbreviates an option to a name that doesn't match any defined option (when abbreviations are enabled)

**Examples:**

```python
# ❌ Unknown long option
spec = CommandSpecification(
    name="cmd",
    options=(FlagOptionSpecification(name="verbose", long_names=frozenset({"verbose"})),)
)
parser = Parser(spec)

try:
    result = parser.parse(["--help"])
except UnknownOptionError as e:
    # Error: Unknown option '--help'
    print(f"Option: {e.option_name}")           # '--help'
    print(f"Form: {e.option_form}")             # 'long'
    print(f"Valid options: {e.valid_options}")  # ['--verbose']
    print(f"Command: {e.command_name}")         # 'cmd'
```

```python
# ❌ Unknown short option
try:
    result = parser.parse(["-h"])
except UnknownOptionError as e:
    # Error: Unknown option '-h'
    print(f"Option: {e.option_name}")           # '-h'
    print(f"Form: {e.option_form}")             # 'short'
    print(f"Valid options: {e.valid_options}")  # ['-v']
```

### AmbiguousOptionError

**When raised:** An option abbreviation matches multiple valid options.

**Timing:** During parsing when abbreviation matching finds multiple candidates.

**Severity:** Non-fatal in isolation.

**Context provided:**

- **`provided_abbreviation`** - The abbreviation as typed by user
- **`matched_options`** - List of option specs that match the abbreviation
- **`matched_option_names`** - Long form names of matched options (tuple of strings)
- **`option_form`** - Form of the option ("long" or "short")
- **`command_name`** - Name of the command where error occurred
- **`minimum_abbreviation_length`** - Minimum abbreviation length from configuration
- **`argv`** - Complete command-line arguments being parsed
- **`argument_index`** - Index in argv where error occurred
- **`subcommand_path`** - Chain of parent→child subcommands

**When does this occur:**

- User enables abbreviation matching with `allow_abbreviated_options=True`
- User provides a prefix that matches multiple long options
- For example, with options `--verbose` and `--verify`, typing `--ver` is ambiguous

**Examples:**

```python
# ❌ Ambiguous long option abbreviation
spec = CommandSpecification(
    name="cmd",
    options=(
        FlagOptionSpecification(name="verbose", long_names=frozenset({"verbose"})),
        FlagOptionSpecification(name="verify", long_names=frozenset({"verify"}))
    )
)
config = Configuration(allow_abbreviated_options=True, minimum_abbreviation_length=2)
parser = Parser(spec, config=config)

try:
    result = parser.parse(["--ver"])
except AmbiguousOptionError as e:
    # Error: Ambiguous option '--ver' matches multiple options
    print(f"Abbreviation: {e.provided_abbreviation}")  # '--ver'
    print(f"Matches: {e.matched_options}")             # [verbose_spec, verify_spec]
    print(f"Form: {e.option_form}")                    # 'long'
```

### InsufficientValuesError

**When raised:** An option or positional argument receives fewer values than its minimum arity requires.

**Timing:** During parsing when consuming arguments for an option or positional.

**Severity:** Non-fatal in isolation.

**Context provided:**

- **`parameter_name`** - Name of the option or positional that needs values
- **`parameter_type`** - "option" or "positional"
- **`required_minimum`** - Minimum number of values required (arity.min)
- **`received_count`** - Number of values actually received
- **`values_received`** - The actual values that were provided
- **`command_name`** - Name of the command where error occurred
- **`arity_min`** - Minimum arity value
- **`arity_max`** - Maximum arity value (int or None if unbounded)
- **`accumulation_mode`** - AccumulationMode enum value (when parameter_type == "option")
- **`option_form`** - Form of option ("long" or "short"), None for positionals
- **`argv`** - Complete command-line arguments being parsed
- **`argument_index`** - Position of the option token in argv
- **`subcommand_path`** - Chain of parent→child subcommands

**When does this occur:**

- User provides fewer values than required by an option's arity
- User provides fewer positional arguments than required
- For example, an option with `arity=(2, 3)` that receives only one value

**Examples:**

```python
# ❌ Option with insufficient values
spec = CommandSpecification(
    name="cmd",
    options=(ValueOptionSpecification(name="coords", long_names=frozenset({"coords"}), arity=Arity(2, 2)),)
)
parser = Parser(spec)

try:
    result = parser.parse(["--coords", "10"])
except InsufficientValuesError as e:
    # Error: Option 'coords' requires 2 values but received 1
    print(f"Parameter: {e.parameter_name}")      # 'coords'
    print(f"Type: {e.parameter_type}")           # 'option'
    print(f"Required: {e.required_minimum}")     # 2
    print(f"Received: {e.received_count}")       # 1
    print(f"Values: {e.values_received}")        # ('10',)
```

```python
# ❌ Positional with insufficient values
spec = CommandSpecification(
    name="cmd",
    positionals=(PositionalSpecification(name="files", arity=Arity(2, None)),)
)
parser = Parser(spec)

try:
    result = parser.parse(["file1.txt"])
except InsufficientValuesError as e:
    # Error: Positional 'files' requires minimum 2 values but received 1
    print(f"Parameter: {e.parameter_name}")      # 'files'
    print(f"Type: {e.parameter_type}")           # 'positional'
    print(f"Required: {e.required_minimum}")     # 2
    print(f"Received: {e.received_count}")       # 1
```

### ValueNotAllowedError

**When raised:** A flag option (arity `(0, 0)`) is provided with an explicit value using equals syntax.

**Timing:** During parsing when encountering a flag with inline value syntax.

**Severity:** Non-fatal in isolation.

**Context provided:**

- **`option_name`** - Name of the flag option
- **`provided_value`** - The value that was provided
- **`command_name`** - Name of the command where error occurred
- **`option_form`** - Form of option ("long" or "short")
- **`argv`** - Complete command-line arguments being parsed
- **`argument_index`** - Index in argv where error occurred
- **`subcommand_path`** - Chain of parent→child subcommands

**When does this occur:**

- Flag option (FlagOptionSpecification with arity `(0, 0)`) receives an explicit value
- User attempts to use equals syntax like `--verbose=true` or attached syntax like `-vtrue`
- Flags represent boolean presence/absence and do not accept values

**Examples:**

```python
# ❌ Flag with explicit value
spec = CommandSpecification(
    name="cmd",
    options=(
        FlagOptionSpecification(
            name="verbose",
            long_names=frozenset({"verbose"}),
        ),
    )
)
parser = Parser(spec)

try:
    result = parser.parse(["--verbose=true"])
except ValueNotAllowedError as e:
    # Error: Flag 'verbose' does not accept values
    print(f"Option: {e.option_name}")           # 'verbose'
    print(f"Value: {e.provided_value}")         # 'true'
```

### DuplicateOptionError

**When raised:** An option with ERROR accumulation mode appears multiple times.

**Timing:** During parsing when encountering a second occurrence of an option configured with `accumulation_mode=AccumulationMode.ERROR`.

**Severity:** Non-fatal in isolation.

**Context provided:**

- **`option_name`** - Name of the option that appeared multiple times
- **`occurrence_count`** - How many times the option appeared
- **`indices`** - All occurrence indices in argv (tuple of int, not just first/second)
- **`command_name`** - Name of the command where error occurred
- **`argv`** - Complete command-line arguments being parsed
- **`subcommand_path`** - Chain of parent→child subcommands

**When does this occur:**

- Option is configured with `accumulation_mode=AccumulationMode.ERROR`
- User specifies the option more than once
- For example, `--once value1 --once value2` when `--once` has ERROR accumulation

**Examples:**

```python
# ❌ Duplicate option with ERROR accumulation
spec = CommandSpecification(
    name="cmd",
    options=(
        ValueOptionSpecification(
            name="once",
            long_names=frozenset({"once"}),
            arity=Arity(1, 1),
            accumulation_mode=ValueAccumulationMode.ERROR
        ),
    )
)
parser = Parser(spec)

try:
    result = parser.parse(["--once", "first", "--once", "second"])
except DuplicateOptionError as e:
    # Error: Option 'once' cannot be specified more than once
    print(f"Option: {e.option_name}")              # 'once'
    print(f"Count: {e.occurrence_count}")          # 2
    print(f"First at: {e.first_occurrence_index}") # 0
    print(f"Second at: {e.second_occurrence_index}") # 2
```

### UnexpectedArgumentError

**When raised:** A positional-like argument appears but all specified positionals have been satisfied, and strict positional mode is enabled.

**Timing:** During parsing after all positional arguments have been consumed but additional positional-like arguments remain.

**Severity:** Non-fatal in isolation.

**Context provided:**

- **`unexpected_argument`** - The unexpected positional argument value
- **`command_name`** - Name of the command where error occurred
- **`argv`** - Complete command-line arguments being parsed
- **`argument_index`** - Index in argv where the unexpected argument occurred
- **`subcommand_path`** - Chain of parent→child subcommands
- **`consumed_positionals`** - Number of positional arguments already consumed
- **`defined_positionals`** - List of defined positional parameter names

**When does this occur:**

- Parser configuration has `strict_options_before_positionals=True` (POSIX-style ordering)
- All defined positional parameters have been satisfied
- Additional arguments remain that are not recognized as options
- These remaining arguments appear where positionals would be expected

This error enforces strict validation in POSIX mode where the command specification defines exactly which positionals are accepted. Unlike flexible mode, where extra positionals might be silently ignored or collected in a variadic positional, strict mode requires that the specification explicitly accounts for every positional argument.

**Examples:**

```python
# ❌ Extra positional in strict mode
spec = CommandSpecification(
    name="copy",
    positionals=(
        PositionalSpecification(name="source", arity=Arity(1, 1)),
        PositionalSpecification(name="destination", arity=Arity(1, 1))
    )
)
config = Configuration(strict_options_before_positionals=True)
parser = Parser(spec, config=config)

try:
    # User provides 3 positionals, but spec only defines 2
    result = parser.parse(["file1.txt", "file2.txt", "file3.txt"])
except UnexpectedArgumentError as e:
    # Error: Unexpected positional argument 'file3.txt' in command 'copy'
    print(f"Argument: {e.unexpected_argument}")      # 'file3.txt'
    print(f"Command: {e.command_name}")               # 'copy'
    print(f"Consumed: {e.consumed_positionals}")      # 2
    print(f"Defined: {e.defined_positionals}")        # ['source', 'destination']
```

```python
# ❌ Option-like argument treated as positional in strict mode
spec = CommandSpecification(
    name="process",
    options=(
        FlagOptionSpecification(name="verbose", short_names=frozenset({"v"})),
    ),
    positionals=(
        PositionalSpecification(name="file", arity=Arity(1, 1)),
    )
)
config = Configuration(strict_options_before_positionals=True)
parser = Parser(spec, config=config)

try:
    # In strict mode, once a positional is encountered, options are no longer recognized
    # So "--verbose" after "input.txt" is treated as a positional
    result = parser.parse(["input.txt", "--verbose"])
except UnexpectedArgumentError as e:
    # Error: Unexpected positional argument '--verbose' in command 'process'
    # (The positional "file" consumed "input.txt", leaving "--verbose" as unexpected)
    print(f"Argument: {e.unexpected_argument}")      # '--verbose'
    print(f"Command: {e.command_name}")               # 'process'
```

**Note:** This error is specific to `strict_options_before_positionals=True` mode. In flexible mode (default), the parser continues recognizing options throughout the argument list, so this situation doesn't arise.

**Cross-references:**

- Configuration: `strict_options_before_positionals` in `specs/parser/configuration.md#posix-style-ordering-mode`
- Behavior: POSIX-style parsing in `specs/parser/behavior.md`

### AmbiguousSubcommandError

**When raised:** A subcommand abbreviation matches multiple valid subcommands.

**Timing:** During parsing when abbreviation matching finds multiple subcommand candidates.

**Severity:** Non-fatal in isolation.

**Context provided:**

- **`provided_abbreviation`** - The abbreviation as typed by user
- **`matched_subcommands`** - List of subcommand specs that match the abbreviation
- **`parent_command_name`** - Name of the parent command where error occurred

**When does this occur:**

- User enables subcommand abbreviation matching with `allow_abbreviated_subcommands=True`
- User provides a prefix that matches multiple subcommands
- For example, with subcommands `commit` and `checkout`, typing `co` is ambiguous

**Examples:**

```python
# ❌ Ambiguous subcommand abbreviation
spec = CommandSpecification(
    name="git",
    subcommands=(
        CommandSpecification(name="commit"),
        CommandSpecification(name="checkout"),
        CommandSpecification(name="config"),
    )
)
config = Configuration(allow_abbreviated_subcommands=True, minimum_abbreviation_length=2)
parser = Parser(spec, config=config)

try:
    result = parser.parse(["co"])
except AmbiguousSubcommandError as e:
    # Error: Ambiguous subcommand 'co' matches multiple subcommands
    print(f"Abbreviation: {e.provided_abbreviation}")  # 'co'
    print(f"Matches: {e.matched_subcommands}")         # [commit_spec, checkout_spec, config_spec]
    print(f"Parent: {e.parent_command_name}")          # 'git'
```

**Cross-references:**

- Configuration: `allow_abbreviated_subcommands` in `specs/parser/configuration.md#allow_abbreviated_subcommands`
- Configuration: `minimum_abbreviation_length` in `specs/parser/configuration.md#minimum_abbreviation_length`

### UnknownSubcommandError

**When raised:** User specifies a subcommand that is not in the specification.

**Timing:** During parsing when a positional-like argument doesn't match any defined subcommand.

**Severity:** Non-fatal in isolation.

**Context provided:**

- **`subcommand_name`** - The unknown subcommand as provided
- **`parent_command_name`** - Name of the parent command
- **`valid_subcommands`** - List of valid subcommand names (raw candidate data for Aclaf's suggestion engine)
- **`argv`** - Complete command-line arguments being parsed
- **`argument_index`** - Position where subcommand was expected in argv
- **`subcommand_path`** - Chain of parent→child subcommands

**When does this occur:**

- User specifies a subcommand that doesn't exist
- When abbreviations are enabled, an abbreviation matches no subcommands
- For example, with subcommands `commit` and `checkout`, typing `branch` is unknown

**Examples:**

```python
# ❌ Unknown subcommand
spec = CommandSpecification(
    name="git",
    subcommands=(
        CommandSpecification(name="commit"),
        CommandSpecification(name="push")
    )
)
parser = Parser(spec)

try:
    result = parser.parse(["branch"])
except UnknownSubcommandError as e:
    # Error: Unknown subcommand 'branch'
    print(f"Subcommand: {e.subcommand_name}")      # 'branch'
    print(f"Parent: {e.parent_command_name}")      # 'git'
    print(f"Valid: {e.valid_subcommands}")         # ['commit', 'push']
```

### ArgumentFileNotFoundError

**When raised:** An argument file reference (`@file`) points to a file that doesn't exist.

**Timing:** During preprocessing before parsing when expanding argument files.

**Severity:** Fatal - prevents parsing from proceeding.

**Context provided:**

- **`file_path`** - The file path that was not found (as resolved)
- **`original_argument`** - The original `@file` argument as provided
- **`resolved_path`** - The absolute path after resolution
- **`command_name`** - Name of the command being parsed
- **`argv`** - Complete command-line arguments being parsed
- **`argument_index`** - Position of the @file token in argv

**When does this occur:**

- User specifies `@filename` but `filename` doesn't exist in the current directory
- Typo in argument file name
- Relative path resolution differs from user expectations

**Examples:**

```python
# ❌ Argument file not found
parser = Parser(spec, argument_file_prefix="@")

try:
    result = parser.parse(["@missing.args", "--verbose"])
except ArgumentFileNotFoundError as e:
    # Error: Argument file not found: missing.args
    print(f"File path: {e.file_path}")           # 'missing.args'
    print(f"Original: {e.original_argument}")    # '@missing.args'
    print(f"Resolved: {e.resolved_path}")        # '/current/dir/missing.args'
```

### ArgumentFileReadError

**When raised:** An argument file exists but cannot be read due to I/O errors or permissions.

**Timing:** During preprocessing when attempting to read file contents.

**Severity:** Fatal - prevents parsing from proceeding.

**Context provided:**

- **`file_path`** - The file path that could not be read
- **`original_argument`** - The original `@file` argument
- **`io_error`** - The underlying I/O exception or error message
- **`command_name`** - Name of the command being parsed
- **`argv`** - Complete command-line arguments being parsed
- **`argument_index`** - Position of the @file token in argv

**When does this occur:**

- File exists but has no read permissions
- File is locked by another process (Windows)
- I/O error during reading (disk error, network share disconnect)

**Examples:**

```python
# ❌ Argument file cannot be read
parser = Parser(spec, argument_file_prefix="@")

try:
    result = parser.parse(["@protected.args"])
except ArgumentFileReadError as e:
    # Error: Cannot read argument file: protected.args (Permission denied)
    print(f"File path: {e.file_path}")           # 'protected.args'
    print(f"I/O error: {e.io_error}")            # 'Permission denied'
```

### ArgumentFileFormatError

**When raised:** An argument file contains malformed content that violates format rules.

**Timing:** During preprocessing when parsing file contents.

**Severity:** Fatal - prevents parsing from proceeding.

**Context provided:**

- **`file_path`** - The file path containing format errors
- **`line_number`** - Line number where error occurred (if applicable)
- **`error_description`** - Description of the format violation
- **`original_argument`** - The original `@file` argument
- **`command_name`** - Name of the command being parsed
- **`argv`** - Complete command-line arguments being parsed
- **`argument_index`** - Position of the @file token in argv

**When does this occur:**

- File contains invalid UTF-8 encoding
- Shell-style format with unmatched quotes (future)
- Syntax violations in file contents

**Examples:**

```python
# ❌ Argument file with format error
parser = Parser(spec, argument_file_prefix="@")

try:
    result = parser.parse(["@malformed.args"])
except ArgumentFileFormatError as e:
    # Error: Format error in argument file malformed.args at line 5
    print(f"File path: {e.file_path}")           # 'malformed.args'
    print(f"Line: {e.line_number}")              # 5
    print(f"Error: {e.error_description}")       # 'Invalid UTF-8 sequence'
```

### ArgumentFileRecursionError

**When raised:** Recursive argument file expansion exceeds depth limit or detects a cycle.

**Timing:** During preprocessing when expanding nested argument files (if recursion supported).

**Severity:** Fatal - prevents parsing from proceeding.

**Context provided:**

- **`file_chain`** - List of file paths showing the expansion chain
- **`depth`** - Current recursion depth
- **`max_depth`** - Maximum allowed depth from configuration
- **`cycle_detected`** - Boolean indicating if this is a circular reference
- **`command_name`** - Name of the command being parsed
- **`argv`** - Complete command-line arguments being parsed
- **`argument_index`** - Position of the initial @file token in argv

**When does this occur:**

- Argument files reference other files beyond `max_argument_file_depth`
- Circular reference detected: file A → file B → file A
- Deep nesting exceeds safety limits

**Examples:**

```python
# ❌ Argument file recursion depth exceeded
parser = Parser(spec, argument_file_prefix="@", max_argument_file_depth=2)

try:
    result = parser.parse(["@level1.args"])
    # level1.args contains @level2.args
    # level2.args contains @level3.args (exceeds depth limit)
except ArgumentFileRecursionError as e:
    # Error: Argument file recursion depth exceeded
    print(f"Chain: {e.file_chain}")              # ['level1.args', 'level2.args', 'level3.args']
    print(f"Depth: {e.depth}")                   # 3
    print(f"Max: {e.max_depth}")                 # 2
```

```python
# ❌ Circular argument file reference
try:
    result = parser.parse(["@circular1.args"])
    # circular1.args contains @circular2.args
    # circular2.args contains @circular1.args (cycle!)
except ArgumentFileRecursionError as e:
    # Error: Circular argument file reference detected
    print(f"Cycle: {e.cycle_detected}")          # True
    print(f"Chain: {e.file_chain}")              # ['circular1.args', 'circular2.args', 'circular1.args']
```

---

## Error context

Each error type carries structured context that enables higher-level components to format user-friendly error messages and provide helpful suggestions.

### Common context fields

Parse-time errors include standard context fields (unless not applicable):

| Field | Type | Description |
|:------|:-----|:------------|
| `argv` | `tuple[str, ...]` | Complete command-line arguments being parsed |
| `argument_index` | `int` | Index in argv where error occurred |
| `command_name` | `str` | Name of command being parsed |
| `subcommand_path` | `tuple[str, ...]` | Chain of parent→child subcommands |
| `severity` | `Severity` | Error severity level (defaults to ERROR) |

These fields enable error renderers to:

- Highlight exact failing token in original input
- Display full command context
- Filter errors by severity
- Support error chaining and enrichment

Individual error types define additional fields specific to their failure mode.

**All SpecificationError instances include:**

- **`message`** - Description of the specification violation
- **`specification_type`** - Type of spec that failed ("command", "option", "positional")
- **`specification`** - Reference to the spec object that failed

### Error message format

Error messages follow a consistent structure that is informative without assuming user expertise:

```text
<Error Type>: <Brief description> in command '<command_name>'
Context: <Details about what was expected vs. what was provided>
```

**Example error messages:**

```text
UnknownOptionError: Unknown option '--help' in command 'process'
Context: Valid options are: --verbose (-v), --input (-i), --output (-o)

AmbiguousOptionError: Ambiguous option '--ver' in command 'analyze'
Context: Matches multiple options: --verbose, --version

InsufficientValuesError: Option '--coords' requires 2 values in command 'plot'
Context: Received 1 value ('10'), but minimum is 2
Expected format: --coords X Y [Z]

ValueNotAllowedError: Flag '--verbose' does not accept values in command 'display'
Context: Attempted to provide value 'true' to flag option

DuplicateOptionError: Option '--once' cannot be specified multiple times in command 'unique'
Context: Occurrences at positions: 0, 2

UnexpectedArgumentError: Unexpected positional argument 'file3.txt' in command 'copy'
Context: All defined positionals have been satisfied (source='file1.txt', destination='file2.txt')
Note: Strict POSIX-style ordering is enabled (strict_options_before_positionals=True)
```

---

## Examples catalog

### Construction-time errors

#### Example 1: Specification with duplicate long option names

```python
# Scenario: Developer defines command with duplicate option names
try:
    spec = CommandSpecification(
        name="backup",
        options=(
            ValueOptionSpecification(name="source", long_names=frozenset({"source", "src"})),
            ValueOptionSpecification(name="dest", long_names=frozenset({"destination", "source"}))  # "source" duplicate!
        )
    )
except DuplicateNameError as e:
    print(f"Error: {e}")
    # Duplicate option long name 'source' in command 'backup'
    print(f"Duplicate names: {e.duplicates}")  # {'source'}
```

#### Example 2: Specification with invalid arity

```python
# Scenario: Developer creates option with invalid arity constraints
try:
    spec = CommandSpecification(
        name="calc",
        options=(
            ValueOptionSpecification(
                name="numbers",
                long_names=frozenset({"numbers"}),
                arity=Arity(10, 2)  # min > max!
            ),
        )
    )
except InvalidArityError as e:
    print(f"Error: {e}")
    # Minimum arity (10) cannot exceed maximum arity (2)
```

#### Example 3: Positional with invalid arity

```python
# Scenario: Developer creates positional with invalid arity constraints
try:
    spec = CommandSpecification(
        name="copy",
        positionals=(
            PositionalSpecification(
                name="files",
                arity=Arity(min=3, max=1)  # min > max!
            ),
        )
    )
except InvalidArityError as e:
    print(f"Error: {e}")
    # Minimum arity (3) cannot exceed maximum arity (1)
```

### Parse-time errors

#### Example 4: User specifies unknown option

```python
# Specification
spec = CommandSpecification(
    name="compile",
    options=(
        ValueOptionSpecification(name="output", short_names=frozenset({"o"}), long_names=frozenset({"output"})),
        FlagOptionSpecification(name="verbose", short_names=frozenset({"v"}), long_names=frozenset({"verbose"}))
    )
)
parser = Parser(spec)

# User command: compile --help
try:
    result = parser.parse(["--help"])
except UnknownOptionError as e:
    print(f"Error: {e}")
    # Unknown option '--help' in command 'compile'
    print(f"Option name: {e.option_name}")     # '--help'
    print(f"Valid options: {e.valid_options}") # ['-o', '--output', '-v', '--verbose']
```

#### Example 5: User provides ambiguous abbreviation

```python
# Specification with abbreviation support
spec = CommandSpecification(
    name="service",
    options=(
        FlagOptionSpecification(name="start", long_names=frozenset({"start"})),
        FlagOptionSpecification(name="stop", long_names=frozenset({"stop"})),
        FlagOptionSpecification(name="status", long_names=frozenset({"status"}))
    )
)
config = Configuration(allow_abbreviated_options=True, minimum_abbreviation_length=2)
parser = Parser(spec, config=config)

# User command: service --st (ambiguous - could be start, stop, or status)
try:
    result = parser.parse(["--st"])
except AmbiguousOptionError as e:
    print(f"Error: {e}")
    # Ambiguous option '--st' matches multiple options in command 'service'
    print(f"Abbreviation: {e.provided_abbreviation}")  # '--st'
    print(f"Matches: {[spec.name for spec in e.matched_options]}")
    # ['start', 'stop', 'status']
```

#### Example 6: Option with insufficient values

```python
# Specification requiring multiple values
spec = CommandSpecification(
    name="draw",
    options=(
        ValueOptionSpecification(
            name="rect",
            long_names=frozenset({"rect"}),
            arity=Arity(4, 4)  # Requires exactly 4 values
        ),
    )
)
parser = Parser(spec)

# User command: draw --rect 10 20 30 (only 3 values, needs 4)
try:
    result = parser.parse(["--rect", "10", "20", "30"])
except InsufficientValuesError as e:
    print(f"Error: {e}")
    # Option 'rect' requires 4 values but received 3 in command 'draw'
    print(f"Required: {e.required_minimum}")    # 4
    print(f"Received: {e.received_count}")      # 3
    print(f"Values: {e.values_received}")       # ('10', '20', '30')
```

#### Example 7: Flag with explicit value

```python
# Specification with flag option
spec = CommandSpecification(
    name="render",
    options=(
        FlagOptionSpecification(
            name="antialiasing",
            long_names=frozenset({"antialiasing"}),
        ),
    )
)
parser = Parser(spec)

# User command: render --antialiasing=true (flags do not accept values)
try:
    result = parser.parse(["--antialiasing=true"])
except ValueNotAllowedError as e:
    print(f"Error: {e}")
    # Flag 'antialiasing' does not accept values
    print(f"Option: {e.option_name}")           # 'antialiasing'
    print(f"Value: {e.provided_value}")         # 'true'
```

#### Example 8: Option with ERROR accumulation mode specified multiple times

```python
# Specification with ERROR accumulation mode
spec = CommandSpecification(
    name="deploy",
    options=(
        ValueOptionSpecification(
            name="environment",
            long_names=frozenset({"env"}),
            arity=Arity(1, 1),
            accumulation_mode=ValueAccumulationMode.ERROR
        ),
    )
)
parser = Parser(spec)

# User command: deploy --env staging --env production (duplicate option)
try:
    result = parser.parse(["--env", "staging", "--env", "production"])
except DuplicateOptionError as e:
    print(f"Error: {e}")
    # Option 'environment' cannot be specified more than once in command 'deploy'
    print(f"Indices: {e.indices}")  # (0, 2)
```

#### Example 9: Unexpected positional argument in strict mode

```python
# Specification with strict positional ordering
spec = CommandSpecification(
    name="backup",
    options=(
        FlagOptionSpecification(name="verbose", short_names=frozenset({"v"})),
    ),
    positionals=(
        PositionalSpecification(name="source", arity=Arity(1, 1)),
        PositionalSpecification(name="target", arity=Arity(1, 1))
    )
)
config = Configuration(strict_options_before_positionals=True)
parser = Parser(spec, config=config)

# User command: backup src.txt dest.txt extra.txt (too many positionals)
try:
    result = parser.parse(["src.txt", "dest.txt", "extra.txt"])
except UnexpectedArgumentError as e:
    print(f"Error: {e}")
    # Unexpected positional argument 'extra.txt' in command 'backup'
    print(f"Unexpected: {e.unexpected_argument}")  # 'extra.txt'
    print(f"Consumed: {e.consumed_positionals}")   # 2
    print(f"Defined: {e.defined_positionals}")     # ['source', 'target']
```

#### Example 10: Unknown subcommand

```python
# Specification with subcommands
spec = CommandSpecification(
    name="git",
    subcommands=(
        CommandSpecification(name="add"),
        CommandSpecification(name="commit"),
        CommandSpecification(name="push"),
        CommandSpecification(name="pull")
    )
)
parser = Parser(spec)

# User command: git fetch (subcommand not defined)
try:
    result = parser.parse(["fetch"])
except UnknownSubcommandError as e:
    print(f"Error: {e}")
    # Unknown subcommand 'fetch' in command 'git'
    print(f"Valid subcommands: {e.valid_subcommands}")
    # ['add', 'commit', 'push', 'pull']
```

#### Example 11: Insufficient positional arguments

```python
# Specification requiring positional arguments
spec = CommandSpecification(
    name="copy",
    positionals=(
        PositionalSpecification(name="source", arity=Arity(1, 1)),
        PositionalSpecification(name="destination", arity=Arity(1, 1))
    )
)
parser = Parser(spec)

# User command: copy file1.txt (missing destination)
try:
    result = parser.parse(["file1.txt"])
except InsufficientValuesError as e:
    print(f"Error: {e}")
    # Positional 'destination' requires 1 value but received 0 in command 'copy'
    print(f"Parameter type: {e.parameter_type}")   # 'positional'
    print(f"Required: {e.required_minimum}")       # 1
    print(f"Received: {e.received_count}")         # 0
```

---

## Error handling patterns

### Pattern 1: Catching specification errors during development

```python
# Developer pattern: catch errors during spec creation
from flagrant.exceptions import (
    SpecificationError,
    DuplicateNameError,
    InvalidArityError
)

def build_command_spec() -> CommandSpecification:
    try:
        return CommandSpecification(
            name="cli",
            options=(
                # Define options...
            )
        )
    except DuplicateNameError as e:
        # Handle duplicate name during development
        print(f"Configuration error: Duplicate {e.name_type} '{e.duplicates}'")
        raise
    except InvalidArityError as e:
        # Handle arity violation
        print(f"Configuration error: Invalid arity {e.arity}")
        raise
    except SpecificationError as e:
        # Catch any other specification errors
        print(f"Configuration error: {e}")
        raise
```

### Pattern 2: Handling parse errors for user feedback

```python
# User interaction pattern: catch and display parse errors nicely
from flagrant.exceptions import (
    ParseError,
    UnknownOptionError,
    AmbiguousOptionError,
    InsufficientValuesError
)

def parse_user_args(args: list[str]) -> ParseResult:
    try:
        return parser.parse(args)
    except UnknownOptionError as e:
        print(f"Error: Unknown option '{e.option_name}'")
        print(f"Valid options: {', '.join(e.valid_options)}")
    except AmbiguousOptionError as e:
        names = [spec.name for spec in e.matched_options]
        print(f"Error: Ambiguous option '{e.provided_abbreviation}'")
        print(f"Could mean: {', '.join(names)}")
    except InsufficientValuesError as e:
        print(f"Error: {e.parameter_name} needs {e.required_minimum} values")
        print(f"You provided {e.received_count}")
    except ParseError as e:
        print(f"Parse error: {e}")
```

### Pattern 3: Construction error recovery

```python
# Framework pattern: provide helpful error context
from flagrant.exceptions import SpecificationError

def safe_spec_builder(spec_dict: dict) -> CommandSpecification | None:
    try:
        options = tuple(
            ValueOptionSpecification(
                name=opt["name"],
                long_names=frozenset(opt.get("long_names", ())),
                short_names=frozenset(opt.get("short_names", ()))
            )
            for opt in spec_dict.get("options", [])
        )
        return CommandSpecification(
            name=spec_dict["name"],
            options=options
        )
    except SpecificationError as e:
        error_context = {
            "spec_file": spec_dict.get("_source"),
            "error": str(e),
            "error_type": type(e).__name__
        }
        log_configuration_error(error_context)
        return None
```

---

## Error extensibility

The error hierarchy can be extended to support domain-specific error types while maintaining compatibility with the base exception structure.

**Guidelines for extending:**

1. All custom errors MUST extend from a base exception in the hierarchy
2. Custom errors SHOULD include relevant context fields
3. Error messages MUST follow the established format
4. Construction-time errors extend `SpecificationError`
5. Parse-time errors extend `ParseError`

**Example: Custom validation error**

```python
class RequiredOptionMissingError(ParseError):
    """Raised when a required option is not provided during parsing."""

    def __init__(
        self,
        option_name: str,
        command_name: str,
        required_because: str | None = None
    ):
        self.option_name = option_name
        self.command_name = command_name
        self.required_because = required_because

        message = (
            f"Required option '{option_name}' not provided "
            f"in command '{command_name}'"
        )
        if required_because:
            message += f" ({required_because})"

        super().__init__(message)
```
