from __future__ import annotations

import numpy as np


def random_rate_matrix(n: int = 3, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    off_diag = rng.uniform(0.1, 2.0, size=(n, n))
    np.fill_diagonal(off_diag, 0.0)
    rates = off_diag.copy()
    np.fill_diagonal(rates, -rates.sum(axis=1))
    return rates


def steady_state_distribution(rates: np.ndarray) -> np.ndarray:
    n = rates.shape[0]
    a = rates.T.copy()
    a[-1, :] = 1.0
    b = np.zeros(n)
    b[-1] = 1.0
    p = np.linalg.solve(a, b)
    return p


def seifert_entropy_production_rate(p: np.ndarray, rates: np.ndarray) -> float:
    sigma = 0.0
    n = rates.shape[0]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if rates[i, j] <= 0.0 or rates[j, i] <= 0.0:
                continue
            flux_ij = p[i] * rates[i, j]
            flux_ji = p[j] * rates[j, i]
            sigma += 0.5 * (flux_ij - flux_ji) * np.log(flux_ij / flux_ji)
    return float(sigma)


def verify_claim() -> bool:
    rates = random_rate_matrix()
    p = steady_state_distribution(rates)
    sigma = seifert_entropy_production_rate(p, rates)
    assert sigma >= -1e-12
    return True


if __name__ == "__main__":
    verify_claim()
