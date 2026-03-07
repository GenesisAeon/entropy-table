# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v0.2.0] – 2026-03-07

### Summary

This release transforms the *Entropy Table* from a solid prototype into a
cross-domain, professional scientific data atlas.  Alongside a major
content expansion into quantum systems and biochemistry, v0.2.0 ships a
fast, fully-reproducible toolchain and a machine-readable validation API.

---

### New Domains

| Domain key | Description |
|---|---|
| `quantum-lindblad` | GKSL / Lindblad master equation with strict CPTP integrity checks and Spohn's inequality |
| `biochemical-cme` | Chemical Master Equation (CME) with Wegscheider cycle-affinity consistency conditions |
| `overdamped-nonisothermal-langevin` | Stochastic thermodynamics with spatially varying temperature fields and anomalous entropy production ($\sigma_\text{anom} \ge 0$) |

### New Relations

- **Quantum → Classical limit:** formal limit from `quantum-lindblad` to the
  classical CTMC (Pauli master equation).
- **CME → Schnakenberg topology:** composition of the Chemical Master Equation
  into the Schnakenberg cycle decomposition.

---

### Toolchain & API

- **`--json` flag on all validators** (`validate.py`, `validate_claims.py`,
  `validate_composition.py`, `validate_bibliography.py`): structured,
  machine-parseable error reports for CI integration and downstream tooling.
  Covered by **86 automated tests**.
- **Automatic knowledge-graph visualisation** (`tools/visualize.py`):
  generates Mermaid.js (`.mmd`) and Graphviz (`.dot`) graphs of the domain
  architecture.  Node shapes encode closure type; colours encode epistemic
  status.
- **Central `Makefile`**: `make validate-all`, `make test`, `make visualize`,
  and `make release` provide a seamless onboarding experience for new
  contributors.

---

### CI / CD & Reproducible Builds

- **`uv` package manager**: dependency management migrated to `uv` with an
  exactly-pinned `uv.lock` for deterministic builds.
- **GitHub Actions upgrade**: the CI pipeline now runs the full, deep
  validation chain on every push, uses `setup-uv` caching (sub-second
  install times), and uploads the generated Mermaid graph as a build
  artefact.

---

### Schema Migration & Cleanup

- **PR #49 (golden domains):** proxy-model domains thermodynamically linked
  (Sekimoto / Sagawa-Ueda) via `[heat, information]` channels.
  `regime_shift` relations now use the dedicated semantic block.
- **README rewrite:** contract-first approach, new features, and the
  `uv` / `make` quickstart prominently documented.

---

### Merged Pull Requests

| # | Title |
|---|---|
| #63 | Add JSON-feature tests for all validators |
| #62 | Add `--json` interface to `validate_composition` and `validate_bibliography` |
| #61 | Refactor validation helpers |
| #60 | Optimise CI pipeline with `uv` caching and artefact upload |
| #59 | Structured JSON error output for `validate.py` |
| #58 | Migrate to `uv` package manager |
| #57 | Fix CI pipeline |
| #53 | Repo-analysis feedback and cleanup |
| #52 | Add `quantum-lindblad` domain (quantum open systems) |
| #51 | Add `biochemical-cme` domain (biochemical reaction networks) |
| #50 | Add `overdamped-nonisothermal-langevin` domain |
| #49 | Link golden proxy-model domains via heat / information channels |
| #48 | Define channel validation |

---

## [v0.1.0] – initial release

Bootstrap of the contract-first atlas skeleton with:

- Domain and relation schemas (`atlas/schema/`)
- CTMC Schnakenberg and overdamped Langevin domains
- Core validation toolchain (`validate.py`, `validate_claims.py`,
  `validate_composition.py`, `validate_bibliography.py`)
- Atlas index builder, read-only query CLI
- Claim layer with evidentiary loop to cases
- Bibliography layer
- Graph-health and metrics reporting
- Release dataset packager (`tools/release.py`)
- Staging workflow and template-based domain extractor

[v0.2.0]: https://github.com/GenesisAeon/entropy-table/releases/tag/v0.2.0
[v0.1.0]: https://github.com/GenesisAeon/entropy-table/releases/tag/v0.1.0
