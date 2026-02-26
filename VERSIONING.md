# Versioning Policy

## Scope
This repository tracks two related version surfaces:
1. **Schema version** (contract shape and meaning)
2. **Data version** (snapshot content)

## Schema version
Schema identity is defined by content hashes of:
- `atlas/schema/domain.schema.json`
- `atlas/schema/relation.schema.json`
- claim contract hash (`docs/claims.md`)

A project may additionally publish human tags (examples):
- `schema-v0.4`
- `schema-v0.5`

## Data version
Data identity is defined by:
- `snapshot_id` (UTC timestamp format `YYYYMMDD-HHMMSSZ`, optional suffix)
- `bundle_sha256` (hash of canonical `bundle.json` bytes)

Recommended tags (examples):
- `atlas-v0.1`
- `atlas-v0.2`

## Breaking vs non-breaking changes
Breaking changes include:
- schema structure changes
- enum/value-space changes
- required-field changes
- semantic meaning changes for existing fields/contracts

Non-breaking changes include:
- adding new domains/relations/claims
- adding optional fields compatible with existing consumers
- adding documentation or release metadata without changing data semantics

## Practical guidance
- Treat schema and data tags independently when useful.
- For citations and reproducibility, prefer `snapshot_id + bundle_sha256` from the release manifest.
