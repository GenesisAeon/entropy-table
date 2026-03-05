from __future__ import annotations

import numpy as np


def _build_random_irreducible_generator(n_states: int = 3) -> np.ndarray:
    rates = np.random.uniform(0.1, 1.0, size=(n_states, n_states))
    np.fill_diagonal(rates, 0.0)
    generator = rates.copy()
    generator[np.diag_indices(n_states)] = -np.sum(rates, axis=0)
    return generator


def _stationary_distribution(generator: np.ndarray) -> np.ndarray:
    eigenvalues, eigenvectors = np.linalg.eig(generator)
    idx = int(np.argmin(np.abs(eigenvalues)))
    stationary = np.real(eigenvectors[:, idx])
    if np.sum(stationary) < 0:
        stationary = -stationary
    stationary = np.abs(stationary)
    stationary = stationary / stationary.sum()
    return stationary


def verify_claim() -> bool:
    generator = _build_random_irreducible_generator()
    stationary = _stationary_distribution(generator)

    n_states = generator.shape[0]
    sigma = 0.0
    for i in range(n_states):
        for j in range(n_states):
            if i == j:
                continue
            forward = generator[i, j] * stationary[j]
            backward = generator[j, i] * stationary[i]
            sigma += (forward - backward) * np.log(forward / backward)

    sigma *= 0.5
    if sigma < -1e-12:
        raise AssertionError(f"Expected non-negative entropy production, got {sigma}")
    return True


if __name__ == "__main__":
    print("PASS" if verify_claim() else "FAIL")
