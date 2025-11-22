# Overview

Welcome to Flagrant's documentation! This page introduces what Flagrant is, where it fits in the command-line application stack, and points you to detailed explanations of its core concepts and architecture.

!!! info "Unreleased project"
    Flagrant is in active development and has not yet been released. The documentation describes the target design being implemented. While substantial functionality exists, not all features described are complete.

## Table of contents

- [What is Flagrant?](#what-is-flagrant)
- [Core capabilities](#core-capabilities)
- [Design principles](#design-principles)
- [Architecture overview](#architecture-overview)
- [Getting started](#getting-started)
- [See also](#see-also)

---

## What is Flagrant?

Flagrant is a specification-driven command-line parser and completion generator for building CLI programs in Python 3.10+. It provides the core parsing and completion engine that transforms raw command-line arguments into structured data and generates shell completions based on declarative specifications.

Think of Flagrant as the foundation layer for command-line interfaces—it handles the mechanics of understanding what users type (syntax) without imposing opinions about what it means (semantics). This focused scope makes it a composable building block for CLI frameworks and applications.

### Core capabilities

Flagrant provides two major capabilities:

**Argument parsing**: Transforms command-line argument strings like `["--verbose", "-o", "file.txt", "build"]` into structured data that your application can work with. The parser understands options (long and short forms), positionals, subcommands, flags, value options, and dictionary arguments.

**Completion generation**: Analyzes partial command-line input to generate shell-specific completion suggestions. When users press Tab, Flagrant determines what options, values, or subcommands make sense at that position and formats them for their shell (Bash, Zsh, Fish, or PowerShell).

Both capabilities are driven by declarative specifications—you describe your command structure once, and Flagrant uses that description for both parsing complete commands and generating completions for partial input.

!!! note "Relationship to Aclaf"
    Flagrant serves as the parsing and completion engine for Aclaf, a comprehensive command-line application framework. While Aclaf provides the complete CLI infrastructure including command routing, type conversion, validation, error reporting, and help generation, Flagrant focuses exclusively on argument parsing and completion generation.

    This architectural separation reflects deliberate design choices:

    **Focused scope**: Flagrant handles the syntactic analysis of command-line arguments—determining what the user typed—while Aclaf handles the semantic interpretation—determining what it means. This clean separation enables thorough testing of parsing logic in isolation and makes both systems easier to understand and maintain.

    **Reusability**: By operating at a lower abstraction level than full CLI frameworks, Flagrant remains composable and reusable. Other frameworks, tools, or applications can build on Flagrant's parsing and completion capabilities without adopting Aclaf's opinions about command execution or application lifecycle.

    **Parallel development**: Flagrant and Aclaf are being developed together, with Flagrant's APIs shaped by Aclaf's requirements while maintaining independence from Aclaf's higher-level concerns.

!!! warning "What Flagrant is not"
    Flagrant intentionally focuses on parsing and completion generation, explicitly excluding concerns that belong to higher-level frameworks:

    **Not a full framework**: Flagrant is a parsing and completion engine, not a complete CLI application framework. It does not provide type conversion (string to int, Path, datetime), validation (range checks, mutual exclusivity), default value management, command execution, or application lifecycle management.

    **Not a validation layer**: Flagrant parses arguments according to specifications but does not enforce application-specific validation rules. Parse results contain raw string values; applications perform validation and type conversion as needed.

    **Not an execution engine**: Flagrant does not dispatch commands to handler functions or manage application state. It produces structured parse results that applications interpret and act upon.

    **Not a configuration system**: Flagrant does not merge configuration from multiple sources (files, environment variables, defaults). It parses command-line arguments only.

    **Not a shell**: Flagrant's completion system generates suggestions but does not execute shell commands, perform filename expansion, or handle environment variable substitution.

    This narrow focus keeps Flagrant composable and reusable as a foundational parsing and completion engine.

## Design principles

Flagrant's design emphasizes several key principles that shape its behavior and APIs:

**Specification-driven behavior**: All parsing and completion is configured through declarative `CommandSpecification`, `OptionSpecification`, and `PositionalSpecification` objects. You describe your command structure; Flagrant figures out how to parse it and complete it.

**Separation of concerns**: The parser handles syntax (what did the user type?), while higher-level frameworks handle semantics (what does it mean?). This separation keeps each layer focused and testable.

**Immutability throughout**: All data structures are immutable after construction, enabling thread safety, aggressive caching, and reasoning about behavior without worrying about hidden mutations.

**Minimal dependencies**: Uses Python standard library exclusively except for `typing-extensions` to provide modern typing features to Python 3.10+. No heavy dependency chains.

**Strong type safety**: Comprehensive type hints throughout with basedpyright validation. The type system helps catch errors before runtime and improves IDE support.

## Architecture overview

Flagrant consists of two major subsystems that share a common specification model but operate independently:

### Parser subsystem

The parser subsystem (`flagrant.parsing`) transforms command-line argument strings into structured `ParseResult` objects through single-pass, fail-fast parsing with comprehensive validation. When parsing fails, it provides detailed error information including what went wrong and where.

The parser is strict: it enforces arity requirements, validates option names, catches ambiguities, and fails fast when encountering invalid input. This strictness helps users catch configuration errors early and provides clear feedback when arguments don't match expectations.

### Completion subsystem

The completion subsystem (`flagrant.completions`) analyzes partial command-line input to generate shell-specific completion suggestions through permissive parsing with graceful degradation. When completion encounters ambiguity or incomplete input, it generates all reasonable possibilities rather than failing.

The completer is permissive: it tolerates incomplete input, handles ambiguity by offering multiple candidates, and degrades gracefully when facing unexpected conditions. This permissiveness matches user expectations during interactive typing—completions should help, not fail.

### Shared specification model

Both subsystems work from the same specification objects, ensuring consistency between parsing and completion behavior. When you define a command structure for parsing, that same structure automatically drives completion generation without duplicate configuration.

For a deeper dive into how these subsystems work together and the rationale behind their design, see the [Architecture explanation](explanation/architecture.md).

## Getting started

### Understanding the foundations

Before diving into parser or completion specifics, we recommend understanding the foundational concepts that both subsystems share:

Start with [Concepts](explanation/concepts.md) to learn about the specification model, arity, accumulation modes, option resolution strategies, and positional argument concepts that appear throughout Flagrant's design.

### Exploring by interest

Once you understand the foundations, explore based on what you're building:

**Building a parser?** Read the [Parsing overview](explanation/parsing/index.md) to understand how Flagrant transforms command-line arguments into structured data, what parsing modes exist, how options and positionals work, and how errors are handled.

**Implementing completions?** Read the [Completions overview](explanation/completions/index.md) to understand how completion differs from parsing, how Flagrant generates candidates, and how it integrates with different shells.

**Comparing approaches?** See [Comparisons](explanation/comparisons/index.md) to understand how Flagrant's design compares to other parsing approaches and when different strategies make sense.

### Learning by example

Throughout the documentation, you'll find extensive examples showing how Flagrant handles common patterns, edge cases, and complex scenarios. The examples progress from simple cases to advanced usage, building intuition for how the system works.

## See also

For deeper understanding of Flagrant's design and behavior:

- **[Architecture](explanation/architecture.md)**: System architecture, component interactions, and design rationale
- **[Concepts](explanation/concepts.md)**: Foundational concepts shared across parser and completer
- **[Parsing overview](explanation/parsing/index.md)**: How argument parsing works in detail
- **[Completions overview](explanation/completions/index.md)**: How completion generation works
- **[Comparisons](explanation/comparisons/index.md)**: How Flagrant compares to other approaches

---

**Next steps**: Choose a topic from the [See also](#see-also) section based on your needs and dive in!
