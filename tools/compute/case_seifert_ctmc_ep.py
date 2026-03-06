"""Computable case for Seifert CTMC entropy production positivity."""

from __future__ import annotations

import numpy as np


def generate_irreducible_rate_matrix(n_states: int = 3, seed: int | None = None) -> np.ndarray:
    """Generate an irreducible CTMC generator matrix W with positive off-diagonal rates."""
    rng = np.random.default_rng(seed)

    # Positive rates on all off-diagonal entries make the jump graph strongly connected.
    W = rng.uniform(0.1, 1.0, size=(n_states, n_states))
    np.fill_diagonal(W, 0.0)

    # Enforce probability conservation: columns sum to zero.
    for j in range(n_states):
        W[j, j] = -np.sum(W[:, j])

    return W


def stationary_distribution(W: np.ndarray) -> np.ndarray:
    """Compute stationary distribution P_st from W @ P_st = 0 with sum(P_st)=1."""
    n_states = W.shape[0]
    A = np.vstack([W, np.ones(n_states)])
    b = np.zeros(n_states + 1)
    b[-1] = 1.0

    p_st, *_ = np.linalg.lstsq(A, b, rcond=None)

    # Numerical cleanup to stay in simplex.
    p_st = np.clip(p_st, 0.0, None)
    p_st /= np.sum(p_st)

    return p_st


def entropy_production_rate(W: np.ndarray, p_st: np.ndarray) -> float:
    """Compute Seifert total entropy production rate.

    sigma = 0.5 * sum_{i,j} (W_ij P_j - W_ji P_i) * ln((W_ij P_j)/(W_ji P_i)).
    """
    n_states = W.shape[0]
    sigma = 0.0

    for i in range(n_states):
        for j in range(n_states):
            if i == j:
                continue
            flux_ij = W[i, j] * p_st[j]
            flux_ji = W[j, i] * p_st[i]
            sigma += 0.5 * (flux_ij - flux_ji) * np.log(flux_ij / flux_ji)

    return float(sigma)


def verify_claim() -> bool:
    """Verify non-negativity of entropy production for a random 3-state CTMC."""
    W = generate_irreducible_rate_matrix(n_states=3)
    p_st = stationary_distribution(W)
    sigma = entropy_production_rate(W, p_st)

    assert sigma >= -1e-12, f"Entropy production is negative: sigma={sigma}"
    return True


if __name__ == "__main__":
    ok = verify_claim()
    print(f"verify_claim: {ok}")
