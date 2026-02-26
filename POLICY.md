# Scientific Release Policy

## Definitions
- **Draft**: working content that may be revised freely.
- **Review**: content under structured review; edits are expected but must remain citable.
- **Stable**: scientific content treated as archival; changes are controlled and auditable.
- **Release snapshot**: deterministic export of `atlas/domains`, `atlas/relations`, and `atlas/claims` plus metadata into a versioned bundle.

## Stability rules
- Stable entries are append-only by default.
- Editing an existing stable entry requires one of:
  1. a new versioned file/identifier, or
  2. an explicit breaking-change declaration in release notes.
- Stable scientific claims/domains must keep must-fail tests and citation requirements enforced by existing validators.

## Change workflow
- PRs intended for release must pass:
  - `python tools/validate.py`
  - `python tools/validate_claims.py`
  - `python tools/validate_composition.py`
  - repository test suite (`pytest`)
- Snapshot generation must be deterministic and reproducible from repository state.

## Citation guidance
- Cite releases using both:
  - `snapshot_id`, and
  - `bundle_sha256` from `MANIFEST.json`.
- External DOI minting (e.g., Zenodo) is out of scope here, but bundle/manifest artifacts are designed for upload and citation.
