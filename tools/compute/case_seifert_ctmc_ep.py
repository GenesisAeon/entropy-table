from __future__ import annotations

import numpy as np


def _random_irreducible_generator(n: int, rng: np.random.Generator) -> np.ndarray:
    rates = rng.uniform(0.05, 1.0, size=(n, n))
    np.fill_diagonal(rates, 0.0)

    # Ensure irreducibility with a directed cycle.
    for i in range(n):
        j = (i + 1) % n
        rates[i, j] = max(rates[i, j], 0.1)

    generator = rates.copy()
    np.fill_diagonal(generator, -np.sum(rates, axis=1))
    return generator


def _stationary_distribution(generator: np.ndarray) -> np.ndarray:
    n = generator.shape[0]
    a = generator.T.copy()
    a[-1, :] = 1.0
    b = np.zeros(n)
    b[-1] = 1.0
    p_st = np.linalg.solve(a, b)
    return p_st


def verify_claim() -> bool:
    rng = np.random.default_rng(7)
    w = _random_irreducible_generator(3, rng)
    p_st = _stationary_distribution(w)

    sigma = 0.0
    for i in range(3):
        for j in range(3):
            if i == j:
                continue
            w_ij = w[i, j]
            w_ji = w[j, i]
            if w_ij <= 0.0 or w_ji <= 0.0:
                continue
            term_forward = w_ij * p_st[j]
            term_backward = w_ji * p_st[i]
            sigma += (term_forward - term_backward) * np.log(term_forward / term_backward)

    sigma *= 0.5
    return bool(sigma >= -1e-12)
