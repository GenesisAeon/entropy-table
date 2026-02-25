# Compute Cases

Case specs are YAML files that let you run compute calculators from either inline JSON input or JSON files.

## Case format

```yaml
id: my-case-id
calculator: ctmc-ep # or diffusion-ep-1d
input:
  format: json-inline # or json-file
  data: {...} # for json-inline
  path: staging/cases/my-input.json # for json-file
expected: # optional
  sigma_min: 0.0
  sigma_max: 1.0
  sigma_close:
    value: 0.5
    tol: 1e-6
notes: optional text
citations: [optional, list, of, ids]
```

Notes:
- Case YAMLs are expected in `staging/cases/` during manual workflows.
- JSON inputs for `json-file` cases can also live in `staging/cases/`.
- In tests/CI, prefer temp paths instead of relying on `staging/` content.

## Example cases

### CTMC equilibrium case (sigma close to 0)

```yaml
id: ctmc-equilibrium
calculator: ctmc-ep
input:
  format: json-inline
  data:
    pi: [0.5, 0.5]
    rates:
      - [0.0, 1.0]
      - [1.0, 0.0]
expected:
  sigma_close:
    value: 0.0
    tol: 1e-12
notes: symmetric rates satisfy detailed balance
```

### Diffusion simple case (sigma close to known value)

```yaml
id: diffusion-simple
calculator: diffusion-ep-1d
input:
  format: json-file
  path: staging/cases/diffusion_simple.json
expected:
  sigma_close:
    value: 4.0
    tol: 1e-12
```

Where `staging/cases/diffusion_simple.json` could be:

```json
{"mobility": 2.0, "force": 2.0, "temperature": 2.0}
```

## Running tools

### Running a directory of cases

You can scan a directory (default: `staging/cases/`) and optionally combine with explicit `--case` arguments:

```bash
python -m tools.compute.case_runner --scan-dir staging/cases/
python -m tools.compute.report --scan-dir staging/cases/ --only-failures --out outputs/compute_report.md
```

`--scan-dir` and repeated `--case` values are unioned with deduplication by exact path.

Run the case runner:

```bash
python -m tools.compute.case_runner --case staging/cases/ctmc_equilibrium.yaml
```

Generate markdown report:

```bash
python -m tools.compute.report --case staging/cases/ctmc_equilibrium.yaml
```

The report is written to `outputs/compute_report.md`.
