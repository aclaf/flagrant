# Argument files specification

This page describes the argument file (response file) feature in Flagrant's command-line parser. It specifies the file format, syntax rules, processing semantics, error handling, and integration points for argument file support. The design draws on established conventions from tools like javac, Clikt, and picocli while prioritizing simplicity and predictability.

## Table of contents

- [Argument files specification](#argument-files-specification)
  - [Table of contents](#table-of-contents)
  - [Overview](#overview)
  - [Motivation and use cases](#motivation-and-use-cases)
  - [File format and syntax](#file-format-and-syntax)
    - [Line-based argument format](#line-based-argument-format)
    - [Comment syntax](#comment-syntax)
    - [Alternative shell-style format](#alternative-shell-style-format)
  - [Argument file specification](#argument-file-specification)
    - [Syntax convention](#syntax-convention)
    - [Path resolution](#path-resolution)
    - [Escaping literal @ symbols](#escaping-literal--symbols)
    - [Recursive expansion](#recursive-expansion)
  - [Processing semantics](#processing-semantics)
    - [Expansion timing and order](#expansion-timing-and-order)
    - [Precedence and override behavior](#precedence-and-override-behavior)
    - [Error handling](#error-handling)
  - [Integration with parser architecture](#integration-with-parser-architecture)
    - [Preprocessing phase](#preprocessing-phase)
    - [Configuration options](#configuration-options)
    - [Type safety and error propagation](#type-safety-and-error-propagation)
  - [Testing strategy](#testing-strategy)
    - [Unit tests for expansion logic](#unit-tests-for-expansion-logic)
    - [Integration tests with parser](#integration-tests-with-parser)
    - [Property-based tests](#property-based-tests)
    - [Error handling tests](#error-handling-tests)
  - [Future enhancements](#future-enhancements)
    - [Shell-style argument format](#shell-style-argument-format)
    - [Recursive expansion with cycle detection](#recursive-expansion-with-cycle-detection)
    - [Argument file search paths](#argument-file-search-paths)
    - [Default argument files](#default-argument-files)
    - [Format validation and linting](#format-validation-and-linting)
  - [Security considerations](#security-considerations)
    - [Path traversal](#path-traversal)
    - [Resource exhaustion](#resource-exhaustion)
    - [Information disclosure](#information-disclosure)
  - [Implementation notes](#implementation-notes)
    - [File encoding](#file-encoding)
    - [Line ending normalization](#line-ending-normalization)
    - [Performance considerations](#performance-considerations)
    - [Compatibility](#compatibility)

---

## Overview

Argument files (also known as response files or @-files) allow users to specify command-line arguments in external files rather than directly on the command line. This feature addresses several practical concerns including command-line length limitations on various platforms, reusability of common argument sets, and improved maintainability for complex invocations. The argument file mechanism expands file contents inline during argument processing, treating the file's contents as if they had been typed directly on the command line at that position.

This specification defines the format, syntax, processing semantics, and integration points for argument file support in Flagrant's parser. The design prioritizes simplicity and predictability while maintaining compatibility with established conventions from tools like javac, Clikt, and picocli. Argument file processing occurs as a preprocessing phase before normal parsing begins, keeping the concerns cleanly separated.

## Motivation and use cases

Command-line interfaces frequently encounter situations where the sheer number or complexity of arguments makes direct specification impractical or error-prone. Operating systems impose limits on command-line length (commonly 8,192 characters on Windows, 2,097,152 on Linux), and beyond practical limits, extremely long command lines become difficult to read, debug, and maintain. Argument files solve these problems by moving complex argument lists into external files that can be versioned, shared, and composed.

Common scenarios include build systems that need to pass extensive compiler flags and file lists, test frameworks that need to specify numerous configuration options, and applications with environment-specific settings that differ between development, staging, and production. Developers frequently need to invoke the same command with slight variations, and argument files enable this by allowing a base configuration file to be combined with command-line overrides. CI/CD pipelines benefit from storing canonical configurations in version-controlled argument files rather than embedding them in scripts where they're harder to audit and modify.

The feature also improves accessibility by reducing the need to type or remember long command sequences. Users can maintain curated argument files for different purposes and simply reference them by name. When combined with shell completion, this provides a powerful workflow where users can quickly select from predefined configurations.

## File format and syntax

### Line-based argument format

The primary format treats each non-empty, non-comment line in the argument file as a single command-line argument string. This format is simple to parse, unambiguous in its interpretation, and matches the default behavior of Python's argparse. A line containing `--output=file.txt` becomes the single argument string `"--output=file.txt"`, while a line containing just `file.txt` becomes the argument `"file.txt"`.

When an option requires a value, users can specify it using either equals syntax (`--option=value`) on a single line, or as separate lines where `--option` appears on one line and `value` on the next. Both approaches are valid and produce identical results. The parser treats consecutive lines as consecutive arguments in the argument stream.

Leading and trailing whitespace on each line is trimmed before processing. This allows for readable indentation in argument files without affecting the actual argument values. Empty lines (lines containing only whitespace) are ignored entirely, allowing files to use blank lines for visual organization.

### Comment syntax

Lines beginning with `#` (optionally preceded by whitespace) are treated as comments and ignored during processing. The comment character causes the entire line to be skipped, including any content after the `#`. This enables argument files to include explanatory notes about why particular arguments are specified or what effect they have.

For example, a file might contain:

```
# Enable verbose logging for debugging
--verbose

# Output to the staging directory
--output=/var/staging

# Input files
input1.txt
input2.txt
```

The parser reads this file and produces the argument list `["--verbose", "--output=/var/staging", "input1.txt", "input2.txt"]`, with all comments removed. If an argument value legitimately needs to start with `#`, it cannot appear at the beginning of a line in this format (this is a known limitation of the line-based approach).

### Alternative shell-style format

As a future enhancement, Flagrant may support an alternative shell-style format where arguments within a file can be separated by any whitespace (spaces, tabs, or newlines). In this mode, the line `--option value --flag` would be parsed as three separate arguments: `"--option"`, `"value"`, and `"--flag"`. Single and double quotes would allow arguments to contain whitespace, with escaping rules similar to shell parsing.

This format is more flexible and natural for users familiar with shell syntax, but introduces complexity around quoting, escaping, and line continuation. The line-based format should be implemented first, with shell-style parsing as an optional extension. Configuration should allow applications to choose which format to use, with clear documentation about the differences in behavior.

## Argument file specification

### Syntax convention

Argument files are specified on the command line using the `@` prefix character followed immediately by a file path. When the parser encounters an argument string beginning with `@`, it treats the remainder of the string as a file path and attempts to read that file. The expanded contents replace the `@file` argument at its position in the argument stream.

For example, the command line `app --debug @common.args --output=result.txt` would cause the parser to read `common.args`, expand its contents inline, and continue parsing. If `common.args` contains the two lines `--verbose` and `--threads=4`, the effective argument list becomes `["--debug", "--verbose", "--threads=4", "--output=result.txt"]`.

The `@` prefix character should be configurable through parser configuration, allowing applications to use a different character if `@` conflicts with their argument syntax. Setting the prefix character to `None` or an empty string disables argument file expansion entirely, treating all arguments literally. This provides an escape hatch for applications that need to accept literal `@` as an argument value.

### Path resolution

File paths in `@file` arguments are resolved relative to the current working directory at the time the parser runs, not relative to the location of any argument file that contains the `@file` reference. This behavior matches javac and most other tools, and provides predictable results regardless of how deeply argument files are nested.

Absolute paths are supported and interpreted normally. Relative paths like `./args.txt`, `../config/args.txt`, or simply `args.txt` are all resolved from the current working directory. The parser does not perform path canonicalization, tilde expansion, or environment variable substitution; the path is used as provided after prepending the current working directory if relative.

### Escaping literal @ symbols

Users need a way to specify a literal argument that begins with `@` without triggering file expansion. The specification defines three escape mechanisms:

The double-@ prefix (`@@file`) treats the argument literally after removing the first `@`. The parser sees `@@file`, removes one `@`, and produces the literal argument `@file` without attempting file expansion. This is the most explicit escape mechanism and works regardless of the argument's position.

The double-dash separator (`--`) disables all special processing for arguments that follow it. Arguments appearing after `--` are treated as positional arguments without any prefix interpretation. This follows the POSIX convention and provides a universal way to pass problematic values to an application.

Disabling argument file expansion through configuration causes all `@` prefixes to be treated literally. When the prefix character is set to `None` or an empty string, no expansion occurs and `@file` is simply the literal argument `@file`.

### Recursive expansion

The specification initially disallows recursive expansion where an argument file itself contains `@file` references. If an argument file contains a line like `@other.args`, that line is treated as the literal argument string `@other.args` rather than triggering further file expansion. This prevents infinite loops, simplifies implementation, and matches javac's documented behavior in several versions.

Future versions may support limited recursive expansion with explicit depth limits and cycle detection. If implemented, the depth limit should be configurable but default to a conservative value like 3 or 5 levels. Cycle detection must prevent infinite loops where file A references file B which references file A. When a cycle is detected, the parser should fail with a clear error message indicating which files form the cycle.

## Processing semantics

### Expansion timing and order

Argument file expansion occurs as a preprocessing phase before normal parsing begins. The parser scans the raw argument list from left to right, and when it encounters an `@file` argument, it immediately reads the file, parses its contents according to the configured format, and splices the resulting arguments into the argument list at that position. Processing then continues with the next argument, which may be from the expanded file or from the original argument list.

This inline expansion means that argument files can appear anywhere in the command line, and their contents are processed exactly as if those arguments had appeared at that position. An argument file referenced early in the command line has its contents processed early, while one referenced late has its contents processed late. This ordering directly affects precedence and override behavior.

The expansion is eager and iterative (in the argument list, not in file references). If the command line contains `@file1 @file2 @file3`, each file is expanded as it's encountered, and the resulting argument list reflects all three expansions in left-to-right order. The parser does not perform a separate "collect all @files" phase; expansion is interleaved with argument list processing.

### Precedence and override behavior

Command-line arguments follow standard last-wins semantics where later specifications override earlier ones for options that can appear multiple times. Since argument files are expanded inline, their position in the command line determines their precedence relative to other arguments.

Arguments specified directly on the command line after an argument file override values from that file. The invocation `app @base.args --output=custom.txt` will use `custom.txt` for output even if `base.args` contains `--output=default.txt`, because the command-line argument appears later in the argument stream. Conversely, `app --output=custom.txt @base.args` results in the file's output setting taking effect if it specifies one.

Multiple argument files can be specified, and they're processed in the order they appear. The command `app @base.args @overrides.args` loads base configuration first, then applies overrides. If both files specify the same option, the value from `overrides.args` wins because it appears later in the expanded argument list.

This precedence model is simple, predictable, and matches user expectations from shell argument processing. It requires no special handling for argument files; they're simply another source of arguments that participate in normal parsing.

### Error handling

When the parser encounters an `@file` argument, several error conditions may arise, and the specification defines how each should be handled.

If the file does not exist, the parser must fail with a clear error message indicating the file path and the fact that it could not be found. This is a hard error that prevents further processing. The error message should include the full resolved path to help users understand exactly what file the parser attempted to read.

If the file exists but cannot be read due to permissions or other I/O errors, the parser fails with an error describing the specific problem. The error message should distinguish between "file not found" and "file cannot be read" to aid debugging. On Unix systems, this might indicate permission issues, while on Windows it might indicate file locking.

If the file contains malformed content (invalid UTF-8, null bytes, or other encoding issues), the parser should fail with an error indicating the problem and the approximate location within the file. Line numbers are helpful here when available.

When recursive expansion is supported, exceeding the maximum depth limit or detecting a cycle should produce clear error messages identifying the chain of argument files that led to the problem. The message should list the files involved: "Circular argument file reference detected: file1.args -> file2.args -> file1.args".

The parser should never silently ignore an argument file error. All errors must be surfaced to the user with actionable information about what went wrong and how to fix it.

## Integration with parser architecture

### Preprocessing phase

Argument file expansion is implemented as a preprocessing transformation that runs before the parser begins its normal argument analysis. The transformation takes the raw argument list (typically `sys.argv[1:]` in Python) and produces an expanded argument list with all `@file` references resolved. This expanded list is then fed to the parser's normal processing pipeline.

Implementing expansion as a separate phase provides several benefits. The core parser remains unchanged and doesn't need to know about argument files. Testing can verify expansion independently of parsing semantics. Applications can optionally perform expansion themselves before calling the parser, allowing for custom file resolution or caching strategies. The preprocessing phase is where file I/O occurs, keeping the parser itself a pure function.

The preprocessing function should have a signature like `expand_argument_files(argv: Sequence[str], config: ArgumentFileConfig) -> list[str]`. It returns a new list with all argument files expanded, leaving the original list unchanged. The function is deterministic and can be called multiple times with the same results.

### Configuration options

Parser configuration should expose several options controlling argument file behavior:

The `argument_file_prefix` property specifies what character triggers file expansion. The default is `@`, but applications can set it to any single character or `None` to disable the feature entirely. An empty string also disables expansion.

The `argument_file_format` property specifies whether to use line-based parsing (one argument per line) or shell-style parsing (whitespace-separated with quoting). The default should be line-based for simplicity and predictability. Shell-style parsing can be added later as an opt-in feature.

The `argument_file_comment_char` property specifies what character introduces line comments. The default is `#`, but applications can set it to any character or `None` to disable comments. Disabling comments allows argument values to start with `#` without special handling.

The `max_argument_file_depth` property (if recursive expansion is supported) limits how deeply argument files can reference other argument files. The default should be conservative (perhaps 1 or 2 levels) with a maximum allowed value around 5 to prevent abuse.

The current working directory override allows applications to specify a directory for resolving relative paths instead of using the actual CWD. This is useful for testing and for applications that want to resolve argument files relative to a config directory.

### Type safety and error propagation

Argument file operations can fail in numerous ways, and these failures must be represented in the type system. The preprocessing function should return a result type that can represent success or various error conditions. In Python, this might use an exception-based approach with specific exception types for each failure mode, or a Result type if the codebase adopts that pattern.

Error types should include `ArgumentFileNotFoundError`, `ArgumentFileReadError`, `ArgumentFileFormatError`, `ArgumentFileRecursionError`, and similar specific exceptions. Each should carry relevant context like the file path, the original argument that triggered expansion, and for format errors, the line number where parsing failed.

The preprocessing function guarantees that if it succeeds, the returned argument list is valid input for the parser (though the parser may still reject invalid combinations or values). If preprocessing fails, no parsing occurs and the error is propagated to the caller.

## Testing strategy

### Unit tests for expansion logic

The preprocessing function should have comprehensive unit tests covering all normal and error cases. Tests should verify that files are read correctly, contents are parsed according to the configured format, and the resulting argument list has files expanded in the correct positions with correct precedence.

Specific test cases include: single argument file with simple arguments, multiple argument files in one command line, argument files containing options with values, argument files with comments and blank lines, files with leading and trailing whitespace, files containing arguments that should override command-line arguments based on position, and empty files.

Error case tests should verify that missing files produce appropriate errors, unreadable files fail correctly, malformed files with invalid encoding are detected, and if recursion is supported, depth limits and cycle detection work correctly.

### Integration tests with parser

Integration tests should verify that argument files work correctly with the full parser, not just the preprocessing function. These tests should cover realistic scenarios like loading a base configuration file and overriding specific values, using argument files to specify lists of input files, and combining argument files with subcommands.

Tests should verify that precedence works correctly in realistic scenarios. For example, if an argument file specifies `--verbose` and the command line specifies `--quiet` afterward, the command-line argument should take precedence. If the parser supports counting flags (like `-vvv` for multiple verbosity levels), argument files should correctly contribute to the count based on their position.

### Property-based tests

Property-based testing with Hypothesis should verify invariants about argument file expansion. One key property is that expansion is idempotent: if an argument list has already been expanded (contains no `@` arguments), expanding it again produces an identical list. Another property is that manual expansion should match automatic expansion: if you manually read a file and splice its contents into the argument list, the result should be identical to what the parser produces.

Order preservation is another important property: if argument file A contains arguments `[a1, a2, a3]` and the command line is `[arg1, @A, arg2]`, the expanded list must be `[arg1, a1, a2, a3, arg2]`. The relative order of arguments from different sources must be preserved.

Property tests can generate random argument lists with randomly placed argument files, write those files to temporary locations, and verify that expansion produces the expected results. They can test edge cases like very long files, files with unusual characters in arguments, and deeply nested structures (if recursion is supported).

### Error handling tests

Dedicated tests should verify that all error conditions produce appropriate error messages with helpful information. Tests should mock file system operations to simulate various failure modes: files that exist but can't be read, files that become unavailable during expansion, files with invalid UTF-8 encoding, and so on.

Error messages should be validated not just for correctness but for usability. They should be clear, specific, and actionable. A test might verify that an error message for a missing file includes the full path, a clear statement that the file wasn't found, and a suggestion to check the spelling or path.

## Future enhancements

### Shell-style argument format

The initial implementation focuses on line-based format, but shell-style parsing with whitespace separation and quoting support is a natural extension. This format would allow argument files to look more like actual command lines, with multiple arguments on a single line separated by spaces.

Implementing this format requires a proper shell-style tokenizer that handles single quotes, double quotes, escape sequences, and line continuations. The tokenizer should follow established shell conventions to minimize surprises for users. However, it doesn't need to implement shell features like variable expansion or command substitution; it only needs to handle quoting and escaping.

The format should be configurable so applications can choose which mode to use. Some applications might benefit from the simplicity of line-based format, while others might prefer the flexibility of shell-style format. The choice affects how users write their argument files and what characters require escaping.

### Recursive expansion with cycle detection

Supporting recursive expansion where argument files can reference other argument files enables modular composition of configurations. A base configuration file can be imported by multiple specialized configurations, and common settings can be factored out into shared files.

Safe implementation requires explicit depth limits and cycle detection. The depth limit prevents abuse and ensures that expansion terminates in reasonable time. Cycle detection prevents infinite loops where files reference each other directly or indirectly. The detection algorithm should track the chain of currently-open files and fail if it encounters a file already in the chain.

Error messages for recursion problems should clearly indicate what went wrong. For depth limit violations, show the depth and the chain of files. For cycles, show the complete cycle path: "A → B → C → A". This helps users understand complex configuration structures and identify the problematic reference.

### Argument file search paths

Currently, argument files are resolved relative to the current working directory, but applications might want to support search paths similar to shell PATH or Python's import system. A configuration directory or set of directories could be searched for argument files that aren't found in the current directory.

This feature would allow users to maintain a library of reusable configuration files in a central location. For example, `.flagrant/argfiles/` in the home directory might contain files like `debug.args`, `production.args`, and `test.args` that can be referenced from anywhere. The search path would be configurable through environment variables or parser configuration.

Implementing search paths requires careful consideration of security implications. Loading argument files from system-wide or user-wide directories could allow privilege escalation if not done carefully. The search path should prefer local directories over system directories, and applications in security-sensitive contexts might want to disable this feature.

### Default argument files

Some applications might benefit from automatically loading argument files if they exist, without requiring explicit `@file` references. For example, if `.apprc` exists in the current directory, load it automatically before processing command-line arguments. This provides configuration file behavior without requiring a separate configuration system.

Default files should have lower precedence than both explicit argument files and command-line arguments. They provide defaults that any explicit argument can override. The order of precedence from lowest to highest would be: default argument files, explicit argument files, command-line arguments.

This feature should be opt-in through configuration, as automatic file loading can surprise users who don't expect it. Applications that enable it should document clearly which files are loaded and from where. Help output might indicate that certain files are automatically loaded if present.

### Format validation and linting

Argument files can become complex, especially if they reference other files or contain many arguments. A validation tool that checks argument files for common problems would improve the user experience. The tool could verify that all referenced files exist, check for syntax errors, detect circular references before runtime, and warn about deprecated or conflicting arguments.

A linting tool could suggest improvements to argument files: consolidating redundant arguments, removing overridden values that have no effect, reorganizing for clarity, or splitting large files into smaller composable pieces. These tools would operate on argument files in isolation, without needing the full application context.

Format validation could also verify that argument files match the application's command structure. By examining the parser configuration, a validator could identify arguments that don't match any defined option or positional, flags used with values, or options missing required values. This catches errors at authoring time rather than runtime.

## Security considerations

### Path traversal

Argument file paths should be validated to prevent path traversal attacks. An attacker-controlled argument file path like `@../../../etc/passwd` should not allow reading arbitrary system files. However, this is more of an application concern than a parser concern; if an attacker can control the command-line arguments, they can already cause arbitrary code execution in most contexts.

The parser should normalize paths and check that they resolve to expected locations. Applications processing untrusted input should restrict argument file paths to specific directories or disable the feature entirely. Absolute paths might be disallowed in security-sensitive contexts.

### Resource exhaustion

Large argument files or deeply nested recursive structures can cause memory exhaustion or long processing times. The parser should impose reasonable limits on file size (perhaps 1MB or 10MB) and recursion depth (3-5 levels). These limits prevent accidental or malicious resource exhaustion.

If an argument file exceeds size limits, the parser fails with a clear error rather than attempting to read it. If expansion exceeds time limits (e.g., 1 second), the parser aborts and reports the problem. These limits should be configurable but have safe defaults.

### Information disclosure

Error messages should be careful about information disclosure. If argument files contain sensitive values like API keys or passwords, error messages should not echo those values. File paths and line numbers can be included in errors, but the actual content should be sanitized or omitted.

Applications handling sensitive data might want to disable argument file expansion entirely or only allow it for files in trusted locations with restricted permissions. The parser should support these use cases through configuration.

## Implementation notes

### File encoding

Argument files should be read as UTF-8 text, as this is the standard encoding for modern text files and matches Python's default behavior. The parser should handle UTF-8 decoding errors gracefully with clear error messages indicating where the invalid sequence was encountered.

BOM (byte order mark) handling should strip UTF-8 BOMs if present at the file start, as some Windows editors insert them. Files saved with other encodings should produce clear errors suggesting the expected encoding.

### Line ending normalization

The parser should normalize line endings, treating `\n`, `\r\n`, and `\r` all as line separators. This ensures argument files work correctly regardless of what system created them. The standard library's text mode reading handles this automatically in most languages.

### Performance considerations

Argument file expansion should be fast enough that users don't notice a delay. Reading and parsing files is I/O bound, but the expansion logic itself should be efficient. Avoid reading files multiple times or performing expensive operations during preprocessing.

For applications that invoke the CLI repeatedly in tight loops (like test frameworks), consider caching expanded results or allowing applications to perform expansion once and reuse the results. The immutable design of the expansion function enables safe caching.

### Compatibility

The implementation should be compatible with Python 3.10+ and work identically across all supported platforms. Path handling should use `pathlib.Path` for correct platform-specific behavior. File reading should handle platform-specific quirks like Windows line endings and case-insensitive file systems.

The feature should integrate cleanly with Flagrant's existing parser without requiring changes to core parsing logic. It should work with all parser features including subcommands, option groups, and advanced arity specifications.

---

**Related pages:**

- [Parser overview](overview.md) - Parser design principles and constraints
- [Configuration](configuration.md) - Parser configuration options
- [Errors](errors.md) - Exception types and error handling
- [Testing](testing.md) - Testing strategy and coverage requirements
- [Types](types.md) - Data structures and type definitions
