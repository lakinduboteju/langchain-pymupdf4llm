# Contributing to `langchain-pymupdf4llm`

Thanks for contributing.

## Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)
- Docker (optional, for containerized development)

## Local setup

```bash
uv sync --extra dev --extra test --extra notebooks
```

## Development workflow

Run quality checks before opening a pull request:

```bash
uv run ruff check .
uv run ruff format . --check
uv run mypy
uv run pytest -v
```

Build package artifacts:

```bash
uv build
```

## Test selection

Markers:

- `unit`
- `integration`
- `network`

Network tests are skipped by default. Run them explicitly:

```bash
uv run pytest -v -m network
```

## Pre-commit hooks

Install hooks locally:

```bash
uv run pre-commit install
```

Run all hooks on demand:

```bash
uv run pre-commit run --all-files
```

## Devcontainer and Docker

- `.devcontainer/devcontainer.json` is the recommended setup for Cursor/VS Code users.
- Manual Docker scripts are available:
  - `bash ./docker_build_dev_env.sh`
  - `bash ./docker_run_dev_env.sh`

## Creating PDF test fixtures

To generate PDF examples from LaTeX:

```bash
apt update -y
apt install -y texlive
cd tests/examples
pdflatex sample_1.tex
```

## Release workflow

- CI runs on pull requests and pushes to `main`.
- Tagged releases (`v*`) publish to PyPI via GitHub Actions.
- Update version in `pyproject.toml` before tagging.

## Licensing note

This package depends directly on `pymupdf4llm` / `pymupdf` under AGPL/commercial terms. Contributions must remain compatible with this repository's `AGPL-3.0-only` licensing.
