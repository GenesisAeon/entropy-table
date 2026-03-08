# Entropy Table

**A living, machine-readable scientific atlas** for stochastic thermodynamics, Markov networks and open quantum systems.

[![PyPI](https://img.shields.io/badge/PyPI-entropy--table-blue)](https://pypi.org/project/entropy-table/)
[![CI](https://github.com/GenesisAeon/entropy-table/actions/workflows/ci.yml/badge.svg)](https://github.com/GenesisAeon/entropy-table/actions)
[![Docs](https://img.shields.io/badge/docs-mkdocs-green)](https://GenesisAeon.github.io/entropy-table/)

## What is this?

Entropy Table manages structured YAML representations of physical systems, their thermodynamic entropy production rates, and the mathematical relations between them. It is built on strict schema validation, falsifiability, and reproducible CI/CD pipelines.

**Domains covered:** Continuous-Time Markov Chains (CTMC), Langevin dynamics (overdamped/underdamped), Biochemical Master Equations (CME), and Quantum Lindblad (GKSL) systems.

## Quickstart

```bash
git clone https://github.com/GenesisAeon/entropy-table.git
cd entropy-table
uv sync --extra dev --extra docs
uv run entropy-table --help
uv run mkdocs serve          # live preview at http://127.0.0.1:8000
```

## CLI Commands

| Command | Description |
|---|---|
| `uv run entropy-table validate-all` | Full schema + claims + composition validation |
| `uv run entropy-table scaffold domain <id>` | Scaffold a new domain YAML |
| `uv run entropy-table visualize --format mermaid` | Regenerate the Atlas graph |
| `uv run entropy-table health --ci-check` | Strict CI health check |
| `uv run entropy-table metrics --format markdown` | Compute atlas metrics |

## Explore the Atlas

- [Schema & Tutorial](schema.md) — how to add a new domain in 5 minutes
- [Developer Guide](developer-guide.md) — CLI reference, pre-commit, new commands
- [Contribution Rules](contribution.md) — all rules for valid contributions
- [Atlas Knowledge Graph](https://github.com/GenesisAeon/entropy-table/blob/main/docs/atlas_graph.mmd) — live Mermaid graph
