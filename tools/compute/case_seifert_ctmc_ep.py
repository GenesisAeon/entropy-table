"""Computable evidence for Seifert CTMC entropy-production positivity."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class CaseResult:
    sigma: float
    passed: bool


def _random_irreducible_generator(seed: int, n_states: int) -> list[list[float]]:
    rng = random.Random(seed)
    rates = [[0.0 for _ in range(n_states)] for _ in range(n_states)]
    for i in range(n_states):
        for j in range(n_states):
            if i == j:
                continue
            rates[i][j] = rng.uniform(0.1, 2.0)

    for i in range(n_states):
        rates[i][i] = -sum(rates[i][j] for j in range(n_states) if j != i)
    return rates


def _solve_linear_system(a: list[list[float]], b: list[float]) -> list[float]:
    n = len(a)
    aug = [row[:] + [b_i] for row, b_i in zip(a, b)]

    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-15:
            raise ValueError("Singular system in stationary distribution solve")
        aug[col], aug[pivot] = aug[pivot], aug[col]

        div = aug[col][col]
        aug[col] = [value / div for value in aug[col]]

        for row in range(n):
            if row == col:
                continue
            factor = aug[row][col]
            aug[row] = [curr - factor * lead for curr, lead in zip(aug[row], aug[col])]

    return [aug[i][-1] for i in range(n)]


def _stationary_distribution(generator: list[list[float]]) -> list[float]:
    n_states = len(generator)
    system = [[generator[j][i] for j in range(n_states)] for i in range(n_states)]
    system[-1] = [1.0 for _ in range(n_states)]
    rhs = [0.0 for _ in range(n_states)]
    rhs[-1] = 1.0

    stationary = _solve_linear_system(system, rhs)
    stationary = [max(0.0, value) for value in stationary]
    total = sum(stationary)
    if total <= 0.0:
        raise ValueError("Invalid stationary distribution normalization")
    return [value / total for value in stationary]


def _seifert_entropy_production(generator: list[list[float]], stationary: list[float]) -> float:
    n_states = len(generator)
    sigma = 0.0
    for i in range(n_states):
        for j in range(n_states):
            if i == j:
                continue
            forward = generator[i][j] * stationary[j]
            backward = generator[j][i] * stationary[i]
            current = forward - backward
            sigma += current * math.log(forward / backward)
    return 0.5 * float(sigma)


def _run_single(seed: int) -> CaseResult:
    generator = _random_irreducible_generator(seed=seed, n_states=3)
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
