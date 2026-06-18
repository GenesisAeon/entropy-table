#!/usr/bin/env python3
"""Computable case for Seifert CTMC entropy production positivity."""

from __future__ import annotations

import numpy as np


def generate_random_irreducible_rate_matrix(rng: np.random.Generator) -> np.ndarray:
    """Generate an irreducible 3-state CTMC rate matrix W with convention dP/dt = W P.

    Off-diagonal entries W_ij (i != j) are transition rates from state j to state i.
    """
    n_states = 3
    rates = rng.uniform(0.1, 1.0, size=(n_states, n_states))
    np.fill_diagonal(rates, 0.0)

    w = rates.copy()
    for j in range(n_states):
        w[j, j] = -np.sum(w[:, j])
    return w


def stationary_distribution(w: np.ndarray) -> np.ndarray:
    """Compute stationary distribution P_st satisfying W P_st = 0 and sum(P_st)=1."""
    n_states = w.shape[0]
    a = w.copy()
    a[-1, :] = 1.0
    b = np.zeros(n_states)
    b[-1] = 1.0
    p_st = np.linalg.solve(a, b)
    return p_st


def entropy_production_rate(w: np.ndarray, p_st: np.ndarray) -> float:
    """Compute Seifert total entropy production rate at steady state.

    sigma = 0.5 * sum_{i,j} (W_ij P_j - W_ji P_i) * ln(W_ij P_j / W_ji P_i)
    """
    sigma = 0.0
    n_states = w.shape[0]
    for i in range(n_states):
        for j in range(n_states):
            if i == j:
                continue
            forward = w[i, j] * p_st[j]
            backward = w[j, i] * p_st[i]
            sigma += (forward - backward) * np.log(forward / backward)
    return 0.5 * float(sigma)


def verify_claim() -> bool:
    """Verify non-negative entropy production for a random irreducible 3-state CTMC."""
    rng = np.random.default_rng(2025)
    w = generate_random_irreducible_rate_matrix(rng)
    p_st = stationary_distribution(w)
    sigma = entropy_production_rate(w, p_st)
    assert sigma >= -1e-12, f"Entropy production should be non-negative, got sigma={sigma}"
    return True


if __name__ == "__main__":
    if verify_claim():
        print("Seifert CTMC entropy production verification passed.")
