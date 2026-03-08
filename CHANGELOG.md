# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v0.4.0] – 2026-03-08

### Summary

v0.4.0 closes the last major integrity gap in the composition layer: physical
exchange channels can no longer silently disappear when subsystems are grouped
into a supersystem.  The release introduces a two-mode channel-inheritance
validator that is grounded in the absorption / coarse-graining semantics of the
atlas schema.

---

### Added

- **Transitive channel-inheritance validation**
  (`validate_transitive_channels` in `tools/validate_composition.py`):
  automatically enforces that every `exchange_channel` of a subsystem is
  accounted for in its supersystem.  Two modes are implemented:

  * **Explicit filter (absorption semantics):** when a composition relation
    declares a `channels` (or `exchange_channels` / `coupling_channels`) field,
    that list acts as a coarse-graining filter.  The validator checks that every
    listed channel appears in *both* `boundary.exchange_channels` of the source
    and target domain; channels absent from the list are treated as internally
    absorbed and are not required to surface in the supersystem.

  * **Implicit transitive inheritance:** when no `channels` field is present,
    the validator computes the set-difference
    `source.exchange_channels − target.exchange_channels`.  Any non-empty
    difference is reported as an `integrity error` naming the missing channels,
    the subsystem, and the supersystem — preventing exchange streams from
    vanishing unintentionally during mere grouping operations.

  Legacy heuristic composition signals (coupling relations carrying a `parts`
  list) emit a `WARNING` and are skipped by the strict transitive check for
  backwards compatibility.

- **Failure-fixture suite** (`tests/fixtures/fail/transitive_channels/`):
  three minimal YAML fixtures (`atom.yaml`, `molecule.yaml`, `comp.yaml`)
  demonstrate the canonical failing case (subsystem declares `information`;
  supersystem only declares `heat`).

- **5 new tests** in `tests/test_validate_composition.py` covering:
  transitive mismatch (text + JSON output), superset-passes, explicit-filter
  passes, and legacy-heuristic warning.
  Full suite: **114 tests**, all passing.  (PR #72)

---

### Merged Pull Requests

| # | Title |
|---|---|
| #72 | Add `validate_transitive_channels` for composition integrity |

---

## [v0.3.0] – 2026-03-08

### Summary

v0.3.0 consolidates the infrastructure of the atlas into a stable, production-ready
foundation.  The sprint introduces strict schema versioning, an automated case
management layer, interactive scaffolding for new domains, and verified DOI
caching — all wired into the existing `make` workflow and the CI pipeline.

---

### Added

- **Case Management Tool** (`tools/manage_cases.py`): two subcommands —
  `create` scaffolds a case file from `templates/case_template.yaml` (with
  optional `--claim-file` to infer domain and category automatically);
  `validate` cross-checks every claim's `evidence.cases` list against actual
  files in `atlas/cases/`, reporting dangling references (hard error) and
  orphaned cases (soft warning, promoted to error with `--strict`).
  Wired into `make new-case`, `make validate-cases`, and the `validate-all`
  target so CI detects referential breaks automatically.
  17 new tests; full 103-test suite passes.  (PR #68)
- **Scaffolding** (`tools/scaffold.py`, `make new-domain`): stamps out a new
  domain YAML from `templates/domain_template.yaml` with the correct `id`
  field injected and every other field left as an explicit `<TODO:…>`
  placeholder.  Prevents the "copy-and-forget-to-change-the-id" class of
  contributor errors; enforces kebab-case for entity IDs and the
  digit-prefixed underscore convention (e.g. `01_physics`) for category
  names.  Interactive prompt fires when `ID` is omitted.  (PR #67)
- **DOI Caching & Network Verification** (`--verify-network` flag on
  `validate_bibliography.py`): persistent DOI cache at
  `cache/valid_dois.json` with exponential backoff on transient HTTP errors;
  placeholder DOIs (`10.0000/…`) are silently skipped so golden fixtures
  never trigger false CI failures.  Cache wired into `actions/cache@v4`,
  keyed on the hash of `refs.yaml`, so it refreshes automatically when
  citations change.  (PR #66)

### Changed

- **Schema Versioning** (`atlas/schema/domain.schema.json`,
  `atlas/schema/relation.schema.json`): `schema_version` is now a required,
  enum-enforced field (`"1.0.0"`) across every domain and relation YAML.
  `tools/validate.py` emits a clear `VersionConflict` pre-check error (with
  declared vs. expected versions) before falling through to jsonschema,
  eliminating redundant enum noise in error output.  All 10 domain YAMLs
  and 9 relation YAMLs migrated; `templates/domain_template.yaml` seeds
  the correct value so `scaffold.py` output is valid out of the box.
  8 new schema-version tests; 111 tests total.  (PR #69)

---

### Merged Pull Requests

| # | Title |
|---|---|
| #69 | Add `schema_version` v1.0.0 to domain and relation schemas |
| #68 | Add case management tool with `create`/`validate` subcommands |
| #67 | Add scaffold tool and `make new-domain` Makefile target |
| #66 | Skip placeholder DOIs and add network verification with DOI caching |

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

[v0.4.0]: https://github.com/GenesisAeon/entropy-table/releases/tag/v0.4.0
[v0.3.0]: https://github.com/GenesisAeon/entropy-table/releases/tag/v0.3.0
[v0.2.0]: https://github.com/GenesisAeon/entropy-table/releases/tag/v0.2.0
[v0.1.0]: https://github.com/GenesisAeon/entropy-table/releases/tag/v0.1.0
