# Staging + Extraction Workflow

This workflow keeps raw research dumps out of the contract atlas and produces auditable YAML drafts.

## 1) Stage raw artifacts (gitignored)

Place raw notes, exports, and DeepResearch dumps under `staging/`.

Examples:

- `staging/notes/domain_x.md`
- `staging/raw/source_export.json`

`staging/` is ignored so noisy intermediate artifacts never enter version control.

## 2) Start from schema-shaped template

Use `templates/domain_template.yaml` as the source for new domain drafts. It includes required sections and `<TODO>` placeholders.

## 3) Apply minimal structured fields with extractor

```bash
python tools/extract_domain_from_template.py \
  --template templates/domain_template.yaml \
  --out atlas/domains/01_physics/new-domain-id.yaml \
  --set id=new-domain-id \
  --set title="New Domain Title" \
  --set system_type.primary=stochastic_thermodynamics \
  --set status=review
```

The extractor:

- loads the template
- applies dotted-path assignments from `--set`
- writes YAML to `--out`
- refuses overwrite unless `--force` is provided

## 4) Human review + completion

Complete remaining placeholders manually. Keep claims conservative and cite supporting sources.

## 5) Validate and render

Before proposing changes:

```bash
python tools/validate.py
pytest -q
python tools/render.py
```
