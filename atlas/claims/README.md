# Claim Layer

The `atlas/claims/` tree stores **append-only research claims** as first-class scientific units.

Claims are intentionally boring and auditable:
- they are short, structured statements;
- they carry assumptions and falsification hooks;
- they link to evidence (citations and optional compute case IDs);
- they are validated by `tools/validate_claims.py`.

This is **not** a new ontology engine. Domains and relations remain the canonical structural graph.
Claims add testable scientific assertions on top of that graph.

## Layout

Claims live under:

- `atlas/claims/<group>/<domain_ref>/claim-<id>.yaml`

Current grouping uses scientific area prefixes (for example `01_physics`).

Examples:
- `atlas/claims/01_physics/overdamped-langevin-st/claim-ep-nonnegative-isothermal.yaml`
- `atlas/claims/01_physics/ctmc-schnakenberg/claim-schnakenberg-ep-rate-definition.yaml`

## Conventions

- Claim IDs are kebab-case and globally unique across all claim files.
- Claim files are append-only research atoms; prefer adding a new claim over rewriting old intent.
- `domain_ref` must point to an existing domain ID in `atlas/domains/`.
- `relations_touched` (optional) should reference existing relation IDs if used.

For the full contract, workflow, and examples, see `docs/claims.md`.
