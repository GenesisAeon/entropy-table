# Atlas Rules

- Source of truth: `atlas/domains/**/*.yaml` and `atlas/relations/**/*.yaml`.
- Domain shape is enforced by `atlas/schema/domain.schema.json`.
- Relation shape is enforced by `atlas/schema/relation.schema.json`.
- Every domain must provide a stable kebab-case `id` so relation refs are deterministic.
- Every domain must include:
  - `entropy_quantity_kind` in `{production_rate, entropy_flux, state_entropy, budget_entropy, proxy_other}`
  - `epistemic_status` in `{theorem, empirical, numerical, heuristic, disputed, open_problem}`
- Every relation must include:
  - `source_domain_ref`, `target_domain_ref`
  - `relation_type`
  - `what_is_preserved`, `what_is_lost`
  - `conditions` (`text` + optional `params`)
  - `expected_effect_on_entropy_measure` (`direction` + `description`)
  - `must_fail_tests` (at least 1)
  - `status` in `{draft, review, stable}`
- Generated output files live in `outputs/` and must stay generated-only.
