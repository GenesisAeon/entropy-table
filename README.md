# Entropy Table

[![CI](https://github.com/GenesisAeon/entropy-table/actions/workflows/ci.yml/badge.svg)](https://github.com/GenesisAeon/entropy-table/actions)
[![Docs](https://img.shields.io/badge/docs-mkdocs--material-green)](https://GenesisAeon.github.io/entropy-table/)
[![PyPI](https://img.shields.io/badge/PyPI-entropy--table-blue)](https://pypi.org/project/entropy-table/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A contract-first scientific data atlas for stochastic thermodynamics, Markov networks, and open quantum systems.

This project manages structured YAML representations of physical systems, their thermodynamic entropy production rates, and the mathematical relations between them. It is built on strict schema validation, falsifiability, and reproducible CI/CD pipelines.

## Key Features

* **Contract-First Data:** Physical domains and relations are defined in YAML and validated against strict JSON schemas (`domain.schema.json`, `relation.schema.json`).
* **Broad Physics Scope:** Covers Continuous-Time Markov Chains (CTMC), Langevin dynamics (overdamped/underdamped, isothermal/non-isothermal), Biochemical Master Equations (CME), and Quantum Lindblad (GKSL) equations.
* **Reproducible Toolchain:** Fast, deterministic dependency management via `uv` and a unified `Makefile` interface.
* **Knowledge Graph:** Automatic generation of Mermaid.js and Graphviz DOT graphs visualizing the composition and approximation limits of the physical systems.
* **Composition Integrity Validation:** Enforces that physical exchange channels cannot silently disappear when subsystems are grouped into a supersystem — via explicit absorption filters or strict transitive inheritance checks.
* **Machine-Readable API:** All validation tools provide a structured `--json` output for easy integration into web frontends or automated reporting.
* **Full Typer CLI:** `entropy-table validate-all`, `scaffold`, `visualize`, `health`, `metrics`, `render`.
* **Beautiful Documentation:** MkDocs Material website with live GitHub Pages deployment.

## Quickstart

We use [`uv`](https://github.com/astral-sh/uv) for lightning-fast, reproducible dependency management.

```bash
git clone https://github.com/GenesisAeon/entropy-table.git
cd entropy-table
uv sync --extra dev --extra docs
uv run entropy-table --help
uv run mkdocs serve          # live website at http://127.0.0.1:8000
```

## Documentation

**[https://GenesisAeon.github.io/entropy-table/](https://GenesisAeon.github.io/entropy-table/)**

## Tooling & Commands

### CLI (recommended)

```bash
uv run entropy-table validate-all          # full validation
uv run entropy-table scaffold domain ...   # new domain scaffold
uv run entropy-table visualize             # regenerate Atlas graph
uv run entropy-table health --ci-check     # CI health check
uv run entropy-table metrics --format markdown
```

### Makefile (backward compatible)

* `make validate` — Runs the strict JSON schema validation for all domains and relations.
* `make validate-all` — Validates schemas, claims, composition integrity, and bibliographical cross-references.
* `make test` — Runs the comprehensive test suite via `pytest`.
* `make visualize` — Generates a visual Mermaid.js graph of the Atlas in `docs/atlas_graph.mmd`.
* `make health` — Checks for orphaned domains and unfalsifiable claims.
* `make render` — Renders the atlas contents to Markdown and LaTeX formats.
* `make docs` — Start local MkDocs dev server.
* `make docs-build` — Build static documentation site.
* `make docs-deploy` — Deploy documentation to GitHub Pages.

> Advanced users or integrations can invoke the underlying Python tools directly, e.g., `python tools/validate.py --json` for structured error reporting.

## Repository Structure

```
atlas/
  domains/    # Definitions of physical systems (e.g., quantum-lindblad.yaml)
  relations/  # Mappings between domains (coarse_graining, approximation_limit, …)
  claims/     # Falsifiable scientific claims linked to specific domains
  schema/     # JSON schemas enforcing the contract-first architecture
src/
  entropy_table/   # Python package + Typer CLI
tools/        # Legacy Python toolchain: validation, metrics, visualization, rendering
docs/         # MkDocs documentation source
tests/        # pytest test suite
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/contribution.md](docs/contribution.md).

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
