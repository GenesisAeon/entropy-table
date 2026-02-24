# Atlas Contract

## Scope
The atlas models entropy-related factors for model-defined systems. A system may be physically open but still treated as **effectively closed** relative to a chosen modeling boundary.

## Data source of truth
- All atlas entries are authored as YAML.
- YAML is validated against JSON Schema in `atlas/schema/`.
- Additional cross-reference checks are enforced by `tools/validate.py`.

## Extensible `system_type` (hybrid)
`DomainSpec.system_type` is an object with:
- `primary`: stable coarse enum.
- `tags[]`: extensible kebab-case descriptors.
- `notes` (optional).

Rule: if `primary=other`, at least one `tags` value is required.

## Citation strategy
Both domains and relations use inline citation objects (`CitationSpec`) with an `id`. Validation checks for duplicate citation IDs and for citation references used in assumptions/tests/limitations/operators.
