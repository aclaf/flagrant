# Explanations

--8<-- "unreleased.md"

!!! warning "Documentation purpose and disclaimer"
    This documentation is primarily for **transparency** into Flagrant's architecture and design. It serves as both a specification of requirements and behavior for development, and as insight into the system's internals.

    **Current position**: Flagrant is the parser engine for [Aclaf](https://aclaf.sh), a full-featured CLI framework. While Flagrant is technically usable standalone, it is not currently meant for end-user consumption outside of Aclaf integration.

    **Future possibility**: If there is sufficient community interest in using Flagrant as a standalone parser, this position may change. For now, consider this documentation a window into how Aclaf's parsing works internally.

    **Use at your own risk**: Flagrant is unreleased and under rapid development. Breaking changes occur frequently. No support will be offered for standalone usage at this time.

Welcome to the Explanations section of the Flagrant documentation. This section provides conceptual understanding and deep dives into how Flagrant works, its design rationale, and how its components fit together.

## What you'll find here

Explanations focus on **understanding** rather than doing. Unlike tutorials (learning-oriented) or how-to guides (problem-oriented), explanations are **theory-oriented** and help you build mental models of the Flagrant architecture, design decisions, and fundamental concepts.

This section is ideal for:

- Understanding the Flagrant architecture and design philosophy
- Learning why Flagrant makes specific design choices
- Exploring how the parsing system works internally
- Comparing the Flagrant approach to other CLI frameworks
- Building deep knowledge to extend or contribute to Flagrant

## Core concepts and architecture

### [Shared concepts](concepts.md)

Essential abstractions that underlie how Flagrant processes command-line arguments. Covers the command specification model, arity constraints, accumulation modes, option resolution strategies, positional arguments, dictionary options, and argument files. Start here to build your vocabulary for understanding Flagrant.

**Key topics:** command specifications, specification immutability and composition, arity models, accumulation strategies, option resolution, positional grouping, dictionary syntax, argument file expansion

### [Architecture](architecture.md)

Comprehensive overview of the Flagrant system architecture and its role as the parsing engine for Aclaf. Explores the separation of concerns between syntactic analysis (Flagrant) and semantic interpretation (Aclaf), component interactions, and the shared specification model that enables this clean division.

**Key topics:** system boundaries, component responsibilities, parser-framework separation, specification-driven design, immutable data flow, extension points

## Parsing system

### [Parsing grammar](grammar.md)

Formal specification of the command-line grammar that Flagrant recognizes. Defines the syntax for options, positionals, subcommands, and special constructs like the double-dash separator. Includes EBNF notation, grammar production rules, and comprehensive examples of valid and invalid syntax.

**Key topics:** EBNF grammar notation, option syntax (short/long/bundled), positional arguments, subcommand delegation, value assignment operators, special tokens, grammar ambiguities and resolution

### [Parsing behavior](behavior.md)

Deep dive into how Flagrant transforms command-line arguments into structured data. Documents the complete parsing algorithm, from initial tokenization through final result construction. Covers option and positional handling, value consumption rules, arity enforcement, error detection, and edge cases.

**Key topics:** parsing phases, argument classification, value consumption algorithm, arity validation, name resolution, subcommand nesting, error detection and recovery, parse result structure

### [Parser configuration](configuration.md)

Comprehensive guide to configuring parser behavior through the Configuration model. Documents all 26 configuration properties, their defaults, interactions, and use cases. Explains how configuration influences parsing behavior and how to choose appropriate settings for different CLI styles.

**Key topics:** configuration properties, POSIX mode, name resolution strategies, negative number handling, argument file settings, value flattening, configuration presets, validation rules

## Advanced features

### [Dictionary parsing](dictionary-parsing.md)

Detailed specification for parsing dictionary options with complex nested structures. Covers lexical analysis, syntactic parsing, AST construction, and merge semantics. Documents the syntax for flat and nested dictionaries, lists in dictionaries, and escaping rules.

**Key topics:** dictionary syntax grammar, key-value notation, nested paths with dots, list notation with brackets, escape sequences, AST representation, merge algorithms (shallow/deep), type conflict resolution

!!! warning "Not yet fully implemented"
    The current parser treats dictionary option values as simple strings. Dictionary option parsing with AST construction and structured merge semantics is coming in a future release.

### [Argument files](argument-files.md)

Complete specification for argument file expansion, allowing arguments from external files. Documents file formats (line-based and shell-style), expansion algorithms, recursion limits, comment handling, and security considerations.

**Key topics:** file prefixes (@-syntax), line-based vs shell-style parsing, comment handling, recursive expansion, security boundaries, path resolution, error handling, platform differences

## Quality assurance

### [Error handling](errors.md)

Structured approach to error detection and reporting in Flagrant. Documents the exception hierarchy, error categories, and context provided with each error type. Explains how Flagrant separates error detection (its responsibility) from error formatting (Aclaf's responsibility).

**Key topics:** exception hierarchy, specification errors vs parse errors, error context and metadata, structured error information, error recovery strategies, diagnostic helpers

### [Testing strategy](testing.md)

Flagrant's comprehensive, multi-layered testing philosophy and approach. Explains the balance between unit tests, integration tests, property-based testing, fuzz testing, and benchmarking. Documents testing scope boundaries and the separation between parser testing and framework testing.

**Key topics:** testing pyramid, coverage philosophy (>95% rule), property-based testing with Hypothesis, fuzz testing with Atheris, benchmark strategies, security testing, test organization patterns

## How to navigate this section

### For new readers

1. Start with [Shared concepts](concepts.md) to learn the fundamental vocabulary
2. Read [Architecture](architecture.md) to understand the system design
3. Explore [Parsing behavior](behavior.md) to see how arguments become structured data
4. Review [Parser configuration](configuration.md) to understand customization options

### For implementers

1. Study [Parsing grammar](grammar.md) for the formal syntax specification
2. Understand [Parsing behavior](behavior.md) for algorithm details
3. Review [Error handling](errors.md) for exception patterns
4. Examine [Testing strategy](testing.md) for quality requirements

### For contributors

1. Read [Architecture](architecture.md) to understand design principles
2. Study [Testing strategy](testing.md) for contribution quality standards
3. Review [Parser configuration](configuration.md) for extension points
4. Understand [Error handling](errors.md) for diagnostic requirements

## Related sections

- **[Reference](../reference/index.md)**: Technical API documentation and specifications
- **[API Reference](../reference/api/index.md)**: Detailed module and class documentation
- **[Glossary](../reference/glossary.md)**: Quick lookup for terms and concepts