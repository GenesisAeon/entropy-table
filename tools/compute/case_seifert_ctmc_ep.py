"""Computable evidence for Seifert CTMC entropy-production positivity."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CaseResult:
    sigma: float
    passed: bool


def _random_irreducible_generator(rng: np.random.Generator, n_states: int) -> np.ndarray:
    rates = rng.uniform(0.1, 2.0, size=(n_states, n_states))
    np.fill_diagonal(rates, 0.0)
    generator = rates.copy()
    np.fill_diagonal(generator, -np.sum(rates, axis=1))
    return generator


def _stationary_distribution(generator: np.ndarray) -> np.ndarray:
    n_states = generator.shape[0]
    system = generator.T.copy()
    system[-1, :] = 1.0
    rhs = np.zeros(n_states)
    rhs[-1] = 1.0
    stationary = np.linalg.solve(system, rhs)
    stationary = np.clip(stationary, 0.0, None)
    stationary = stationary / stationary.sum()
    return stationary


def _seifert_entropy_production(generator: np.ndarray, stationary: np.ndarray) -> float:
    n_states = generator.shape[0]
    sigma = 0.0
    for i in range(n_states):
        for j in range(n_states):
            if i == j:
                continue
            forward = generator[i, j] * stationary[j]
            backward = generator[j, i] * stationary[i]
            current = forward - backward
            sigma += current * np.log(forward / backward)
    return 0.5 * float(sigma)


def _run_single(seed: int) -> CaseResult:
    rng = np.random.default_rng(seed)
    generator = _random_irreducible_generator(rng, n_states=3)
    stationary = _stationary_distribution(generator)
    sigma = _seifert_entropy_production(generator, stationary)
    return CaseResult(sigma=sigma, passed=sigma >= -1e-12)


def verify_claim() -> bool:
    """Return True when Seifert entropy production is nonnegative over deterministic trials."""
    seeds = [3, 11, 23, 37, 101]
    failures: list[str] = []
    for seed in seeds:
        result = _run_single(seed)
        if not result.passed:
            failures.append(f"seed={seed}, sigma={result.sigma:.18e}")

    if failures:
        raise AssertionError("Entropy production negativity detected: " + "; ".join(failures))
    return True


if __name__ == "__main__":
    ok = verify_claim()
    if not ok:
        raise SystemExit(1)
    print("case-seifert-ctmc-ep-positivity: PASS")
