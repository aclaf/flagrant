set unstable

default_python := "3.11"

# List available recipes
default:
  @just --list

# Install all dependencies (Python + Node.js)
install:
  uv sync --frozen

install-all:
  uv sync --frozen --all-groups --all-extras

install-benchmarking:
  uv sync --frozen --group benchmarking

install-fuzzing:
  uv sync --frozen --group fuzzing

install-mutation:
  uv sync --frozen --group mutation

install-profiling:
  uv sync --frozen --group profiling

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
benchmark:
  uv run --frozen --group benchmarking pytest tests/benchmarks/ --benchmark-only --benchmark-json=benchmark_results.json

# Save benchmark baseline
benchmark-save:
  uv run --frozen --group benchmarking pytest tests/benchmarks/ --benchmark-only --benchmark-save=baseline

# Compare benchmarks against latest saved run
benchmark-compare:
  uv run --frozen --group benchmarking pytest tests/benchmarks/ --benchmark-only --benchmark-compare

# Compare benchmarks against baseline and fail if regression > 15%
benchmark-compare-strict: install
  uv run --frozen --group benchmarking pytest tests/benchmarks/ --benchmark-only --benchmark-compare --benchmark-compare-fail=mean:15%

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
  uv run --frozen lint-imports

lint-python: install
  uv run --frozen ruff check .
  uv run --frozen ruff format --check .
  uv run --frozen basedpyright

# Lint import dependencies
lint-imports: install
  uv run --frozen lint-imports

# Lint GitHub Actions workflows
lint-actions: install
  actionlint

# Lint documentation
lint-docs: install
  uv run yamllint --strict mkdocs.yml
  pnpm exec markdownlint-cli2 "**/*.md"
  uv run --frozen djlint docs/.overrides
  pnpm exec biome check docs/

# Run Vale linter
lint-vale:
  vale docs/ CONTRIBUTING.md README.md SECURITY.md

# Sync Vale styles and dictionaries
vale-sync:
  vale sync

# Run pre-commit hooks
prek: install
  uv run --frozen prek

# Clean build artifacts
clean:
  rm -rf site/
  rm -rf dist/
  rm -rf build/
  find . -type d -name __pycache__ -exec rm -rf {} +
  find . -type d -name .pytest_cache -exec rm -rf {} +
  find . -type d -name .ruff_cache -exec rm -rf {} +

# Build the latest documentation
build-docs: clean
  FLAGRANT_DOCS_ENV=latest uv run mkdocs build
  uv pip freeze > requirements.txt

# Build the documentation for PR preview
[script]
build-docs-pr number: clean
  rm -f mkdocs.pr.yml
  cat << EOF >> mkdocs.pr.yml
  INHERIT: ./mkdocs.yml
  site_name: Flagrant Documentation (PR-{{number}})
  site_url: https://{{number}}-flagrant-docs-pr.tbhb.workers.dev/
  EOF
  uv run --group docs mkdocs build
  echo "User-Agent: *\nDisallow: /" > site/robots.txt
  uv pip freeze > requirements.txt

# Deploy latest documentation
deploy-docs: build-docs
  pnpm exec wrangler deploy --env latest

# Deploy documentation preview
deploy-docs-pr number: (build-docs-pr number)
  pnpm exec wrangler versions upload --env pr --preview-alias pr-{{number}}

# Develop the documentation site locally
dev-docs:
  uv run --group docs mkdocs serve --livereload --dev-addr 127.0.0.1:8001

mermaid *args:
  pnpm exec mmdc {{args}}
