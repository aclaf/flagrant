# Explanations

Welcome to the Explanations section of Flagrant's documentation. This section provides conceptual understanding and deep dives into how Flagrant works, why it's designed the way it is, and how its components fit together.

## What you'll find here

Explanations focus on **understanding** rather than doing. Unlike tutorials (learning-oriented) or how-to guides (problem-oriented), explanations are **theory-oriented** and help you build mental models of Flagrant's architecture, design decisions, and fundamental concepts.

This section is ideal for:

- Understanding Flagrant's architecture and design philosophy
- Learning why Flagrant makes specific design choices
- Exploring how parsing and completion systems work internally
- Comparing Flagrant's approach to other CLI frameworks
- Building deep knowledge to extend or contribute to Flagrant

## Explanation categories

### [Architecture and concepts](architecture.md)

Understand Flagrant's system architecture, component interactions, and foundational concepts including specifications, arity, accumulation modes, option resolution, and positional grouping. Start here to build your mental model of how Flagrant operates.

**Key topics**: System architecture, design rationale, component interactions, separation of concerns, shared specification model

### [Parsing grammar](grammar.md)

### [Parsing behavior](behavior.md)

Dive deep into how Flagrant transforms command-line arguments into structured data. Learn about the parsing algorithm, grammar rules, option and positional handling, error detection, and configuration strategies.

**Key topics**: Argument classification, value consumption, arity enforcement, name resolution, subcommand nesting, error handling, grammar specification

### [Framework comparisons](comparisons/index.md)

Compare Flagrant's design philosophy and capabilities to other Python CLI frameworks including argparse, Click, Typer, and Cyclopts. Understand when to choose Flagrant versus established alternatives and how Flagrant's specification-driven approach differs from traditional frameworks.

**Key topics**: Philosophy differences, feature comparisons, architectural tradeoffs, ecosystem positioning, selection criteria

## How to use this section

If you're new to Flagrant, start with [Architecture](architecture.md) to understand the big picture, [Concepts](concepts.md) to learn fundamental ideas, then the [Parser](parser.md). If you're evaluating Flagrant against other frameworks, jump to [Comparisons](comparisons/index.md).

For practical usage and recipes, see the [Guides](../guides/index.md) section. For step-by-step learning, check out [Tutorials](../tutorials/index.md). For detailed API documentation, visit the [Reference](../reference/index.md) section.

---

**Related sections:**

- **[Overview](../overview.md)**: Quick introduction to Flagrant's purpose and capabilities
- **[Tutorials](../tutorials/index.md)**: Learning-oriented lessons for getting started
- **[Guides](../guides/index.md)**: Problem-oriented recipes for common tasks
- **[Reference](../reference/index.md)**: Technical reference and API documentation
