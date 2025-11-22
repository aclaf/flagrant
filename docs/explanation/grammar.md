# Parser grammar specification

This specification defines the formal grammar for valid command-line input that Flagrant's parser accepts. The grammar covers how arguments are classified as options versus positionals, the syntax rules for long and short options (including value assignment), positional argument identification, and special constructs like dictionary arguments and the end-of-options delimiter.

The grammar presented here is **prescriptive**, defining what input is syntactically valid. The parser's behavior specification (`specs/parser/behavior.md`) describes how the parser processes valid input to produce parse results. The configuration specification (`specs/parser/configuration.md`) documents how parser configuration affects grammar interpretation.

This document uses Extended Backus-Naur Form (EBNF) notation for formal grammar rules, supplemented with prose explanations and concrete examples. The grammar is **deterministic given a parser configuration**. Different configurations (strict mode, negative number handling, subcommand definitions) result in different effective grammars, but each configuration produces deterministic parsing without ambiguity.

!!! important "Important distinction"
    This specification defines **syntactic rules** (token structure and classification). Semantic rules (option name matching, abbreviation, case conversion) are applied during parsing based on parser configuration and are documented in [Parser behavior](behavior.md).

## Table of contents

- [Purpose](#purpose)
- [Grammar notation](#grammar-notation)
- [Argument classification](#argument-classification)
- [Long option syntax](#long-option-syntax)
- [Short option syntax](#short-option-syntax)
- [Positional argument syntax](#positional-argument-syntax)
- [Dictionary argument syntax](#dictionary-argument-syntax)
- [Value syntax](#value-syntax)
- [Complete formal grammar](#complete-formal-grammar)
- [Examples and edge cases](#examples-and-edge-cases)

---

## Grammar notation

This specification uses Extended Backus-Naur Form (EBNF) with the following conventions:

- `::=` defines a production rule
- `|` separates alternatives
- `( )` groups elements
- `[ ]` indicates optional elements (zero or one occurrence)
- `{ }` indicates repetition (zero or more occurrences)
- `" "` denotes literal strings or characters
- `< >` denotes terminal symbols or character classes
- `?` suffix means zero or one occurrence (equivalent to `[ ]`)
- `+` suffix means one or more occurrences
- `*` suffix means zero or more occurrences

Character classes use standard notation:

- `<ALPHA>` = alphabetic characters (a-z, A-Z)
- `<DIGIT>` = decimal digits (0-9)
- `<ALNUM>` = alphanumeric characters (any character in `<ALPHA>` or `<DIGIT>`)
- `<CHAR>` = any character except null; in practice, any character that can appear in shell arguments
- `<SPACE>` = space (U+0020) or tab (U+0009)

The grammar defines the **syntactic structure** of command-line input. Semantic constraints (like arity validation) are enforced during parsing but are not part of the grammar itself.

## Argument classification

The parser classifies each argument into one of several categories based on its structure and position in the argument sequence. This classification determines how the argument is processed.

### Classification rules

Arguments are classified using the following precedence:

1. **End-of-options delimiter:** A standalone `--` argument marks the boundary between parsed arguments and trailing arguments
2. **Long option:** An argument starting with `--` followed by at least one character
3. **Short option:** An argument starting with `-` followed by exactly one character (or a cluster of characters)
4. **Negative number:** An argument matching the negative number pattern (configurable, default: `-?\d+(\.\d+)?`)
5. **Subcommand name:** An argument matching a defined subcommand name
6. **Positional argument:** Any other argument

The classification algorithm operates left-to-right with context from previous classifications. In strict positional mode, once the first positional is encountered, all subsequent arguments become positionals regardless of their structure.

### Formal classification grammar

```ebnf
argument ::= end_of_options
           | long_option
           | short_option
           | negative_number
           | subcommand_name
           | positional_argument
           | single_dash

end_of_options ::= "--"

long_option ::= "--" long_option_name [ inline_value ]

short_option ::= "-" short_option_chars [ inline_value ]

single_dash ::= "-"

negative_number ::= "-" <DIGIT>+ [ "." <DIGIT>+ ]

subcommand_name ::= <IDENTIFIER>

positional_argument ::= <ARGUMENT_STRING>
```

Where:

- `<IDENTIFIER>` is a valid subcommand name as defined in the command specification
- `<ARGUMENT_STRING>` is any string that doesn't match other patterns
- `inline_value` is defined in later sections for long and short options

### Classification context rules

**After end-of-options delimiter:** All arguments following `--` are placed in trailing arguments without classification or parsing. They are preserved exactly as provided.

```bash
program --verbose -- --not-an-option file.txt
# Options: {verbose: True}
# Trailing: ["--not-an-option", "file.txt"]
```

**In strict positional mode:** Once the first positional argument is encountered, all subsequent arguments become positionals even if they structurally match option patterns.

```bash
# With strict_options_before_positionals=True
program --verbose file.txt --output result.txt
# Options: {verbose: True}
# Positionals: ["file.txt", "--output", "result.txt"]
```

**Negative numbers:** When `allow_negative_numbers=True` and positional specs are defined, arguments matching the negative number pattern are classified as positionals rather than short options.

```bash
# With allow_negative_numbers=True
program --threshold -5 --count -10
# Options: {threshold: "-5", count: "-10"}
# Both values are positionals consumed by their respective options
```

### Single dash special case

The single dash `-` (hyphen with no following characters) is always classified as a positional argument, following Unix convention where `-` represents stdin or stdout.

```bash
cat - file.txt
# Positional arguments: ["-", "file.txt"]
```

## Long option syntax

Long options use a double dash prefix followed by multi-character names. They support two value assignment methods: space-separated and equals-separated.

### Basic long option syntax

```ebnf
long_option ::= "--" long_option_name [ inline_value ]

long_option_name ::= <ALPHA> { <CHAR> }

inline_value ::= "=" value_string
               | <SPACE> value_string
```

Where:

- `long_option_name` must be at least one character
- The first character must be alphabetic
- Subsequent characters can be alphanumeric, dash, or underscore (subject to normalization)

**Minimum length:** Long option names must be at least 1 character. Single-character long options like `--v` are valid and distinct from short options `-v`.

**Valid characters:** By default, long option names can contain:

- Alphabetic characters (a-z, A-Z)
- Digits (0-9)
- Dashes (`-`)
- Underscores (`_`)

**Character normalization:** When `convert_underscores=True`, underscores and dashes are treated identically during matching.

**Case sensitivity:** When `case_sensitive_options=False`, all characters are normalized to lowercase during matching.

### Value assignment: space-separated

The standard syntax separates the option from its value with whitespace:

```bash
--output file.txt
--files file1.txt file2.txt file3.txt
```

The parser consumes values from following arguments until:

- Reaching the option's maximum arity
- Encountering another option (argument starting with `-`)
- Encountering a subcommand name
- Reaching the end of arguments

### Value assignment: equals-separated

Long options can use equals syntax for explicit value assignment:

```bash
--output=file.txt
--log-level=debug
```

**Equals syntax semantics:**

- **Single value consumption:** Only the value immediately after `=` is consumed, regardless of the option's maximum arity
- **Empty values allowed:** `--output=` assigns an empty string value
- **Equals in values:** The parser splits on the **first** equals sign only, so `--option=a=b=c` assigns value `a=b=c`
- **Arity validation:** Options requiring more than one value (`arity.min > 1`) raise `InsufficientValuesError` (see `specs/parser/errors.md`) when using equals syntax with a single value

```ebnf
equals_value ::= "=" value_content

value_content ::= <CHAR>*
```

The `value_content` extends from the first character after `=` to the end of the argument string, including any subsequent equals signs.

### Negation syntax

Long flags with defined negation words support negated forms:

```bash
--verbose          # Sets to True
--no-verbose       # Sets to False
--disable-verbose  # Sets to False (with negation_prefixes=frozenset({"no", "disable"}))
```

**Negation grammar:**

```ebnf
negated_flag ::= "--" negation_prefix "-" long_option_name
```

**Important:** Negated flags do not accept values (see `specs/parser/behavior.md`). Attempting to provide a value to a negated flag raises `FlagWithValueError`. Negation syntax is only supported for long options; short options use independent negation short names (see `FlagOptionSpecification.negation_short_names`).

Negation prefixes are configured per-option via `FlagOptionSpecification.negation_prefixes`. Each negation prefix word creates a valid negated form.

### Option name transformations

**Important:** The transformations described in this section (case-insensitive matching, abbreviation, underscore-dash equivalence) are **semantic matching rules** applied during parsing. They do not affect the syntactic grammar (what constitutes a valid option syntactically), only how option names are matched against defined specifications. These rules are documented in `specs/parser/behavior.md` under option resolution.

**Underscore to dash conversion:** When `convert_underscores=True`, both forms match:

```bash
--log_level=debug    # Matches "log-level" or "log_level"
--log-level=debug    # Matches "log-level" or "log_level"
```

**Case-insensitive matching:** When `case_sensitive_options=False`, all case variations match:

```bash
--verbose, --Verbose, --VERBOSE, --VeRbOsE
# All match the same option
```

**Abbreviated options:** When `allow_abbreviated_options=True`, unambiguous prefixes match:

```bash
# With options: verbose, version, verify
--verb     # Matches verbose (unambiguous)
--vers     # Matches version (unambiguous)
--ver      # Error: ambiguous (matches verbose, version, verify)
```

Minimum abbreviation length is configurable via `minimum_abbreviation_length` (default: 3).

## Short option syntax

Short options use a single dash prefix followed by single-character names. They support clustering (combining multiple flags), attached values, and equals-separated values.

### Basic short option syntax

```ebnf
short_option ::= "-" short_option_chars [ inline_value ]

short_option_chars ::= <ALPHA> { <ALNUM> }

inline_value ::= "=" value_string
               | value_string
               | <SPACE> value_string
```

Where:

- Each character in `short_option_chars` must be a valid short option name
- The first character must be alphabetic (`<ALPHA>`)
- Subsequent characters can be alphanumeric (`<ALNUM>`: letters or digits)
- `value_string` is consumed only if the last option accepts values

**Single character requirement:** Each short option name is exactly one character. Multi-character sequences like `-abc` represent clustering (multiple short options), not a single multi-character option.

**Valid characters:** Short option names can be:

- Alphabetic characters (a-z, A-Z) - required for first character in cluster
- Digits (0-9) - allowed in cluster positions after the first character when explicitly defined as short option names

### Option clustering

Short flags can combine into a single argument:

```bash
-abc     # Equivalent to: -a -b -c
-vqf     # Equivalent to: -v -q -f
```

**Clustering rules:**

1. All inner options (except the last) must be flags (arity `(0, 0)`)
2. Only the last option in a cluster can accept values
3. Each character must match a defined short option
4. Unknown characters raise `UnknownOptionError`

**Clustering with values:**

```bash
-vfo file.txt    # Valid: -v, -f are flags, -o takes "file.txt"
-vof file.txt    # Invalid: -o requires value but -f follows it
```

**Clustering grammar:**

```ebnf
short_option_cluster ::= "-" flag_char+ [ value_option_char [ inline_value ] ]

flag_char ::= <ALPHA>    /* Must match a flag option */

value_option_char ::= <ALPHA>    /* Must match an option accepting values */
```

### Value assignment: space-separated

The standard syntax separates the option from its value with whitespace:

```bash
-o file.txt
-f file1.txt file2.txt
```

The parser consumes values from following arguments using the same rules as long options: stopping at maximum arity, other options, subcommands, or end of arguments.

### Value assignment: attached values

Values can attach directly to short options without any separator:

```bash
-ofile.txt         # Equivalent to: -o file.txt
-abcofile.txt      # Equivalent to: -a -b -c -o file.txt
```

**Attached value grammar:**

```ebnf
attached_value ::= value_string    /* Immediately following option character */
```

**Important:** Attached values are **not valid** for flags (arity `(0, 0)`). Attempting to attach a value to a flag raises `OptionDoesNotAcceptValueError`:

```bash
-vverbose    # Error: 'v' is a flag and cannot accept "verbose"
```

### Value assignment: equals-separated

Short options can use equals syntax:

```bash
-o=file.txt
-abc -o=file.txt
```

The equals syntax has the same semantics as long options:

- Single value consumption (only value after `=`)
- Empty values allowed: `-o=`
- Equals signs in values: `-o=a=b` assigns `a=b`

**Equals in clusters:**

An equals sign within a clustered string marks the start of an inline value for the last option:

```bash
-abc=value     # Sets -a, -b; assigns "value" to -c
-ab=c          # Sets -a; assigns "c" to -b (even if -c is defined)
```

### Accumulation with clustering

Short option clustering interacts with accumulation modes:

```bash
# With COUNT accumulation mode
-vvv    # verbose = 3 (each 'v' increments count)
```

Each occurrence of an option character in a cluster is processed as a separate instance, applying the accumulation mode accordingly.

## Positional argument syntax

Positional arguments are identified by position rather than prefix markers. They are the arguments remaining after option processing.

### Positional classification

An argument is positional if it:

1. Does not start with `-` (unless it's a single dash `-`)
2. Does not match a subcommand name
3. Has not been consumed as an option value
4. Does not appear after the `--` delimiter (those become trailing arguments)

Additionally, in strict positional mode, arguments that structurally look like options become positionals if they appear after the first positional argument.

### Positional syntax

```ebnf
positional_argument ::= <ARGUMENT_STRING>

<ARGUMENT_STRING> ::= <CHAR>+
```

Where `<ARGUMENT_STRING>` is any non-empty string that doesn't match option patterns or subcommand names in the current context.

**No syntactic restrictions:** Positional arguments can contain any characters including dashes, equals signs, and special characters. The parser treats them as opaque strings.

### Positional grouping

Positional arguments are **collected during parsing** and **grouped after option processing**. The grouping algorithm assigns arguments to positional specs based on arity constraints.

The grouping algorithm is detailed in `specs/parser/behavior.md` and `specs/concepts.md`. Key points:

- Arguments are assigned left-to-right to positional specs in order
- Each positional spec consumes arguments according to its arity
- Unbounded positionals consume as much as possible while reserving values for later positionals with minimum requirements

**Implicit positional spec:** When no positional specs are defined, the parser creates an implicit spec named "args" with arity `(0, None)` to capture all positionals.

### Interaction with strict mode

When `strict_options_before_positionals=True`:

- Once the first positional is encountered, all subsequent arguments become positionals
- This includes arguments that structurally look like options

```bash
# With strict mode
program --verbose file.txt --output result.txt
# Positionals: ["file.txt", "--output", "result.txt"]
```

Without strict mode, options and positionals can be freely intermixed.

## Dictionary argument syntax

Dictionary arguments enable users to pass structured key-value data through the command line. This section provides a **summary** of dictionary syntax; see `specs/parser/dictionary-parsing.md` for the comprehensive specification.

### Flat dictionary syntax

Basic key-value pairs use equals as the separator:

```bash
--config key=value
--config key1=value1 key2=value2
--config key1=value1 --config key2=value2
```

**Multiple pairs:** Dictionary arguments support both repeated option pattern and accumulated pattern (multiple pairs after a single flag).

### Nested dictionary syntax

Dot notation creates nested structures:

```bash
--config database.host=localhost
--config database.connection.timeout=30
```

**Nesting rules:**

- Dots (`.`) separate nesting levels
- Escaped dots (`\.`) become literal dots in keys
- Nested paths can be specified in any order

### List syntax in dictionaries

Bracket notation specifies list indices:

```bash
--config servers[0]=web1
--config servers[1]=web2
--config matrix[0][0]=1 matrix[0][1]=2
```

**Index rules:**

- Indices are zero-based integers
- Indices need not be consecutive (gaps filled with defaults)
- Negative indices are not supported

### Lists of dictionaries

Combining brackets and dots creates structured list elements:

```bash
--config users[0].name=alice users[0].role=admin
--config users[1].name=bob users[1].role=user
```

### Special character escaping

**Dots in keys:** Escape with backslash within quotes:

```bash
--config 'service\.kubernetes\.io/name=myservice'
```

**Brackets in keys:** Escape with backslash:

```bash
--config 'metadata\[annotation\]=value'
```

**Equals in keys:** Escape with backslash:

```bash
--config 'key\=with\=equals=value'
```

**Equals in values:** No escaping needed (parser splits on first equals):

```bash
--config equation="x=y+z"
```

### JSON fallback syntax

For complex structures, JSON format provides an alternative:

```bash
--config-json '{"database": {"host": "localhost", "port": 5432}}'
```

JSON and key-value syntax can be mixed, with later values overriding earlier ones.

### Dictionary grammar (summary)

```ebnf
dict_argument ::= dict_pair { <SPACE> dict_pair }

dict_pair ::= key_path "=" value_string

key_path ::= segment { accessor }

segment ::= <IDENTIFIER> | <QUOTED_STRING>

accessor ::= "." segment
           | "[" <DIGIT>+ "]"

value_string ::= <CHAR>*
```

See `specs/parser/dictionary-parsing.md` for complete grammar, type conversion rules, and error handling.

## Value syntax

Values are the arguments consumed by options and positionals. The parser treats all values as strings without type conversion.

### Value structure

```ebnf
value_string ::= <CHAR>*
```

Values are arbitrary character sequences. The parser does not interpret their content or perform type conversion.

### Empty values

Empty values are valid when specified explicitly:

```bash
--output=           # Empty string value
--config key=       # Empty string value for "key"
```

Empty values satisfy minimum arity requirements. An option with arity `(1, 1)` accepts an empty string as its single required value.

### Quoted values

Shell quoting affects how values are parsed **before** they reach Flagrant. The parser receives values after shell processing:

```bash
--name="Alice Smith"       # Parser receives: name → "Alice Smith"
--message='Hello, World!'  # Parser receives: message → "Hello, World!"
```

The parser does not perform its own quote processing; it operates on the argument array provided by the shell.

### Values with special characters

**Spaces:** Require shell quoting to prevent splitting:

```bash
--description "A long description with spaces"
```

**Equals signs:** No escaping needed in values (parser splits on first equals only):

```bash
--equation "x=y+z"
--query "name=value&foo=bar"
```

**Dashes:** No special handling required:

```bash
--range "1-100"
--pattern "multi-word-pattern"
```

**Whitespace:** Leading and trailing whitespace is preserved:

```bash
--value "  content  "    # Preserves spaces
```

## Complete formal grammar

This section presents the complete formal grammar in EBNF notation, consolidating all rules from previous sections.

### Top-level grammar

```ebnf
command_line ::= { argument }

argument ::= end_of_options
           | long_option
           | short_option
           | negative_number
           | subcommand_name
           | positional_argument
           | single_dash

end_of_options ::= "--"

single_dash ::= "-"
```

### Long option grammar

```ebnf
long_option ::= "--" long_option_name [ inline_value ]
              | "--" negation_prefix "-" long_option_name [ inline_value ]

long_option_name ::= <ALPHA> { <ALNUM> | "-" | "_" }

inline_value ::= "=" value_content
               | <SPACE> value_string

value_content ::= <CHAR>*

negation_prefix ::= <ALPHA> { <ALNUM> | "-" | "_" }
```

### Short option grammar

```ebnf
short_option ::= "-" short_option_chars [ inline_value ]

short_option_chars ::= flag_char* [ value_option_char ]

flag_char ::= <ALPHA>

value_option_char ::= <ALPHA>

inline_value ::= "=" value_content
               | value_string
               | <SPACE> value_string
```

### Positional grammar

```ebnf
positional_argument ::= <ARGUMENT_STRING>

<ARGUMENT_STRING> ::= <CHAR>+
```

### Subcommand grammar

```ebnf
subcommand_invocation ::= subcommand_name [ { argument } ]

subcommand_name ::= <IDENTIFIER>

<IDENTIFIER> ::= <ALPHA> { <ALNUM> | "-" | "_" }
```

**Subcommand semantics:** When a subcommand name is matched:

- All remaining arguments (including those that syntactically match option patterns) are classified as arguments to the subcommand
- Subcommand arguments are not processed by the parent command's parser
- The parser transitions to the subcommand's specification for further parsing

### Negative number grammar

```ebnf
negative_number ::= "-" <DIGIT>+ [ "." <DIGIT>+ ]
```

### Dictionary argument grammar (summary)

```ebnf
dict_argument ::= dict_pair { <SPACE> dict_pair }

dict_pair ::= key_path "=" value_string

key_path ::= segment { accessor }

segment ::= <IDENTIFIER>
          | <QUOTED_STRING>

accessor ::= "." segment
           | "[" <DIGIT>+ "]"

value_string ::= <CHAR>*
```

**Note on special character escaping:** The dictionary grammar above shows the basic structure. Special characters (dots, brackets, equals signs) within keys are handled through shell quoting and escape sequences. See `specs/parser/dictionary-parsing.md` for the complete grammar including escape rules, type conversion rules, and error handling.

### Character classes

```ebnf
<ALPHA> ::= "a" | "b" | ... | "z" | "A" | "B" | ... | "Z"

<DIGIT> ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"

<ALNUM> ::= <ALPHA> | <DIGIT>

<CHAR> ::= /* any printable character */

<SPACE> ::= " " | "\t"
```

## Examples and edge cases

This section provides concrete examples demonstrating grammar rules and documenting edge cases.

### Long option examples

**Basic long options:**

```bash
--verbose
--output file.txt
--files file1.txt file2.txt file3.txt
```

**Equals syntax:**

```bash
--output=file.txt
--log-level=debug
--equation=x=y+z        # Value is "x=y+z"
```

**Empty values:**

```bash
--output=               # Empty string
--path=                 # Empty string
```

**Negation:**

```bash
--verbose               # True
--no-verbose            # False
--disable-color         # False (with negation_prefixes=frozenset({"no", "disable"}))
```

**Single-character long options:**

```bash
--v                     # Valid long option named "v"
-v                      # Short option named "v"
# These are distinct options
```

### Short option examples

**Basic short options:**

```bash
-v
-o file.txt
-f file1.txt file2.txt
```

**Clustering:**

```bash
-abc                    # Equivalent to: -a -b -c
-vfo file.txt           # -v, -f flags; -o takes "file.txt"
```

**Attached values:**

```bash
-ofile.txt              # Equivalent to: -o file.txt
-abcofile.txt           # -a, -b, -c flags; -o takes "file.txt"
```

**Equals syntax:**

```bash
-o=file.txt
-abc=value              # -a, -b flags; -c takes "value"
```

**Invalid clustering:**

```bash
-vof file.txt           # Error: -o requires value but -f follows
-vverbose               # Error: -v is flag, cannot accept "verbose"
```

### Positional examples

**Basic positionals:**

```bash
program file1.txt file2.txt
program src/ dest/
```

**Mixed with options:**

```bash
program --verbose file.txt --output result.txt
# Options: {verbose: True, output: "result.txt"}
# Positionals: ["file.txt"]
```

**Strict mode:**

```bash
# With strict_options_before_positionals=True
program --verbose file.txt --output result.txt
# Options: {verbose: True}
# Positionals: ["file.txt", "--output", "result.txt"]
```

**Single dash as positional:**

```bash
cat - file.txt
# Positionals: ["-", "file.txt"]
```

### Dictionary examples

**Flat dictionaries:**

```bash
--config debug=true log_level=INFO
--config key1=value1 --config key2=value2
```

**Nested dictionaries:**

```bash
--config database.host=localhost database.port=5432
--config database.connection.timeout=30
```

**Lists in dictionaries:**

```bash
--config servers[0]=web1 servers[1]=web2
--config matrix[0][0]=1 matrix[0][1]=2 matrix[1][0]=3 matrix[1][1]=4
```

**Lists of dictionaries:**

```bash
--config users[0].name=alice users[0].role=admin
--config users[1].name=bob users[1].role=user
```

**Escaped keys:**

```bash
--config 'service\.kubernetes\.io/name=myservice'
--config 'metadata\[annotation\]=value'
```

### Trailing argument examples

**Basic trailing:**

```bash
program --verbose -- --not-an-option file.txt
# Options: {verbose: True}
# Trailing: ["--not-an-option", "file.txt"]
```

**Subprocess arguments:**

```bash
docker run image -- command --flag value
# Options for docker: {run: ...}
# Trailing: ["command", "--flag", "value"]
```

**Disambiguating option-like values:**

```bash
grep -- -pattern file.txt
# Positionals: []
# Trailing: ["-pattern", "file.txt"]
```

### Edge cases

**Empty equals syntax:**

```bash
--option=               # Valid for value options: empty string
```

**Equals in option names (not supported):**

```bash
--key=name=value        # Parsed as: option="key", value="name=value"
```

**Multiple equals in values:**

```bash
--option=a=b=c          # Value is "a=b=c"
--url=http://example.com?foo=bar&baz=qux
# Value is "http://example.com?foo=bar&baz=qux"
```

**Negative numbers:**

```bash
# With allow_negative_numbers=True
--count -5              # count gets value "-5"
-5                      # Positional argument "-5"

# With allow_negative_numbers=False
-5                      # Treated as short option cluster (error if -5 not defined)
```

**Option-like positionals in strict mode:**

```bash
# strict_options_before_positionals=True
program file.txt --verbose
# Positionals: ["file.txt", "--verbose"]
```

**Underscore and dash equivalence:**

```bash
# With convert_underscores=True
--log_level=debug       # Matches "log-level" or "log_level"
--log-level=debug       # Matches "log-level" or "log_level"
```

**Case-insensitive matching:**

```bash
# With case_sensitive_options=False
--Verbose, --verbose, --VERBOSE    # All match the same option
```

**Abbreviated options:**

```bash
# With allow_abbreviated_options=True, options: verbose, version, verify
--verb                  # Matches "verbose"
--ver                   # Error: ambiguous (verbose, version, verify)
--verbos                # Matches "verbose"
```

---

**Related pages:**

- [Concepts](concepts.md) - Arity, accumulation modes, option resolution
- [Behavior](behavior.md) - Value consumption algorithm, positional grouping
- [Configuration](configuration.md) - Parser configuration affecting grammar interpretation
- [Dictionary parsing](dictionary-parsing.md) - Complete dictionary argument specification
- [Types](types.md) - Parse result types and value structures
- [Errors](errors.md) - Validation errors and error conditions
