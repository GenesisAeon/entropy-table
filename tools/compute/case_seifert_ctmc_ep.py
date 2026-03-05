from __future__ import annotations

import numpy as np


def _random_irreducible_rate_matrix(rng: np.random.Generator, n: int = 3) -> np.ndarray:
    rates = rng.uniform(0.1, 2.0, size=(n, n))
    np.fill_diagonal(rates, 0.0)
    for col in range(n):
        rates[:, col] += 0.1
        rates[col, col] = 0.0
    diag = -np.sum(rates, axis=0)
    return rates + np.diag(diag)


def _stationary_distribution(rate_matrix: np.ndarray) -> np.ndarray:
    n = rate_matrix.shape[0]
    a = rate_matrix.copy()
    a[-1, :] = 1.0
    b = np.zeros(n)
    b[-1] = 1.0
    return np.linalg.solve(a, b)


def verify_claim() -> bool:
    rng = np.random.default_rng(0)
    w = _random_irreducible_rate_matrix(rng, n=3)
    p_st = _stationary_distribution(w)

    sigma = 0.0
    for i in range(3):
        for j in range(3):
            if i == j:
                continue
            forward = w[i, j] * p_st[j]
            backward = w[j, i] * p_st[i]
            sigma += 0.5 * (forward - backward) * np.log(forward / backward)

    return bool(sigma >= -1e-12)
