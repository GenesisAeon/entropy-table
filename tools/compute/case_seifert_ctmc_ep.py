"""Computable evidence for Seifert CTMC entropy production non-negativity."""

from __future__ import annotations

import numpy as np


def _random_generator(n: int = 3, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    rates = rng.uniform(0.05, 2.0, size=(n, n))
    np.fill_diagonal(rates, 0.0)
    generator = rates.copy()
    np.fill_diagonal(generator, -generator.sum(axis=1))
    return generator


def _steady_state(generator: np.ndarray) -> np.ndarray:
    n = generator.shape[0]
    a = generator.T.copy()
    a[-1, :] = 1.0
    b = np.zeros(n)
    b[-1] = 1.0
    pi = np.linalg.solve(a, b)
    return np.clip(pi, 0.0, None) / np.clip(pi, 0.0, None).sum()


def _sigma_seifert(generator: np.ndarray, pi: np.ndarray, eps: float = 1e-15) -> float:
    n = generator.shape[0]
    sigma = 0.0
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            forward = float(pi[i] * generator[i, j])
            backward = float(pi[j] * generator[j, i])
            sigma += 0.5 * (forward - backward) * np.log((forward + eps) / (backward + eps))
    return float(sigma)


def verify_claim() -> bool:
    generator = _random_generator(n=3, seed=11)
    pi = _steady_state(generator)
    sigma = _sigma_seifert(generator, pi)
    return sigma >= -1e-12
