set unstable

default_python := "3.13"

# List available recipes
default:
  @just --list

# Install all dependencies (Python + Node.js)
install:
  uv sync --frozen --all-packages --all-groups --all-extras

# Build the Python package
build: install
  uv build

# Run tests
test target=default_python *args: install
  #!/bin/sh
  if [ "{{target}}" = "{{default_python}}" ]; then
    uv run --frozen pytest "$@"
  else
    uv run --isolated --python={{target}} --frozen pytest "$@"
  fi

# Run performance benchmarks
benchmark: install
  uv run --frozen pytest tests/benchmarks/ --benchmark-only --benchmark-json=benchmark_results.json

# Save benchmark baseline
benchmark-save: install
  uv run --frozen pytest tests/benchmarks/ --benchmark-only --benchmark-save=baseline

# Compare benchmarks against latest saved run
benchmark-compare: install
  uv run --frozen pytest tests/benchmarks/ --benchmark-only --benchmark-compare

# Compare benchmarks against baseline and fail if regression > 15%
benchmark-compare-strict: install
  uv run --frozen pytest tests/benchmarks/ --benchmark-only --benchmark-compare --benchmark-compare-fail=mean:15%

# Format code
format: install
  uv run --frozen codespell -w
  uv run --frozen ruff format .

# Lint code
lint: install
  uv run --frozen codespell
  uv run --frozen yamllint --strict .
  uv run --frozen ruff check .
  uv run --frozen basedpyright

lint-python: install
  uv run --frozen ruff check .
  uv run --frozen ruff format --check .
  uv run --frozen basedpyright

# Lint GitHub Actions workflows
lint-actions: install
  actionlint

# Run pre-commit hooks
prek: install
  uv run --frozen prek

# Clean build artifacts
clean:
  rm -rf dist/
  find . -type d -name __pycache__ -exec rm -rf {} +
  find . -type d -name .pytest_cache -exec rm -rf {} +
  find . -type d -name .ruff_cache -exec rm -rf {} +
