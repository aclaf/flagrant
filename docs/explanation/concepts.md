# Shared concepts

--8<-- "unreleased.md"

This page describes the core abstractions that underlie how Flagrant processes command-line arguments. These concepts provide a common vocabulary used throughout the Flagrant documentation and APIs. While the concepts themselves are implementation-agnostic, this page links to technical specifications where appropriate if you need implementation details.

## Table of contents

- [Command specification model](#command-specification-model)
- [Specification immutability](#specification-immutability)
- [Specification composition](#specification-composition)
- [Arity](#arity)
- [Accumulation modes](#accumulation-modes)
- [Option resolution](#option-resolution)
- [Positional arguments](#positional-arguments)
- [Dictionary options](#dictionary-options)
- [Argument files](#argument-files)

---

## Command specification model

A command specification is a declarative blueprint that describes the structure, parameters, and behavior of a command-line interface. The specification model consists of three primary types: command specs, option specs, and positional specs. These types compose hierarchically to define complete CLI programs.

### What is a specification?

A specification is an immutable data structure that captures all information needed to parse command-line arguments for a command. Specifications are validated at construction time to ensure correctness before any parsing occurs. This fail-fast validation approach catches configuration errors early, preventing runtime surprises.

The specification model serves as the single source of truth for parsing behavior. When a specification defines an option with specific arity constraints, the parser validates those constraints during parsing to ensure correct argument processing.

### Terminology note

!!! tip "API names vs. shorthand"
    Throughout the Flagrant documentation, you'll see both full API names and convenient shorthand. When reading code or API references, you'll always see the full names. In explanatory prose like this document, the documentation uses the shorter forms for readability.

**Canonical API names** (use these in code):

- `CommandSpecification` - Defines a command or subcommand structure
- `FlagOptionSpecification` - Boolean flag options with negation and counting
- `ValueOptionSpecification` - Options accepting one or more string values
- `DictOptionSpecification` - Options parsing key-value pairs into dictionaries
- `PositionalSpecification` - Position-based parameters
- `ParseResult` - Output from parsing operations

**Shorthand for prose** (you'll see these in explanations and discussions, but not in code):

- `command spec` - Shorthand for CommandSpecification
- `option spec` - Generic shorthand for any option specification type
- `positional spec` - Shorthand for PositionalSpecification

### Command specs

A command spec defines the complete structure of a command or subcommand, orchestrating the relationships between options, positional arguments, and nested subcommands. It serves as the root of the specification tree.

Each command spec contains a name and optional aliases that identify the command in parse results and provide convenient shortcuts for users. The canonical name serves as the primary identifier in error messages and parsed results, while aliases enable alternative invocations. Options define named parameters that users provide via `--long` or `-short` syntax, appearing in any order by default though strict parsing modes may enforce constraints. Positionals define parameters identified by position rather than name, consumed in the order specified with arity constraints controlling value counts. Subcommands create nested hierarchies, delegating to child command specs when their names are encountered during parsing. Case sensitivity settings control whether option names and command aliases match case-sensitively or case-insensitively.

Command specs are composable. Complex CLI programs build by nesting command specs within one another, creating multi-level hierarchies like `git remote add` or `docker container run`. Each level in the hierarchy maintains its own namespace for options and positionals, preventing naming conflicts between parent and child commands. See [Specification composition](#specification-composition) for detailed rules on hierarchical composition.

### Option specs

An option spec defines a named parameter that accepts zero or more values, recognized by prefix characters: `--` introduces long-form names, while `-` introduces short-form names. An option can have multiple long names, multiple short names, or both, providing flexibility in how users invoke the option.

Flagrant uses a three-tier option specification hierarchy to model different parameter types with type-specific behaviors:

**OptionSpecification (base class)** - The abstract base class that all option types inherit from. It defines the common attributes shared by all options:

- `name`: The canonical name used to identify the option in parse results
- `long_names`: frozenset of long-form names (minimum one character) specified with `--` prefix
- `short_names`: frozenset of single-character names specified with `-` prefix

**FlagOptionSpecification** - Specialized for boolean flags that typically accept no values but can support negation and counting:

- `accumulation_mode`: Type-specific `FlagAccumulationMode` enum (FIRST, LAST, COUNT, ERROR)
- `negation_prefixes`: Words that create negated forms like `--no-verbose`
- `negation_short_names`: Short names for negated forms

**ValueOptionSpecification** - Specialized for options that accept one or more string values:

- `accumulation_mode`: Type-specific `ValueAccumulationMode` enum (FIRST, LAST, APPEND, EXTEND, ERROR)
- `arity`: Number of values expected per occurrence (see [Arity](#arity))
- `greedy`: Whether to consume all remaining arguments
- `allow_item_separator`: Enable shorthand syntax for list values
- `allow_negative_numbers`: Allow negative numbers as values
- Multiple separator and pattern configuration fields

**DictOptionSpecification** - Specialized for dictionary options that parse key-value pairs into structured data:

- `accumulation_mode`: Type-specific `DictAccumulationMode` enum (MERGE, FIRST, LAST, APPEND, ERROR)
- `merge_strategy`: Controls shallow vs deep merging when `accumulation_mode=MERGE`
- `arity`: Number of key-value arguments expected per occurrence
- Multiple separator and behavior configuration fields

Each option type has its own accumulation mode enum tailored to that type's semantics. Flag options count occurrences or track boolean state, value options collect or replace string values, and dictionary options merge or accumulate structured data. See [Accumulation modes](#accumulation-modes) for detailed semantics of each mode.

Option specs are immutable after construction and can be safely shared across multiple command specs. Common options like `--verbose` or `--config` can be defined once and reused throughout a command hierarchy. See [Specification immutability](#specification-immutability) for implications of this guarantee.

For detailed dictionary parsing algorithms and syntax, see the [dictionary parsing specification](dictionary-parsing.md).

### Positional specs

A positional spec defines a parameter identified by its position in the argument sequence rather than by a name or prefix. Positionals are matched to their specs in order after all options are consumed, with arity constraints controlling how many values each positional receives.

Each positional spec contains a name that identifies the positional in parse results. Unlike option names which must be unique across all long and short forms, positional names only need to be unique within a command's positional collection. Arity specifies the number of values this positional accepts, working identically to option arity by specifying a minimum and maximum range. Unbounded positionals (where max is None) consume as many values as possible while reserving values for later positionals with minimum requirements, as detailed in the positional grouping algorithm described in [Positional arguments](#positional-arguments).

Positional specs define a strict ordering within a command. The parser assigns arguments to positionals left-to-right based on arity constraints, ensuring that later positionals with minimum requirements receive their needed values before earlier unbounded positionals consume remaining arguments. See the [parser behavior specification](behavior.md) for the complete positional grouping algorithm with worked examples.

When no positional specs are defined, the parser creates an implicit spec named "args" with unbounded arity to capture any positional arguments provided. This ensures positional arguments are never lost even when not explicitly configured.

### Specification validation

All specs validate during construction, before any parsing occurs. Validation checks ensure that specs are internally consistent and follow naming rules.

Name uniqueness requirements state that within a command, all option names (both long and short forms) must be unique. Similarly, subcommand names and aliases must be unique, and positional names must be unique. Name format rules require command names to start with an alphabetic character and may contain alphanumeric characters, dashes, and underscores. Option long names must be at least one character. Short names must be exactly one character. Positional names have minimal validation requirements since they primarily serve as identifiers in parse results.

Arity constraints require that minimum arity must be non-negative, maximum arity must be non-negative or unbounded (None), and minimum must not exceed maximum. Negation word validity requires that negation words must be non-empty and must not contain whitespace.

#### Understanding validation timing and errors

Validation happens at two different times during your CLI application's lifecycle, with different error types for each:

**Construction-time validation** happens when creating spec objects and catches structural configuration errors:

- `SpecificationError` - Base exception for all specification validation failures
- `DuplicateNameError` - Raised when option names, subcommand names, or positional names conflict
- `InvalidNameFormatError` - Raised when names violate format rules (for example, empty long option name)
- `InvalidArityError` - Raised when arity constraints are structurally invalid (for example, min > max)

Construction-time validation raises specific errors for structural configuration problems: arity constraints where minimum exceeds maximum are invalid, empty option long names are invalid, and positional indices that conflict with existing specs are invalid.

**Parse-time validation** happens during argument processing and catches user input errors:

- `ParseError` - Base exception for all parsing failures
- `InsufficientValuesError` - Raised when a parameter receives fewer values than its minimum arity
- `AmbiguousOptionError` - Raised when abbreviation matching finds multiple candidates
- `DuplicateOptionError` - Raised when an option with ERROR accumulation mode appears multiple times

Parse-time validation catches cases where user input violates arity constraints: an option defined with arity constraint (2, 2) requiring exactly two values will raise an error if only one value is provided, with the error message identifying the option name, the required count, and the actual count received.

This two-phase validation approach catches configuration errors early with detailed error messages that identify the specific constraint violation and conflicting names or values. By failing fast at construction time, you get immediate feedback while building your CLI's specification, rather than discovering problems later during actual parsing.

## Specification immutability

All specification objects in Flagrant are immutable after construction. This immutability is a foundational architectural guarantee with significant implications for implementation, performance, and thread safety.

### Understanding the immutability guarantee

Once you create a spec object and it passes validation, nothing about it can change. This applies to `CommandSpec`, `OptionSpec`, `PositionalSpec`, and all nested structures they contain. This immutability brings multiple benefits: specifications can be safely shared across threads, cached aggressively for performance, and reasoned about without worrying about hidden state changes.

Immutability is enforced through construction-time validation combined with the use of immutable collection types for all container fields. Collections are represented using immutable types (tuples instead of lists, frozen sets instead of mutable sets) and structural modifications after construction are prevented at the implementation level.

### Sharing and reuse safety

Because specs are immutable, they can be freely shared without defensive copying. A common option specification for a verbose flag can be defined once and included in dozens of different command specifications without risk of one command's modifications affecting others. This sharing reduces memory overhead and enables consistent behavior across commands that use the same option definitions.

The parser can safely maintain references to specs without worrying about external modifications. Internal caches built during parsing remain valid for the lifetime of the spec, enabling performance optimizations that would be unsafe with mutable specifications.

### Caching and performance

Immutability enables aggressive caching strategies. The parser can precompute resolution maps from option names to canonical option specifications during initialization, caching these maps for the entire parse session.

Validation results can be cached indefinitely. Once a spec passes validation at construction time, no re-validation is ever needed. Derived computations like negated option names (generated by prepending negation words and separators during spec initialization) can be computed once and stored, eliminating redundant work on every parse invocation.

### How immutability affects validation

Immutability determines when validation can happen. All structural validation happens at construction time because the spec never changes after creation—there's no opportunity to validate later. This gives you immediate feedback when defining your CLI interface, catching errors right at the point of definition rather than discovering them during runtime parsing.

Parse-time validation then focuses exclusively on user input, not spec configuration. The parser knows that all specs are internally consistent, so it only needs to check whether the user's arguments meet the spec's constraints, not whether the specs themselves are valid.

## Specification composition

Command specs compose hierarchically to build complex CLI programs. Understanding the composition rules is essential for designing multi-level command structures and reasoning about namespace isolation and option inheritance.

### Hierarchical composition model

Flagrant uses strict hierarchical composition where subcommands are nested within parent commands, creating tree structures with `CommandSpec` objects as nodes. Each level of the tree represents a potential command invocation point with its own options, positionals, and further subcommands.

Commands like `git remote add` or `docker container run` exemplify this hierarchy: the root command (`git` or `docker`) has its own options and subcommands, each subcommand (`remote` or `container`) has its own options and nested subcommands, and leaf commands (`add` or `run`) define the final set of parameters for their specific operations.

### Namespace isolation

Each command maintains completely isolated namespaces for options, positionals, and subcommands. A parent command's options do not propagate to child commands, and a child command's options do not affect the parent. This isolation prevents naming conflicts and allows each command level to define its interface independently.

For example, if the root command `program` defines option `--verbose` and subcommand `deploy` also defines option `--verbose`, these are entirely separate options that can have different arities, accumulation modes, and semantics. The parser determines which `--verbose` option applies based on where the option appears in the argument sequence relative to the subcommand name.

Namespace isolation extends to positionals. A parent command can define positional specs, and a child subcommand can define its own positional specs without conflict. The parser assigns positional arguments to the appropriate command level based on where they appear relative to the subcommand delimiter.

### Why there's no inheritance model

Flagrant doesn't implement option or parameter inheritance between parent and child commands. There's no mechanism for child commands to automatically inherit their parent's options or for defining "global" options that apply at all levels.

This explicit no-inheritance design has a clear benefit: each command's specification completely and unambiguously describes its interface. When you examine a `CommandSpec`, you can understand all available options, positionals, and subcommands without traversing the hierarchy to discover inherited parameters. This trades potential code duplication for clarity and independence.

If consistent options are needed across multiple commands (like `--verbose` or `--config`), those options should be defined as shared `OptionSpec` objects and explicitly included in each command's option collection. This explicit inclusion makes the interface obvious while still enabling reuse through immutable spec sharing.

### Boundary semantics for subcommands

The boundary between a parent command and its subcommand is the subcommand name itself. Arguments before the subcommand name belong to the parent command and are parsed according to the parent's spec. Arguments after the subcommand name belong to the child command and are parsed according to the child's spec.

Consider the invocation: `program --parent-opt value1 subcommand --child-opt value2 positional`. The parser processes `--parent-opt value1` using the root command's spec, recognizes `subcommand` as a subcommand name, then delegates remaining arguments `--child-opt value2 positional` to the subcommand's spec. The parent command's parse result contains `parent-opt` and a reference to the invoked subcommand, while the subcommand's parse result contains `child-opt` and `positional`.

This boundary is unambiguous because subcommand names are matched before positional arguments are classified. An argument that matches a known subcommand name triggers delegation even if it could theoretically be consumed as a positional value for the parent command.

### Composition validation

When a `CommandSpec` contains subcommands, validation ensures that subcommand names do not conflict with each other or with option values that might be confused as subcommands. Subcommand name uniqueness is enforced within each command level—two subcommands at the same level cannot share names or aliases.

Validation does not prevent subcommand names from matching parent command option names or positional values because the parsing context makes these unambiguous. An option name and a subcommand name can coincide without conflict since the parser knows whether it's processing an option value or looking for a subcommand based on parsing state.

## Arity

Arity defines how many values a parameter (option or positional) accepts. It specifies both a minimum and maximum count, allowing precise control over value consumption and enabling meaningful validation of user input.

### What is arity?

In the context of command-line parsing, arity represents the number of values associated with a parameter. For options, arity determines how many arguments following the option flag belong to that option. For positionals, arity determines how many consecutive arguments the positional consumes from the remaining argument sequence.

Arity is expressed as a tuple of two integers: `(min, max)`. The minimum specifies how many values are required at a minimum. The maximum specifies the upper bound, or None for unbounded parameters that consume as many values as available (subject to stopping conditions). This representation enables rich parameter semantics without custom parsing logic. A flag option has arity `(0, 0)` since it accepts no values. A typical option requiring exactly one value has arity `(1, 1)`. An option collecting multiple files might have arity `(1, None)` to require at least one file but accept arbitrarily many. A coordinate pair might have arity `(2, 2)` to require exactly two numeric values.

### How arity is represented

Arity uses a structured type with two components: a minimum value and a maximum value.

The minimum component tells you the minimum number of values required. If fewer values are provided, the parser raises a validation error indicating insufficient values for the parameter. The maximum component specifies the maximum number of values the parameter will consume. When the maximum is unbounded (represented as infinity or null), the parameter consumes as many values as possible until encountering a stopping condition (another option, a subcommand, or the end of arguments). When the maximum is a specific integer, the parameter stops consuming values after reaching that limit.

### Common arity patterns

Common arity patterns occur frequently in command-line interfaces and carry conventional semantics:

Flags with arity `(0, 0)` represent boolean options that accept no values. When present, the flag is true; when absent, false. Examples include `--verbose`, `--debug`, and `--help`. Required single value options with arity `(1, 1)` form the most common pattern for options requiring exactly one value. Examples include `--output file.txt`, `--config app.yaml`, and `--port 8080`. The optional single value pattern with arity `(0, 1)` can appear without a value or with one value, with the parser using a constant value when no value is provided. Examples include `--color` (defaults to "auto") and `--optimize` (defaults to highest level).

Required variable length parameters with arity `(1, None)` require at least one value but accept many, useful for collecting lists. Examples include `--input file1 file2 file3` and `--define KEY1=VAL1 KEY2=VAL2`. The optional variable length pattern with arity `(0, None)` is optional but can accept many values when provided. Examples include `--include pattern1 pattern2` and variadic positional arguments for extra files.

Exact count parameters with arity `(n, n)` require a specific number of values. Examples include `--coordinate 10 20` (exactly 2) and `--rgb 255 128 0` (exactly 3). Bounded range parameters with arity `(min, max)` accept a range of values. Examples include `--range 1 100` (1 or 2 values for start and optional end) and `--names alice bob charlie` (2 to 4 names).

### Greedy versus non-greedy consumption

For unbounded arity patterns where `max` is `None`, the `greedy` parameter controls consumption behavior when the parser encounters remaining arguments. This distinction is critical for options that need to consume all remaining values versus those that should stop at natural boundaries.

**Non-greedy unbounded arity** (`greedy=False`) - The default behavior for unbounded options. The parser consumes values until encountering a stopping condition: another option (arguments starting with `-`), a subcommand name, the end-of-options delimiter `--`, or the end of the argument sequence. This mode respects natural command-line boundaries and allows other options and positionals to follow.

The optional non-greedy unbounded pattern with arity `(0, None)` and `greedy=False` consumes zero or more values until hitting a boundary:

```bash
program --include *.txt --verbose
# include: ("*.txt",), verbose: True
# Parser stopped at --verbose boundary

program --include
# include: (), no values consumed
```

Required non-greedy unbounded with arity `(1, None)` and `greedy=False` requires at least one value, then consumes until hitting a boundary:

```bash
program --files file1.txt file2.txt --output result.txt
# files: ("file1.txt", "file2.txt"), output: "result.txt"
# Parser stopped at --output boundary

program --files
# Error: Option 'files' requires at least 1 value
```

**Greedy unbounded arity** (`greedy=True`) - Forces the parser to consume ALL remaining arguments in the sequence, regardless of whether they look like options or subcommands. This mode is useful for wrapper commands that pass arbitrary arguments to subprocesses, or for collecting all remaining inputs without interpretation.

The optional greedy unbounded pattern with arity `(0, None)` and `greedy=True` consumes everything that follows:

```bash
program --args --verbose --output file.txt
# args: ("--verbose", "--output", "file.txt")
# Everything after --args was consumed, even option-like arguments

program --args
# args: (), no remaining arguments to consume
```

Required greedy unbounded with arity `(1, None)` and `greedy=True` requires at least one value, then consumes everything:

```bash
program --command docker run --rm -it alpine sh
# command: ("docker", "run", "--rm", "-it", "alpine", "sh")
# All arguments consumed for subprocess invocation

program --command
# Error: Option 'command' requires at least 1 value
```

**Use case guidance:**

Use non-greedy unbounded (`greedy=False`, the default) when you want natural command-line parsing where options and arguments can be freely mixed, and the parser should respect option boundaries. This pattern suits most collecting options like file lists, include patterns, or configuration entries that appear alongside other options.

Use greedy unbounded (`greedy=True`) when you need to capture all remaining arguments without interpretation, typically for wrapper commands that delegate to subprocesses, pass-through argument collections, or commands that need to treat everything following an option as data rather than parsed arguments. The greedy option effectively acts as a terminator for parsing, similar to `--` but bound to a specific option.

**Interaction with positionals:**

When an option with unbounded arity appears before positional arguments, non-greedy behavior allows positionals to be recognized, while greedy behavior consumes them as option values. For greedy options, it's recommended to place them at the end of the command invocation or use the `--` delimiter to explicitly separate parsed arguments from pass-through values.

### Arity validation

Arity validation occurs at two points: during spec construction and during argument parsing.

Construction-time validation ensures arity values are structurally valid. Minimum arity must not be negative, maximum arity must not be negative (when not unbounded), and minimum arity must not exceed maximum arity. These structural checks catch configuration errors early before any parsing begins. An arity specification like `(-1, 5)` or `(10, 3)` raises an `InvalidArityError` immediately during option or positional spec construction.

Parse-time validation ensures that user input satisfies arity constraints. After consuming values for a parameter, the parser must verify that at least `min` values were consumed. The parser stops consuming values when `max` is reached. If insufficient values are available to satisfy `min`, the parser must raise an error specific to the parameter type (option vs positional). Minimum arity violations produce actionable error messages identifying which parameter failed validation and how many values were required versus provided. Maximum arity violations never produce errors; instead, the parser stops consuming values and moves to the next argument, potentially treating the excess as another option, a positional, or a subcommand.

See the [parser behavior specification](behavior.md) for the complete value consumption algorithm with detailed error handling procedures.

### Conceptual value consumption

Arity defines constraints that the parser uses to determine valid value counts. The parser enforces these constraints during value consumption. The fundamental principle is that parameters consume values up to their maximum arity while ensuring minimum requirements are met, stopping when encountering boundaries like other options, subcommands, or argument sequence termination.

The detailed algorithm for value consumption, including stopping conditions for option-like arguments, subcommand names, and special markers like `--` and `-`, is specified in the [parser behavior specification](behavior.md). That specification covers precise behaviors for edge cases like negative numbers as positional values and the interaction between strict mode and value consumption.

### Arity and result structure

Arity patterns influence result structure in the parser's output. Single-value parameters (where `min == max == 1` and accumulation mode is first-wins or last-wins) naturally map to scalar results. Multi-value parameters (where `max > 1` or `max` is None) naturally map to collections. Flags with arity `(0, 0)` naturally map to booleans. Counters (flags with COUNT accumulation mode) naturally map to integers representing occurrence counts.

The conceptual relationship between arity patterns and result structure remains consistent: single-value parameters yield scalar results, multi-value parameters yield collection results, flags yield boolean results, and counters yield integer results.

## Accumulation modes

Accumulation mode determines how the parser handles repeated occurrences of the same option. When a user specifies an option multiple times, the accumulation mode controls whether to keep the first value, keep the last value, collect all values into a sequence, count the occurrences, merge structures, or raise an error.

### What is accumulation?

Accumulation addresses the question: what should happen when an option appears more than once? Different use cases demand different semantics. Sometimes the last value should win, allowing command-line arguments to override earlier configuration file settings. Sometimes all values should be collected into a list, like include patterns or environment variables. Sometimes repetition should be counted, like verbosity levels. Sometimes dictionaries should be merged together. Sometimes repetition is an error that should be reported to the user.

Accumulation applies only to options, not to positional arguments. Positionals are matched to their specs sequentially based on position and arity, making repetition semantically distinct from options.

### Type-specific accumulation enums

Each option type has its own dedicated accumulation mode enum tailored to its specific semantics. This type-specific design ensures that only semantically appropriate modes are available for each option type:

- **FlagAccumulationMode** - For `FlagOptionSpecification` (boolean flags)
- **ValueAccumulationMode** - For `ValueOptionSpecification` (string values)
- **DictAccumulationMode** - For `DictOptionSpecification` (dictionaries)

While these enums share common modes (FIRST, LAST, ERROR), each type defines additional modes specific to its behavior. This approach prevents nonsensical configurations like attempting to COUNT a dictionary option or MERGE a flag option.

### Understanding the architectural approach

Accumulation modes form a **closed enumeration** representing a finite set of strategies. The set of accumulation modes is fixed and complete, with the parser implementing each mode with specific logic tailored to that mode's semantics. This differs from option resolution strategies (described in [Option resolution](#option-resolution)), which are **compositional configuration flags** that you can independently enable or combine, and from positional grouping (described in [Positional arguments](#positional-arguments)), which is a **single algorithm with parametric behavior** that adapts to arity constraints.

This fixed enumeration ensures predictable, well-defined behavior for each mode. New accumulation modes require careful design consideration and can't be added through simple configuration—they represent fundamental semantic choices in how repeated options are interpreted.

### Flag option accumulation modes

Flag options use `FlagAccumulationMode` with the following modes:

**FIRST** - Keeps only the first occurrence, silently ignoring all later occurrences. When a flag appears multiple times, the parser accepts the first occurrence and discards all following ones. The final parsed result contains the boolean value from the first occurrence.

```bash
# With FIRST mode:
program --verbose --no-verbose
# Parsed value: true (first occurrence wins)
```

**LAST** - Keeps only the most recent occurrence, replacing earlier values. This is the default for flag options. Each new occurrence completely replaces the previous value, making the final parsed result contain only the boolean value from the last occurrence.

```bash
# With LAST mode (default):
program --verbose --no-verbose
# Parsed value: false (last occurrence wins)
```

**COUNT** - Counts the number of times the flag appears (or evaluates to true), storing the count as an integer. This mode enables incrementing verbosity or debug levels. The count starts at zero and increments for each occurrence that evaluates to true. Negated flags that evaluate to false do not increment the count.

```bash
# With COUNT mode:
program -v -v -v
# Parsed value: 3

# Combined short option syntax:
program -vvv
# Parsed value: 3

# Negation does not increment:
program -v -v --no-v -v
# Parsed value: 3 (negation doesn't increment)
```

**ERROR** - Raises an exception if the flag appears more than once, enforcing single-specification semantics. The parser raises an error immediately upon encountering the second occurrence, with an error message identifying the repeated flag.

```bash
# With ERROR mode:
program --verbose --verbose
# Error: Option 'verbose' cannot be specified multiple times
```

### Value option accumulation modes

Value options use `ValueAccumulationMode` with the following modes:

**FIRST** - Keeps only the first value, silently ignoring all later occurrences. When an option appears multiple times, the parser accepts the first occurrence and discards all following occurrences. The final parsed result contains only the value from the first occurrence.

```bash
# With FIRST mode:
program --output result.txt --output other.txt
# Parsed value: "result.txt"
```

**LAST** - Keeps only the most recent value, replacing earlier values. This is the default for value options. Each new occurrence completely replaces the previous value, enabling configuration override patterns.

```bash
# With LAST mode (default):
program --output result.txt --output final.txt
# Parsed value: "final.txt"
```

**APPEND** - Accumulates each occurrence as a separate tuple within a tuple of tuples. Each occurrence with its arity-bounded values forms one tuple, and all such tuples are collected into an outer tuple. This preserves the grouping of values from each occurrence.

```bash
# With APPEND mode and arity (2, 2):
program --coord 10 20 --coord 30 40
# Parsed value: ((10, 20), (30, 40))
```

**EXTEND** - Flattens all values from all occurrences into a single flat tuple. Unlike APPEND which preserves per-occurrence grouping, EXTEND combines all values regardless of which occurrence they came from.

```bash
# With EXTEND mode and arity (2, 2):
program --coord 10 20 --coord 30 40
# Parsed value: (10, 20, 30, 40)
```

**ERROR** - Raises an exception if the option appears more than once, enforcing single-specification semantics.

```bash
# With ERROR mode:
program --config app.yaml --config override.yaml
# Error: Option 'config' cannot be specified multiple times
```

### Dictionary option accumulation modes

Dictionary options use `DictAccumulationMode` with the following modes. Note that dictionary options uniquely support the MERGE mode, which is their default accumulation strategy:

**MERGE** - Merges dictionaries together, combining keys and values according to the configured merge strategy. This is the default for dictionary options and unique to dictionaries. The `merge_strategy` field (SHALLOW or DEEP) controls how nested structures are combined.

```bash
# With MERGE mode and DEEP merge strategy (default):
program --config db.host=localhost --config db.port=5432
# Parsed value: {"db": {"host": "localhost", "port": "5432"}}
# The nested "db" dictionaries are recursively merged

# With MERGE mode and SHALLOW merge strategy:
program --config db.host=localhost --config db.port=5432
# Parsed value: {"db": {"port": "5432"}}
# Second top-level "db" key completely replaces first
```

**FIRST** - Keeps only the first dictionary, silently ignoring all later occurrences. The final parsed result contains only the dictionary from the first occurrence.

```bash
# With FIRST mode:
program --env VAR1=value1 --env VAR2=value2
# Parsed value: {"VAR1": "value1"}  # Only first occurrence kept
```

**LAST** - Keeps only the most recent dictionary, replacing earlier dictionaries entirely. Each new occurrence completely replaces the previous dictionary.

```bash
# With LAST mode:
program --env VAR1=value1 --env VAR2=value2
# Parsed value: {"VAR2": "value2"}  # Only last occurrence kept
```

**APPEND** - Accumulates each dictionary as a separate entry in a tuple. Each occurrence produces one dictionary, and all dictionaries are collected into a tuple without merging. This preserves each occurrence as a distinct dictionary.

```bash
# With APPEND mode:
program --env VAR1=value1 --env VAR2=value2
# Parsed value: ({"VAR1": "value1"}, {"VAR2": "value2"})
# Tuple of separate dictionaries, not merged
```

**ERROR** - Raises an exception if the option appears more than once, enforcing single-specification semantics.

```bash
# With ERROR mode:
program --define KEY1=VAL1 --define KEY2=VAL2
# Error: Option 'define' cannot be specified multiple times
```

### Dictionary merge strategies

When `DictAccumulationMode.MERGE` is used, the `merge_strategy` field controls how dictionaries are combined. This strategy is specific to dictionary options and only applies when the MERGE accumulation mode is active:

**SHALLOW** - Performs a shallow merge where only top-level keys are combined. If the same top-level key appears in multiple dictionaries, the last occurrence's value completely replaces earlier values, even if those values are nested dictionaries. This provides simple top-level key overriding.

```bash
# With MERGE mode and SHALLOW strategy:
program --config db.host=localhost db.user=admin --config db.timeout=30
# First occurrence: {"db": {"host": "localhost", "user": "admin"}}
# Second occurrence: {"db": {"timeout": "30"}}
# Result: {"db": {"timeout": "30"}}  # Last value for "db" key wins entirely
```

**DEEP** - Performs a deep merge that recursively combines nested dictionary structures (default). When the same key appears at any nesting level with dictionary values, those dictionaries are merged recursively. This provides intuitive merging for configuration-style dictionaries.

```bash
# With MERGE mode and DEEP strategy (default):
program --config db.host=localhost db.user=admin --config db.timeout=30
# First occurrence: {"db": {"host": "localhost", "user": "admin"}}
# Second occurrence: {"db": {"timeout": "30"}}
# Result: {"db": {"host": "localhost", "user": "admin", "timeout": "30"}}
# Nested "db" dictionaries merged recursively
```

The merge strategy only applies when `accumulation_mode=DictAccumulationMode.MERGE`. Other accumulation modes (FIRST, LAST, APPEND, ERROR) ignore this field since they do not perform merging.

### Choosing an accumulation mode

Selecting the appropriate accumulation mode depends on the option type and semantics:

**For flag options:**

- Use LAST (default) when the most recent boolean value should win
- Use FIRST when the flag represents an immutable setting
- Use COUNT for verbosity levels or other incrementing counters
- Use ERROR when multiple flag specifications suggest user error

**For value options:**

- Use LAST (default) when overriding values makes sense (output paths, configuration files, formats)
- Use FIRST when the value should not change once established (security tokens, session identifiers)
- Use APPEND when maintaining per-occurrence grouping is important
- Use EXTEND when all values should be flattened into a single collection (include patterns, input files)
- Use ERROR when repetition likely indicates user error

**For dictionary options:**

- Use MERGE (default) with DEEP strategy for combining configuration naturally
- Use MERGE with SHALLOW strategy when only top-level merging is desired
- Use FIRST when the initial dictionary should lock in values
- Use LAST when the most recent dictionary should completely replace earlier ones
- Use APPEND when maintaining separate dictionaries is important
- Use ERROR when multiple dictionary specifications suggest user error

## Option resolution

Option resolution is the process of matching user-provided option names to their canonical option specs. The parser must support multiple resolution strategies including exact matching, alias resolution, abbreviation matching, negation resolution, case-insensitive matching, and underscore-to-dash normalization.

### What is option resolution?

When the parser encounters an option-like argument (one starting with `-` or `--`), it must determine which option spec the argument corresponds to. This matching process is option resolution. The parser strips the leading dashes to obtain the option name, then attempts to match that name against defined option specs using various strategies in priority order.

Resolution strategies can be independently configured through parser settings. When multiple strategies are enabled, the parser uses the most specific match available. Exact matches take precedence over aliases, which take precedence over abbreviations. If abbreviations match multiple options, the parser must raise an ambiguity error rather than guessing which option the user intended.

### Understanding resolution strategies

Unlike accumulation modes which form a closed enumeration, option resolution strategies are **compositional configuration flags** that you can independently enable or disable and combine in various ways. Exact matching is always enabled, but abbreviation matching, case-insensitive matching, and underscore-to-dash normalization are optional features you can mix and match.

This compositional design lets you configure parsers for different CLI conventions without requiring entirely different resolution implementations. A POSIX-style parser might disable abbreviations and normalization while keeping case sensitivity. A Windows-style parser might enable case-insensitive matching. A user-friendly modern CLI might enable all strategies for maximum flexibility.

### Exact matching

Exact matching is the baseline resolution strategy, always enabled and checked first. The user-provided option name must exactly match an option's long or short name character-for-character (subject to case sensitivity and normalization settings). When an option defines long name "verbose" and short name "v," both `--verbose` and `-v` match via exact matching. The parser strips leading dashes before comparing, so `--verbose` becomes "verbose" for matching purposes, and `-v` becomes "v."

Exact matching includes all defined aliases. If an option has long names ("recursive," "recurse," "r"), all three match exactly with equal priority. The canonical option name (from the option spec's name field) identifies the option in parse results, while the specific alias the user provided is preserved for reference.

### Alias resolution

Options can have multiple long names and multiple short names, all functioning as aliases that resolve to the same canonical option. Aliases provide alternative ways to specify the option, improving usability and backward compatibility. All aliases have equal priority in exact matching. The parser treats all defined names identically during resolution—there is no concept of "primary" versus "secondary" aliases. When an option has long names ("verbose," "v") and the user provides `--v`, the parser matches via exact alias resolution, not abbreviation.

The parse result must preserve both the canonical option name and the specific alias the user provided. This allows applications to track which variant users prefer while maintaining a consistent canonical identifier for the option across all occurrences.

### Abbreviation resolution

Abbreviation resolution allows users to type a prefix of an option name instead of the full name, as long as the prefix uniquely identifies the option. This feature is disabled by default and must be explicitly enabled through parser configuration. When abbreviation matching is enabled with a minimum abbreviation length (default 3 characters), the parser accepts any unambiguous prefix of an option name. For options "verbose," "version," and "verify," the abbreviation "verb" uniquely matches "verbose," while "ver" is ambiguous and produces an error listing all matching candidates.

Abbreviation matching operates against all valid names, including long forms, short forms, and aliases. If an option has aliases, users can abbreviate any of them. The parser uses prefix matching to find all option names that start with the provided abbreviation, raising an ambiguity error if multiple matches exist. The minimum abbreviation length prevents accidentally matching single-character prefixes that are likely to be ambiguous. A minimum length of 3 requires users to type at least three characters, reducing accidental matches while still providing substantial typing savings for long option names.

### Negation resolution

Boolean flag options can support negation through two mechanisms: prefix words for long names and explicit short names for short forms.

**Negation prefixes** create negated long-form variants by prepending words to the flag's long names. An option "verbose" with negation prefix "no" accepts both `--verbose` (sets to true) and `--no-verbose` (sets to false). You can define multiple negation prefixes, creating multiple negated forms: negation prefixes ("no," "disable") create `--no-verbose` and `--disable-verbose`.

The parser generates negated names for all long forms during spec initialization by prepending negation prefixes and separators (typically dashes). If a flag has long names ("color," "colorize") with negation prefix "no," the parser accepts `--color`, `--colorize`, `--no-color`, and `--no-colorize`. When the user-provided name starts with a known negation prefix followed by a separator, the parser strips the prefix, matches the remaining name against flag long names, and sets the flag to false instead of true.

**Negation short names** provide independent short options that explicitly negate the flag. Unlike negation prefixes which modify long names, negation short names are separate short options defined alongside the flag's regular short names. If a flag has short name "v" (sets to true) and negation short name "q" (sets to false), then `-v` sets the flag to true and `-q` sets it to false. These are distinct short options, not prefix-based transformations.

This dual mechanism enables flexible negation patterns: long forms use prefix-based negation (`--no-verbose`), while short forms use independent negation characters (`-q` to negate `-v`).

### Case sensitivity

By default, option matching is case-sensitive: `--verbose` differs from `--Verbose` or `--VERBOSE`. The parser supports case-insensitive matching through configuration, which is particularly useful for Windows-style command-line interfaces where case-insensitive conventions are common. When case-insensitive matching is enabled, the parser normalizes all option names to lowercase during spec construction and during argument parsing. This allows `--verbose`, `--Verbose`, `--VERBOSE`, and any other case variation to match the same option spec.

Canonical option names are preserved as defined in the spec regardless of the case used by the user. If an option's canonical name is "verbose" and the user provides `--VERBOSE`, the parse result contains the canonical name "verbose" while the alias field reflects the exact user input "VERBOSE." Case normalization applies to all resolution strategies including exact matching, alias matching, abbreviation matching, and negation matching. When abbreviations are enabled with case-insensitive matching, the prefix comparison occurs after case normalization.

### Underscore and dash conversion

Python conventionally uses snake_case for identifiers, while command-line interfaces typically use kebab-case. The parser can be configured to treat underscores and dashes interchangeably, allowing users to specify options with either convention. When underscore-to-dash conversion is enabled, the parser normalizes both option definitions and user input by converting underscores to dashes (or vice versa). This allows an option defined as "output-file" to match user input `--output_file`, and an option defined as "max_retries" to match user input `--max-retries`.

The conversion is bidirectional: options defined with dashes can be specified with underscores, and options defined with underscores can be specified with dashes. The canonical option name remains as defined in the spec, but matching becomes flexible to accommodate different naming conventions. This normalization enables Python-friendly option names in specs while allowing CLI-friendly dash syntax for users, bridging the conventional gap between Python identifier style and command-line interface style.

!!! note "Configuration reference"
    For detailed configuration of option resolution strategies, see the [parser configuration specification](configuration.md). Configuration options include:
    - `case_insensitive_options` - Enable case-insensitive option matching
    - `allow_abbreviated_options` - Enable abbreviation matching
    - `minimum_abbreviation_length` - Minimum characters required for abbreviations (default: 3)
    - `convert_underscores_to_dashes` - Enable underscore-dash normalization
    - Negation handling via `FlagOptionSpecification.negation_prefixes` and `negation_short_names`

## Positional arguments

Positional arguments are parameters identified by their position in the argument sequence rather than by a name or prefix. Unlike options which are marked with `-` or `--` and can appear in any order, positionals are recognized purely by their position and are matched to specs sequentially.

### What are positional arguments?

A positional argument is any command-line argument that is not an option, not a subcommand, and not part of the special trailing arguments collection. Positionals commonly represent required inputs like file paths, resource identifiers, or commands where meaning is clear from position and context.

The parser identifies positional arguments by process of elimination during parsing. After classifying arguments as options (those starting with `-` or `--`), subcommands (those matching subcommand names), and trailing arguments (those following the `--` separator), the remaining arguments become positionals. These positionals are then matched to positional specs based on position and arity constraints.

Positional arguments differ fundamentally from options in several ways. Options are recognized by prefix markers (`-` or `--`) while positionals are recognized by not being options, subcommands, or trailing arguments. Options can appear in any order by default (unless strict mode enforces ordering) while positionals are matched sequentially in the order specified. Options are named explicitly by the user (like `--output`) while positionals derive meaning from their position. Options provide maximum flexibility in specification order while positionals provide maximum brevity by eliminating the need for names.

### Positional classification

The parser uses a systematic classification algorithm to determine whether each argument is a positional. Arguments after the `--` separator are all placed in a separate trailing arguments collection and are never parsed as options or positionals. Arguments starting with `--` are treated as long options unless strict mode has activated and the parser has already encountered the first positional, in which case they become positionals. Arguments starting with `-` (but not exactly `-` or `--`) are treated as short options unless they match the negative number pattern and positionals are defined, in which case they are treated as positional values. The standalone `-` argument is always treated as a positional argument, following Unix convention where `-` represents stdin or stdout. All other arguments are checked against subcommand names first; if no subcommand matches, they are treated as positional arguments.

This classification algorithm ensures that option-like arguments are distinguished from true options based on context, enabling patterns like passing negative numbers as positional values while still treating `-v` as an option flag. See the [parser behavior specification](behavior.md) for the complete classification algorithm with edge case handling.

### Strict positional mode

Strict positional mode enforces POSIX-style ordering where all options must precede all positional arguments. Once the parser encounters the first positional argument in strict mode, all following arguments that look like options are treated as positional values instead.

Without strict mode (the default), options, and positionals can be freely interspersed: `program file.txt --verbose --output result.txt` is equivalent to `program --verbose --output result.txt file.txt`. Both orderings produce the same parse result. With strict mode enabled, the first positional argument acts as a boundary. Everything before it is parsed normally (options as options, positionals as positionals). Everything after it becomes positional, even if it looks like an option: `program --verbose file.txt --output result.txt` would parse `--verbose` as an option but `--output` and `result.txt` as positionals because they follow the first positional `file.txt`.

Strict mode is useful for implementing POSIX-compliant parsers and for commands that need to accept option-like values as positional arguments without ambiguity. It shifts the parser from flexible GNU-style ordering to strict POSIX-style ordering.

### Trailing arguments

The double-dash `--` is a special separator that terminates option parsing entirely. All arguments following `--` are placed in a separate trailing arguments collection, bypassed from normal option and positional processing.

Trailing arguments are useful for passing arguments to subprocesses, disambiguating option-like values, and preventing option parsing. Commands like `docker run image -- subprocess-command --subprocess-flag` use `--` to separate container configuration from the command to run inside the container. Commands like `grep -- -pattern file.txt` use `--` to search for a literal "-pattern" string without the parser treating it as an option. Any command that needs to accept arbitrary strings including ones that look like options can use `--` to mark where option parsing should stop.

Trailing arguments are preserved as-is in the parse result in a separate field, typically named `extra_args` or `trailing_args`. Applications can then pass these arguments directly to subprocess invocations, use them as data, or process them with custom logic.

### How positional grouping works

Positional grouping is the process of assigning collected positional arguments to named positional specs. Unlike options which are parsed individually as encountered, the parser collects all positional arguments during parsing and then groups them in a single pass after option parsing completes.

The grouping algorithm is a **single algorithm with parametric behavior** that adapts to arity constraints defined in positional specs. This differs architecturally from accumulation modes (which are a closed enumeration) and option resolution strategies (which are compositional flags). The algorithm's behavior changes based on the arity parameters you provide, but the algorithm itself remains constant.

The algorithm respects arity constraints and assigns arguments left-to-right, ensuring each positional spec receives the correct number of values while reserving arguments for later positionals that have minimum requirements. For each positional spec in order, the algorithm calculates the minimum number of values needed by all following positionals, determines how many values are available for this positional (total remaining minus later minimum needs), consumes up to the maximum arity or all available values (whichever is less), and assigns the consumed values to this positional.

This algorithm ensures that unbounded positionals consume as much as possible while leaving enough arguments for later positionals to satisfy their minimum arity. Consider a copy command with sources and destination: `copy file1 file2 file3 dest/` where the sources positional has arity `(1, None)` and destination has arity `(1, 1)`. The algorithm reserves one value for destination and assigns the remaining values to sources.

**Worked example with arithmetic:**

Given positional specs `[sources: (1, None), destination: (1, 1)]` and arguments `["file1", "file2", "file3", "dest/"]`:

1. Processing `sources` positional:
   - Total remaining arguments: 4
   - Minimum needed by following positionals: `destination` needs min=1, so reserve 1
   - Available for `sources`: 4 - 1 = 3
   - `sources` max arity is None (unbounded), so consume min(3, unlimited) = 3
   - Assign `["file1", "file2", "file3"]` to `sources`
   - Remaining arguments: `["dest/"]`

2. Processing `destination` positional:
   - Total remaining arguments: 1
   - Minimum needed by following positionals: 0 (no more positionals)
   - Available for `destination`: 1 - 0 = 1
   - `destination` max arity is 1, so consume min(1, 1) = 1
   - Assign `["dest/"]` to `destination`
   - Remaining arguments: `[]`

Result: `sources=("file1", "file2", "file3")`, `destination="dest/"`

See the [parser behavior specification](behavior.md) for the complete grouping algorithm specification with additional worked examples and edge cases.

### Implicit positional spec

When a command spec defines no positional specs, the parser automatically creates an implicit positional spec to capture any positional arguments. This implicit spec has name "args" and arity `(0, None)`, collecting all positional arguments into a tuple.

The implicit spec ensures that positional arguments are never lost, even when not explicitly configured. Applications can always access positionals under the "args" key without checking whether positional specs were defined. Commands that do not need sophisticated positional handling benefit from this sensible default. The parser creates the implicit spec dynamically when the positional specs collection is empty or undefined. This provides a consistent interface for accessing positionals regardless of whether they were explicitly specified or implicitly captured.

## Dictionary options

!!! warning "Not yet implemented"
    Dictionary option parsing with AST construction and structured merge semantics is planned but not yet fully implemented. The current parser treats dictionary option values as simple strings. The features described in this section represent the intended design and will be added in a future release.

Dictionary options enable users to specify structured key-value data through command-line arguments, supporting both flat dictionaries and arbitrarily nested structures with lists. This feature allows passing configuration directly on the command line using syntax patterns familiar from tools like Helm, AWS CLI, and kubectl.

For complete dictionary parsing algorithms, syntax specification, and detailed examples, see the [dictionary parsing specification](dictionary-parsing.md).

### What are dictionary options?

A dictionary option is a specialized option type that parses command-line arguments as key-value pairs and constructs dictionary structures. Unlike value options which treat each argument as an independent string, dictionary options interpret arguments with special syntax to build nested data.

You define dictionary options using `DictOptionSpecification`, which inherits from `OptionSpecification` in the three-tier option hierarchy alongside `FlagOptionSpecification` and `ValueOptionSpecification`. The parser recognizes dictionary options through their specification type and applies dictionary-specific parsing algorithms. See the [dictionary parsing specification](dictionary-parsing.md) for detailed parsing algorithms.

### Basic dictionary syntax

The fundamental syntax for dictionary entries uses the equals sign as the key-value separator. This pattern matches user expectations from virtually all modern CLI tools:

```bash
command --config key=value
```

The parser splits on the first equals sign, treating everything before as the key and everything after as the value. This allows values to contain equals signs without ambiguity:

```bash
command --config equation="x=y+z"
# Produces: {"equation": "x=y+z"}
```

You can specify multiple key-value pairs through repeated option flags or as space-separated arguments:

```bash
# Repeated option pattern
command --config key1=value1 --config key2=value2

# Accumulated pattern (when arity permits)
command --config key1=value1 key2=value2 key3=value3

# Both produce: {"key1": "value1", "key2": "value2", "key3": "value3"}
```

### Nested dictionaries

Nested dictionary access uses dot notation, where dots separate levels of nesting from outermost to innermost. This syntax mirrors property access in programming languages:

```bash
command --config database.host=localhost
# Produces: {"database": {"host": "localhost"}}

command --config database.connection.timeout=30
# Produces: {"database": {"connection": {"timeout": "30"}}}
```

You can specify multiple nested paths, with the parser automatically creating intermediate dictionary levels as needed:

```bash
command --config \
  database.host=localhost \
  database.port=5432 \
  database.connection.timeout=30 \
  cache.enabled=true
# Produces:
# {
#   "database": {
#     "host": "localhost",
#     "port": "5432",
#     "connection": {"timeout": "30"}
#   },
#   "cache": {"enabled": "true"}
# }
```

### Lists in dictionaries

Lists within dictionaries use bracket notation with zero-based indices:

```bash
command --config servers[0]=web1.example.com
# Produces: {"servers": ["web1.example.com"]}

command --config servers[0]=web1 servers[1]=web2 servers[2]=web3
# Produces: {"servers": ["web1", "web2", "web3"]}
```

Nested properties within list elements use continued dot notation after the bracket:

```bash
command --config servers[0].host=web1 servers[0].port=8080
# Produces: {"servers": [{"host": "web1", "port": "8080"}]}
```

This syntax enables specifying lists of dictionaries:

```bash
command --config \
  users[0].name=alice users[0].role=admin \
  users[1].name=bob users[1].role=user
# Produces:
# {
#   "users": [
#     {"name": "alice", "role": "admin"},
#     {"name": "bob", "role": "user"}
#   ]
# }
```

### Dictionary option accumulation

Dictionary options use distinct accumulation modes defined in `DictAccumulationMode` that control how multiple occurrences are combined. The default accumulation mode is `MERGE`, which merges dictionaries together rather than replacing them.

When `accumulation_mode=DictAccumulationMode.MERGE`, the `merge_strategy` field controls whether merging is shallow (top-level keys only) or deep (recursive merging of nested structures):

```bash
# With accumulation_mode=MERGE and merge_strategy=DEEP (default)
command --config database.host=localhost --config database.port=5432
# Result: {"database": {"host": "localhost", "port": "5432"}}

# With accumulation_mode=MERGE and merge_strategy=SHALLOW
command --config database.host=localhost --config database.port=5432
# Result: {"database": {"port": "5432"}}  # Second occurrence replaces first
```

Other accumulation modes include `FIRST` (keep only first dictionary), `LAST` (keep only last dictionary), `APPEND` (collect dictionaries into tuple), and `ERROR` (raise exception on duplicate). See [Dictionary option accumulation modes](#dictionary-option-accumulation-modes) for detailed semantics and examples of each mode.

### Escaping special characters

Keys containing dots, brackets, or equals signs require escaping to distinguish them from syntax elements. The backslash serves as the escape character:

```bash
# Key with literal dots
command --config 'service\.kubernetes\.io/name=myservice'
# Produces: {"service.kubernetes.io/name": "myservice"}

# Without escaping, dots show nesting
command --config service.kubernetes.io/name=myservice
# Produces: {"service": {"kubernetes": {"io/name": "myservice"}}}
```

Values containing spaces, quotes, or other special characters rely on shell quoting:

```bash
command --config name="Alice Smith"
# Produces: {"name": "Alice Smith"}
```

### DictOptionSpecification overview

Dictionary options are configured through `DictOptionSpecification`, which provides comprehensive control over parsing behavior. Key configuration fields include:

- **`arity`**: Number of key-value arguments accepted (default: `AT_LEAST_ONE_ARITY`)
- **`accumulation_mode`**: Strategy for combining repeated occurrences (default: `MERGE`)
- **`merge_strategy`**: Shallow or deep merging when accumulation mode is `MERGE` (default: `DEEP`)
- **`allow_nested`**: Enable nested dictionary syntax via dot notation (default: `True`)
- **`allow_item_separator`**: Enable providing multiple key-value pairs in single argument (default: `True`)
- **`case_sensitive_keys`**: Control case-sensitive key matching (default: `True`)
- **`allow_sparse_lists`**: Control whether lists can have missing indices (default: `False`)
- **`allow_duplicate_list_indices`**: Control duplicate index handling (default: `False`)

Separator and escape character fields control the specific characters used for parsing:

- **`key_value_separator`**: Separates keys from values (default: `=`, inherits from global configuration)
- **`nesting_separator`**: Indicates nested keys (default: `.`, inherits from global configuration)
- **`item_separator`**: Separates multiple pairs in single argument (default: None, inherits from global configuration)
- **`escape_character`**: Escapes special characters (default: `\\`, inherits from global configuration)

### How dictionary parsing works

The parser transforms dictionary argument strings into structured dictionary values through lexical analysis, syntactic analysis, abstract syntax tree construction, and tree building phases. The complete algorithms including tokenization, path parsing, value consumption, merging strategies, and error handling are specified in the [dictionary parsing specification](dictionary-parsing.md).

Key aspects of dictionary parsing include:

- **Lexical analysis**: tokenizes input strings, recognizing identifiers, separators, brackets, and escape sequences
- **Path parsing**: Parses dot-separated keys and bracket-indexed lists into path segments
- **Tree construction**: Builds nested dictionary and list structures from parsed assignments
- **Merging**: Combines dictionaries according to accumulation mode and merge strategy
- **Validation**: Enforces structural constraints and detects conflicts

### Integration with parser

Dictionary options integrate seamlessly with the parser. The parser recognizes `DictOptionSpecification` and applies dictionary-specific value consumption and accumulation algorithms. Parse results contain dictionary values with type `dict[str, DictValue]` or `tuple[dict[str, DictValue], ...]` depending on accumulation mode, where `DictValue` is a recursive type supporting strings, nested dictionaries, and lists.

See the [parser behavior specification](behavior.md) for how dictionary options interact with general parsing behavior.

## Argument files

Argument files (also known as response files or @-files) provide a mechanism for specifying command-line arguments in external files rather than directly on the command line. This addresses practical concerns including operating system command-line length limitations, reusability of common argument sets, and maintainability for complex invocations.

### Motivation

Command-line interfaces frequently encounter situations where the number or complexity of arguments makes direct specification impractical. Operating systems impose limits on command-line length, typically 8,192 characters on Windows and over 2 million on Linux. Build systems need to pass extensive compiler flags and file lists. Test frameworks require numerous configuration options. Applications have environment-specific settings that differ between development, staging, and production. Argument files solve these problems by moving complex argument lists into external files that can be versioned, shared, and composed.

### How argument files work

The parser expands argument file references (`@file.txt`) inline during a preprocessing phase, treating file contents as if you had typed them directly at that position on the command line. When the parser encounters an argument beginning with `@` (configurable prefix), it reads that file and splices the contents into the argument stream. The expansion occurs left-to-right as files are encountered, with each file's contents replacing the `@file` argument at its position.

A simple line-based format treats each non-empty, non-comment line as a single argument. Leading and trailing whitespace is trimmed. Lines beginning with `#` are comments. For example, a file containing the lines `--verbose`, `--output=/tmp/result`, and `input.txt` expands to three arguments in that order.

### Understanding precedence and composition

Since argument files expand inline, their position determines precedence. Arguments you specify directly on the command line after an argument file override values from that file (last-wins semantics). The invocation `app @base.args --output=custom.txt` uses the command-line output value even if `base.args` specifies a different output. The parser processes multiple argument files in order: `app @base.args @overrides.args` applies base configuration first, then overrides.

### How argument files integrate

Argument file expansion is a preprocessing transformation that runs before normal parsing begins. The preprocessing function takes the raw argument list and produces an expanded list with all `@file` references resolved. This expanded list then feeds into the parser's normal argument classification and value consumption algorithms. The parser itself remains unchanged and doesn't need to know about argument files.

You can control argument file behavior through multiple configuration options: `argument_file_prefix` (character triggering expansion, default `@`), `argument_file_format` (line-based or shell-style), `argument_file_comment_char` (comment prefix, default `#`), and `max_argument_file_depth` (recursion limit if supported). Setting the prefix to `None` disables the feature entirely.

!!! note "Shell completions in Aclaf"
    Shell completion for argument files (suggesting `@config.yaml` when the user types `@`) will be handled by Aclaf, not Flagrant. The Flagrant parser is responsible only for expanding argument file references during parsing.

### Error handling

Argument file operations can fail in several ways, each with a specific error type. `ArgumentFileNotFoundError` when the file doesn't exist. `ArgumentFileReadError` when the file exists but cannot be read due to permissions or I/O errors. `ArgumentFileFormatError` when the file contains malformed content like invalid UTF-8. `ArgumentFileRecursionError` when recursive expansion exceeds depth limits or detects cycles. All errors provide detailed context including file paths, line numbers, and actionable error messages.

### Where to learn more

See the [argument files specification](argument-files.md) for complete syntax specification, processing semantics, configuration options, security considerations, and testing strategy. The specification documents how argument files integrate with the preprocessing phase, error propagation, and type safety guarantees.

---

## See also

- **[Parser behavior](behavior.md)**: Complete value consumption algorithm and positional grouping details
- **[Dictionary parsing specification](dictionary-parsing.md)**: Complete dictionary parsing algorithms and syntax
- **[Parser configuration](configuration.md)**: Parser configuration options and resolution strategies
- **[Argument files specification](argument-files.md)**: Complete argument file syntax and processing semantics
