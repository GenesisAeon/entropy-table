"""Computable evidence for Seifert CTMC entropy-production positivity."""

from __future__ import annotations

import numpy as np


def generate_random_irreducible_ctmc(n_states: int = 3, seed: int = 7) -> np.ndarray:
    """Generate an irreducible CTMC generator W with convention W_ij: j -> i."""
    if n_states != 3:
        raise ValueError("This evidence case is defined for a 3-state CTMC.")

    rng = np.random.default_rng(seed)
    W = rng.uniform(0.1, 1.0, size=(n_states, n_states))
    np.fill_diagonal(W, 0.0)

    # Enforce generator condition with column-sum convention: sum_i W_ij = 0.
    for j in range(n_states):
        W[j, j] = -np.sum(W[:, j])

    return W


def stationary_distribution(W: np.ndarray) -> np.ndarray:
    """Solve W @ P_st = 0 with normalization sum(P_st)=1."""
    n_states = W.shape[0]
    A = W.copy()
    b = np.zeros(n_states)

    # Replace one equation with normalization to get a full-rank linear system.
    A[-1, :] = 1.0
    b[-1] = 1.0

    p_st = np.linalg.solve(A, b)
    return p_st


def seifert_entropy_production_rate(W: np.ndarray, p_st: np.ndarray) -> float:
    """Compute Seifert entropy production rate.

    sigma = 0.5 * sum_{i,j} (W_ij P_j - W_ji P_i) * ln(W_ij P_j / W_ji P_i)
    """
    n_states = W.shape[0]
    sigma = 0.0

    for i in range(n_states):
        for j in range(n_states):
            if i == j:
                continue
            forward = W[i, j] * p_st[j]
            backward = W[j, i] * p_st[i]
            current = forward - backward
            sigma += current * np.log(forward / backward)

    return 0.5 * float(sigma)


def verify_claim() -> bool:
    """Verify non-negative steady-state entropy production for the generated CTMC."""
    W = generate_random_irreducible_ctmc()
    p_st = stationary_distribution(W)
    sigma = seifert_entropy_production_rate(W, p_st)
    assert sigma >= -1e-12, f"Entropy production should be nonnegative, got {sigma}"
    return True


if __name__ == "__main__":
    ok = verify_claim()
    print({"verified": ok})
