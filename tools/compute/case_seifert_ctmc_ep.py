from __future__ import annotations

import numpy as np


def generate_random_ctmc_generator(n_states: int = 3, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    rates = rng.uniform(0.1, 2.0, size=(n_states, n_states))
    np.fill_diagonal(rates, 0.0)
    generator = rates.copy()
    np.fill_diagonal(generator, -generator.sum(axis=1))
    return generator


def steady_state_distribution(generator: np.ndarray) -> np.ndarray:
    n_states = generator.shape[0]
    a = generator.T.copy()
    a[-1, :] = 1.0
    b = np.zeros(n_states)
    b[-1] = 1.0
    pi = np.linalg.solve(a, b)
    return pi


def seifert_entropy_production_rate(generator: np.ndarray, pi: np.ndarray, eps: float = 1e-15) -> float:
    sigma = 0.0
    n_states = generator.shape[0]
    for i in range(n_states):
        for j in range(i + 1, n_states):
            forward_flux = pi[i] * generator[i, j]
            backward_flux = pi[j] * generator[j, i]
            current = forward_flux - backward_flux
            ratio = (forward_flux + eps) / (backward_flux + eps)
            sigma += current * np.log(ratio)
    return float(sigma)


def verify_claim() -> bool:
    generator = generate_random_ctmc_generator(n_states=3, seed=42)
    pi = steady_state_distribution(generator)
    sigma = seifert_entropy_production_rate(generator, pi)
    assert sigma >= -1e-12
    return True


if __name__ == "__main__":
    print(verify_claim())
