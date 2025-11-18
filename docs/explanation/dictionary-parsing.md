# Dictionary parsing specification

--8<-- "unreleased.md"

!!! warning "Not yet implemented"
    Dictionary option parsing with AST construction and structured merge semantics is planned but not yet fully implemented. This document describes the intended design and specification. The current parser treats dictionary option values as simple strings. Full dictionary parsing will be added in a future release.

This page specifies the parsing algorithms for dictionary options in Flagrant. It covers lexical analysis, syntactic parsing, abstract syntax tree construction, tree building, merging strategies, and error handling for transforming key-value argument strings into structured dictionary values.

Dictionary options use `DictAccumulationMode` to control how multiple occurrences are combined. The accumulation mode determines whether dictionaries are merged (MERGE with SHALLOW or DEEP strategy), replaced (FIRST/LAST), collected separately (APPEND), or rejected (ERROR). See [Concepts](concepts.md) and [Parser behavior](behavior.md) for complete accumulation mode semantics.

## Table of contents

- [Syntax specification](#syntax-specification)
  - [Flat dictionaries](#flat-dictionaries)
  - [Nested dictionaries](#nested-dictionaries)
  - [Lists in dictionaries](#lists-in-dictionaries)
  - [Escaping special characters](#escaping-special-characters)
- [Lexical analysis](#lexical-analysis)
  - [Token types](#token-types)
  - [Escaping rules](#escaping-rules)
- [Syntactic analysis](#syntactic-analysis)
  - [Path parsing](#path-parsing)
  - [Value parsing](#value-parsing)
- [Abstract syntax tree](#abstract-syntax-tree)
  - [AST representation](#ast-representation)
- [Tree construction algorithm](#tree-construction-algorithm)
  - [Construction steps](#construction-steps)
  - [List handling](#list-handling)
  - [Type conflict detection](#type-conflict-detection)
- [Merging algorithms](#merging-algorithms)
  - [Shallow merge](#shallow-merge)
  - [Deep merge](#deep-merge)
  - [Conflict resolution](#conflict-resolution)
- [Value consumption](#value-consumption)
- [Error handling](#error-handling)
- [Examples](#examples)
  - [Basic configuration](#basic-configuration)
  - [Nested database configuration](#nested-database-configuration)
  - [Server pool with list of dictionaries](#server-pool-with-list-of-dictionaries)
  - [Kubernetes annotations with escaped keys](#kubernetes-annotations-with-escaped-keys)
  - [Mixed types with deep merging](#mixed-types-with-deep-merging)

---

## Syntax specification

Dictionary option syntax supports flat key-value pairs, nested dictionaries using dot notation, and lists using bracket notation. This section defines the complete syntax grammar.

### Flat dictionaries

The fundamental syntax for dictionary entries uses `key=value` format:

```ebnf
flat_entry     ::= key "=" value
key            ::= identifier | escaped_identifier
value          ::= <any string after first equals sign>
identifier     ::= [a-zA-Z_][a-zA-Z0-9_-]*
```

multiple entries are provided as separate arguments when arity permits:

```bash
--config key1=value1 key2=value2 key3=value3
```

Produces: `{"key1": "value1", "key2": "value2", "key3": "value3"}`

### Nested dictionaries

Nested dictionaries use dot notation to specify paths through nested structures:

```ebnf
nested_entry   ::= nested_key "=" value
nested_key     ::= key_segment ("." key_segment)*
key_segment    ::= identifier | escaped_identifier
```

Examples:

```bash
--config database.host=localhost
# {"database": {"host": "localhost"}}

--config database.connection.timeout=30
# {"database": {"connection": {"timeout": "30"}}}
```

The parser creates intermediate dictionary levels as needed. multiple nested paths can coexist and merge:

```bash
--config database.host=localhost database.port=5432
# {"database": {"host": "localhost", "port": "5432"}}
```

### Lists in dictionaries

Lists use bracket notation with zero-based integer indices:

```ebnf
list_entry     ::= list_path "=" value
list_path      ::= path_segment ("[" index "]" path_segment?)*
path_segment   ::= identifier ("." identifier)*
index          ::= [0-9]+
```

Examples:

```bash
--config servers[0]=web1
# {"servers": ["web1"]}

--config servers[0].host=web1 servers[0].port=80
# {"servers": [{"host": "web1", "port": "80"}]}
```

Mixed nesting with dictionaries and lists:

```bash
--config users[0].name=alice users[0].tags[0]=admin users[0].tags[1]=dev
# {
#   "users": [
#     {
#       "name": "alice",
#       "tags": ["admin", "dev"]
#     }
#   ]
# }
```

### Escaping special characters

Keys containing special characters (`.`, `[`, `]`, `=`) require backslash escaping:

```ebnf
escaped_identifier ::= (character | escaped_char)*
escaped_char       ::= "\\" special_char
special_char       ::= "." | "[" | "]" | "="
```

Examples:

```bash
# Key with literal dots
--config 'service\.kubernetes\.io/name=myservice'
# {"service.kubernetes.io/name": "myservice"}

# Key with brackets
--config 'metadata\[annotation\]=value'
# {"metadata[annotation]": "value"}
```

The backslash is removed during lexical analysis, producing the literal character.

## Lexical analysis

Lexical analysis tokenizes input strings into a stream of tokens representing keys, operators, values, and structural elements.

### Token types

The lexer recognizes these token categories:

| Token Type | Description | Examples |
|------------|-------------|----------|
| IDENTIFIER | Unquoted sequences of word characters, dots, slashes, hyphens | `key`, `host`, `io/name` |
| EQUALS | Key-value separator | `=` |
| LBRACKET | Opens list index | `[` |
| RBRACKET | Closes list index | `]` |
| DOT | Nesting separator (when not part of identifier) | `.` |
| INTEGER | Numeric list index within brackets | `0`, `42`, `100` |
| QUOTED_STRING | Content within quotes (quotes stripped) | `"value"`, `'value'` |
| ESCAPED_CHAR | Backslash followed by special character | `\.`, `\[`, `\=` |

### Escaping rules

Backslash escapes the following character, preventing it from being interpreted as syntax. The escape character itself is removed during lexical analysis.

```text
Input:  key\.with\.dots=value
Tokens: IDENTIFIER("key.with.dots"), EQUALS, IDENTIFIER("value")

Input:  data\[0\]=value
Tokens: IDENTIFIER("data[0]"), EQUALS, IDENTIFIER("value")
```

Shell quoting is processed before the lexer sees input, so the lexer handles both escaped characters that survived shell processing and quoted strings.

## Syntactic analysis

Syntactic analysis builds an abstract syntax tree representing the structure of dictionary assignments by parsing paths and values.

### Path parsing

Paths consist of alternating names and accessors (dots for nesting, brackets for indexing):

```ebnf
path      ::= segment (accessor segment)*
segment   ::= IDENTIFIER | QUOTED_STRING
accessor  ::= DOT | LBRACKET INTEGER RBRACKET
```

Examples:

```text
simple           → ["simple"]
nested.path      → ["nested", "path"]
list[0]          → ["list", 0]
complex[0].key   → ["complex", 0, "key"]
```

The parser validates path structure during parsing, ensuring:

- Brackets contain only non-negative integers
- Dots separate valid identifiers
- Path is non-empty

### Value parsing

Values are initially treated as strings, with type conversion deferred to later phases. The parser preserves exact string value including leading/trailing whitespace if explicitly quoted.

```bash
--config key=value              # "value"
--config key="  value  "        # "  value  " (whitespace preserved)
--config key=''                 # "" (empty string)
--config key="contains=equals"  # "contains=equals"
```

## Abstract syntax tree

The parser produces an immutable abstract syntax tree representing all parsed dictionary operations.

### AST representation

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class DictPath:
    """Path through nested dictionaries and lists."""
    segments: tuple[str | int, ...]

@dataclass(frozen=True, slots=True)
class DictAssignment:
    """Assignment to a dictionary location."""
    path: DictPath
    value: str  # Always string at this stage

@dataclass(frozen=True, slots=True)
class DictAST:
    """Collection of assignments forming a dictionary specification."""
    assignments: tuple[DictAssignment, ...]
```

Example AST for `--config database.host=localhost database.port=5432`:

```python
DictAST(
    assignments=(
        DictAssignment(
            path=DictPath(segments=("database", "host")),
            value="localhost"
        ),
        DictAssignment(
            path=DictPath(segments=("database", "port")),
            value="5432"
        ),
    )
)
```

## Tree construction algorithm

The construction phase transforms the AST into an actual dictionary structure, handling merging, conflict detection, and list construction.

### Construction steps

The algorithm processes assignments in order, building the dictionary incrementally:

```python
def construct_dict(ast: DictAST) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for assignment in ast.assignments:
        current = result
        path = assignment.path.segments

        # Navigate to target location
        for i, segment in enumerate(path[:-1]):
            next_segment = path[i + 1]

            if isinstance(next_segment, int):
                # Next level is a list
                if segment not in current:
                    current[segment] = []
                elif not isinstance(current[segment], list):
                    if isinstance(current[segment], dict):
                        raise TypeError(f"Cannot use '{segment}' as both list and dict")
                    else:
                        raise TypeError(f"Cannot use '{segment}' as list (current type: {type(current[segment]).__name__})")
                current = current[segment]
            else:
                # Next level is a dict
                if segment not in current:
                    current[segment] = {}
                elif not isinstance(current[segment], dict):
                    if isinstance(current[segment], list):
                        raise TypeError(f"Cannot use '{segment}' as both dict and list")
                    else:
                        raise TypeError(f"Cannot use '{segment}' as dict (current type: {type(current[segment]).__name__})")
                current = current[segment]

        # Set final value
        final_key = path[-1]
        if isinstance(current, list):
            # Validate that final_key is an integer for list indexing
            if not isinstance(final_key, int):
                raise TypeError(f"List indices must be integers, got {type(final_key).__name__}: {final_key!r}")
            # Extend list if needed
            while len(current) <= final_key:
                current.append(None)
            current[final_key] = assignment.value
        else:
            current[final_key] = assignment.value

    return result
```

### List handling

When list indices are specified:

1. The list is created if it doesn't exist
2. The list is extended with `None` values to reach the required index
3. The value is assigned at the specified index

For sparse lists (when `allow_sparse_lists=False`):

- Validation checks for missing indices after construction
- Raises error if gaps exist

For duplicate indices (when `allow_duplicate_list_indices=False`):

- Tracks seen indices during construction
- Raises error if same index appears multiple times

### Type conflict detection

Type conflicts occur when attempting to use the same key path as both a dictionary and a list:

```bash
--config database.connection.timeout=30 --config database.connection=invalid
# Error: Cannot assign string to 'database.connection' which has nested structure
```

The algorithm detects conflicts by checking the current type at each path segment before navigation.

## Merging algorithms

When `accumulation_mode=DictAccumulationMode.MERGE`, dictionaries from multiple option occurrences are merged according to the `merge_strategy`.

### Shallow merge

Shallow merge combines top-level keys only. Nested dictionaries are replaced entirely:

```python
def shallow_merge(dict1: dict[str, Any], dict2: dict[str, Any]) -> dict[str, Any]:
    """Shallow merge: dict2 keys overwrite dict1 keys."""
    result = dict1.copy()
    result.update(dict2)
    return result
```

Example:

```bash
# First occurrence: --config database.host=localhost
# {"database": {"host": "localhost"}}

# Second occurrence: --config database.port=5432
# {"database": {"port": "5432"}}

# Shallow merge result:
# {"database": {"port": "5432"}}  # First occurrence replaced
```

### Deep merge

Deep merge recursively merges nested dictionary structures:

```python
def deep_merge(dict1: dict[str, Any], dict2: dict[str, Any]) -> dict[str, Any]:
    """Deep merge: recursively merge nested dictionaries."""
    result = dict1.copy()

    for key, value2 in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value2, dict):
            # Both values are dicts: merge recursively
            result[key] = deep_merge(result[key], value2)
        else:
            # Otherwise: overwrite
            result[key] = value2

    return result
```

Example:

```bash
# First occurrence: --config database.host=localhost
# {"database": {"host": "localhost"}}

# Second occurrence: --config database.port=5432
# {"database": {"port": "5432"}}

# Deep merge result:
# {"database": {"host": "localhost", "port": "5432"}}  # Merged
```

### Conflict resolution

When merging dictionaries with conflicting types (for example, string vs. nested dict):

- The later value overwrites the earlier value
- No error is raised unless `strict_structure=True`

With `strict_structure=True`:

- Type mismatches raise validation errors
- Ensures dictionary structure remains consistent

## Value consumption

Dictionary options consume values according to their `arity` specification. The parser applies standard value consumption rules (see [parser behavior specification](behavior.md)) with dictionary-specific considerations:

1. **Parse each argument as key=value**: Split on first `=` to extract key and value
2. **Parse key path**: Tokenize and parse the key into path segments
3. **Accumulate assignments**: Build AST with all parsed assignments
4. **Construct dictionary**: Build final dictionary from AST
5. **Merge if needed**: Apply merge strategy if accumulation mode is MERGE

When `allow_item_separator=True`, a single argument can contain multiple key-value pairs separated by the item separator character:

```bash
# With item_separator=","
--config a=1,b=2,c=3
# Equivalent to: --config a=1 b=2 c=3
```

## Error handling

Dictionary parsing can encounter several error conditions:

**Parse errors** (malformed syntax):

```text
Error parsing dictionary argument: missing value
  Argument: 'key='
  Expected a value after the equals sign

Error parsing dictionary argument: invalid list index
  Argument: 'list[abc]=value'
  List indices must be non-negative integers
```

**Structural errors** (type conflicts):

```text
Error: Type mismatch at 'database'
  Current type: dict
  Attempted use: list (via database[0])

You cannot use 'database' as both a dictionary and a list
```

**Validation errors** (constraint violations):

```text
Error: Sparse list not allowed at 'items'
  Indices: [0, 2, 5]
  Missing indices: [1, 3, 4]

Use consecutive indices or enable allow_sparse_lists

Error: Duplicate list index at 'servers'
  Index: 0

Use unique indices or enable allow_duplicate_list_indices
```

See the [error types specification](errors.md) for complete error type hierarchy and error message formatting.

## Examples

### Basic configuration

```bash
myapp --config debug=true --config log_level=INFO --config timeout=30
```

Result:

```python
{"debug": "true", "log_level": "INFO", "timeout": "30"}
```

### Nested database configuration

```bash
myapp \
  --config database.host=localhost \
  --config database.port=5432 \
  --config database.name=mydb \
  --config database.connection.timeout=30 \
  --config database.connection.retries=3
```

Result:

```python
{
    "database": {
        "host": "localhost",
        "port": "5432",
        "name": "mydb",
        "connection": {
            "timeout": "30",
            "retries": "3"
        }
    }
}
```

### Server pool with list of dictionaries

```bash
myapp \
  --config servers[0].host=web1.example.com \
  --config servers[0].port=80 \
  --config servers[1].host=web2.example.com \
  --config servers[1].port=80 \
  --config servers[2].host=web3.example.com \
  --config servers[2].port=8080
```

Result:

```python
{
    "servers": [
        {"host": "web1.example.com", "port": "80"},
        {"host": "web2.example.com", "port": "80"},
        {"host": "web3.example.com", "port": "8080"}
    ]
}
```

### Kubernetes annotations with escaped keys

```bash
myapp --config 'annotations.service\.beta\.kubernetes\.io/load-balancer=internal'
```

Result:

```python
{
    "annotations": {
        "service.beta.kubernetes.io/load-balancer": "internal"
    }
}
```

### Mixed types with deep merging

```bash
myapp \
  --config app.name="My Application" \
  --config app.version=2.1 \
  --config app.debug=false \
  --config app.features[0]=auth \
  --config app.features[1]=api
```

Result:

```python
{
    "app": {
        "name": "My Application",
        "version": "2.1",
        "debug": "false",
        "features": ["auth", "api"]
    }
}
```

---

## See also

- **[Concepts](concepts.md)**: Dictionary option concepts and overview
- **[Parser behavior](behavior.md)**: General parsing behavior and value consumption
- **[Errors](errors.md)**: Error types and exception hierarchy
