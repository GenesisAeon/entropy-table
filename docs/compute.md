# Compute helpers (toy entropy-production calculators)

This repository includes small, auditable calculators for entropy production (EP). These are convenience tools for quick checks, not full simulation engines.

## Scope and limitations

- These are **toy** computations with simple discrete formulas.
- Inputs are assumed to already represent valid model quantities (e.g., rates/currents from another workflow).
- No inference, fitting, simulation, or solver is included.

## 1) CTMC Schnakenberg EP rate

Implemented in `tools/compute/ctmc_ep.py`.

Formula:

\[
\sigma = \frac{1}{2}\sum_{i\neq j} J_{ij}\,\ln\left(\frac{p_i W_{ij} + \varepsilon}{p_j W_{ji} + \varepsilon}\right),
\quad
J_{ij}=p_iW_{ij}-p_jW_{ji}
\]

Assumptions:

- `p` is nonnegative with positive sum (normalized internally).
- `W` is an `n x n` generator with nonnegative off-diagonals.
- Diagonals should satisfy `W[i][i] = -sum_{j!=i} W[i][j]`; small mismatch is corrected.

CLI:

```bash
python -m tools.compute.cli ctmc-ep --in ctmc_input.json
```

JSON input:

```json
{
  "p": [0.5, 0.5],
  "W": [[-1.0, 1.0], [1.0, -1.0]]
}
```

Output:

```text
sigma=0.0
detailed_balance=true
```

## 2) 1D diffusion EP rate (discretized)

Implemented in `tools/compute/diffusion_ep_1d.py`.

Formula:

\[
\sigma \approx \sum_k \frac{J_k^2}{\max(D_k,\varepsilon)\,\max(p_k,\varepsilon)}\,\Delta x
\]

Assumptions:

- `p[k] >= 0` and `J[k]` are sampled on the same 1D grid.
- `D` is either a scalar or an array matching `p`.
- `dx > 0`.

CLI:

```bash
python -m tools.compute.cli diffusion-ep-1d --in diffusion_input.json
```

JSON input:

```json
{
  "p": [1.0, 1.0, 1.0],
  "J": [1.0, 1.0, 1.0],
  "D": 1.0,
  "dx": 1.0
}
```

Output:

```text
sigma=3.0
```
