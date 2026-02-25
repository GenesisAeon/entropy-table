# Compute helpers (toy calculators)

This repository includes lightweight helpers for entropy-production (EP) calculations.
They are intentionally minimal and are not full simulators.

## What is implemented

- **CTMC Schnakenberg EP rate** from a probability vector `p` and generator matrix `W`.
- **1D diffusion EP rate** from discretized arrays `p`, `J`, `D`, and spacing `dx`.

Code lives in:

- `tools/compute/ctmc_ep.py`
- `tools/compute/diffusion_ep_1d.py`
- `tools/compute/cli.py`

## Assumptions and limitations

- These are **toy calculators** for quick checks.
- Inputs are treated as already-discretized quantities.
- No dynamics integration is performed.
- Small positive `eps` is used to avoid `log(0)` and division-by-zero singularities.

## CTMC calculator

### Formula

For `i != j`, define current:

`J_ij = p_i W_ij - p_j W_ji`

Then:

`sigma = 0.5 * sum_{i!=j} J_ij * ln((p_i W_ij + eps)/(p_j W_ji + eps))`

### Input JSON

```json
{
  "p": [0.5, 0.5],
  "W": [[-1.0, 1.0], [1.0, -1.0]]
}
```

### CLI

```bash
python -m tools.compute.cli ctmc-ep --in ctmc.json
```

Output:

```text
sigma=<value>
detailed_balance=<true|false>
```

## Diffusion 1D calculator

### Formula

Discrete approximation of:

`sigma = ∫ J(x)^2 / (D(x) p(x)) dx`

using:

`sigma ≈ sum_k (J[k]^2)/(max(D[k],eps)*max(p[k],eps)) * dx`

### Input JSON

```json
{
  "p": [1.0, 1.0, 1.0],
  "J": [1.0, 1.0, 1.0],
  "D": 1.0,
  "dx": 1.0
}
```

`D` may be a scalar or an array of the same length as `p`.

### CLI

```bash
python -m tools.compute.cli diffusion-ep-1d --in diffusion.json
```

Output:

```text
sigma=<value>
```
