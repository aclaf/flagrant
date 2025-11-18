# Reference

--8<-- "unreleased.md"

Welcome to the Reference section of the Flagrant documentation. This section provides comprehensive technical specifications, API documentation, and lookup resources for working with Flagrant.

## What you'll find here

Reference documentation is **information-oriented**, designed for accurate and complete technical descriptions. Unlike tutorials (learning through doing) or explanations (understanding concepts), reference documentation provides factual, authoritative specifications you can look up when needed.

This section is ideal for:

- Looking up API signatures and parameters
- Finding exact type definitions and constraints
- Checking module organization and imports
- Understanding technical specifications
- Referencing glossary terms and definitions

## API documentation

### [API index](api/index.md)

Complete overview of the Flagrant API surface, organized by module. Start here to understand the API structure and find the module you need.

### Core modules

#### [flagrant.parser](api/flagrant.parser.md)

The parsing engine that processes command-line arguments according to specifications. Contains the `Parser` class for parsing operations and `ParseResult` for immutable result structures.

**Key exports:** `Parser`, `ParseResult`, parsing configuration options

#### [flagrant.specification](api/flagrant.specification.md)

Declarative specifications that define CLI structure. All specifications are immutable dataclasses that can be validated, serialized, and composed independently of parsing.

**Key exports:** `CommandSpecification`, `FlagOptionSpecification`, `ValueOptionSpecification`, `DictOptionSpecification`, `SubcommandSpecification`, `PositionalSpecification`

### Supporting modules

#### [flagrant.constraints](api/flagrant.constraints.md)

Constraint validation utilities for specifications. Provides validators for arity constraints, name patterns, and other specification rules.

**Key exports:** arity validators, name validators, specification constraint checkers

#### [flagrant.enums](api/flagrant.enums.md)

Enumeration types for configuration and behavior control. Defines modes for accumulation, parsing styles, and other configurable behaviors.

**Key exports:** `AccumulationMode`, `DictAccumulationMode`, `ArgumentFileFormat`, `PositionalMode`

#### [flagrant.exceptions](api/flagrant.exceptions.md)

Complete exception hierarchy for error handling. Separates specification errors (invalid definitions) from parse errors (invalid user input).

**Key exports:** `FlagrantError`, `SpecificationError`, `ParseError`, and specialized error types

#### [flagrant.types](api/flagrant.types.md)

Type definitions and aliases used throughout Flagrant. Provides consistent type hints for complex structures and unions.

**Key exports:** type aliases, protocol definitions, generic type variables

## Technical specifications

### [Glossary](glossary.md)

Alphabetical reference of key terms, concepts, and technical vocabulary used throughout Flagrant. Each entry provides a concise definition, context, and cross-references to related concepts.

**Coverage:** over 100 terms including arity, accumulation, specifications, parsing concepts, configuration options, and architectural components

## Module organization

Flagrant's public API follows a clear organizational structure:

### Primary interfaces

The main entry points for using Flagrant:

- **`flagrant.parser`** - Parsing operations and results
- **`flagrant.specification`** - CLI structure definitions

### Type system

Supporting the primary interfaces with strong typing:

- **`flagrant.types`** - Type aliases and protocols
- **`flagrant.enums`** - Enumerated configuration values
- **`flagrant.constraints`** - Validation utilities

### Error handling

Structured error reporting:

- **`flagrant.exceptions`** - Exception hierarchy for all error cases

## Working with specifications

Specifications are immutable dataclass trees that define CLI structure in a declarative way:

1. **Root specification**: `CommandSpecification` defines the top-level command
2. **Option specifications**: Define flags, value options, and dictionary options
3. **Positional specifications**: Define positional arguments with arity constraints
4. **Subcommand specifications**: Define nested command structures

All specifications are:

- **Immutable**: Frozen dataclasses remain unchanged after creation
- **Validating**: Construction-time validation ensures correctness
- **Composable**: Combine to build complex CLI structures
- **Serializable**: Convert to/from dictionaries for persistence

## Working with the parser

The parser processes raw arguments according to specifications:

1. **Create parser**: Initialize with configuration options
2. **Parse arguments**: Pass specification and argument list
3. **Handle results**: Process immutable `ParseResult` or catch `ParseError`

Parser characteristics:

- **Stateless**: No internal state between parse operations
- **Thread-safe**: Share safely across threads
- **Configurable**: Extensive options for different CLI styles
- **Deterministic**: Same inputs always produce same outputs

## Type safety

Flagrant emphasizes comprehensive type safety:

- All public APIs have complete type hints
- Uses `basedpyright` for strict type checking
- Leverages `typing-extensions` for modern type features
- Protocols define structural interfaces
- Generic types enable flexible yet safe APIs

## Error handling patterns

Flagrant uses structured exceptions with rich context:

- **Base exception**: `FlagrantError` for all Flagrant errors
- **Categories**: Specification vs parse errors
- **Context**: Structured data about error location and cause
- **No string parsing**: Errors provide data, not formatted messages

## Quick reference

### Common imports

```python
from flagrant.parser import Parser, ParseResult
from flagrant.specification import (
    CommandSpecification,
    FlagOptionSpecification,
    ValueOptionSpecification,
    DictOptionSpecification,
    SubcommandSpecification,
    PositionalSpecification,
)
from flagrant.enums import AccumulationMode, DictAccumulationMode
from flagrant.exceptions import ParseError, SpecificationError
```

### Basic usage pattern

```python
# Define specification
spec = CommandSpecification(
    name="myapp",
    options=[
        FlagOptionSpecification(names=["--verbose", "-v"]),
        ValueOptionSpecification(names=["--output", "-o"]),
    ],
    positionals=[
        PositionalSpecification(name="input", arity="1"),
    ],
)

# Create parser
parser = Parser()

# Parse arguments
try:
    result = parser.parse(spec, ["--verbose", "-o", "out.txt", "input.txt"])
    # Process result...
except ParseError as e:
    # Handle parse error...
```

## Related sections

- **[Explanations](../explanation/index.md)**: Conceptual understanding and design rationale
- **[Architecture](../explanation/architecture.md)**: System design and component interactions
- **[Parsing behavior](../explanation/behavior.md)**: How parsing works internally
- **[Error handling](../explanation/errors.md)**: Exception patterns and error recovery
