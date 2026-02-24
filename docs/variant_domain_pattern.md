# Variant Domain Pattern for Regime Shifts

This repository uses a **relation-first pattern** for physics regime shifts (e.g., nonisothermal baths, multiplicative noise, active-noise forcing) while preserving schema compatibility.

## Core pattern

1. Keep a baseline domain as the canonical model contract (for example `overdamped-langevin-st`).
2. Encode assumption breaks as a relation in `atlas/relations/01_physics/`.
3. Put the failure mode in `relation.conditions` and enforce it with a structured `must_fail_tests` entry.
4. Use a separate variant domain only when the shift needs persistent semantic identity beyond one relation.

## Required relation fields for variants

- `relation_type`: prefer `regime_shift`.
- `conditions.text`: explain which baseline assumptions break.
- `conditions.params`: machine-readable toggles (for example `temperature_uniformity: false`).
- `expected_effect`: state directional bias (`decrease` for naive EP underestimation, or `context_dependent`).
- `must_fail_tests`: include at least one hard test proving that baseline formulas fail in the shifted regime.

## Minimal variant-domain rule

If a variant domain is needed, keep it intentionally small and reference the baseline domain for shared semantics. Most detail should remain in relations to avoid ontology duplication.

## Example in this repo

- Relation: `overdamped-nonisothermal-anomalous-ep`
- Baseline source: `overdamped-langevin-st`
- Assumption break: nonuniform `T(x)` / `gamma(x)` and multiplicative-noise convention sensitivity
- Failure contract: rejecting naive isothermal overdamped EP as complete in this regime (Celani et al., 2012)
