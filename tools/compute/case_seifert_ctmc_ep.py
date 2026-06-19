"""Computable evidence for Seifert CTMC entropy production positivity."""

from __future__ import annotations

import numpy as np


def generate_irreducible_rate_matrix(rng: np.random.Generator) -> np.ndarray:
    """Generate a random irreducible 3-state CTMC rate matrix W.

    Convention: W[i, j] is the rate from state j to state i.
    Diagonal entries satisfy W[j, j] = -sum_{i!=j} W[i, j].
    """
    n = 3
    # Positive off-diagonal rates in both directions ensure irreducibility.
    off_diag = rng.uniform(0.1, 2.0, size=(n, n))
    np.fill_diagonal(off_diag, 0.0)

    w = off_diag.copy()
    for j in range(n):
        w[j, j] = -np.sum(w[:, j])
    return w


def stationary_distribution(w: np.ndarray) -> np.ndarray:
    """Compute stationary distribution P_st from W P_st = 0 and sum(P_st)=1."""
    n = w.shape[0]
    a = w.copy()
    b = np.zeros(n)

    # Replace one equation with normalization constraint.
    a[-1, :] = 1.0
    b[-1] = 1.0

    p_st = np.linalg.solve(a, b)
    return p_st


def seifert_entropy_production_rate(w: np.ndarray, p_st: np.ndarray) -> float:
    """Compute sigma = 1/2 * sum_{i,j} J_{ij} * ln(F_{ij}/F_{ji})."""
    sigma = 0.0
    n = w.shape[0]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            forward = w[i, j] * p_st[j]
            backward = w[j, i] * p_st[i]
            current = forward - backward
            sigma += 0.5 * current * np.log(forward / backward)
    return float(sigma)


def verify_claim() -> bool:
    """Verify non-negativity of Seifert entropy production for a random 3-state CTMC."""
    rng = np.random.default_rng(12345)
    w = generate_irreducible_rate_matrix(rng)
    p_st = stationary_distribution(w)
    sigma = seifert_entropy_production_rate(w, p_st)

    assert sigma >= -1e-12, f"Entropy production must be non-negative, got {sigma}"
    return True


if __name__ == "__main__":
    verify_claim()
