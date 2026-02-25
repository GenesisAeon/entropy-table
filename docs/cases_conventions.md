# Compute Cases Conventions

This document defines lightweight conventions for adding and running compute cases.

## Naming

- **Case ID format:** `<domain-or-topic>-<short-purpose>-v<nn>`
  - Examples: `ctmc-equilibrium-v01`, `diffusion-high-force-v02`
- **Case file name:** `<id>.yaml`
  - Keep one case per file for clean scan + reporting.

## When to create a case

Create a case when you need one of the following:

- A **regression** for a must-fail or previously broken behavior.
- A **numeric sanity check** with known/controlled expected sigma behavior.
- A **boundary or assumption break** (for example, nonisothermal assumptions or edge parameter ranges).

## Minimal expected fields

At minimum, include:

- `id`
- `calculator`
- `input` (`json-inline` or `json-file`)

Recommended for robust checks:

- `expected` with one or more constraints: `sigma_min`, `sigma_max`, `sigma_close`
- `notes` (short rationale)
- `citations` (stable IDs if the case is tied to a source)

## Using `staging/cases/` safely

- Keep manually authored case YAML files in `staging/cases/` while iterating.
- Do **not** commit temporary staging artifacts or generated reports.
- Prefer direct report output overrides during experiments:
  - `python -m tools.compute.report --scan-dir staging/cases/ --out <tmpdir>/report.md`
- In automated tests, use temp directories instead of real `staging/` data.

## Example “good case” snippet

```yaml
id: diffusion-sanity-v01
calculator: diffusion-ep-1d
input:
  format: json-inline
  data:
    mobility: 2.0
    force: 2.0
    temperature: 2.0
expected:
  sigma_close:
    value: 4.0
    tol: 1e-12
notes: simple positive control for diffusion sigma
citations: [diffusion-ref-001]
```
