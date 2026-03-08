# Schema & Contract – How to Add a New Domain

This is the official hands-on tutorial. For the full RFC, see [schema_rfc_pr14.md](schema_rfc_pr14.md).

## 1. Scaffold a new domain

```bash
uv run entropy-table scaffold domain quantum-new-model
```

This creates `atlas/domains/quantum-new-model.yaml` pre-filled with all required fields.

## 2. Required fields

Every domain **must** define all of the following (enforced by `validate-all`):

| Field | Description |
|---|---|
| `entropy_quantity_kind` | Type of entropy (e.g. `gibbs`, `shannon`, `von_neumann`) |
| `epistemic_status` | `established`, `conjectured`, or `speculative` |
| `boundary` | System boundary definition |
| `exchange_channels` | List of energy/matter exchange channels |
| `entropy_accounting` | LaTeX expression for entropy production rate |
| `must_fail_tests` | ≥ 2 falsifiable failure conditions |
| `citations` | ≥ 1 citation with DOI and author |

## 3. Example: `must_fail_tests`

```yaml
must_fail_tests:
  - name: negative_entropy_production
    condition: sigma < 0
    expected: "Spohn inequality violation"
  - name: missing_exchange_channel
    condition: heat_bath not in exchange_channels
    expected: "Composition integrity failure"
```

## 4. Example: `entropy_accounting`

```yaml
entropy_accounting:
  latex: "\\dot{S} = \\sum_\\alpha J_\\alpha X_\\alpha"
  description: "Entropy production as sum of flux-force products"
```

## 5. Validate your new domain

```bash
uv run entropy-table validate-all
uv run entropy-table health --ci-check
```

## 6. Full schema reference

See `atlas/schema/domain.schema.json` for the complete JSON Schema with all fields, types, and constraints.
