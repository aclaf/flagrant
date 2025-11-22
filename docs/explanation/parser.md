# The parser

This guide explains Flagrant's parser design, capabilities, and integration within the Flagrant ecosystem. It covers what the parser does, what it doesn't do, and how it fits with other components.

## Table of contents

- [Glossary of terms](#glossary-of-terms)
- [Purpose](#purpose)
- [Quick start example](#quick-start-example)
- [What the parser does](#what-the-parser-does)
- [What the parser does not do](#what-the-parser-does-not-do)
- [Design constraints](#design-constraints)
- [Architectural principles](#architectural-principles)
- [Core capabilities](#core-capabilities)
- [Integration with Flagrant ecosystem](#integration-with-flagrant-ecosystem)

---

## Glossary of terms

This glossary defines key terminology used throughout the parser documentation. Terms are organized alphabetically for quick reference.

**Abbreviation matching:** A name resolution strategy that allows users to specify unambiguous prefixes of option or subcommand names instead of full names. For example, `--verb` matches `--verbose` if no other option starts with "verb". Controlled by `allow_abbreviated_options` and `allow_abbreviated_subcommands` configuration flags.

**Accumulation mode:** A strategy defining how multiple occurrences of the same option are combined. Flag options support FIRST, LAST, COUNT, and ERROR modes. Value options support FIRST, LAST, APPEND, EXTEND, and ERROR modes. Dictionary options support MERGE, FIRST, LAST, APPEND, and ERROR modes. See the [concepts guide](concepts.md) for detailed semantics.

**Arity:** The number of values a parameter (option or positional) accepts, expressed as a tuple `(min, max)` where `min` is the minimum required values and `max` is the maximum allowed values (or `None` for unbounded). Common patterns include `(0, 0)` for flags, `(1, 1)` for single values, and `(1, None)` for one-or-more values.

**Argument classification:** The process of categorizing raw command-line argument strings into syntactic types: long options (starting with `--`), short options (starting with `-`), positionals, subcommands, or trailing arguments (after `--` separator).

**Canonical name:** The primary identifier for an option or command, used as the key in parse results. All aliases, short names, long names, and abbreviations resolve to the same canonical name for consistent access.

**Dictionary option:** An option specification that parses key-value pairs into dictionary structures with support for nested dictionaries and lists using dot notation and bracket notation. Specified using `DictOptionSpecification`.

**Flag option:** An option specification representing boolean presence/absence with arity `(0, 0)`. Flags have value `True` when present, `False` when negated, or an integer count when using COUNT accumulation mode. Specified using `FlagOptionSpecification`.

**Greedy consumption:** A value consumption mode where an option consumes all remaining arguments until reaching the end of the argument list or the `--` separator, ignoring normal stopping conditions like option-like arguments or subcommand names. Controlled by the `greedy` field on option specifications.

**Inline value syntax:** Syntax for providing option values within the same argument as the option name. Long options use equals syntax (`--option=value`), while short options support both equals (`-o=value`) and concatenated syntax (`-ovalue`).

**Long option:** An option specified with a multi-character name prefixed by `--` (configurable). Long option names must be at least 2 characters. Examples: `--verbose`, `--output-file`.

**Negation:** For flag options, the ability to explicitly set a flag to false using negation prefixes (for long names) or negation short names. For example, with negation prefix "no", the flag `--verbose` can be negated using `--no-verbose`.

**Option resolution:** The process of matching user-provided option names to canonical option specifications. Resolution strategies include exact matching, alias resolution, abbreviation matching, case-insensitive matching, and underscore-to-dash conversion.

**Positional argument:** An argument identified by its position in the command line rather than by a prefix or name. Positionals are collected during parsing and grouped according to positional specifications after option processing completes.

**Positional grouping:** The algorithm that distributes collected positional arguments to named positional parameters according to their arity constraints, ensuring later positionals with minimum requirements receive sufficient values while allowing earlier unbounded positionals to consume as much as possible.

**POSIX-style ordering:** A parsing mode (enabled via `strict_options_before_positionals=True`) requiring all options to precede all positional arguments. Once the first positional is encountered, all subsequent arguments are treated as positionals even if they look like options.

**Resolution:** See "Option resolution" and "Subcommand resolution".

**Short option:** An option specified with a single-character name prefixed by `-` (configurable). Short options can be combined (clustered) in a single argument like `-abc` representing three separate flags. Examples: `-v`, `-o`.

**Short option clustering:** The ability to combine multiple short options in a single argument. For example, `-abc` expands to three separate short options `-a`, `-b`, and `-c`. All options except the last must be flags or have arity `(0, 0)`.

**Specification:** An immutable data structure defining the expected structure of a command, option, or positional parameter. Command specifications contain options, positionals, and subcommands. Option specifications define names, arity, and accumulation modes. See the [types guide](types.md).

**Strict dictionary structure:** A validation mode (controlled by `strict_structure` field) that enforces strict adherence to expected dictionary structure during parsing, rejecting ambiguous or malformed key-value assignments.

**Subcommand:** A nested command within a parent command, creating hierarchical command structures. Each subcommand has its own complete specification with independent options, positionals, and further subcommands. Examples: `git remote add`, `docker container run`.

**Subcommand resolution:** The process of matching positional arguments against defined subcommand names. When a match is found, the parser delegates remaining arguments to recursive parsing using the subcommand's specification.

**Trailing arguments:** Arguments appearing after the standalone `--` delimiter. These arguments are preserved without interpretation and stored separately in parse results, useful for passing arbitrary arguments to subprocesses or disambiguating option-like values.

**Value option:** An option specification that accepts one or more string values according to its arity. Values can be accumulated across multiple occurrences using APPEND or EXTEND modes. Specified using `ValueOptionSpecification`.

---

## Purpose

The Flagrant parser is a high-performance, specification-driven command-line argument parser designed for correctness, flexibility, and strict separation of concerns. Its singular purpose is syntactic analysis: transforming raw command-line argument strings into structured data representations without performing any semantic interpretation, validation, or type conversion.

The parser operates on simple inputs and produces simple outputs. It accepts an array of strings (typically `sys.argv[1:]`) and a command specification that describes the expected structure. It produces an immutable parse result containing classified arguments, resolved option names, grouped positional values, and nested subcommand results. Everything in between these inputs and outputs focuses on one question: what did the user type, and how does it map to the defined command structure?

This narrow focus enables the parser to excel at what it does while remaining composable with higher-level components. Flagrant's completer shares the same specification model to generate shell completions. Aclaf builds on the parser's output to provide type conversion, validation, default value management, and command execution. Each component has a clear responsibility, and the parser's responsibility is purely syntactic.

## Quick start example

A concrete example demonstrates the parser's role in transforming user input into structured data.

**User invocation:**

```bash
build --output dist/ --verbose src/main.py src/utils.py
```

**Command specification:**

The command specification defines the structure expected by the parser:

- Command name: "build"
- Value option named "output" with long name "output" and arity (1, 1) requiring exactly one value
- Flag option named "verbose" with long name "verbose" and arity (0, 0) accepting no values
- Positional parameter named "files" with arity (1, None) requiring at least one value but accepting unlimited values

**Parsing and result:**

The parser processes the argument sequence and produces a structured parse result:

- Command: "build"
- Original arguments preserved: `('build', '--output', 'dist/', '--verbose', 'src/main.py', 'src/utils.py')`
- Options dictionary containing:
  - 'output' → 'dist/' (string value)
  - 'verbose' → True (boolean flag)
- Positionals dictionary containing:
  - 'files' → ('src/main.py', 'src/utils.py') (tuple of strings)
- Subcommand: None (no subcommand invoked)

**What happened:**

The parser recognized `build` as the command name matching the specification. It identified `--output` as a long option and consumed `dist/` as its single required value based on arity `(1, 1)`. It identified `--verbose` as a flag option with arity `(0, 0)` and set its value to `True` since flags represent boolean presence. It collected `src/main.py` and `src/utils.py` as positional arguments and grouped them under the `files` parameter according to its arity specification `(1, None)` which requires at least one value but accepts unlimited values. All string values remained as strings in the result; the parser performed no type conversion.

**What the parser did not do:**

The parser did not verify that `dist/` is a valid directory path or that the source files exist on disk. It did not convert the verbose flag into a logging level configuration or integrate it with any logging system. It did not apply any default values for options that were not specified on the command line. It did not generate help text, usage strings, or user-facing error messages. It focused exclusively on syntactic analysis—understanding the structure of what the user typed and organizing it into a format that application code can process.

**Using the parse result:**

Application code accesses parsed values through the structured result interface. Option values are available in the options dictionary keyed by option name. Positional values are available in the positionals dictionary keyed by positional name. The parse result provides methods for retrieving values with default fallbacks when options were not specified. Subcommand results are accessible through the subcommand field, which contains a nested parse result when a subcommand was invoked or None otherwise.

The immutable parse result provides a clean interface for retrieving values that higher-level components can then validate, convert to appropriate types, and use for command execution.

## What the parser does

The parser's responsibilities center on syntactic analysis and structural validation. It classifies arguments, assigns values, enforces arity constraints, handles accumulation, resolves names, and detects structural errors.

### Argument classification

The parser classifies raw argument strings into syntactic categories based on their structure and position. Long options start with `--` and are parsed as complete option names like `--verbose` or `--output`. Short options start with `-` followed by a single character like `-v` or `-o`, and can be combined like `-abc` which parses as three separate flags `-a`, `-b`, and `-c`. Positional arguments are identified by not being options, not matching subcommand names, and not appearing after the `--` separator. Subcommands are special positional arguments that match defined subcommand names and trigger delegation to nested command specifications. Trailing arguments appear after the standalone `--` delimiter and are preserved without interpretation, useful for passing arguments to subprocesses or disambiguating option-like values.

Classification happens during a single left-to-right pass through the argument array. The parser maintains state about what it has seen and makes classification decisions immediately without backtracking or speculation.

See the [grammar guide](grammar.md) for the complete formal grammar defining argument classification rules and syntactic structures.

### Value assignment and arity enforcement

Options and positionals consume values according to their arity specifications. Arity defines both a minimum and maximum number of values a parameter accepts, expressed as a tuple `(min, max)` where `max` can be `None` for unbounded parameters.

The parser assigns values by consuming arguments following an option or positional until reaching the maximum arity, encountering another option or subcommand, or exhausting available arguments. For flag options with arity `(0, 0)`, the parser assigns boolean `True` when the flag is present. For options with arity `(1, 1)`, the parser consumes exactly one following argument as the option's value. For options with arity `(2, 2)`, the parser consumes exactly two arguments as a tuple. For unbounded options with arity `(1, None)`, the parser consumes all following arguments until hitting another option or subcommand boundary.

After consuming values, the parser validates that the count satisfies the minimum arity requirement. If an option specifies arity `(2, 5)` but only one value is available, the parser raises an error identifying the option and the arity violation. This validation catches incomplete commands early with actionable error messages.

See the [behavior guide](behavior.md) for the complete value consumption algorithm including stopping conditions and edge cases.

### Accumulation handling

When an option appears multiple times in the argument sequence, the parser applies the configured accumulation mode to determine how to combine the values. Accumulation modes form a closed enumeration of strategies with well-defined semantics.

Last-wins mode keeps only the final occurrence, allowing later specifications to override earlier ones. This is the default mode and matches user expectations for configuration hierarchies where command-line arguments override file-based settings. First-wins mode keeps only the initial occurrence, providing immutable semantics where the first specification locks in the value. Collect mode accumulates all values into a tuple, enabling patterns like `--include pattern1 --include pattern2 --include pattern3` that build lists through repetition. Count mode counts occurrences rather than collecting values, supporting verbosity flags like `-vvv` where the count represents intensity. Error mode raises an exception on the second occurrence, enforcing single-specification semantics when repetition indicates user error.

Each mode produces different value types in the parse result. Last-wins and first-wins produce scalar values matching the option's arity pattern. Collect produces tuples containing all accumulated values. Count produces integer occurrence counts. The specific Python types are detailed in the [types guide](types.md).

### Name resolution

The parser resolves user-provided names to canonical option and command names through multiple strategies that can be independently configured. Exact matching is always enabled and checks for character-for-character matches between the user input and defined names. Alias resolution treats all defined long names and short names as equal aliases that resolve to the same canonical option. Abbreviation matching allows unambiguous prefixes when enabled, so `--verb` can match `--verbose` if no other option starts with "verb". Case-insensitive matching normalizes all names to lowercase when enabled, useful for Windows-style CLIs. Underscore-to-dash conversion treats underscores and dashes interchangeably when enabled, bridging Python's snake_case conventions with CLI kebab-case conventions. Negation support generates negated forms for flag options using configured negation words, enabling patterns like `--no-color` to explicitly disable features.

Resolution strategies are compositional configuration flags that combine to produce rich matching behavior. A parser can enable abbreviations while disabling case-insensitive matching, or enable all strategies for maximum user convenience. The parser resolves names using the most specific match available, with exact matches taking precedence over abbreviations. If abbreviation matching finds multiple candidates, the parser raises an ambiguity error listing all matches rather than guessing.

See the [concepts guide](concepts.md) for detailed explanations of each resolution strategy and their precedence rules.

### Inline value syntax

The parser extracts values from inline syntax where the option name and value are combined in a single argument. Long options support equals syntax like `--option=value` where the parser splits on the first equals sign to separate the option name from its value. This splitting handles values containing equals signs correctly: `--option=a=b=c` assigns the value `a=b=c` to the option. Short options support both equals syntax `-o=value` and concatenated syntax `-ovalue` where the value immediately follows the option character.

Special handling applies to flag options. Flags represent boolean presence with arity `(0, 0)` and cannot accept inline values. Attempting to use equals syntax with flags (e.g., `--verbose=true`) raises an error.

### Positional grouping

The parser collects positional arguments during parsing and groups them according to positional specifications after all options are processed. The grouping algorithm distributes arguments to named positional parameters while respecting arity constraints and reserving values for later positionals that have minimum requirements.

For each positional spec in order, the algorithm calculates how many values are needed by all following positionals, determines how many values can be assigned to the current positional without violating later minimum requirements, consumes values up to the positional's maximum arity or all available values (whichever is less), and assigns the consumed values to the named positional. This ensures that unbounded positionals like "sources" with arity `(1, None)` consume as much as possible while leaving enough arguments for required positionals like "destination" with arity `(1, 1)`.

**Concrete example:** Consider a `copy` command with the invocation `copy file1 file2 dest/` where the specification defines sources with arity `(1, None)` and destination with arity `(1, 1)`. The algorithm first calculates that the destination requires 1 value minimum. With 3 total positional arguments available, it allocates 2 values to sources (`file1`, `file2`) and reserves 1 for destination (`dest/`), satisfying both arity constraints.

When no positional specs are defined, the parser creates an implicit positional named "args" with arity `(0, None)` to capture all positional arguments. This ensures positionals are never lost even when not explicitly configured.

See the [behavior guide](behavior.md) and [concepts guide](concepts.md) for the complete grouping algorithm with worked examples.

### Subcommand nesting

The parser handles arbitrary levels of subcommand nesting by recognizing subcommand names and recursively parsing remaining arguments with the subcommand's specification. Each command level maintains completely isolated namespaces for options, positionals, and nested subcommands, preventing naming conflicts and allowing independent interface design at each level.

When the parser encounters an argument that matches a defined subcommand name, it builds the parent command's parse result with all options and positionals collected so far, then delegates the remaining arguments to a recursive parse using the subcommand's specification. The resulting subcommand parse result is attached to the parent result, creating a nested structure that mirrors the command hierarchy.

Commands like `git remote add` or `docker container run` exemplify this nesting. The root command `git` has options and the subcommand `remote`, which itself has options and the nested subcommand `add`. Each level's parse result contains its own options and positionals plus a reference to the invoked subcommand's result.

### Error detection

The parser detects syntactic errors and provides structured exception information that application code can format into user-facing messages. Errors are categorized into several types:

**Structural errors** (specification validation):

- Invalid specification configurations detected at parser construction
- Duplicate option or subcommand names within the same command
- Malformed option names or invalid arity configurations

**User input errors** (argument processing):

- Unknown option errors when arguments look like options but don't match any defined names
- Ambiguous abbreviation errors when abbreviation matching finds multiple candidates
- Insufficient values errors when options or positionals lack enough values for minimum arity
- Flag with value errors when flags receive explicit values via equals syntax
- Duplicate option errors when options with error accumulation mode appear multiple times

All exceptions carry structured data identifying which parameter failed validation, what constraint was violated, and what values were involved. The parser does not format these into end-user messages; it provides the raw information needed for applications to construct appropriate error displays, potentially with internationalization, styling, or context-specific guidance.

See the [errors guide](errors.md) for the complete error hierarchy, validation rules, and structured exception details.

## What the parser does not do

The parser's scope is intentionally limited to syntactic analysis. Several concerns that might seem related to parsing are explicitly excluded because they represent semantic, presentation, or integration concerns that belong in higher-level components.

### Type conversion

The parser does not convert string values to other types. All values remain as strings in the parse result, even if they represent numbers, dates, paths, or other structured data. When parsing `--port 8080`, the parser creates `ParsedOption(name="port", value="8080")` with the value as a string, not an integer.

This limitation is deliberate. Type conversion is a semantic concern that depends on application-specific knowledge. The parser cannot know whether `"42"` should be interpreted as an integer, a string identifier, part of a version number, or something else entirely. By leaving values as strings, the parser remains agnostic to application semantics and allows higher-level components like Aclaf to perform context-aware type conversion with proper error handling and domain validation.

### Validation beyond structure

The parser does not check that values are semantically correct or meet business logic constraints. It validates only syntactic constraints like arity, known options, and structural completeness. When parsing `--count -5`, the parser successfully creates `ParsedOption(name="count", value="-5")` without checking whether negative counts make sense for the application.

Semantic validation requires domain knowledge. The parser cannot know that port numbers must be in range 1-65535, that file paths should exist on disk, that mutually exclusive options shouldn't appear together, or that certain option combinations are invalid. These checks belong in application validation logic that runs after parsing and has access to business rules.

### Default value assignment

The parser does not assign default values to options or positionals that were not specified on the command line. The parse result contains only what the user explicitly provided. If the user runs `program --verbose`, the result contains only the verbose option, not defaults for other options like `output` or `config-file`.

Default values are configuration concerns that vary by application, environment, and context. Different deployments might have different defaults, and the same application might use different defaults in development versus production. The parser focuses on representing user input accurately, and higher-level configuration layers merge defaults as appropriate for the execution context.

### Dependency resolution

The parser does not check whether required options are present, whether option combinations are valid, or whether options depend on each other. When parsing `git commit --amend` without `--message`, the parser succeeds and produces a result with only the `amend` option. Application logic determines what to do when required combinations are missing.

Dependency relationships are application-specific rules. The parser cannot know that `--username` requires `--password`, that `--verbose` and `--quiet` are mutually exclusive, or that `--format=json` requires `--output`. These constraints belong in declarative validation schemas or imperative validation logic that runs after parsing.

### Help text generation

The parser does not generate help text, usage strings, or formatted error messages for end users. It provides structured error information that Aclaf or other frameworks format for display. When encountering `UnknownOptionError`, the parser provides the unknown option name and list of valid options as structured data, not a formatted string like "Error: unknown option --foo. Did you mean --bar?".

Help formatting is a presentation concern with complex requirements around internationalization, terminal capabilities, style preferences, and content organization. Applications need control over how help is rendered, when it's shown, and what additional context is included. The parser provides the raw specification data needed to generate help but leaves formatting to presentation layers.

### Environment variable integration

The parser does not read from environment variables or merge environment-based configuration with command-line arguments. Even if `PORT=8080` is set in the environment, the parser does not incorporate this when parsing command-line arguments.

Environment variable handling involves complex precedence rules, naming conventions, and value parsing strategies that vary widely between applications. Some applications use uppercase environment variables, others use lowercase with prefixes, and others use entirely different naming schemes. The parser focuses solely on the list of command-line arguments it receives, leaving environment integration to configuration management components.

### Configuration file loading

The parser does not load or merge values from configuration files in JSON, YAML, TOML, or other formats. When the parser processes `--config config.json`, it creates `ParsedOption(name="config", value="config.json")` without loading or parsing the file.

Configuration file handling involves file I/O, format parsing, path resolution, and precedence rules that are orthogonal to command-line parsing. These concerns belong in dedicated configuration management systems that can handle file loading errors, format validation, and merging strategies appropriate to the application's needs.

### Interactive prompting

The parser does not prompt users for missing values or accept input interactively. It operates on a fixed argument list and performs no I/O. When a required option is missing, the parser completes successfully with no value for that option. Higher-level validation detects the missing requirement and decides whether to prompt the user, raise an error, or use a default based on the execution context.

Interactive behavior depends on whether the program is running in a TTY, whether input is available, and what user experience patterns the application follows. The parser operates purely on the provided argument array, leaving interactive patterns to application layers that can access terminal capabilities and user interaction libraries.

### Context-aware parsing

The parser does not change its behavior based on runtime context, previous values, or application state. It parses arguments according to the static specification without considering what other options were specified, what values were provided, or what the application is doing. When parsing `--verbose` followed by `--quiet`, the parser processes both options independently without knowing they might conflict.

Context-aware parsing creates complex coupling between the parser and application logic. By maintaining strict separation, the parser remains predictable, testable, and composable. Applications can layer context-aware logic on top of the parse result, examining combinations of options and applying business rules as appropriate.

## Design constraints

The parser operates under strict design constraints that shape its architecture, performance characteristics, and integration patterns. These constraints are not limitations but deliberate choices that enable the parser to excel in its domain.

### Specification-driven behavior

All parser behavior is configured through declarative specifications rather than imperative code or runtime introspection. The `CommandSpecification`, `OptionSpecification`, and `PositionalSpecification` objects completely define what the parser accepts and how it processes arguments. No hidden conventions exist, no runtime discovery occurs, and no magic based on naming patterns applies.

This specification-driven approach provides several benefits that enhance the parser's reliability and usability:

**Explicit behavior:** Parser behavior is completely explicit and visible in the specification objects, making it easy to understand what a parser accepts without reading implementation code. There are no hidden conventions or implicit rules to discover through trial and error.

**Construction-time validation:** Specifications can be validated at construction time, catching configuration errors before any parsing occurs. Invalid arity configurations, duplicate option names, and malformed specifications are detected immediately rather than causing runtime failures.

**Synchronized parsing and completion:** The same specifications drive both parsing and completion generation, ensuring these components remain synchronized. When a specification changes, both the parser's validation and the completer's suggestions automatically reflect the update without requiring separate configuration.

**Immutability benefits:** Specifications are immutable and can be safely shared across threads or cached globally without defensive copying. This enables parser instances to be reused concurrently and specification objects to be treated as constants.

**Specification validation boundaries:** The parser validates specifications at construction to ensure they define consistent, parseable command structures. This validation establishes clear boundaries for what constitutes a valid specification:

- Arity constraints must be coherent: minimum cannot exceed maximum, and `(0, 0)` arity is valid only for flag options
- Options must have at least one name (long or short) for resolution to succeed
- Option names must follow valid format rules: long names minimum two characters, short names exactly one character
- Subcommand names cannot collide with option names within the same command level
- Option names cannot collide with other option names at the same command level

Invalid specifications are rejected at parser construction with structured errors that identify the specific constraint violation. See the [errors guide](errors.md) for complete validation rules and error types.

### Single-pass parsing

The parser processes arguments in exactly one left-to-right pass through the argument array with no backtracking, speculation, or multi-pass analysis. When the parser examines an argument, it makes a final classification decision immediately based on current state and the specification.

Single-pass parsing provides optimal and predictable performance. The time complexity is strictly O(n) where n is the number of arguments, with no hidden quadratic behaviors from backtracking or speculative parsing. Memory usage is minimal, requiring only the current parsing state without alternative parses or rollback points. Behavior is completely deterministic: given the same specification and arguments, the parser always produces exactly the same result.

**Trade-offs of fail-fast error reporting:** The single-pass constraint means the parser stops at the first error and raises an exception rather than accumulating multiple errors for comprehensive reporting. This creates a trade-off between performance and user experience:

**Benefits:**

- Optimal performance with guaranteed O(n) complexity
- Deterministic behavior with no ambiguity in error precedence
- Simpler implementation without error collection and prioritization logic
- Consistent with the parser's overall fail-fast philosophy

**Costs:**

- Users see only the first error, not a complete list of all problems
- Fixing one error may reveal additional errors requiring multiple parse attempts
- Applications cannot provide comprehensive error summaries in a single parse

**Justification:** This trade-off aligns with the parser's architectural principle of single-pass processing and fail-fast error detection. Applications requiring comprehensive error reporting can invoke the parser multiple times, fixing errors iteratively. The performance and simplicity benefits outweigh the user experience cost for the parser's target use cases.

### Immutability

All parser data structures are immutable after construction. Parse results, specifications, and all nested objects use frozen dataclasses and immutable collection types. No field can be modified after creation, and no methods mutate state.

Immutability enables thread safety without synchronization. Parse results can be safely passed between threads, cached globally, or shared across async tasks without locks or defensive copying. Parser instances can be reused concurrently without risk of state corruption. Specifications can be shared across many parsers and parse operations without concern for modification.

Immutability also enables aggressive caching. Name resolution results, specification lookups, and derived computations can be cached indefinitely because the underlying data never changes. This turns potentially expensive operations like case-insensitive prefix matching into constant-time lookups after the first invocation.

The constraint requires constructing new objects for any changes. Parse results cannot be patched or modified; applications must use functions like `dataclasses.replace()` to create new instances with different values. This is intentional: the immutability guarantee prevents entire classes of bugs related to shared mutable state.

**Parser state model:** Parser instances are stateless after construction. The `parse()` method is a pure function that depends only on its arguments and the immutable specification provided at construction. Given the same specification and argument list, `parse()` always produces identical results regardless of how many times it's called or whether previous parses succeeded or failed. This statelessness enables safe concurrent reuse of parser instances across threads without synchronization.

### Performance

The parser optimizes for speed without sacrificing correctness or clarity. Target performance is sub-millisecond parsing for typical CLI usage, measured concretely as parsing fewer than 1ms for 50 arguments with 20 options across 3 command levels. The algorithm exhibits O(n) linear scaling where n is the number of arguments, ensuring predictable performance even for complex command lines.

Performance optimizations include caching name resolution results to avoid repeated lookups, using frozen sets for O(1) membership testing, minimizing allocations through tuple reuse and slots-based classes, and structuring the main parsing loop for efficient branch prediction. These optimizations are measured through benchmarking rather than applied speculatively, following the "Measure, Don't Guess" principle.

The performance constraint does not justify sacrificing correctness or introducing subtle bugs. When a performance optimization conflicts with correct behavior or makes the code significantly harder to understand, correctness and clarity take precedence. The parser balances performance with maintainability, applying optimizations only where benchmarks demonstrate meaningful improvement.

### Separation of syntax and semantics

The parser strictly separates syntactic analysis (what did the user type) from semantic interpretation (what does it mean). This separation is an architectural boundary that shapes the entire implementation and integration model.

Syntactic concerns handled by the parser include classifying arguments by structure (option vs positional vs subcommand), extracting values from inline syntax, grouping values according to arity, applying accumulation modes, and resolving names to canonical forms. Semantic concerns explicitly excluded include type conversion (strings to integers, dates, paths, etc.), validation (range checks, file existence, mutual exclusivity), default values (applying configuration defaults for unspecified options), and dependency resolution (required options, option combinations).

This separation allows the parser to be tested in isolation without application dependencies, parse results to be reused across different execution contexts with different semantic interpretations, and the parser implementation to be replaced or extended without affecting application logic. It also provides clarity: the parser does one thing well rather than trying to handle all aspects of command-line processing.

### Security considerations

The parser implements security-conscious validation and establishes clear boundaries between parser responsibilities and application responsibilities for security-sensitive operations.

**Parser security responsibilities (enforced):**

- **Input sanitization:** The parser validates that all input arguments are well-formed strings and rejects malformed specifications that could cause parsing ambiguities or vulnerabilities
- **Arity bounds enforcement:** The parser strictly enforces minimum and maximum arity constraints, preventing unbounded value consumption that could lead to resource exhaustion
- **ReDoS protection:** When applications provide custom regular expressions for negative number patterns or other matching, the parser validates that patterns don't contain nested quantifiers like `(a+)+` that could cause Regular Expression Denial of Service attacks. While not exhaustive, this catches the most dangerous ReDoS patterns
- **Safe name resolution:** All name resolution strategies operate on validated, immutable specifications and cannot be influenced by external input to bypass security checks

**Application security responsibilities (out of scope):**

- **Command injection prevention:** Applications must sanitize option and positional values before passing them to shell commands or subprocesses. The parser provides raw string values; it does not validate against command injection patterns
- **Path traversal prevention:** Applications must validate file paths extracted from parse results to prevent directory traversal attacks like `../../etc/passwd`. The parser treats paths as opaque strings
- **Privilege escalation prevention:** Applications must enforce authorization and permission checks based on parsed commands and options. The parser has no concept of users, permissions, or security contexts

**Security principles:**

The parser follows fundamental security principles:

- **Secure by Default:** Default parser configuration rejects ambiguous inputs, enforces strict arity validation, and fails fast on unexpected patterns rather than attempting recovery
- **Defense in Depth:** The parser provides multiple validation layers: specification validation at construction, argument classification during parsing, and arity enforcement after value consumption. Each layer operates independently so failure of one doesn't compromise others

**Architectural boundary:** The parser provides the syntactic foundation for secure CLI applications but does not attempt to solve application-layer security concerns. Applications building on Flagrant must implement their own security controls for domain-specific threats based on validated, structured parse results.

## Architectural principles

Beyond the fundamental design constraints, several architectural principles guide the parser's implementation and evolution. These principles inform decisions about code structure, feature design, and trade-offs.

### Immutability by default

This principle extends the immutability constraint into a design philosophy. Every data structure should be immutable unless there is a compelling reason for mutability. When adding new features, the default choice is immutable types with explicit justification required for any mutable state.

The parser achieves immutability through frozen dataclasses with slots for all result types, private attributes with property accessors for configuration, frozen collections (frozensets and tuples) for all container fields, and defensive copying when interfacing with mutable external data. These mechanisms work together to enforce compile-time immutability while maintaining runtime performance.

### Pattern matching for dispatch

The parser extensively uses Python's structural pattern matching for argument classification and value extraction. Pattern matching provides exhaustiveness checking, clear intent, and potential compiler optimizations compared to chains of conditional statements.

The main parsing loop uses pattern matching to dispatch on argument prefixes, distinguishing between long options (`--`), short options (`-`), and potential positionals. Value extraction uses pattern matching to handle combinations of flag versus non-flag options, inline versus separate values, and various arity patterns. This pattern matching ensures that all valid combinations are explicitly handled and unexpected combinations are caught immediately during development.

The pattern matching principle requires Python 3.10+ (when pattern matching was introduced) and means the parser cannot run on earlier versions. This is acceptable for Flagrant, which targets Python 3.10+ and prioritizes clarity and modern Python idioms over backward compatibility with legacy interpreters.

### Consolidated parsing implementation

The entire parsing algorithm lives in a single function rather than being decomposed into many smaller functions. This is a deliberate architectural decision that deviates from the Single Responsibility Principle but provides specific benefits that justify the trade-off.

**Benefits of consolidation:**

The monolithic function keeps all parsing logic visible in one place without requiring jumps between functions to follow control flow. All parsing state is local variables rather than instance attributes or parameters threaded through many functions. Performance is optimal with no function call overhead or parameter marshaling. The structure uses clearly marked regions with comments to organize the logic into conceptual blocks while maintaining locality.

**SOLID principles acknowledgment:**

This design intentionally violates the Single Responsibility Principle (SRP) from SOLID, which suggests functions should have one reason to change. The parsing function has multiple responsibilities (classification, value consumption, arity validation, accumulation) that could be separated into distinct functions. However, the performance benefits, improved locality of reference, and reduced parameter passing complexity outweigh the maintainability cost for this specific use case. The decision is made consciously with full awareness of the trade-off.

Testing focuses on comprehensive integration tests that exercise all branches and edge cases through complete parsing scenarios. This approach matches the consolidated implementation and ensures that the parsing algorithm is tested as a cohesive whole rather than testing individual helper functions in isolation.

### Explicit configuration over conventions

The parser makes every decision based on explicit configuration rather than inferring behavior from context or following implicit conventions. Applications must explicitly choose whether options can appear after positionals, whether abbreviations are allowed, how case sensitivity works, and what accumulation modes apply.

This explicit configuration means applications document their parsing behavior through configuration rather than relying on "standard" or "conventional" behavior that users must learn. It also means the parser provides mechanisms (how to parse) without enforcing policies (what is correct), allowing applications to configure the parser for their specific conventions rather than conforming to parser-imposed conventions.

### Value flattening control

When options use collect accumulation mode with multi-value arity, repeated occurrences can create nested tuples like `((val1, val2), (val3, val4))`. The parser provides three-level precedence for controlling flattening behavior: option-level configuration that overrides all defaults for specific options, command-level configuration that overrides the parser default for all options in a command, and parser-level configuration that provides the global default.

This three-level control enables different commands to have different flattening policies and specific options to override command or parser defaults. The precedence rules are explicit and unambiguous: the most specific configuration always wins.

### Arity as first-class concept

The parser treats arity as a first-class type with explicit minimum and maximum bounds rather than using plain tuples or integers. The `Arity` named tuple provides type safety, semantic clarity, and self-documenting code compared to anonymous tuples.

Common arity patterns are defined as named constants: `ZERO_ARITY` for flags, `EXACTLY_ONE_ARITY` for typical options, `ONE_OR_MORE_ARITY` for required variadic parameters, and `ZERO_OR_MORE_ARITY` for optional variadic parameters. These constants improve code readability and reduce errors from typos in arity tuples.

## Core capabilities

The parser provides rich functionality for handling diverse command-line parsing scenarios. These capabilities combine to support both simple single-command CLIs and complex multi-level command hierarchies.

### Long and short options

Options can have multiple long forms (minimum two characters) specified with `--`, multiple short forms (single character) specified with `-`, or both. An option might define long names `("verbose", "v")` and short name `"v"`, allowing users to specify `--verbose`, `--v`, or `-v` with all forms resolving to the same canonical option.

Short options support combining, where `-abc` expands to three separate short options `-a`, `-b`, and `-c`. This POSIX-style behavior enables compact flag specifications like `tar -xzf` for "extract, gzip, file". The parser processes combined short options character-by-character, resolving each character against short option definitions.

### Inline value assignment

Long options support equals syntax for providing values: `--output=file.txt` is equivalent to `--output file.txt`. The parser splits on the first equals sign, so `--option=a=b=c` correctly assigns the value `a=b=c` to the option. Short options support both equals syntax `-o=value` and concatenated syntax `-ovalue` where the value immediately follows the option character.

For flag options with arity `(0, 0)`, inline values are prohibited because flags represent boolean presence. Attempting to use equals syntax with flags (e.g., `--verbose=true`) raises a `FlagWithValueError`.

### Flexible option ordering

By default, options and positionals can be freely intermixed in any order. The command `program file.txt --verbose --output result.txt` is equivalent to `program --verbose --output result.txt file.txt`. Both produce the same parse result with the parser classifying each argument regardless of position.

When strict positional mode is enabled, the parser enforces POSIX-style ordering where all options must precede all positional arguments. Once the first positional is encountered in strict mode, everything following becomes positional even if it looks like an option. This enables commands to accept option-like strings as positional values without ambiguity.

### Subcommand hierarchies

Commands can contain nested subcommands with arbitrary depth. Each subcommand has its own complete specification with independent options, positionals, and further subcommands. This enables complex CLI tools like `git` with commands like `git remote add` or `docker` with commands like `docker container run`.

Each command level maintains completely isolated namespaces. A parent command's options do not propagate to child commands, and child options do not affect the parent. When parsing encounters a subcommand name, it completes the parent command's parse result and recursively parses remaining arguments using the subcommand's specification. The resulting parse results nest hierarchically, mirroring the command structure.

### Accumulation modes

Options can use five accumulation modes to control how repeated occurrences are handled. Last-wins keeps the final value, enabling command-line arguments to override configuration file settings. First-wins keeps the initial value, providing immutable semantics. Collect accumulates all values into a tuple, supporting patterns like `--include pattern1 --include pattern2`. Count increments an integer counter for each occurrence, supporting verbosity flags like `-vvv`. Error raises an exception on the second occurrence, enforcing single-specification semantics.

The accumulation mode shapes the result type. Last-wins and first-wins produce scalar values. Collect produces tuples. Count produces integers. Applications can choose the appropriate mode based on the option's semantics and how users should interact with it.

### Option resolution strategies

The parser supports multiple name resolution strategies that can be independently configured. Exact matching is always enabled and handles character-for-character matches. Abbreviation matching allows unambiguous prefixes when enabled, so `--verb` matches `--verbose` if no other option starts with "verb". Case-insensitive matching normalizes names to lowercase when enabled. Underscore-to-dash conversion treats underscores and dashes interchangeably when enabled. Negation support generates negated forms for flags like `--no-color`.

These strategies compose to provide rich matching behavior. A parser might enable abbreviations and negation while disabling case-insensitive matching, creating a user-friendly but precise matching system. When multiple strategies apply, the parser uses the most specific match and raises ambiguity errors when multiple options match rather than guessing.

### Arbitrary arity patterns

Options and positionals support rich arity specifications beyond simple single values. Exact count arity like `(2, 2)` requires exactly two values, useful for coordinate pairs or ranges. Bounded arity like `(1, 3)` accepts one to three values. Unbounded arity like `(1, None)` accepts one or more values without limit. Optional arity like `(0, 1)` accepts zero or one value, enabling optional arguments with constant value defaults.

The parser consumes values according to arity constraints while respecting boundaries like other options and subcommands. For positionals, the grouping algorithm distributes arguments to satisfy all minimum arity requirements while allowing unbounded positionals to consume as much as possible. This enables sophisticated positional patterns like copy commands with variable sources and a required destination.

### Trailing argument support

The standalone `--` delimiter terminates option parsing entirely. All arguments following `--` are placed in a separate trailing arguments collection without interpretation. This enables passing arbitrary strings including option-like arguments to subprocesses or using option-like strings as data.

Commands like `docker run image -- subprocess-command --subprocess-flag` use `--` to separate container configuration from the command to run inside the container. Commands like `grep -- -pattern file.txt` use `--` to search for literal strings that look like options. The trailing arguments are preserved exactly as provided in the parse result for application use.

### Argument files

Argument files (also known as response files or @-files) allow users to specify command-line arguments in external files instead of directly on the command line. This feature addresses command-line length limitations, enables reusable argument sets, and improves maintainability for complex invocations.

The parser expands argument file references (`@file.txt`) inline during preprocessing, treating file contents as if they had been typed directly at that position. A line-based format is supported where each non-empty, non-comment line becomes a single argument. The `@` prefix is configurable, and escaping mechanisms (`@@file` for literal @-prefixed arguments, `--` separator) allow passing literal `@` values when needed.

Argument files are resolved relative to the current working directory. Files are expanded during a preprocessing phase before normal parsing begins, keeping concerns cleanly separated. Error handling provides clear messages for missing files, read errors, and format problems. See the [argument files guide](argument-files.md) for complete syntax, processing semantics, and security considerations.

### Comprehensive error detection

The parser detects syntactic errors and provides structured exception information. Unknown option errors identify option-like arguments that don't match any defined option. Ambiguous abbreviation errors list all matching candidates when abbreviations find multiple options. Insufficient values errors identify which parameter didn't receive enough values to satisfy its minimum arity. Flag with value errors identify when flags receive explicit values via equals syntax. Duplicate option errors identify options that appear multiple times when using error accumulation mode.

All errors are structured exceptions carrying parameter names, constraint values, and actual values involved. Applications format these into user-facing messages with appropriate context, style, and potentially internationalization.

## Integration with Flagrant ecosystem

The parser is one component in the Flagrant package, working alongside the completer and providing the foundation for Aclaf's full CLI framework.

### Parser as low-level engine

The parser focuses exclusively on syntactic analysis, producing structured data that higher-level components interpret. It does not perform type conversion, validation, default assignment, or command execution. This narrow focus makes the parser composable and testable in isolation.

Applications using Flagrant directly work with parse results as immutable data structures. They extract option values, convert types, apply validation rules, merge defaults, and execute commands based on the structured parse output. This explicit control over each step enables sophisticated workflows like validation layers, configuration merging, and execution strategies.

### Aclaf builds on parser foundation

Aclaf is a full-featured CLI framework being developed in parallel with Flagrant. Aclaf uses Flagrant's parser as its low-level parsing engine but adds type conversion (string to int, path, date, etc.), validation (range checks, mutual exclusivity, required options), default value management (from specifications, configuration files, environment variables), command execution (dispatch to handler functions), and application lifecycle (startup, shutdown, error handling).

The parser handles the syntactic question "what did the user type?" while Aclaf handles the semantic questions "what does it mean?" and "what should happen?". This division of responsibilities allows Flagrant to remain focused and reusable while Aclaf provides the rich framework features needed for building complete CLI applications.

---

## Related documentation

- [Concepts](concepts.md) - Shared conceptual foundations including arity, accumulation modes, option resolution, and positional grouping
- [Types](types.md) - Parser result types, Python type mappings, and value structures
- [Grammar](grammar.md) - Formal syntax rules and argument classification grammar
- [Behavior](behavior.md) - Detailed parsing algorithms including value consumption and positional grouping with worked examples
- [Configuration](configuration.md) - Complete reference for parser configuration options and modes
- [Errors](errors.md) - Complete error hierarchy, validation rules, and structured exception details
