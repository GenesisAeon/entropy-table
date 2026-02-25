# Composition Integrity Validation

`tools/validate_composition.py` adds a focused integrity layer for **systems in systems** checks.
It complements schema validation by enforcing cross-file constraints that keep composition claims
scientifically coherent as the atlas grows.

## Why this exists

Schema checks ensure each file is well-formed. Composition integrity checks ensure that the
network formed by composition relations remains physically interpretable and auditable across files.

## Effective closure in this repository

In this atlas, `boundary.closure_type: effectively_closed` means the model treats external exchange
as negligible or controlled at the modeling scale. It does **not** imply absolute physical isolation.
The boundary declaration should state those assumptions in `boundary.closure_notes`.

## Rules enforced

1. **Composition endpoint integrity**
   - Composition edges must reference existing domains.
   - Composition edges must not be self-loops.

2. **Acyclic composition graph**
   - Composition edges must form a DAG.
   - Cycles are reported with a cycle path and fail validation.

3. **Effective-closure subsystem checks**
   - Any domain used as a subsystem in composition (`source_domain_id`) must declare
     `boundary.closure_type`.
   - If closure type is `effectively_closed`, `boundary.closure_notes` must be non-empty.
   - If closure type is `effectively_closed` and `boundary.exchange_channels` is empty, emit a warning.

4. **Explicit channel compatibility (relation-declared channels)**
   - If a relation explicitly declares channels via `exchange_channels`, `coupling_channels`, or `channels`,
     every declared channel must appear in both endpoint domains' `boundary.exchange_channels`.
   - Missing declarations on either endpoint are validation errors.
   - If relation channels are omitted, validation leaves channel semantics implicit.

5. **Composition depth sanity warning**
   - The validator computes maximum composition depth.
   - Depth above 8 emits a warning (configurable via CLI).

## Short examples

Good composition relation (minimal sketch):

```yaml
id: sub-to-super
source_domain_id: subsystem-a
target_domain_id: supersystem-b
relation_type: composition
parts: [subsystem-a]
```

Bad cycle (fails):

```yaml
# r1
source_domain_id: a
target_domain_id: b
relation_type: composition

# r2
source_domain_id: b
target_domain_id: a
relation_type: composition
```

## Workflow

Run core contract checks and composition integrity together:

```bash
python tools/validate.py
python tools/validate_composition.py
python tools/validate_claims.py
```

Use **composition** when asserting subsystem-to-supersystem containment structure.
Use **coarse-graining** when asserting a reduced description or abstraction map across scales.

## Forward-looking note

Aggregation rules are not first-class in this validation layer yet; planned schema evolution is tracked
for PR14.
