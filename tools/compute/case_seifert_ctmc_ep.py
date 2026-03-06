from __future__ import annotations

import numpy as np


def _build_random_generator() -> np.ndarray:
    rng = np.random.default_rng(seed=202503)
    rates = rng.uniform(0.2, 1.4, size=(3, 3))
    np.fill_diagonal(rates, 0.0)
    return rates


def _generator_from_rates(rates: np.ndarray) -> np.ndarray:
    q = rates.copy()
    row_sums = np.sum(q, axis=1)
    np.fill_diagonal(q, -row_sums)
    return q


def _steady_state(q: np.ndarray) -> np.ndarray:
    evals, evecs = np.linalg.eig(q.T)
    idx = int(np.argmin(np.abs(evals)))
    vec = np.real(evecs[:, idx])
    vec = np.maximum(vec, 0.0)
    if float(np.sum(vec)) <= 0.0:
        vec = np.abs(np.real(evecs[:, idx]))
    pi = vec / np.sum(vec)
    return pi


def _sigma_rate(pi: np.ndarray, rates: np.ndarray) -> float:
    sigma = 0.0
    n = rates.shape[0]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            forward = pi[i] * rates[i, j]
            backward = pi[j] * rates[j, i]
            if forward <= 0.0 or backward <= 0.0:
                continue
            sigma += 0.5 * (forward - backward) * np.log(forward / backward)
    return float(sigma)


def verify_claim() -> bool:
    rates = _build_random_generator()
    q = _generator_from_rates(rates)
    pi = _steady_state(q)

    # Numerical consistency check for stationarity.
    residual = pi @ q
    if np.linalg.norm(residual, ord=1) > 1e-8:
        return False

    sigma = _sigma_rate(pi, rates)
    return bool(sigma >= -1e-12)
