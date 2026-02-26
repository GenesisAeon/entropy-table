# Schema RFC PR14: Explicit Composition, Aggregation, and Regime Semantics

## Motivation

PR14 removes ambiguity in relation semantics by making composition and aggregation first-class schema concepts. This improves scientific reproducibility by ensuring nested systems and aggregation constraints are explicit rather than inferred from weak heuristics.

## Changelog (Relation Schema)

### 1) `relation_type` additions/refinement

The relation enum now explicitly includes:

- `composition`
- `aggregation_rule`
- `regime_shift`

### 2) Standardized channels

Optional top-level field:

```yaml
channels: [heat, work, information]
```

- Channels are kebab-case tags.
- Field is optional for backward compatibility.

### 3) Explicit composition block

Optional block with strict type coupling:

```yaml
relation_type: composition
composition:
  kind: subsystem_of
  parts:
    - domain_ref: subsystem-langevin
      role: subsystem
      weight: 1.0
  notes: Explicit nesting semantics.
```

Rules:

- `relation_type: composition` requires `composition` block.
- Presence of `composition` block requires `relation_type: composition`.

### 4) Explicit aggregation semantics block

Optional block with strict type coupling:

```yaml
relation_type: aggregation_rule
aggregation:
  target_quantity: entropy_production
  rule_kind: upper_bound
  statement:
    text: Total entropy production is bounded by the sum of local rates.
    latex: "\\Sigma_{tot} \\le \\sum_i \\Sigma_i"
  conditions: weak coupling, finite observation window
  failure_modes: [strong-nonlocal-correlation]
```

Rules:

- `relation_type: aggregation_rule` requires `aggregation` block.
- Presence of `aggregation` block requires `relation_type: aggregation_rule`.

### 5) Regime shift semantics block

Optional block:

```yaml
relation_type: regime_shift
regime:
  breaks_assumptions: [markovianity, local-equilibrium]
  new_assumptions: [coarse-memory-kernel]
  singular_limit: true
```

Rule:

- Presence of `regime` requires `relation_type: regime_shift`.

## Backward compatibility

- Existing relations remain valid unless they use an invalid enum value.
- Legacy composition signals (e.g., `parts`, composition tags, older composition hints) are still detected by `tools/validate_composition.py`, but now produce a migration warning.
- No forced bulk edits are required to keep current datasets parseable.

## Migration steps (gradual)

1. Pick a legacy relation currently treated as composition by heuristic detection.
2. Set `relation_type: composition`.
3. Add `composition.kind` and `composition.parts` entries (`domain_ref`, optional `role`, optional `weight`).
4. Optionally add explicit `channels` for coupling/exchange semantics.

## Tooling behavior in PR14

- `tools/validate_composition.py` now prefers explicit `relation_type: composition` + `composition` block.
- Legacy inference remains as fallback and emits warnings.
- Channel compatibility is checked against domain boundary exchange channels:
  - warning if either domain omits `boundary.exchange_channels`
  - error if both domains declare channels and relation channels are not present on both sides

## Future (PR15)

Potential follow-up: explicit claim↔relation binding semantics and bibliography normalization.
