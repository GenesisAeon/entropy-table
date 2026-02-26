# Claims

## Purpose

The Claim Layer introduces a small, explicit unit for scientific assertions that can be reviewed, queried, and reported independently of domain/relation schemas.

A claim is an append-only research atom with:
- a precise statement,
- assumptions,
- falsification hooks,
- evidence links,
- a lifecycle status.

## YAML Contract

Each claim YAML must follow this shape (enforced by `tools/validate_claims.py`).

### Required fields

- `id`: string, kebab-case, globally unique across all claims.
- `title`: string.
- `domain_ref`: string, must match an existing domain ID.
- `claim_kind`: one of:
  - `definition`
  - `theorem`
  - `lemma`
  - `heuristic`
  - `empirical`
  - `limitation`
- `statement`:
  - `text`: string (short, precise)
  - `latex`: optional string
- `assumptions`: list of strings (minimum 1 unless `claim_kind=definition`)
- `falsification`:
  - `must_fail_refs`: list of strings (minimum 1 unless `claim_kind=definition`)
  - `notes`: optional string
- `evidence`:
  - `citations`: list of citation IDs
  - `cases`: optional list of case IDs
  - `provenance`: string
- `status`: one of `draft`, `review`, `stable`

### Optional fields

- `relations_touched`: list of relation IDs
- `tags`: list of kebab-case strings
- `notes`: short freeform string

### Validation policy details

- `id` regex: `^[a-z0-9]+(?:-[a-z0-9]+)*$`
- For `review` and `stable` claims, `evidence.citations` must contain at least one item.
- For `draft`, `evidence.citations` may be empty.
- `relations_touched` IDs, when present, must exist in `atlas/relations/`.

## Compute Evidence (Claim ↔ Case binding)

Claims and compute cases use a **soft linkage** convention so staging data remains optional.

- Claim-side linkage uses `evidence.cases` and stores **case IDs**, not file paths.
- Case-side linkage may use `claims: [claim_id, ...]` in `staging/cases/*.yaml`.
- Validation always checks **syntax** for linkage IDs.
- Validation does **not** require staging files or case existence by default.

### ID formats

- `claim_id` regex (kebab-case):
  - `^[a-z0-9]+(?:-[a-z0-9]+)*$`
- `case_id` regex (kebab-case + optional version suffix):
  - `^[a-z0-9]+(?:-[a-z0-9]+)*(?:-v[0-9]+)?$`

Examples:

- `ctmc-3cycle-nonzero-v1`
- `diffusion-ep-zero-current-v1`

### Reporting behavior

- Claim reports summarize stable/review claims with and without linked compute cases.
- Compute reports can optionally scan case YAMLs and summarize claim IDs referenced by cases.
- If atlas claims are present, compute report may emit warnings for unknown referenced claim IDs.

## Location and naming

Claims are stored at:

- `atlas/claims/<group>/<domain_ref>/claim-<id>.yaml`

The validator checks path consistency:
- filename must be exactly `claim-<id>.yaml`
- parent directory name must match `domain_ref`

## Example (minimal)

```yaml
id: ep-nonnegative-isothermal
title: Isothermal overdamped total EP is nonnegative
domain_ref: overdamped-langevin-st
claim_kind: theorem
statement:
  text: Total entropy production is nonnegative under local detailed balance in isothermal overdamped diffusion.
assumptions:
  - Markovian overdamped diffusion dynamics.
  - Local detailed balance with an isothermal bath.
falsification:
  must_fail_refs:
    - equilibrium-zero-ep
evidence:
  citations: [seifert2012-rpp, lebowitz-spohn1999-jsp]
  provenance: Derived from path-probability ratio representation.
status: review
tags: [second-law, stochastic-thermodynamics]
```

## Workflow

1. Add a new claim file under `atlas/claims/<group>/<domain_ref>/`.
2. Run claim validation:
   - `python tools/validate_claims.py`
3. Explore claims:
   - `python tools/query_claims.py list-claims`
   - `python tools/query_claims.py graph-summary`
4. Generate report:
   - `python tools/report_claims.py`
   - output: `outputs/claims_report.md`

Keep claims concise and falsifiable. Avoid universal or ontology-expanding statements.
