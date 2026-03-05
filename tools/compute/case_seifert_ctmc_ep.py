from __future__ import annotations

import numpy as np


def _random_irreducible_rate_matrix(n: int = 3, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    rates = rng.uniform(0.1, 2.0, size=(n, n))
    np.fill_diagonal(rates, 0.0)
    np.fill_diagonal(rates, -rates.sum(axis=0))
    return rates


def _stationary_distribution(w: np.ndarray) -> np.ndarray:
    n = w.shape[0]
    a = w.copy()
    a[-1, :] = 1.0
    b = np.zeros(n)
    b[-1] = 1.0
    p_st = np.linalg.solve(a, b)
    return p_st


def _seifert_entropy_production_rate(w: np.ndarray, p_st: np.ndarray) -> float:
    sigma = 0.0
    n = w.shape[0]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            forward = w[i, j] * p_st[j]
            backward = w[j, i] * p_st[i]
            sigma += (forward - backward) * np.log(forward / backward)
    return 0.5 * sigma


def verify_claim() -> bool:
    w = _random_irreducible_rate_matrix(n=3)
    p_st = _stationary_distribution(w)
    sigma = _seifert_entropy_production_rate(w, p_st)
    return bool(sigma >= -1e-12)
