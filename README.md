# Entropy Table

A contract-first scientific data atlas for stochastic thermodynamics, Markov networks, and open quantum systems.

This project manages structured YAML representations of physical systems, their thermodynamic entropy production rates, and the mathematical relations between them. It is built on strict schema validation, falsifiability, and reproducible CI/CD pipelines.

## Key Features

* **Contract-First Data:** Physical domains and relations are defined in YAML and validated against strict JSON schemas (`domain.schema.json`, `relation.schema.json`).
* **Broad Physics Scope:** Covers Continuous-Time Markov Chains (CTMC), Langevin dynamics (overdamped/underdamped, isothermal/non-isothermal), Biochemical Master Equations (CME), and Quantum Lindblad (GKSL) equations.
* **Reproducible Toolchain:** Fast, deterministic dependency management via `uv` and a unified `Makefile` interface.
* **Knowledge Graph:** Automatic generation of Mermaid.js and Graphviz DOT graphs visualizing the composition and approximation limits of the physical systems.
* **Composition Integrity Validation:** `validate_composition.py` enforces that physical exchange channels cannot silently disappear when subsystems are grouped into a supersystem — via explicit absorption filters or strict transitive inheritance checks.
* **Machine-Readable API:** All validation tools provide a structured `--json` output for easy integration into web frontends or automated reporting.

## Quickstart

We use [`uv`](https://github.com/astral-sh/uv) for lightning-fast, reproducible dependency management.

```bash
# 1. Clone the repository
git clone https://github.com/your-org/entropy-table.git
cd entropy-table

# 2. Install dependencies via uv (creates a .venv and syncs uv.lock)
uv sync

# 3. Activate the virtual environment
source .venv/bin/activate
```

## Tooling & Commands

The project provides a unified `Makefile` to handle all workflows:

* `make validate` — Runs the strict JSON schema validation for all domains and relations.
* `make validate-all` — Validates schemas, claims, composition integrity, and bibliographical cross-references.
* `make test` — Runs the comprehensive test suite (114 tests) via `pytest`.
* `make visualize` — Generates a visual Mermaid.js graph of the Atlas in `docs/atlas_graph.mmd`.
* `make health` — Checks for orphaned domains and unfalsifiable claims.
* `make render` — Renders the atlas contents to Markdown and LaTeX formats.

> Advanced users or integrations can invoke the underlying Python tools directly, e.g., `python tools/validate.py --json` for structured error reporting.

## Repository Structure

```
atlas/
  domains/    # Definitions of physical systems (e.g., quantum-lindblad.yaml)
  relations/  # Mappings between domains (coarse_graining, approximation_limit, …)
  claims/     # Falsifiable scientific claims linked to specific domains
  schema/     # JSON schemas enforcing the contract-first architecture
tools/        # Python toolchain: validation, metrics, visualization, rendering
outputs/      # Rendered artifacts (not committed)
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
