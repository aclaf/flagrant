# Overview

--8<-- "unreleased.md"

Welcome to the Flagrant documentation. This page introduces what Flagrant is, where it fits in the command-line application stack, and points you to detailed explanations of its core concepts and architecture.

!!! info "Unreleased project"
    Flagrant and its parent project [Aclaf](https://aclaf.sh) are in active development and have not yet been released. The documentation describes the target design being implemented. While substantial functionality exists, not all features described are complete.

!!! warning "Documentation purpose"
    This documentation is primarily for **transparency** into Flagrant's architecture and design decisions. It serves as a specification of requirements and behavior, providing insight into how Aclaf's parsing engine works internally.

    Flagrant is not currently meant for direct consumption outside of its integration with Aclaf. Use at your own risk during this early development phase—breaking changes are frequent and no support is offered for standalone usage.

## Table of contents

- [Overview](#overview)
  - [Table of contents](#table-of-contents)
  - [What is Flagrant?](#what-is-flagrant)
  - [Design principles](#design-principles)
  - [Architecture overview](#architecture-overview)
  - [Getting started](#getting-started)
  - [See also](#see-also)

---

## What is Flagrant?

Flagrant is a specification-driven command-line parser for building CLI programs in Python 3.10+. It provides the core parsing engine that transforms raw command-line arguments into structured data based on declarative specifications.

Think of Flagrant as the foundation layer for command-line interfaces—it handles the mechanics of understanding what users type (syntax) without imposing opinions about what it means (semantics). This focused scope makes it a composable building block for CLI frameworks and applications.

### Core capabilities

Flagrant provides focused argument parsing capabilities:

**Argument parsing**: Transforms command-line argument strings like `["--verbose", "-o", "file.txt", "build"]` into structured data that your application can work with. The parser understands options (long and short forms), positionals, subcommands, flags, value options, and dictionary arguments.

Parsing is driven by declarative specifications—you describe your command structure once, and Flagrant uses that description to parse user input into structured data.

!!! note "Relationship to Aclaf"
    Flagrant serves as the parsing engine for [Aclaf](https://aclaf.sh), a comprehensive command-line application framework. While Aclaf provides the complete CLI infrastructure including command routing, type conversion, validation, error reporting, help generation, and shell completions, Flagrant focuses exclusively on argument parsing.

    This architectural separation reflects deliberate design choices:

    **Focused scope**: Flagrant handles the syntactic analysis of command-line arguments—determining what the user typed—while Aclaf handles the semantic interpretation—determining what it means, along with presentation concerns like help text and completions. This clean separation enables thorough testing of parsing logic in isolation and makes both systems easier to understand and maintain.

    **Reusability**: By operating at a lower abstraction level than full CLI frameworks, Flagrant remains composable and reusable. Other frameworks, tools, or applications can build on Flagrant's parsing capabilities without adopting Aclaf's opinions about command execution or application lifecycle.

    **Parallel development**: Flagrant and Aclaf are being developed together, with Flagrant's APIs shaped by Aclaf's requirements while maintaining independence from Aclaf's higher-level concerns.

!!! warning "What Flagrant is not"
    Flagrant intentionally focuses on parsing only, explicitly excluding concerns that belong to higher-level frameworks:

    **Not a full framework**: Flagrant is a parsing engine, not a complete CLI application framework. It does not provide type conversion (string to int, Path, datetime), validation (range checks, mutual exclusivity), default value management, command execution, shell completions, or application lifecycle management.

    **Not a validation layer**: Flagrant parses arguments according to specifications but does not enforce application-specific validation rules. Parse results contain raw string values; applications perform validation and type conversion as needed.

    **Not an execution engine**: Flagrant does not dispatch commands to handler functions or manage application state. It produces structured parse results that applications interpret and act upon.

    **Not a configuration system**: Flagrant does not merge configuration from multiple sources (files, environment variables, defaults). It parses command-line arguments only.

    **Not a presentation layer**: Flagrant does not generate help text or format error messages for users. These presentation concerns are handled by higher-level frameworks like Aclaf.

    This narrow focus keeps Flagrant composable and reusable as a foundational parsing engine.

## Design principles

Flagrant design emphasizes several key principles that shape its behavior and APIs:

**Specification-driven behavior**: All parsing is configured through declarative `CommandSpecification`, `OptionSpecification`, and `PositionalSpecification` objects. You describe your command structure; Flagrant figures out how to parse it.

**Separation of concerns**: The parser handles syntax (what did the user type?), while higher-level frameworks handle semantics (what does it mean?). This separation keeps each layer focused and testable.

**Immutability throughout**: All data structures are immutable after construction, enabling thread safety, aggressive caching, and reasoning about behavior without worrying about hidden mutations.

**Minimal dependencies**: Uses Python standard library exclusively except for `typing-extensions` to provide modern typing features to Python 3.10+. No heavy dependency chains.

**Strong type safety**: Comprehensive type hints throughout with basedpyright validation. The type system helps catch errors before runtime and improves IDE support.

## Architecture overview

Flagrant provides a focused parser subsystem built on a declarative specification model:

### Parser subsystem

The parser subsystem (`flagrant.parser`) transforms command-line argument strings into structured `ParseResult` objects through single-pass, fail-fast parsing with comprehensive validation. When parsing fails, it provides detailed error information including what went wrong and where.

The parser is strict: it enforces arity requirements, validates option names, catches ambiguities, and fails fast when encountering invalid input. This strictness helps users catch configuration errors early and provides clear feedback when arguments don't match expectations.

### Specification model

The specification model (`flagrant.specification`) defines CLI structure through immutable dataclasses: `CommandSpecification`, `OptionSpecification`, and `PositionalSpecification`. These specifications drive parser behavior, ensuring consistent and predictable parsing.

For a deeper dive into the parser architecture and specification model, see the [Architecture explanation](explanation/architecture.md).

## Getting started

### Understanding the foundations

Before diving into parser specifics, we recommend understanding the foundational concepts:

Start with [Concepts](explanation/concepts.md) to learn about the specification model, arity, accumulation modes, option resolution strategies, and positional argument concepts that appear throughout Flagrant design.

### Exploring by interest

Once you understand the foundations, explore based on what you're building:

**Building a parser?** Read the [Behavior](explanation/behavior.md) documentation to understand how Flagrant transforms command-line arguments into structured data, what parsing modes exist, how options and positionals work, and how errors are handled.

### Learning by example

Throughout the documentation, you'll find extensive examples showing how Flagrant handles common patterns, edge cases, and complex scenarios. The examples progress from simple cases to advanced usage, building intuition for how the system works.

## See also

For deeper understanding of Flagrant design and behavior:

- **[Architecture](explanation/architecture.md)**: System architecture, component interactions, and design rationale
- **[Concepts](explanation/concepts.md)**: Foundational concepts for the parser and specification model
- **[Behavior](explanation/behavior.md)**: How argument parsing works in detail

---

**Next steps**: Choose a topic from the [See also](#see-also) section based on your needs and dive in.
