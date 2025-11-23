# Glossary

--8<-- "unreleased.md"

This glossary defines key terms used throughout Flagrant documentation. Terms are organized alphabetically for quick reference. Each entry provides a concise definition with cross-references to related concepts where helpful.

## Table of contents

- [A](#a)
- [B](#b)
- [C](#c)
- [D](#d)
- [E](#e)
- [F](#f)
- [G](#g)
- [H](#h)
- [I](#i)
- [K](#k)
- [L](#l)
- [M](#m)
- [N](#n)
- [O](#o)
- [P](#p)
- [R](#r)
- [S](#s)
- [T](#t)
- [U](#u)
- [V](#v)
- [See also](#see-also)

---

## A

### Abbreviation matching

A name resolution strategy that allows users to specify unambiguous prefixes of option or subcommand names instead of full names. For example, `--verb` matches `--verbose` if no other option starts with "verb." Controlled by `allow_abbreviated_options` and `allow_abbreviated_subcommands` configuration flags with a minimum abbreviation length (default: 3 characters).

See also: [Option resolution](#option-resolution), [Name resolution](#name-resolution)

### Accumulation mode

A strategy defining how the parser combines multiple occurrences of the same option. Flag options support FIRST, LAST, COUNT, and ERROR modes. Value options support FIRST, LAST, APPEND, EXTEND, and ERROR modes. Dictionary options support MERGE, FIRST, LAST, APPEND, and ERROR modes.

    Flag accumulation: COUNT increments an integer counter, LAST keeps the final boolean value, FIRST keeps the initial value, ERROR raises an exception on duplicates.

    Value accumulation: APPEND creates nested tuples preserving per-occurrence grouping, EXTEND flattens all values into a single tuple, LAST keeps the final values, FIRST keeps the initial values, ERROR raises an exception.

    Dictionary accumulation: MERGE combines dictionaries according to merge strategy (SHALLOW or DEEP), APPEND creates a tuple of separate dictionaries, LAST keeps the final dictionary, FIRST keeps the initial dictionary, ERROR raises an exception.

    See also: [Merge strategy](#merge-strategy), [Arity](#arity)

### Argument

A string provided on the command line by the user. Arguments are classified during parsing as options, positionals, subcommands, or trailing arguments based on their syntactic structure and position.

    See also: [Argument classification](#argument-classification), [Positional argument](#positional-argument)

### Argument classification

The process of categorizing raw command-line argument strings into syntactic types: long options (starting with `--`), short options (starting with `-`), positionals, subcommands, or trailing arguments (after `--` separator). Classification occurs during a single left-to-right pass through the argument array.

    See also: [Long option](#long-option), [Short option](#short-option), [Positional argument](#positional-argument)

### Argument file

An external file containing command-line arguments referenced using a prefix (default `@`). When the parser encounters an argument like `@config.txt`, it reads the file's contents and expands them inline at that position. Also known as response files or @-files.

    Argument files support line-based format where each non-empty, non-comment line becomes a single argument. Recursion depth is configurable to prevent circular references. The prefix character can be customized or disabled entirely.

    See also: [Trailing arguments](#trailing-arguments)

### Arity

The number of values a parameter (option or positional) accepts, expressed as a tuple `(min, max)` where `min` is the minimum required values and `max` is the maximum allowed values (or `None` for unbounded).

    Common patterns: `(0, 0)` for flags, `(1, 1)` for single values, `(2, 2)` for exactly two values, `(1, None)` for one-or-more values, `(0, None)` for zero-or-more values.

    Arity determines both validation constraints (minimum values required) and result structure (scalar string vs tuple of strings).

    See also: [Greedy consumption](#greedy-consumption), [Positional grouping](#positional-grouping)

## B

### Bounded arity

An arity specification where the maximum value is a specific integer rather than unbounded (None). For example, `(2, 5)` accepts between 2 and 5 values. Bounded arity parameters stop consuming values after reaching the maximum, even if more arguments are available.

    See also: [Arity](#arity), [Unbounded arity](#unbounded-arity)

## C

### Canonical name

The primary identifier for an option or command, used as the key in parse results. All aliases, short names, long names, and abbreviations resolve to the same canonical name for consistent access.

    For example, an option with long names `{"output", "out"}` and short name `"o"` has a single canonical name "output" that appears in parse results regardless of which form the user specified.

    See also: [Option resolution](#option-resolution), [Alias resolution](#alias-resolution)

### Case sensitivity

Configuration controlling whether option names, command names, and dictionary keys match case-sensitively or case-insensitively. When case-insensitive matching is enabled, all case variations of a name are accepted and normalized to the canonical form.

    Three independent flags control case sensitivity: `case_sensitive_options` for option names, `case_sensitive_commands` for subcommand names, and `case_sensitive_keys` for dictionary keys.

    See also: [Name resolution](#name-resolution), [Option resolution](#option-resolution)

### Command specification

An immutable data structure defining the complete structure of a command or subcommand, including options, positionals, nested subcommands, and their relationships. Specifications are validated at construction time to ensure correctness before any parsing occurs.

    Command specifications form hierarchical trees where each subcommand has its own complete specification with independent options, positionals, and further subcommands.

    See also: [Option specification](#option-specification), [Positional specification](#positional-specification), [Specification](#specification)

### Configuration

Settings that control parser behavior such as option resolution strategies, positional ordering modes, negative number handling, and argument file processing. Configuration is provided when constructing a parser instance and is immutable thereafter.

    Many configuration properties can be overridden at the option level. When an option specification defines its own value for a configuration property, that value takes precedence over the global configuration.

    See also: [Construction-time validation](#construction-time-validation), [Parse-time validation](#parse-time-validation)

### Configuration error

An exception raised during parser or completer initialization when configuration values violate constraints. For example, setting `minimum_abbreviation_length` to 0 raises a configuration error because the minimum must be at least 1.

    See also: [Specification error](#specification-error), [Parse error](#parse-error)

### Construction-time validation

Validation that occurs when creating specification objects, catching structural configuration errors before any parsing begins. Construction-time validation raises `SpecificationError` for invalid specifications (duplicate option names, invalid arity constraints, conflicting configurations) and `ConfigurationError` for invalid parser configuration.

    This fail-fast approach catches configuration errors immediately with detailed messages, rather than discovering problems during parsing.

    See also: [Parse-time validation](#parse-time-validation), [Specification error](#specification-error)

## D

### Dictionary option

An option specification that parses key-value pairs into dictionary structures with support for nested dictionaries and lists using dot notation (`database.host=localhost`) and bracket notation (`servers[0]=web1`).

    Dictionary options use `DictOptionSpecification` with type-specific accumulation modes (MERGE, FIRST, LAST, APPEND, ERROR) and merge strategies (SHALLOW, DEEP) for combining multiple occurrences.

    See also: [Merge strategy](#merge-strategy), [Nesting separator](#nesting-separator), [Key-value separator](#key-value-separator)

## E

### End-of-options delimiter

The standalone `--` argument that terminates option parsing entirely. All arguments following `--` are placed in a separate trailing arguments collection without interpretation or parsing.

    This enables passing arbitrary strings (including option-like arguments) to subprocesses or using option-like strings as data without ambiguity.

    See also: [Trailing arguments](#trailing-arguments), [POSIX-style ordering](#posix-style-ordering)

## F

### Flag option

An option specification representing boolean presence/absence with arity `(0, 0)`. Flags have value `True` when present, `False` when negated using negation prefixes, or an integer count when using COUNT accumulation mode.

    Flag options are specified using `FlagOptionSpecification` with type-specific accumulation modes (FIRST, LAST, COUNT, ERROR) and support for negation through prefixes (for long names) or negation short names.

    See also: [Negation](#negation), [Accumulation mode](#accumulation-mode), [Option specification](#option-specification)

### Flagrant error

The base exception class for all errors raised by the Flagrant library. All Flagrant exceptions extend `FlagrantError`, enabling applications to catch all Flagrant errors with a single handler.

    The `FlagrantError` base class provides a `message` field with a human-readable error description and a `context` dictionary for structured information about the error.

    See also: [Specification error](#specification-error), [Parse error](#parse-error), [Configuration error](#configuration-error)

## G

### Greedy consumption

A value consumption mode where an option consumes all remaining arguments until reaching the end of the argument list or the `--` separator, ignoring normal stopping conditions like option-like arguments or subcommand names.

    Greedy consumption is useful for wrapper commands that pass arbitrary arguments to subprocesses. Controlled by the `greedy` field on value and dictionary option specifications.

    Non-greedy consumption (the default) stops at natural boundaries like other options or subcommand names, allowing options and positionals to be intermixed.

    See also: [Arity](#arity), [Value consumption](#value-consumption), [Trailing arguments](#trailing-arguments)

## H

### Hierarchical composition

The organization of command specifications into tree structures where subcommands are nested within parent commands. Each level of the hierarchy maintains completely isolated namespaces for options, positionals, and nested subcommands.

    For example, `git remote add` represents a three-level hierarchy: the root `git` command, the `remote` subcommand, and the `add` nested subcommand.

    See also: [Command specification](#command-specification), [Subcommand](#subcommand), [Namespace isolation](#namespace-isolation)

## I

### Immutability

The architectural guarantee that all specification objects, parse results, and configurations are immutable after construction. Once created and validated, these objects cannot be modified.

    Immutability enables thread safety without synchronization, aggressive caching of derived computations, and simpler reasoning about program behavior. Specifications can be safely shared across threads and parser instances can be reused concurrently.

    See also: [Construction-time validation](#construction-time-validation), [Specification](#specification)

### Inline value syntax

Syntax for providing option values within the same argument as the option name. Long options use equals syntax (`--option=value`), while short options support both equals (`-o=value`) and concatenated syntax (`-ovalue`).

    Inline values provide exactly one value regardless of the option's maximum arity. For options requiring multiple values, inline syntax with a single value raises an error.

    See also: [Long option](#long-option), [Short option](#short-option), [Value consumption](#value-consumption)

## K

### Key-value separator

The character separating keys from values in dictionary option syntax (default `=`). Used in dictionary arguments like `database.host=localhost` where the separator is between "database.host" and "localhost."

    The key-value separator can be customized globally via `Configuration.key_value_separator` or per-option via `DictOptionSpecification.key_value_separator`.

    See also: [Dictionary option](#dictionary-option), [Nesting separator](#nesting-separator)

## L

### Long option

An option specified with a multi-character name prefixed by `--` (configurable). Long option names must be at least one character and can contain alphabetic characters, digits, dashes, and underscores.

    Long options support equals syntax for value assignment (`--output=file.txt`) and can have multiple long names serving as aliases that all resolve to the same canonical option.

    See also: [Short option](#short-option), [Inline value syntax](#inline-value-syntax), [Option resolution](#option-resolution)

## M

### Merge strategy

Controls how dictionaries are combined when `DictAccumulationMode.MERGE` accumulation mode is used. SHALLOW performs shallow merge where only top-level keys are combined (last value for duplicate keys wins). DEEP performs deep merge that recursively combines nested dictionary structures (default).

    Merge strategy only applies when accumulation mode is MERGE. Other accumulation modes (FIRST, LAST, APPEND, ERROR) ignore this setting.

    See also: [Dictionary option](#dictionary-option), [Accumulation mode](#accumulation-mode)

## N

### Name resolution

The process of matching user-provided option or subcommand names to their canonical specifications. Resolution strategies include exact matching (always enabled), alias resolution, abbreviation matching, case-insensitive matching, and underscore-to-dash conversion.

    Resolution strategies are compositional configuration flags that can be independently enabled or disabled. When multiple strategies could apply, the parser uses the most specific match available.

    See also: [Option resolution](#option-resolution), [Abbreviation matching](#abbreviation-matching), [Canonical name](#canonical-name)

### Namespace isolation

The architectural principle that each command maintains completely isolated namespaces for options, positionals, and subcommands. A parent command's options do not propagate to child commands, and child options do not affect the parent.

    This isolation prevents naming conflicts and allows each command level to define its interface independently. Options with the same name can exist at different command levels with different semantics.

    See also: [Hierarchical composition](#hierarchical-composition), [Command specification](#command-specification)

### Negation

For flag options, the ability to explicitly set a flag to false using negation prefixes (for long names) or negation short names. With negation prefix "no," the flag `--verbose` can be negated using `--no-verbose`.

    Negation is configured per-option via `FlagOptionSpecification.negation_prefixes` (for long names) and `FlagOptionSpecification.negation_short_names` (for short names). Each negation prefix word creates a valid negated form.

    See also: [Flag option](#flag-option), [Option resolution](#option-resolution)

### Nesting separator

The character indicating nested dictionary keys in dot notation (default `.`). Used in dictionary arguments like `database.host=localhost` where dots separate nesting levels.

    The nesting separator can be customized globally via `Configuration.nesting_separator` or per-option via `DictOptionSpecification.nesting_separator`. Escaped separators become literal characters in keys.

    See also: [Dictionary option](#dictionary-option), [Key-value separator](#key-value-separator)

## O

### Option

A named parameter that accepts zero or more values, recognized by prefix characters: `--` introduces long-form names, while `-` introduces short-form names. An option can have multiple long names, multiple short names, or both.

    Flagrant supports three option types: flags (boolean presence/absence), value options (accepting string values), and dictionary options (parsing key-value pairs).

    See also: [Long option](#long-option), [Short option](#short-option), [Option specification](#option-specification)

### Option resolution

The process of matching user-provided option names to canonical option specifications using configured resolution strategies. Strategies include exact matching, alias resolution, abbreviation matching, negation resolution, case-insensitive matching, and underscore-to-dash conversion.

    Resolution strategies are compositional and combine to produce rich matching behavior. The parser resolves names using the most specific match available, with exact matches taking precedence over abbreviations.

    See also: [Name resolution](#name-resolution), [Abbreviation matching](#abbreviation-matching), [Canonical name](#canonical-name)

### Option specification

An immutable data structure defining a named parameter including its names (long and short forms), arity constraints, accumulation mode, and type-specific behaviors. Option specifications use a three-tier hierarchy:

    - `FlagOptionSpecification` for boolean flags with negation and counting
    - `ValueOptionSpecification` for options accepting string values
    - `DictOptionSpecification` for options parsing key-value pairs

    See also: [Flag option](#flag-option), [Value option](#value-option), [Dictionary option](#dictionary-option), [Specification](#specification)

## P

### Parse error

An exception raised during argument processing when user input violates specification constraints. Parse errors represent user input mistakes rather than configuration problems.

    Parse errors provide structured context including the command path, full argument array, position where the error occurred, and error-specific details (option name, required arity, actual values received). This context enables higher-level frameworks to format user-friendly error messages.

    See also: [Specification error](#specification-error), [Parse-time validation](#parse-time-validation)

### Parser

The low-level parsing engine that transforms command-line arguments into structured parse results through a single-pass, left-to-right algorithm. The parser handles syntactic parsing only—it classifies arguments, assigns values, enforces arity constraints, and detects structural errors.

    The parser does not perform type conversion, validation beyond structure, default value assignment, or semantic interpretation. These are responsibilities of higher-level frameworks like Aclaf.

    See also: [Parse result](#parse-result), [Specification-driven](#specification-driven)

### Parse result

The immutable structured output from parsing containing the canonical command name, options dictionary (keyed by canonical option names), positionals dictionary (keyed by positional spec names), any trailing arguments, and a reference to the subcommand parse result if a subcommand was invoked.

    All option and positional values are strings or tuples of strings—the parser performs no type conversion. Parse results can be safely shared across threads and cached aggressively.

    See also: [Parser](#parser), [Immutability](#immutability)

### Parse-time validation

Validation that occurs during argument processing when user input violates specification constraints. Parse-time validation raises `ParseError` for user input problems such as unknown options, insufficient values for arity requirements, ambiguous abbreviations, or duplicate options with ERROR accumulation mode.

    Parse-time errors represent user mistakes rather than configuration problems, and include structured context for error rendering.

    See also: [Construction-time validation](#construction-time-validation), [Parse error](#parse-error)

### Positional argument

An argument identified by its position in the command line rather than by a prefix or name. Positionals are collected during parsing and grouped according to positional specifications after option processing completes.

    Arguments are positional if they don't start with `-` (unless it's the single dash `-`), don't match subcommand names, haven't been consumed as option values, and don't appear after the `--` delimiter.

    See also: [Positional specification](#positional-specification), [Positional grouping](#positional-grouping)

### Positional grouping

The algorithm that distributes collected positional arguments to named positional parameters according to their arity constraints. The algorithm processes specs left-to-right, ensuring later positionals with minimum requirements receive sufficient values while allowing earlier unbounded positionals to consume as much as possible.

    For each positional spec, the algorithm calculates how many values are needed by following specs, determines available values, consumes up to maximum arity or all available values (whichever is less), and assigns consumed values to the named positional.

    See also: [Positional argument](#positional-argument), [Arity](#arity)

### Positional specification

An immutable data structure defining a parameter identified by position rather than name. Each positional spec contains a name (for identifying in parse results), arity constraints controlling value consumption, and optional greedy flag.

    Positional specs define strict ordering within a command. The parser assigns arguments to positionals left-to-right based on arity constraints using the positional grouping algorithm.

    See also: [Positional argument](#positional-argument), [Positional grouping](#positional-grouping), [Specification](#specification)

### POSIX-style ordering

A parsing mode (enabled via `strict_posix_options=True`) requiring all options to precede all positional arguments. Once the first positional is encountered, all subsequent arguments are treated as positionals even if they structurally look like options.

    This mode enables commands to accept option-like strings as positional values without ambiguity, following POSIX.2 conventions for traditional Unix utilities.

    See also: [Positional argument](#positional-argument), [End-of-options delimiter](#end-of-options-delimiter)

## R

### Resolution

See [Name resolution](#name-resolution) and [Option resolution](#option-resolution).

## S

### Short option

An option specified with a single-character name prefixed by `-` (configurable). Short options can be combined (clustered) in a single argument like `-abc` representing three separate flags.

    Short options support attached values (`-ovalue`), equals syntax (`-o=value`), and space-separated values (`-o value`). All options except the last in a cluster must be flags.

    See also: [Long option](#long-option), [Short option clustering](#short-option-clustering), [Inline value syntax](#inline-value-syntax)

### Short option clustering

The ability to combine multiple short options in a single argument. For example, `-abc` expands to three separate short options `-a`, `-b`, and `-c`. All options except the last must be flags (arity `(0, 0)` or is_flag=True).

    Only the last option in a cluster can accept values, either through attached syntax (`-abcvalue`), equals syntax (`-abc=value`), or space-separated syntax (`-abc value`).

    See also: [Short option](#short-option), [Flag option](#flag-option)

### Single-pass parsing

The architectural constraint that the parser processes arguments in exactly one left-to-right pass through the argument array with no backtracking, speculation, or multi-pass analysis. Each argument is classified and processed immediately based on current state and the specification.

    Single-pass parsing provides O(n) linear complexity, deterministic behavior, and predictable performance without pathological inputs.

    See also: [Parser](#parser), [Argument classification](#argument-classification)

### Specification

An immutable data structure that captures all information needed to parse command-line arguments. Specifications define the expected structure (commands, options, positionals, subcommands), behavioral rules (arity, accumulation modes, negation), and validation constraints.

    Specifications are validated at construction time to ensure correctness before parsing begins. The specification model serves as the single source of truth for parsing behavior.

    See also: [Command specification](#command-specification), [Option specification](#option-specification), [Positional specification](#positional-specification)

### Specification-driven

The architectural approach where all parser behavior is configured through declarative specifications rather than imperative code or runtime introspection. The specification completely defines what the parser accepts and how it processes arguments.

    This approach enables static analysis of CLI structure, serialization for documentation generation, construction-time validation, and clear separation between CLI structure (specification) and runtime behavior (parser).

    See also: [Specification](#specification), [Construction-time validation](#construction-time-validation)

### Specification error

An exception raised when constructing command specifications that violate structural or semantic constraints. Specification errors prevent invalid specifications from reaching the parser by failing fast during initialization.

    Common specification errors include duplicate option names, invalid arity constraints (min > max, negative values), malformed option names, and conflicting configurations. All specification errors are detected at construction time before any parsing begins.

    See also: [Construction-time validation](#construction-time-validation), [Parse error](#parse-error)

### Subcommand

A nested command within a parent command, creating hierarchical command structures. Each subcommand has its own complete specification with independent options, positionals, and further subcommands.

    When the parser encounters a subcommand name, it builds the parent command's parse result with accumulated options and positionals, then delegates remaining arguments to recursive parsing using the subcommand's specification.

    See also: [Hierarchical composition](#hierarchical-composition), [Command specification](#command-specification), [Namespace isolation](#namespace-isolation)

### Subcommand resolution

The process of matching positional arguments against defined subcommand names. When a match is found, the parser delegates remaining arguments to recursive parsing using the subcommand's specification.

    Subcommand resolution applies similar strategies to option resolution: exact name matching, alias resolution, abbreviation matching (if enabled), and case-insensitive matching (if enabled).

    See also: [Name resolution](#name-resolution), [Subcommand](#subcommand)

## T

### Trailing arguments

Arguments appearing after the standalone `--` delimiter. These arguments are preserved without interpretation and stored separately in parse results, useful for passing arbitrary arguments to subprocesses or disambiguating option-like values.

    The `--` separator terminates option parsing entirely. All following arguments bypass normal classification and are placed in a trailing arguments collection.

    See also: [End-of-options delimiter](#end-of-options-delimiter), [Positional argument](#positional-argument)

### Type safety

Flagrant maintains comprehensive type hints throughout the codebase, validated by basedpyright in strict mode. All public APIs and internal code have complete type annotations, enabling IDE autocomplete, type checking during development, and safe large-scale refactoring.

    Type hints serve as machine-checked documentation that catches bugs early during development rather than at runtime.

    See also: [Immutability](#immutability), [Parse result](#parse-result)

## U

### Unbounded arity

An arity specification where the maximum value is `None`, allowing the parameter to consume as many values as possible. For example, `(1, None)` requires at least one value but accepts unlimited values.

    Unbounded parameters stop consuming values when encountering stopping conditions: another option, a subcommand name, the end-of-options delimiter `--`, or the end of arguments. With greedy consumption, unbounded parameters consume all remaining arguments.

    See also: [Arity](#arity), [Greedy consumption](#greedy-consumption), [Positional grouping](#positional-grouping)

### Underscore-to-dash conversion

Name normalization that treats underscores and dashes interchangeably in option and command names (enabled by `convert_underscores=True` by default). This bridges Python's snake_case naming conventions with CLI's kebab-case conventions.

    With conversion enabled, `--output-file` and `--output_file` both match the same option specification, regardless of whether it was defined with dashes or underscores.

    See also: [Name resolution](#name-resolution), [Option resolution](#option-resolution)

## V

### Value consumption

The algorithm that collects argument values from the remaining argument stream for options and positionals according to their arity constraints. Value consumption stops when reaching maximum arity, encountering another option or subcommand, or exhausting available arguments.

    After collecting values, the parser validates that the count satisfies minimum arity requirements. Insufficient values raise an error identifying the parameter and arity violation.

    See also: [Arity](#arity), [Greedy consumption](#greedy-consumption)

### Value option

An option specification that accepts one or more string values according to its arity. Values can be accumulated across multiple occurrences using APPEND (preserving per-occurrence grouping) or EXTEND (flattening into single tuple) modes.

    Value options are specified using `ValueOptionSpecification` with type-specific accumulation modes (FIRST, LAST, APPEND, EXTEND, ERROR), arity constraints, and optional greedy consumption.

    See also: [Option specification](#option-specification), [Accumulation mode](#accumulation-mode), [Arity](#arity)

---

## See also

For more detailed information about these concepts, see:

- **[Concepts guide](../explanation/concepts.md)**: Detailed explanations of core concepts including arity, accumulation modes, option resolution, and positional grouping with extensive examples
- **[Architecture](../explanation/architecture.md)**: Overall system architecture, design philosophy, and component relationships
- **[Parser behavior](../explanation/behavior.md)**: Detailed parsing algorithms including value consumption and positional grouping with worked examples
- **[Grammar specification](../explanation/grammar.md)**: Formal syntax rules and argument classification grammar
- **[Configuration](../explanation/configuration.md)**: Complete reference for parser configuration options and modes
- **[Error handling](../explanation/errors.md)**: Complete error hierarchy, validation rules, and structured exception details
