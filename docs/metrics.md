# Atlas Metrics

`tools/metrics.py` computes reproducible reporting metrics from existing atlas YAML fields.

## Purpose

These metrics are **operational heuristics** for comparison and review workflows. They are **not** universal physical truth claims.

## Computed per-domain metrics

- `hard_test_count` / `soft_test_count` from `must_fail_tests[].severity`
- `citation_count` from top-level `citations`
- `outgoing_relation_count` / `incoming_relation_count`
- `relation_type_counts` across incident relations
- `closure_risk` heuristic score and explanation:
  - `+2` if `boundary.closure_type == effectively_closed`
  - `+1` if `information` is in `boundary.exchange_channels`
  - `+1` if limitations count >= 2
  - `+1` if incident relation types include `regime_shift` or `coarse_graining`
- coverage flags:
  - `has_boundary`
  - `has_entropy_accounting`
  - `has_entropy_definition`
  - `has_operators`

## Usage

```bash
python tools/metrics.py
```

Outputs:

- `cache/metrics.json` (machine readable)
- `outputs/metrics.md` (human readable)

The tool optionally checks for `cache/index.json` and reports whether it was present in the markdown output.
