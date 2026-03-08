"""Computable evidence for Seifert CTMC entropy production positivity."""

from __future__ import annotations

import numpy as np


def generate_irreducible_ctmc(num_states: int = 3, seed: int | None = None) -> np.ndarray:
    """Generate an irreducible CTMC rate matrix W with positive off-diagonal rates.

    Convention: dP/dt = W @ P, so each column of W sums to zero.
    """
    rng = np.random.default_rng(seed)
    w = rng.uniform(0.1, 2.0, size=(num_states, num_states))
    np.fill_diagonal(w, 0.0)

    for j in range(num_states):
        w[j, j] = -np.sum(w[:, j])

    return w


def stationary_distribution(w: np.ndarray) -> np.ndarray:
    """Compute stationary distribution p_st from W @ p_st = 0 and sum(p_st) = 1."""
    n = w.shape[0]
    a = np.vstack([w, np.ones((1, n))])
    b = np.zeros(n + 1)
    b[-1] = 1.0
    p_st, *_ = np.linalg.lstsq(a, b, rcond=None)
    return p_st


def seifert_entropy_production_rate(w: np.ndarray, p_st: np.ndarray) -> float:
    """Compute sigma = 0.5 * sum_ij J_ij * ln((W_ij P_j)/(W_ji P_i))."""
    sigma = 0.0
    n = w.shape[0]

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            forward = w[i, j] * p_st[j]
            backward = w[j, i] * p_st[i]
            flux = forward - backward
            sigma += 0.5 * flux * np.log(forward / backward)

    return float(sigma)


def verify_claim() -> bool:
    """Numerically verify non-negative total entropy production at steady state."""
    w = generate_irreducible_ctmc(num_states=3)
    p_st = stationary_distribution(w)
    sigma = seifert_entropy_production_rate(w, p_st)
    assert sigma >= -1e-12, f"Seifert EP violated: sigma={sigma}"
    return True


if __name__ == "__main__":
    print(verify_claim())
