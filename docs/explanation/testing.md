# Parser testing specification

This page describes a comprehensive testing strategy for the Flagrant parser. Testing ensures that the parser correctly transforms command-line arguments into structured parse results according to its formal specifications. The strategy balances multiple testing approaches—unit tests for component isolation, integration tests for end-to-end scenarios, property-based tests for invariants, and fuzz tests for robustness—to achieve high confidence in parser correctness while maintaining >95% code coverage.

The testing strategy focuses on verifiable behaviors defined in the formal specifications ([Grammar](grammar.md), [Behavior](behavior.md)) rather than implementation details. This approach ensures that tests remain valid across refactorings and that test failures clearly indicate specification violations rather than just changed code.

## Table of contents

- [Parser testing specification](#parser-testing-specification)
  - [Table of contents](#table-of-contents)
  - [Testing philosophy](#testing-philosophy)
  - [Testing levels](#testing-levels)
    - [Unit tests](#unit-tests)
    - [Integration tests](#integration-tests)
    - [Property-based tests](#property-based-tests)
    - [Fuzz tests](#fuzz-tests)
    - [Benchmarks](#benchmarks)
  - [Property-based test invariants](#property-based-test-invariants)
    - [Parse determinism](#parse-determinism)
    - [Arity enforcement](#arity-enforcement)
    - [Accumulation mode correctness](#accumulation-mode-correctness)
    - [Name resolution consistency](#name-resolution-consistency)
    - [Positional grouping correctness](#positional-grouping-correctness)
    - [Subcommand nesting correctness](#subcommand-nesting-correctness)
    - [Configuration isolation](#configuration-isolation)
    - [Specification validation](#specification-validation)
    - [Error-focused properties](#error-focused-properties)
    - [Argument file properties](#argument-file-properties)
    - [Security-focused properties](#security-focused-properties)
    - [Mutation testing guidance](#mutation-testing-guidance)
    - [Snapshot testing](#snapshot-testing)
  - [Boundary conditions and edge cases](#boundary-conditions-and-edge-cases)
    - [Argument boundaries](#argument-boundaries)
    - [Arity boundaries](#arity-boundaries)
    - [Option/positional interaction](#optionpositional-interaction)
    - [Subcommand boundaries](#subcommand-boundaries)
    - [Accumulation edge cases](#accumulation-edge-cases)
    - [Name resolution edge cases](#name-resolution-edge-cases)
    - [Trailing argument handling](#trailing-argument-handling)
    - [Negative number handling](#negative-number-handling)
    - [Configuration combinations](#configuration-combinations)
    - [Error condition boundaries](#error-condition-boundaries)
  - [Coverage requirements](#coverage-requirements)
    - [Coverage mandate](#coverage-mandate)
    - [Critical paths](#critical-paths)
    - [Coverage tracking](#coverage-tracking)
  - [Test organization](#test-organization)
    - [Test file naming](#test-file-naming)
    - [Test class organization within files](#test-class-organization-within-files)
    - [Pytest markers](#pytest-markers)
  - [Specification validation testing](#specification-validation-testing)
    - [Validation test scope](#validation-test-scope)
  - [Argument file testing](#argument-file-testing)
    - [Expansion logic tests](#expansion-logic-tests)
    - [Integration with parser](#integration-with-parser)
    - [Property-based tests](#property-based-tests-1)
  - [Error detection testing](#error-detection-testing)
    - [Error types and test coverage](#error-types-and-test-coverage)

---

## Testing philosophy

The parser's testing strategy is built on several foundational principles that guide test design and quality standards:

**Specification-driven testing:** Tests verify that implementation matches formal specifications. When a test documents expected behavior, the specification documents why that behavior is required. Tests serve as executable specifications that validate implementation correctness.

**Deterministic and repeatable:** All parsing operations are deterministic given identical inputs and configuration. Tests are deterministic and repeatable without relying on mutable state or randomness (property-based tests use seeded randomness to enable replay of failures).

**Isolation and composability:** Unit tests isolate individual components (argument classification, value consumption, accumulation, resolution). Integration tests exercise complete parsing scenarios. Properties verify that components compose correctly. Fuzz tests explore unexpected input combinations.

**Measurable coverage:** Test coverage is measured and tracked with mandatory >95% threshold for all new code. Coverage includes branch coverage to ensure all conditional paths are exercised. Critical paths identified in parser design receive additional coverage through property-based and example-based tests.

**Performance validation:** Benchmarking validates that the parser meets its O(n) performance constraint and sub-millisecond typical-case target. Performance regressions are detected through benchmark comparisons.

**Security-conscious:** Tests validate that parser enforces security boundaries (arity bounds, safe name resolution, input validation). Tests exercise error conditions to ensure robust failure modes.

## Testing levels

The parser testing strategy combines five complementary testing levels, each serving distinct purposes in validating parser correctness and robustness.

### Unit tests

Unit tests exercise individual parser components and functions in isolation, using fixtures and mocks to control dependencies. Given the parser's design with minimal external dependencies, mocking is primarily used for file system operations (argument file tests) and for isolating components during testing.

**Component scope:**

- **Argument classification** - Tests that arguments are correctly classified as long options, short options, positionals, subcommands, or trailing arguments based on syntax and parser state
- **Long option parsing** - Tests extraction of option names and inline values from `--option` and `--option=value` syntax
- **Short option parsing** - Tests extraction of option names from `-o` and `-abc` clustering, including attached values
- **Value consumption** - Tests that values are consumed according to arity constraints, stopping at option boundaries, subcommand boundaries, and arity limits
- **Option accumulation** - Tests that repeated option occurrences are combined according to accumulation mode (last-wins, first-wins, collect, count, error)
- **Name resolution** - Tests that option names are resolved with exact matching, case-insensitive matching, abbreviation matching, and underscore-dash conversion
- **Positional grouping** - Tests that positional arguments are distributed to positional specs according to arity constraints and minimum requirements
- **Subcommand resolution** - Tests that subcommand names are recognized and remaining arguments are delegated to subcommand parsers
- **Specification validation** - Tests that parser construction validates specifications and rejects invalid configurations

**Testing approach:**

Example-based tests with concrete input-output pairs demonstrating expected behavior. Tests focus on valid inputs and expected outputs, with separate error condition tests.

**Coverage targets:**

Each component receives unit tests covering:

- Normal case behavior (common usage patterns)
- Boundary cases (empty input, single argument, maximum arity)
- Option/positional interactions
- Interaction with parser configuration flags

**Example test patterns:**

```python
# tests/unit/parsing/test_argument_classification.py

@pytest.mark.parsing
class TestArgumentClassification:
    def test_long_option_recognized(self):
        # Arrange
        spec = CommandSpecification("test", options=(
            FlagOptionSpecification(name="verbose", long_names=frozenset({"verbose"})),
        ))
        parser = Parser(spec)

        # Act
        result = parser.parse(["--verbose"])

        # Assert
        assert "verbose" in result.options
        assert result.options["verbose"].value is True

    def test_short_option_clustering_with_value_consumption(self):
        # Test that -abc expands to -a -b -c
        # with only last option consuming values
        spec = CommandSpecification(
            "test",
            options=(
                FlagOptionSpecification(name="a", short_names=frozenset({"a"})),
                FlagOptionSpecification(name="b", short_names=frozenset({"b"})),
                ValueOptionSpecification(name="c", short_names=frozenset({"c"}), arity=Arity(1, 1)),
            ),
        )
        parser = Parser(spec)
        result = parser.parse(["-abc", "value"])

        assert result.options["a"].value is True
        assert result.options["b"].value is True
        assert result.options["c"].value == "value"

    def test_single_dash_always_positional(self):
        # Single dash "-" is always treated as positional (stdin/stdout convention)
        spec = CommandSpecification(
            "test",
            positionals=(PositionalSpecification(name="file", arity=Arity(1, 1)),),
        )
        parser = Parser(spec)
        result = parser.parse(["-"])

        assert result.positionals["file"].value == "-"
```

### Integration tests

Integration tests exercise the parser end-to-end with realistic command specifications and argument sequences, validating that components work together correctly.

**Scenario scope:**

- **Mixed options and positionals** - Options and positionals in various orders (normal mode and strict mode)
- **Complex specifications** - Commands with many options, multiple positionals, subcommands
- **Subcommand hierarchies** - Multi-level subcommand nesting with independent specifications at each level
- **Accumulation with complex specs** - Options using different accumulation modes in the same specification
- **Name resolution interactions** - Multiple resolution strategies enabled simultaneously
- **Trailing arguments** - Options followed by `--` delimiter and remaining arguments
- **Configuration combinations** - Different parser configurations affecting overall behavior
- **Real-world scenarios** - Patterns commonly encountered in CLI tools (file operations, service configuration, build systems)

**Testing approach:**

Example-based tests with realistic command specifications resembling actual CLI tools. Each test defines a specification, invokes the parser with arguments, and validates the complete parse result structure.

**Coverage targets:**

Integration tests verify:

- Correct extraction of all option values
- Correct grouping of positional values
- Correct subcommand nesting and recursion
- Correct accumulation of repeated options
- Correct name resolution across mixed options
- Correct interaction of multiple parser configuration flags
- Correct error detection and reporting

**Example test patterns:**

```python
# tests/integration/parsing/test_realistic_commands.py

@pytest.mark.parsing
@pytest.mark.integration
class TestBuildCommand:
    def test_build_with_multiple_sources_and_output(self):
        # Realistic build command: build --output dist/ src/main.py src/utils.py
        spec = CommandSpecification(
            name="build",
            options=(
                ValueOptionSpecification(name="output", long_names=frozenset({"output"}), arity=Arity(1, 1)),
                FlagOptionSpecification(name="verbose", long_names=frozenset({"verbose"})),
            ),
            positionals=(
                PositionalSpecification(name="files", arity=Arity(1, None)),
            ),
        )
        parser = Parser(spec)

        result = parser.parse(["--output", "dist/", "--verbose", "src/main.py", "src/utils.py"])

        assert result.options["output"].value == "dist/"
        assert result.options["verbose"].value is True
        assert result.positionals["files"].value == ("src/main.py", "src/utils.py")

    def test_git_remote_add_subcommand_nesting(self):
        # git remote add origin https://example.com
        # Validate that subcommands nest correctly across multiple levels
        spec = CommandSpecification(
            name="git",
            subcommands=(
                CommandSpecification(
                    name="remote",
                    subcommands=(
                        CommandSpecification(
                            name="add",
                            positionals=(
                                PositionalSpecification(name="name", arity=Arity(1, 1)),
                                PositionalSpecification(name="url", arity=Arity(1, 1)),
                            ),
                        ),
                    ),
                ),
            ),
        )
        parser = Parser(spec)
        result = parser.parse(["remote", "add", "origin", "https://example.com"])

        assert result.subcommand.command == "remote"
        assert result.subcommand.subcommand.command == "add"
        assert result.subcommand.subcommand.positionals["name"].value == "origin"
        assert result.subcommand.subcommand.positionals["url"].value == "https://example.com"

    def test_strict_mode_options_after_positional_become_positional(self):
        # With strict_options_before_positionals=True
        # validate that options after first positional become positionals
        spec = CommandSpecification(
            name="copy",
            options=(FlagOptionSpecification(name="verbose", long_names=frozenset({"verbose"})),),
            positionals=(PositionalSpecification(name="files", arity=Arity(1, None)),),
        )
        config = Configuration(strict_options_before_positionals=True)
        parser = Parser(spec, config=config)

        result = parser.parse(["file.txt", "--verbose", "result.txt"])

        # --verbose becomes a positional because it appears after first positional
        assert "verbose" not in result.options
        assert result.positionals["files"].value == ("file.txt", "--verbose", "result.txt")
```

### Property-based tests

Property-based tests use Hypothesis to generate thousands of valid and edge-case inputs, then verify that parser-defined invariants hold across all cases.

**Invariant scope:**

Property-based testing verifies properties that must hold for all valid inputs:

- **Parse determinism** - Given identical specification, arguments, and configuration, parsing always produces identical results
- **Arity enforcement** - Values consumed for each option/positional satisfy minimum and maximum arity constraints
- **Accumulation correctness** - Each accumulation mode (last-wins, first-wins, collect, count, error) produces correct values
- **Name resolution consistency** - Option resolution produces consistent results for equivalent input
- **Positional grouping correctness** - Positional values are distributed according to arity constraints and minimum requirements
- **Subcommand nesting correctness** - Subcommand results nest correctly with parent results
- **Configuration immutability** - Parser configuration doesn't affect parse results in unexpected ways
- **Specification validation** - Invalid specifications are rejected with specific error types

**Test strategy with Hypothesis:**

Use Hypothesis strategy composition to generate:

1. Valid command specifications with controlled complexity (options, positionals, subcommands)
2. Valid argument arrays according to generated specifications
3. Parser configuration variations
4. Repeat parsing with identical inputs to verify determinism

**Example property definitions:**

```python
# tests/properties/parsing/test_parsing_properties.py

from hypothesis import given, strategies as st

@pytest.mark.parsing
@pytest.mark.properties
class TestParsingProperties:
    @given(
        command_spec=st.builds(CommandSpecification, ...),
        arguments=st.lists(st.text()),
        config=st.builds(Configuration, ...),
    )
    def test_parse_is_deterministic_across_invocations(self, command_spec, arguments, config):
        parser = Parser(command_spec, config=config)

        result1 = parser.parse(arguments)
        result2 = parser.parse(arguments)

        assert result1 == result2

    @given(
        command_spec=st.builds(CommandSpecification, ...),
        arguments=st.lists(st.text()),
        config=st.builds(Configuration, ...),
    )
    def test_parse_result_fields_identical_on_repeat(self, command_spec, arguments, config):
        # Verify idempotence: parsing same args/config twice yields identical
        # ParseResult object fields (including nested subcommand results)
        parser = Parser(command_spec, config=config)

        result1 = parser.parse(arguments)
        result2 = parser.parse(arguments)

        # Deep equality check on all fields
        assert result1.command == result2.command
        assert result1.options == result2.options
        assert result1.positionals == result2.positionals
        assert result1.subcommand == result2.subcommand
        assert result1.trailing_arguments == result2.trailing_arguments

    @given(
        option_spec=st.builds(ValueOptionSpecification, arity=st.just(Arity(2, 4))),
    )
    def test_arity_constraints_enforced_for_values(self, option_spec):
        parser = Parser(CommandSpecification("test", options=(option_spec,)))

        # Generate valid argument counts (2, 3, or 4)
        valid_counts = [2, 3, 4]
        for count in valid_counts:
            # Get first long name from frozenset
            long_name = next(iter(option_spec.long_names))
            args = [f"--{long_name}"] + [f"val{i}" for i in range(count)]
            result = parser.parse(args)

            # Verify value count satisfies arity
            values = result.options[option_spec.name].value
            value_count = 1 if isinstance(values, str) else len(values)
            assert option_spec.arity.min <= value_count <= option_spec.arity.max

    @given(
        spec=st.builds(CommandSpecification, ...),
        args=st.lists(st.text()),
    )
    def test_parse_result_is_immutable(self, spec, args):
        parser = Parser(spec)
        result = parser.parse(args)

        # Verify immutability through frozen dataclass properties
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            result.command = "different"

    @given(arguments=st.lists(st.text()))
    def test_input_arguments_not_mutated(self, arguments):
        # Verify no mutation of input sequence
        spec = CommandSpecification("test")
        parser = Parser(spec)
        original = arguments.copy()

        try:
            parser.parse(arguments)
        except FlagrantException:
            pass  # Parsing may fail, but inputs must not be mutated

        assert arguments == original
```

**Targeted property groups:**

- **Argument classification properties** - Arguments are classified consistently, single-dash is always positional, option-like strings in strict mode become positionals after first positional
- **Value consumption properties** - Values are consumed up to arity max, stopped at option boundaries, stopped at subcommand boundaries
- **Accumulation properties** - Last-wins discards non-final values, first-wins discards non-initial values, APPEND preserves occurrence grouping, EXTEND flattens all values, COUNT produces monotonic integers
- **Name resolution properties** - Exact matches take precedence, abbreviations are unambiguous or error, case insensitivity is consistent, normalization equivalences hold
- **Positional grouping properties** - Positionals satisfy arity constraints, later positionals' minimums are reserved, unbounded positionals maximize consumption, greedy specs never starve later specs' minima
- **Strict mode properties** - Once first positional seen, subsequent option-like args become positionals; boundary is deterministic
- **Negative number properties** - Classification invariant under custom patterns, toggling `allow_negative_numbers` only changes classification for matching tokens
- **Normalization equivalences** - When case-insensitive/underscore-conversion enabled, equivalent spellings parse to identical canonical names; abbreviations obey minimum length and ambiguity rules

### Fuzz tests

Fuzz tests use Atheris to generate random inputs and explore parser behavior under unexpected or malformed input. Fuzz tests focus on robustness rather than correct behavior—the goal is to ensure the parser never crashes or hangs, produces reasonable error messages, and maintains security boundaries.

**Fuzzing scope:**

- **Malformed arguments** - Arguments with unusual character combinations, very long strings, special characters, Unicode
- **Invalid option combinations** - Options that don't exist, options with wrong arity, flag options with values
- **Configuration edge cases** - Empty specifications, specifications with conflicts, unusual arity patterns
- **Stress conditions** - Very large argument counts, very deep subcommand nesting, very long option values
- **Boundary violations** - Attempting to violate security assumptions, resource exhaustion attempts

**Fuzzing objectives:**

1. **No crashes** - The parser never crashes on any input, malformed or not
2. **Fail fast** - The parser raises structured exceptions (not generic exceptions) on invalid input
3. **Resource safety** - The parser doesn't consume unbounded memory or CPU time
4. **Security boundaries** - The parser doesn't leak sensitive information or violate arity bounds in error conditions

**Fuzz test structure with Atheris:**

```python
# tests/fuzz/parsing/test_parser_fuzz.py

import atheris
from flagrant.parsing import Parser
from flagrant.specification import CommandSpecification

@atheris.instrument_func
def test_parser_robustness_with_random_inputs(data):
    fdp = atheris.FuzzedDataProvider(data)

    # Generate random specification
    num_options = fdp.ConsumeIntInRange(0, 10)
    spec = CommandSpecification(
        name="fuzz_test",
        options=tuple(
            OptionSpecification(
                name=f"opt{i}",
                long_names=(f"option{i}",),
                arity=Arity(fdp.ConsumeIntInRange(0, 3), fdp.ConsumeIntInRange(0, 5)),
            )
            for i in range(num_options)
        ),
    )

    # Generate random arguments
    num_args = fdp.ConsumeIntInRange(0, 50)
    args = [fdp.ConsumeUnicode(10) for _ in range(num_args)]

    # Parse should not crash
    parser = Parser(spec)
    try:
        result = parser.parse(args)
        # If parsing succeeded, result should be well-formed
        assert isinstance(result, ParseResult)
    except FlagrantException:
        # Parser exceptions are acceptable
        pass
    except Exception as e:
        # Any other exception is a bug
        raise AssertionError(f"Unexpected exception: {type(e).__name__}: {e}")
```

**Corpus and seed values:**

Fuzz testing maintains a corpus of interesting inputs discovered during fuzzing, including:

- Inputs that trigger boundary conditions
- Inputs that previously caused crashes
- Inputs that exercise specific code paths
- Security-relevant inputs (long strings, unicode edge cases, ReDoS patterns)

Example corpus entries stored in `tests/fuzz/parsing/corpus/`:

```text
# corpus/long-option-with-unicode.txt
--option=值
--опция=значение

# corpus/boundary-hyphen-runs.txt
--------
--option-------value
-----------

# corpus/unicode-dashes.txt
–option  # EN DASH (U+2013)
—option  # EM DASH (U+2014)
⸺option  # TWO-EM DASH (U+2E3A)

# corpus/negative-numbers-edge.txt
-123
-3.14
-1e5
-1.2e-3

# corpus/short-option-cluster.txt
-abcdefghijklmnopqrstuvwxyz
```

### Benchmarks

Benchmarks measure parser performance and validate that it meets the O(n) linear time complexity target with sub-millisecond typical-case performance.

**Performance targets:**

- **Linear scaling** - O(n) time complexity where n is the number of arguments
- **Typical single-command parse** - Parsing ≤50 arguments completes in <1ms
- **Complex multi-level parse** - Parsing 50 arguments with 20 options across 3 command levels completes in <2ms
- **Memory usage** - Linear memory usage proportional to input and specification complexity, no memory leaks
- **Constant factors** - Fast inner loops with efficient branch prediction and cache locality
- **Regression detection** - Benchmark comparisons fail if performance degrades by >10% from baseline

**Benchmark scenarios:**

Benchmarks test various argument counts, specification complexities, and configuration combinations:

```python
# tests/benchmarks/parsing/test_parser_benchmarks.py

@pytest.mark.benchmark
class TestParserPerformance:
    def test_simple_command_baseline(self, benchmark):
        spec = CommandSpecification(
            name="cmd",
            options=(
                FlagOptionSpecification(name="v", long_names=frozenset({"verbose"})),
                ValueOptionSpecification(name="o", long_names=frozenset({"output"}), arity=Arity(1, 1)),
            ),
        )
        parser = Parser(spec)
        args = ["--verbose", "--output", "file.txt", "input.txt"]

        result = benchmark(parser.parse, args)

        # Verify result correctness
        assert result.options["verbose"].value is True
        assert result.options["output"].value == "file.txt"

    def test_complex_command_with_many_options(self, benchmark):
        # Create specification with 20 options, 3 positionals
        options = tuple(
            ValueOptionSpecification(
                name=f"opt{i}",
                long_names=frozenset({f"option{i}"}),
                arity=Arity(0, 2),
            )
            for i in range(20)
        )
        spec = CommandSpecification(name="cmd", options=options)
        parser = Parser(spec)

        # Generate 50 arguments
        args = [f"--option{i % 20}" for i in range(50)]

        benchmark(parser.parse, args)

    def test_linear_scaling_with_argument_count(self, benchmark):
        # Verify O(n) scaling with varying argument counts
        spec = CommandSpecification(
            name="cmd",
            options=(
                ValueOptionSpecification(name="o", long_names=frozenset({"option"}), arity=Arity(1, 1)),
            ),
        )
        parser = Parser(spec)

        # Parametrize across different argument counts
        for count in [10, 50, 100, 500]:
            args = ["--option", "value"] * count
            benchmark(parser.parse, args)
```

**Benchmark execution:**

Benchmarks use pytest-benchmark for measurement and comparison. Align with Justfile commands for consistency:

```bash
# Run benchmarks and save baseline
just benchmark-save

# Compare against baseline (using Justfile targets)
just benchmark-compare

# Strict comparison with fail threshold (±10%)
just benchmark-compare-strict

# Direct pytest-benchmark usage
uv run pytest tests/benchmarks/ -v --benchmark-compare
uv run pytest tests/benchmarks/ --benchmark-save=baseline

# Compare with fail threshold
uv run pytest tests/benchmarks/ --benchmark-compare --benchmark-compare-fail=mean:10%
```

## Property-based test invariants

This section formalizes the invariants that property-based tests verify. These invariants express fundamental properties that must hold for all valid parser operations.

### Parse determinism

**Invariant:** Given identical specification, arguments, and parser configuration, the parser produces identical results on repeated invocations.

**Justification:** The parser is stateless after construction, and parsing is a pure function. Repeated calls with identical inputs must produce identical outputs.

**Property definition:**

```text
For all specifications S, argument arrays A, and configurations C:
    let parser = Parser(S, config=C)
    let result1 = parser.parse(A)
    let result2 = parser.parse(A)
    then result1 == result2
```

**Test implementation:** Generate valid specifications and arguments, parse twice, assert results are equal.

### Arity enforcement

**Invariant:** The parser enforces minimum and maximum arity constraints. For each option or positional parameter with arity (min, max), the value count satisfies `min <= count <= max`.

**Justification:** Arity constraints are fundamental to parser correctness. The parser must validate that all value assignments satisfy their specifications.

**See also:** [Arity boundaries](#arity-boundaries) for concrete edge cases testing arity limits.

**Property definition:**

```text
For all options O with arity (min, max):
    let values = ParseResult.options[O.name].value
    let count = 1 if value is scalar else len(value)
    then min <= count <= max

For all positionals P with arity (min, max):
    let values = ParseResult.positionals[P.name].value
    let count = 1 if value is scalar else len(value)
    then min <= count <= max
```

**Special cases:**

- Flag options with arity (0, 0) produce boolean values (True when present)
- Options with arity (1, 1) produce scalar string values
- Options with arity (1, None) can produce scalar or tuple values
- Accumulation mode affects value structure but not arity validation

### Accumulation mode correctness

**Invariant:** Each accumulation mode produces predictable value structures from repeated option occurrences.

**Justification:** Accumulation modes provide explicit semantics for combining repeated options. Correctness depends on each mode producing its specified behavior.

**See also:** [Accumulation edge cases](#accumulation-edge-cases) for concrete testing scenarios.

**Property definitions by mode:**

**Last-wins accumulation:**

```text
For repeated options with LAST_WINS mode:
    let result = parser.parse([..., --option a, ..., --option b, ...])
    then result.options[option].value == b
    (only final value retained)
```

**First-wins accumulation:**

```text
For repeated options with FIRST_WINS mode:
    let result = parser.parse([..., --option a, ..., --option b, ...])
    then result.options[option].value == a
    (only initial value retained)
```

**Append accumulation:**

```text
For repeated options with APPEND mode:
    let result = parser.parse([..., --option a, ..., --option b, ...])
    then result.options[option].value == ((a,), (b,))
    (each arity-bounded set appended as tuple)
```

**Extend accumulation:**

```text
For repeated options with EXTEND mode:
    let result = parser.parse([..., --option a, ..., --option b, ...])
    then result.options[option].value == (a, b)
    (all values extended into single tuple)
```

**Count accumulation:**

```text
For repeated options with COUNT mode:
    let result = parser.parse([--option, ..., --option, ..., --option, ...])
    then result.options[option].value == count
    (value is integer count of occurrences)
```

**Error accumulation:**

```text
For repeated options with ERROR mode:
    let result = parser.parse([..., --option a, ..., --option b, ...])
    then raises DuplicateOptionError
    (second occurrence raises error)
```

### Name resolution consistency

**Invariant:** Option name resolution produces consistent, deterministic results for equivalent inputs. When multiple resolution strategies are enabled, they compose correctly without ambiguity.

**Justification:** Name resolution determines which option specification matches a user-provided name. Consistency ensures predictable behavior and prevents surprising matches.

**See also:** [Name resolution edge cases](#name-resolution-edge-cases) for boundary testing scenarios.

**Property definitions:**

**Exact matching consistency:**

```text
For option with long name "verbose":
    parser.parse(["--verbose"]) resolves to same option as
    parser.parse(["--verbose"])
```

**Case-insensitive consistency:**

```text
With case_sensitive_options=False for option "verbose":
    parser.parse(["--verbose"]) ==
    parser.parse(["--Verbose"]) ==
    parser.parse(["--VERBOSE"])
```

**Abbreviation unambiguity:**

```text
With allow_abbreviated_options=True:
    if multiple options match prefix, raises AmbiguousOptionError
    if exactly one option matches prefix, matches that option
    if no options match prefix, raises UnknownOptionError
```

**Underscore-dash equivalence:**

```text
With convert_underscores=True:
    parser.parse(["--log_level"]) resolves to same option as
    parser.parse(["--log-level"])
```

### Positional grouping correctness

**Invariant:** Positional arguments are distributed to positional specs respecting arity constraints and reserving values for later specs with minimum requirements.

**Justification:** The positional grouping algorithm is deterministic and must allocate arguments correctly to satisfy all arity constraints.

**See also:** [Option/positional interaction](#optionpositional-interaction) and [Configuration combinations](#configuration-combinations) for related test scenarios.

**Property definition:**

```text
For positionals P1, P2, ..., Pn with arities (min1, max1), (min2, max2), ..., (minn, maxn):
    let collected = [positional arguments in parse order]
    let allocated = grouping_algorithm(collected, [P1, P2, ..., Pn])
    then for each i:
        min(i) <= len(allocated[i]) <= max(i)
    and
        total allocated == total collected
    and
        each positional consumes values respecting its arity
        while reserving values for remaining positionals' minimum requirements
```

**Concrete example property:**

```text
For copy command with sources (1, None) and destination (1, 1):
    parser.parse(["file1", "file2", "dest/"]) =>
    positionals["sources"] = ("file1", "file2")
    positionals["destination"] = ("dest/",)

    (not:
    positionals["sources"] = ("file1", "file2", "dest/")
    positionals["destination"] = ()
    which violates destination's minimum requirement)
```

### Subcommand nesting correctness

**Invariant:** Subcommand results nest correctly with parent results, maintaining isolated namespaces for each command level.

**Justification:** Subcommand handling must correctly transition from parent to child parsing and maintain the result structure.

**Property definition:**

```text
For command with subcommand "sub":
    let result = parser.parse(["--parent-option", "value", "sub", "--sub-option", "value"])
    then result.subcommand is not None
    and result.subcommand.command == "sub"
    and result.options contains only parent options
    and result.subcommand.options contains only subcommand options
```

### Configuration isolation

**Invariant:** Parser configuration flags don't have unexpected interactions. Each flag affects only its intended behavior.

**Justification:** Configuration should be composable and predictable. Enabling one flag should not cause unintended side effects.

**Property definition:**

```text
For configurations C1 and C2 where C1 and C2 differ only in flag F:
    parser_results differ only in behavior affected by F
    (no surprising interactions with other parser behaviors)
```

### Specification validation

**Invariant:** Invalid specifications are rejected during parser construction with appropriate error types. Valid specifications are accepted.

**Justification:** Specification validation establishes a clear boundary between valid and invalid configurations.

**Property definition:**

```text
For specification S:
    if S is valid (all names unique, arities valid, etc.):
        Parser(S) succeeds
    else:
        Parser(S) raises SpecificationError
```

**Validity constraints:**

- All option names (long and short) are unique within the command
- All subcommand names and aliases are unique
- All positional names are unique
- Arity constraints are coherent (min <= max)
- Option names follow format rules
- Negation word sets don't conflict with option names

### Error-focused properties

These properties verify that the parser raises appropriate errors for invalid inputs with correct error types and context.

**Ambiguity detection:**

```text
For two options sharing a prefix when abbreviations enabled:
    let shared_prefix = longest common prefix shorter than each option
    then parser.parse([f"--{shared_prefix}"]) raises AmbiguousOptionError
    and error.matches contains both option names
```

**Equals syntax with multi-value arity:**

```text
For option with arity (min > 1, max):
    let args = ["--option=single_value"]
    then parser.parse(args) raises InsufficientValuesError
    (single inline value cannot satisfy multi-value minimum)
```

**Flag value prohibition:**

```text
For flag option (arity 0, 0):
    let args_equals = ["--flag=value"]
    let args_attached = ["-fvalue"]  # for short flag
    then parser.parse(args_equals) raises FlagWithValueError
    and parser.parse(args_attached) raises FlagWithValueError
    (flags never accept values through inline syntax)
```

### Argument file properties

Properties specific to argument file expansion and integration.

**Recursion depth limits:**

```text
For parser with argument_file_recursion_limit=N:
    let files = chain of N+1 nested argument files
    then parser.parse([f"@{files[0]}"]) raises ArgumentFileRecursionError
```

**Comment character handling:**

```text
For argument file with lines starting with comment_char:
    let file_content = "# comment\n--option\nvalue\n# another comment"
    then expanded args exclude comment lines
    and expanded args == ["--option", "value"]
```

**Multi-file precedence:**

```text
For argument files A, B with conflicting option values:
    let args = [f"@{A}", f"@{B}"]
    then later file (B) values override earlier file (A) values
    (last-wins semantics across file boundaries)

For inline args overriding file args:
    let args = [f"@{file}", "--option", "inline_value"]
    then inline_value wins over file value
    (command-line position dictates precedence)
```

**Expansion order preservation:**

```text
For argument file with ordered arguments:
    let file_content = "arg1\narg2\narg3"
    then expansion preserves order: ["arg1", "arg2", "arg3"]

For multiple files:
    let args = [f"@{file1}", f"@{file2}"]
    then expansion order: [*file1_args, *file2_args]
    (left-to-right file processing)
```

### Security-focused properties

Properties that validate security boundaries and prevent common vulnerabilities.

**Regex ReDoS protection:**

```text
For custom negative number pattern with nested quantifiers:
    let pattern = r"(-+\d+)+"  # Potentially catastrophic backtracking
    then parser construction raises ParserConfigurationError
    (reject patterns with nested quantifiers)
```

**Resource safety under stress:**

```text
For very large argument arrays:
    let args = ["--option", "value"] * 10000
    then parsing completes in bounded time (O(n))
    and memory usage is linear in input size
    (no unbounded resource consumption)

For deeply nested subcommands:
    let depth = 100 nested subcommands
    then parsing either succeeds with correct nesting
    or raises bounded-depth error
    (no stack overflow or unbounded recursion)
```

**Unicode handling safety:**

```text
For unicode option names and values:
    let unicode_args = ["--опция", "值", "🚀"]
    then parsing handles unicode correctly
    and no encoding errors occur
    and normalization is consistent
```

### Mutation testing guidance

**Mutation testing strategy:**

Use `mutmut` to validate test suite effectiveness by introducing mutations in critical parsing paths and verifying that tests detect the changes.

**Critical paths for mutation testing:**

- **Argument classification logic** - Mutate classification conditions to verify tests catch misclassification
- **Value consumption algorithm** - Mutate arity checking and boundary conditions
- **Accumulation mode handling** - Mutate mode selection and value combination logic
- **Name resolution matching** - Mutate matching conditions and precedence rules
- **Positional grouping algorithm** - Mutate minimum reservation and distribution logic

**Running mutation tests:**

```bash
# Run mutation testing on hot paths
uv run mutmut run --paths-to-mutate=src/flagrant/parsing/_parser.py

# Show mutation results
uv run mutmut results

# Apply specific mutation to see what changed
uv run mutmut show <mutation_id>
```

**Mutation score targets:**

- Critical parsing paths should achieve >80% mutation score
- Mutations that survive indicate weak or missing assertions
- Add targeted tests for surviving mutations

### Snapshot testing

**Snapshot testing strategy:**

Use structured snapshots of `ParseResult` dictionary representations to make test diffs readable in code reviews and catch unintended result structure changes.

**Snapshot test examples:**

```python
# tests/unit/parsing/test_result_snapshots.py

def test_complex_parse_result_structure_snapshot(snapshot):
    # Parse complex command and snapshot result structure
    spec = CommandSpecification(
        name="app",
        options=(
            FlagOptionSpecification(name="verbose", long_names=frozenset({"verbose"})),
            ValueOptionSpecification(name="output", long_names=frozenset({"output"}), arity=Arity(1, 1)),
        ),
        positionals=(
            PositionalSpecification(name="files", arity=Arity(1, None)),
        ),
    )
    parser = Parser(spec)
    result = parser.parse(["--verbose", "--output", "dist/", "src/main.py", "src/utils.py"])

    # Snapshot the dictionary representation
    result_dict = {
        "command": result.command,
        "options": {name: {"value": opt.value, "source": opt.source} for name, opt in result.options.items()},
        "positionals": {name: {"value": pos.value} for name, pos in result.positionals.items()},
        "subcommand": result.subcommand,
        "trailing_arguments": result.trailing_arguments,
    }

    assert result_dict == snapshot
```

**Benefits:**

- Structural changes to ParseResult become visible in diffs
- Easier to review complex parsing scenarios
- Catches unintended changes to result structure
- Documents expected output for complex cases

## Boundary conditions and edge cases

This section documents boundary conditions and edge cases that must be explicitly tested to ensure correct behavior at system limits.

### Argument boundaries

**Empty arguments array:**

- Parsing with no arguments should produce a result with no options, no positionals, and no subcommand
- Useful for validating default behavior

**Single argument:**

- Single option flag: `["--verbose"]` → option recognized, value set to True
- Single positional: `["file.txt"]` → positional collected
- Single subcommand: `["sub"]` → subcommand invoked

**Maximum argument count:**

- Parser should handle very large argument arrays (1000+) without degraded performance
- Memory usage should scale linearly with argument count

### Arity boundaries

**Arity (0, 0) - flags:**

- Flag present → value True
- Flag absent → option not in result
- Flag with equals syntax → raises FlagWithValueError
- Flag with attached value → raises FlagWithValueError
- Flag without inline value when required → error or default behavior

**Arity (1, 1) - required single value:**

- Exactly one value provided → scalar value
- No value provided → error (insufficient values)
- More than one value provided → only first value consumed
- Value from inline syntax → full value consumed

**Arity (1, None) - one or more values:**

- Single value → scalar value or single-element tuple (accumulation dependent)
- Multiple values → tuple of values
- Values consumed up to next option or subcommand
- Values reserved for later positionals with minimum requirements

**Arity (0, 1) - optional single value:**

- No value → option not in result (or zero count for count mode)
- One value → scalar value
- More than one value → only first value consumed

**Unbounded maximum (None):**

- Consume all available values matching boundaries
- Stop at next option, subcommand, or `--` delimiter
- For positionals, stop when positional specs exhausted

### Option/positional interaction

**Options after positionals (non-strict mode):**

- Options can appear after positional arguments
- Both are recognized and processed correctly

**Positional-like option values:**

- Positional arguments starting with `-` are correctly recognized as positionals
- Examples: file paths, negative numbers, `-` for stdin

**Option consuming positional-like values:**

- Options can consume values that look like options
- Example: `--pattern -abc` where `-abc` is the pattern value

**Positionals with option names:**

- When using strict mode, option-like strings after first positional become positionals
- Example: `copy file.txt --verbose result.txt` (strict mode) → `--verbose` is positional

### Subcommand boundaries

**No subcommand defined:**

- Arguments that could be subcommand names are treated as positionals
- Parser doesn't treat special keywords as subcommands

**Subcommand not invoked:**

- Parsing completes at parent command level
- Subcommand field in result is None

**Subcommand invoked:**

- Remaining arguments after subcommand name are delegated to subcommand parser
- Subcommand uses its own specification independent of parent

**Deeply nested subcommands:**

- Parsing should handle multiple levels of subcommand nesting (git, docker patterns)
- Result nests correctly reflecting command hierarchy

**Ambiguous subcommand names:**

- Subcommand name conflicts with option name → subcommand takes precedence in argument classification (after all options consumed)

### Accumulation edge cases

**Zero occurrences:**

- Unspecified option absent from result
- Count mode would have zero, but option not in result if count is zero

**One occurrence:**

- Last-wins and first-wins: scalar value
- Collect: single-element tuple
- Count: count of 1

**Many occurrences:**

- Last-wins: only last value retained (earlier values discarded)
- First-wins: only first value retained (later values discarded)
- Collect: all values in tuple
- Count: count of all occurrences
- Error: raises on second occurrence (first occurrence retained)

**Mixed value counts:**

- Option appears once with single value, once with multiple values (if multi-value arity)
- Accumulation mode determines how values are combined

### Name resolution edge cases

**Empty option names:**

- Short options must be exactly one character
- Long options must be at least two characters
- Empty names rejected during specification validation

**Very long option names:**

- Parser should handle long option names (100+ characters) without performance degradation
- Matching should remain O(1) with proper caching

**Unusual characters in option names:**

- Dashes and underscores allowed in option names
- Case conversion preserves characters correctly
- Special characters (., /, @) not allowed in option names (syntax conflict)

**Case sensitivity edges:**

- `--verbose` vs `--Verbose` treated as same option (with case-insensitive flag)
- Case preservation: lowercase names matched case-insensitively maintain original case in spec
- Mixed case names: e.g. `--MyOption` normalized to `--myoption` when case-insensitive

**Abbreviation ambiguity:**

- Abbreviation matches multiple options → error with list of candidates
- Abbreviation matches exactly one → matches that option
- Exact match takes precedence over abbreviation

### Trailing argument handling

**No `--` delimiter:**

- All arguments processed for options and positionals
- No trailing arguments in result

**Empty trailing arguments:**

- `--` at end of arguments produces empty trailing arguments tuple

**Trailing arguments with option-like syntax:**

- Arguments after `--` preserved exactly as provided
- Not interpreted as options or positionals

**Subcommand before `--`:**

- Subcommand recognized, delegates remaining to subcommand
- Subcommand parser processes arguments after subcommand name including `--`

**Nested `--` in subcommands:**

- `program --parent-option -- subcommand --sub-option`
- `--` at top level, subcommand processes remaining args with its own parsing

### Negative number handling

**With `allow_negative_numbers=False` (default):**

- `-5` treated as short option cluster (likely error if not defined)
- Negative numbers require positive identification

**With `allow_negative_numbers=True`:**

- `-5` treated as positional argument
- Float patterns like `-3.14` recognized as positionals
- Scientific notation like `-1e5` recognized as positionals

**Negative number as option value:**

- `--count -5` with positive identification enabled
- Value `-5` consumed as option value (not short option cluster)

**Single-dash special case:**

- `-` (single dash only) always treated as positional (stdin/stdout convention)
- Never treated as option or negative number

### Configuration combinations

**All flags disabled:**

- Only exact option matching, no abbreviation, no case-insensitive, no negation
- Strictest matching behavior

**All flags enabled:**

- Abbreviation, case-insensitive, underscore-dash conversion, negation all enabled
- Most permissive matching behavior
- Potential for ambiguity (tested for error handling)

**Mixed configurations:**

- Case-insensitive with abbreviation → abbreviations case-insensitive too
- Underscore-dash conversion with case-insensitive → multiple equivalent forms match
- Negation with abbreviation → negated abbreviations work correctly

**Strict positional mode effects:**

- Options before first positional work normally
- First positional encountered → `positionals_started` flag set
- Subsequent option-like arguments become positionals
- Normal value consumption rules apply for those arguments

### Error condition boundaries

**Insufficient values:**

- Option requiring 2 values gets 1 → error with details
- Positional requiring 3 values gets 2 → error with details

**Unknown option:**

- Option not defined in specification → UnknownOptionError naming the unknown option
- Suggestion mechanism (if present) suggests similar options

**Abbreviation ambiguity:**

- Abbreviation matches 3+ options → AmbiguousOptionError listing all matches
- User gets clear information about which options matched

**Flag with value error:**

- Flag with explicit value via equals syntax → FlagWithValueError
- Error identifies the flag and the attempted value

**Duplicate option (error mode):**

- Option with error mode appears twice → error on second occurrence
- First occurrence retained in result

## Coverage requirements

This section specifies mandatory coverage standards and critical paths that require additional verification.

### Coverage mandate

**Minimum coverage:** >95% code coverage for all new parser code in `src/flagrant/parsing/`.

**Coverage measurement:**

```bash
# Run tests with coverage report
uv run pytest --cov=flagrant.parsing --cov-report=html --cov-report=term-missing
```

**Branch coverage:** The >95% requirement includes branch coverage (decision points, loop entry/exit, exception handling). All conditional branches must be exercised by tests.

**Excluded from coverage:**

- `pass` statements and ellipsis in stub implementations
- Unreachable code (verified by type checker)
- External library code

### Critical paths

These code paths are critical for parser correctness and require additional verification beyond coverage percentage:

**Core parsing loop:**

- Argument classification and dispatching
- Option value consumption
- Accumulation mode handling
- Positional collection and grouping

**Value consumption algorithm:**

- Consuming exact arity
- Respecting option/subcommand boundaries
- Handling inline syntax (equals values)
- Handling attached values for short options

**Positional grouping algorithm:**

- Distributing arguments to positional specs
- Respecting minimum and maximum arity
- Reserving values for later positionals
- Handling unbounded positionals

**Name resolution:**

- Exact matching (baseline)
- Case-insensitive matching
- Abbreviation matching and ambiguity detection
- Underscore-dash conversion
- Negation matching

**Specification validation:**

- Detecting duplicate option names
- Detecting duplicate subcommand names
- Validating arity constraints
- Validating option name formats

**Critical paths receive additional verification through:**

- Property-based tests exercising various input combinations
- Fuzz tests discovering edge cases
- Integration tests with realistic scenarios
- Benchmarks validating performance characteristics

### Coverage tracking

Coverage is tracked across:

- **Line coverage** - Every executable line executed
- **Branch coverage** - Every conditional branch executed
- **Path coverage** - Critical paths through algorithms

Tools:

- `pytest-cov` for measurement
- HTML reports for detailed analysis
- CI validation on pull requests

## Test organization

Tests are organized by domain/feature area, not by testing category. This domain-centric organization ensures tests remain cohesive and maintainable as the codebase evolves.

### Test file naming

Test files are named by the domain/feature they test:

**Unit tests** (`tests/unit/parsing/`):

- `test_parser.py` - Core parser functionality
- `test_argument_classification.py` - Argument classification and grammar
- `test_long_options.py` - Long option syntax and parsing
- `test_short_options.py` - Short option syntax and clustering
- `test_option_values.py` - Option value consumption and arity
- `test_option_accumulation.py` - Accumulation modes
- `test_option_resolution.py` - Name resolution strategies
- `test_positionals.py` - Positional argument handling and grouping
- `test_subcommands.py` - Subcommand nesting and resolution
- `test_trailing_arguments.py` - Trailing argument handling with `--`
- `test_parser_configuration.py` - Configuration flags and their effects
- `test_specification_validation.py` - Specification validation and error conditions
- `test_argument_files.py` - Argument file expansion and integration
- `test_negative_numbers.py` - Negative number classification
- `test_result_snapshots.py` - Snapshot testing for ParseResult structures

**Integration tests** (`tests/integration/parsing/`):

- `test_realistic_commands.py` - End-to-end parsing scenarios
- `test_complex_workflows.py` - Multi-level command workflows

**Property-based tests** (`tests/properties/parsing/`):

- `test_parsing_properties.py` - Property-based test invariants
- `test_error_properties.py` - Error-focused property tests
- `test_argument_file_properties.py` - Argument file expansion properties
- `test_security_properties.py` - Security-focused property tests

**Fuzz tests** (`tests/fuzz/parsing/`):

- `test_parser_fuzz.py` - Fuzz testing for robustness

**Benchmarks** (`tests/benchmarks/parsing/`):

- `test_parser_benchmarks.py` - Performance benchmarks

### Test class organization within files

Within each test file, tests are grouped by component or scenario:

```python
@pytest.mark.parsing
class TestLongOptionExtraction:
    def test_basic_long_option_recognized(self): ...
    def test_long_option_with_equals_value_extracted(self): ...
    def test_long_option_with_empty_value_handled(self): ...

@pytest.mark.parsing
class TestLongOptionNegation:
    def test_negated_flag_with_no_prefix_parsed(self): ...
    def test_negated_flag_with_custom_negation_word_matched(self): ...
```

### Pytest markers

Tests are marked with domain-specific markers for selective execution:

```bash
# Run only parser tests
uv run pytest -m parsing

# Run only long option tests
uv run pytest -m parsing tests/unit/parsing/test_long_options.py

# Run all tests except benchmarks
uv run pytest -m "not benchmark"
```text

Standard markers:

- `parsing` - Parser component tests (applied automatically in conftest)
- `unit` - Unit tests (applied automatically)
- `integration` - Integration tests
- `properties` - Property-based tests
- `fuzz` - Fuzz tests
- `benchmark` - Performance benchmarks

### Test fixtures and factories

Common fixtures and factories enable test reusability without duplication:

**Fixtures in `conftest.py`:**

```python
@pytest.fixture
def empty_parser():
    # Parser with minimal specification
    return Parser(CommandSpecification("test"))

@pytest.fixture
def option_parser():
    # Parser with various option definitions for testing
    spec = CommandSpecification(
        "test",
        options=(
            FlagOptionSpecification(name="v", long_names=frozenset({"verbose"})),
            ValueOptionSpecification(name="o", long_names=frozenset({"output"}), arity=Arity(1, 1)),
            ValueOptionSpecification(name="i", long_names=frozenset({"include"}), arity=Arity(1, None)),
        ),
    )
    return Parser(spec)

@pytest.fixture
def positional_parser():
    # Parser with positional specs for testing positional grouping
    spec = CommandSpecification(
        "test",
        positionals=(
            PositionalSpecification(name="source", arity=Arity(1, 1)),
            PositionalSpecification(name="dest", arity=Arity(1, 1)),
        ),
    )
    return Parser(spec)
```

**Factories for generating test data:**

Factories generate various command specifications for testing:

```python
def build_value_option_spec(name="test", arity=None, **kwargs):
    # Factory for ValueOptionSpecification with defaults
    return ValueOptionSpecification(
        name=name,
        long_names=kwargs.get("long_names", frozenset({name})),
        arity=arity or Arity(1, 1),
        **{k: v for k, v in kwargs.items() if k != "long_names"},
    )

def build_flag_option_spec(name="test", **kwargs):
    # Factory for FlagOptionSpecification with defaults
    return FlagOptionSpecification(
        name=name,
        long_names=kwargs.get("long_names", frozenset({name})),
        **{k: v for k, v in kwargs.items() if k != "long_names"},
    )

def build_command_spec(name="test", options=None, positionals=None):
    # Factory for CommandSpecification with defaults
    return CommandSpecification(
        name=name,
        options=options or (),
        positionals=positionals or (),
    )
```

## Specification validation testing

Specification validation ensures that parser construction rejects invalid specifications before parsing occurs.

### Validation test scope

**Duplicate detection:**

- Duplicate option names (same long name) → rejected
- Duplicate option names (same short name) → rejected
- Duplicate subcommand names → rejected
- Duplicate positional names → rejected

**Arity validation:**

- Invalid arity constraints (min > max) → rejected
- Negative arity values (min < 0 or max < 0) → rejected
- Arity (0, 0) only valid for flags → otherwise rejected
- Non-zero arity for positionals with unbounded maximum → validated

**Option name validation:**

- Empty option names → rejected
- Short names not exactly one character → rejected
- Long names less than two characters → rejected
- Names with invalid characters → rejected

**Format validation:**

- Command names starting with non-alpha character → rejected
- Subcommand names with invalid characters → rejected
- Option names with invalid characters → rejected

**Test pattern:**

```python
@pytest.mark.parsing
class TestSpecificationValidation:
    def test_duplicate_long_option_names_rejected(self):
        with pytest.raises(DuplicateOptionNameError):
            CommandSpecification(
                "test",
                options=(
                    FlagOptionSpecification(name="v1", long_names=frozenset({"verbose"})),
                    FlagOptionSpecification(name="v2", long_names=frozenset({"verbose"})),  # Duplicate
                ),
            )

    def test_invalid_arity_min_greater_than_max(self):
        with pytest.raises(InvalidArityError):
            ValueOptionSpecification(
                name="test",
                long_names=frozenset({"test"}),
                arity=Arity(3, 2),  # min > max
            )
```

## Argument file testing

Argument file tests verify that argument file expansion works correctly in isolation and integrates properly with the full parser.

### Expansion logic tests

Unit tests should cover the preprocessing function that expands argument files:

**Basic expansion:**

- Single argument file with simple arguments
- Multiple argument files in one command line
- Argument files containing options with values (equals syntax and separate lines)
- Argument files with comments and blank lines
- Files with leading and trailing whitespace
- Empty files (should expand to nothing)

**Precedence and ordering:**

- Arguments from files expanded at correct position in argument stream
- Command-line arguments after file override file contents
- Command-line arguments before file are overridden by file
- Multiple files processed in left-to-right order

**Escaping and special cases:**

- `@@file` produces literal `@file` argument
- `--` separator disables expansion for subsequent arguments
- Argument files with `@` in content (should be treated as literal)

**Error conditions:**

- File not found produces `ArgumentFileNotFoundError`
- File exists but cannot be read produces `ArgumentFileReadError`
- File with invalid UTF-8 produces `ArgumentFileFormatError`
- Recursive expansion beyond depth limit (if supported)
- Circular references detected (if supported)

```python
@pytest.mark.parsing
class TestArgumentFileExpansion:
    def test_single_file_basic_arguments(self, tmp_path):
        # Create temporary argument file
        arg_file = tmp_path / "test.args"
        arg_file.write_text("--verbose\n--output\nfile.txt\n")

        parser = Parser(spec, argument_file_prefix="@")
        result = parser.parse([f"@{arg_file}"])

        assert result.options["verbose"].value is True
        assert result.options["output"].value == "file.txt"

    def test_file_with_comments_and_blanks(self, tmp_path):
        arg_file = tmp_path / "test.args"
        arg_file.write_text("""
# This is a comment
--verbose

# Another comment
--output
result.txt
""")

        parser = Parser(spec, argument_file_prefix="@")
        result = parser.parse([f"@{arg_file}"])

        assert result.options["verbose"].value is True
        assert result.options["output"].value == "result.txt"

    def test_precedence_command_line_overrides_file(self, tmp_path):
        arg_file = tmp_path / "base.args"
        arg_file.write_text("--output\ndefault.txt\n")

        parser = Parser(spec, argument_file_prefix="@")
        result = parser.parse([f"@{arg_file}", "--output", "custom.txt"])

        # Command-line argument appears later, should win
        assert result.options["output"].value == "custom.txt"

    def test_file_not_found_error(self):
        parser = Parser(spec, argument_file_prefix="@")

        with pytest.raises(ArgumentFileNotFoundError) as exc_info:
            parser.parse(["@nonexistent.args"])

        assert "nonexistent.args" in str(exc_info.value.file_path)
```

### Integration with parser

Integration tests verify that argument files work correctly with all parser features:

**Options and positionals:**

- Argument files containing both options and positionals
- Positionals from files respect arity constraints
- Options from files participate in accumulation

**Subcommands:**

- Argument files before subcommand apply to parent
- Argument files after subcommand apply to child
- Subcommand invocation from argument file

**Accumulation modes:**

- File contents participate in option accumulation
- Last-wins, first-wins, append, extend modes work correctly
- Count mode counts occurrences from files
- Error mode detects duplicates across files and command line

```python
@pytest.mark.parsing
class TestArgumentFileIntegration:
    def test_file_with_subcommands(self, tmp_path):
        # File contains parent options, command line has subcommand
        arg_file = tmp_path / "parent.args"
        arg_file.write_text("--verbose\n")

        spec = CommandSpecification(
            name="app",
            options=(FlagOptionSpecification(name="verbose", long_names=frozenset({"verbose"})),),
            subcommands=(CommandSpecification(name="deploy"),)
        )
        parser = Parser(spec, argument_file_prefix="@")
        result = parser.parse([f"@{arg_file}", "deploy"])

        assert result.options["verbose"].value is True
        assert result.subcommand is not None
        assert result.subcommand.command == "deploy"

    def test_file_with_accumulation(self, tmp_path):
        arg_file = tmp_path / "config.args"
        arg_file.write_text("--include\nfile1.txt\n--include\nfile2.txt\n")

        spec = CommandSpecification(
            name="app",
            options=(
                ValueOptionSpecification(
                    name="include",
                    long_names=frozenset({"include"}),
                    arity=Arity(1, 1),
                    accumulation_mode=ValueAccumulationMode.EXTEND
                ),
            )
        )
        parser = Parser(spec, argument_file_prefix="@")
        result = parser.parse([f"@{arg_file}"])

        assert result.options["include"].value == ("file1.txt", "file2.txt")
```

### Property-based tests

Property-based tests should verify invariants about argument file expansion:

**Expansion idempotence:** If an argument list contains no `@` prefixes, expanding it produces an identical list.

**Manual vs automatic expansion:** Manually reading a file and splicing its contents should produce the same result as automatic expansion.

**Order preservation:** Arguments from files appear in the expanded list in the same order they appear in the file, and files are expanded in left-to-right order.

```python
@given(
    arguments=st.lists(st.text(alphabet=st.characters(blacklist_characters="@"))),
)
def test_expansion_idempotent_without_at_prefix(arguments):
    """Expanding arguments without @ prefix produces identical list."""
    parser = Parser(spec, argument_file_prefix="@")
    expanded = expand_argument_files(arguments, parser.config)
    assert expanded == arguments
```

## Error detection testing

Error detection tests verify that the parser detects and reports syntactic errors with appropriate exception types and context information.

### Error types and test coverage

**UnknownOptionError:**

- User provides option name not in specification
- Error includes option name and list of similar options (if applicable)

**AmbiguousOptionError:**

- Abbreviation matches multiple options
- Error lists all matching options

**InsufficientValuesError:**

- Option or positional receives fewer values than minimum arity
- Error identifies the parameter and required count

**FlagWithValueError:**

- Flag receives explicit value via equals syntax
- Error identifies the flag and attempted value

**DuplicateOptionError:**

- Option with error accumulation mode appears multiple times
- Error on second occurrence

**SpecificationError (and subclasses):**

- Invalid specification provided at parser construction
- Specific subtypes: DuplicateNameError, InvalidArityError, InvalidNameFormatError, InvalidFlagConfigError
- Error describes the specific validation failure

**Test patterns:**

```python
@pytest.mark.parsing
class TestErrorDetection:
    def test_unknown_option_raises_error(self):
        parser = Parser(CommandSpecification("test", options=()))

        with pytest.raises(UnknownOptionError) as exc_info:
            parser.parse(["--unknown"])

        assert exc_info.value.option_name == "--unknown"

    def test_insufficient_values_raises_error(self):
        spec = CommandSpecification(
            "test",
            options=(
                ValueOptionSpecification(name="o", long_names=frozenset({"output"}), arity=Arity(2, 2)),
            ),
        )
        parser = Parser(spec)

        with pytest.raises(InsufficientValuesError) as exc_info:
            parser.parse(["--output", "file.txt"])  # Only 1 value, needs 2

        assert exc_info.value.option_name == "output"
        assert exc_info.value.required_count == 2
        assert exc_info.value.actual_count == 1
```

---

**Related pages:**

- [Parser](parser.md) - Parser design principles and constraints
- [Grammar](grammar.md) - Formal syntax and argument classification
- [Behavior](behavior.md) - Parsing algorithms and semantics
- [Configuration](configuration.md) - Parser configuration options
- [Types](types.md) - Data structures and type system
- [Concepts](concepts.md) - Shared terminology and foundations
**Target audience:** Test developers implementing parser tests, contributors adding parser features, and code reviewers validating test coverage.
