# entropy-table

Atlas-first repository skeleton for a mechanism table of entropy production proxies.

## What this is

- Source-of-truth domain definitions live in YAML files under `atlas/domains/`.
- A JSON Schema (`atlas/schema/domain.schema.json`) enforces required structure.
- Tooling validates YAML and renders generated artifacts to `outputs/`.

## Repository rules

- Edit only files under `atlas/domains/**/*.yaml` for domain content.
- Generated files under `outputs/` are artifacts and should not be hand-edited.
- `outputs/` is gitignored by default.

## Add a domain

1. Create a new YAML under `atlas/domains/<group>/your_domain.yaml`.
2. Include required fields:
   - `domain`, `system_type`, `scope`
   - `entropy_proxy`
   - `spectral_bands`
   - `operators`
   - `bands` (must include `beta` and `theta`)
   - `must_fail_tests` (at least 2 entries)
   - `citations`, `status`
3. Run validation locally.

## Validate

```bash
python tools/validate_atlas.py
```

## Render

```bash
python tools/render_atlas.py
```

Outputs are written to:

- `outputs/atlas.md`
- `outputs/atlas.tex`
