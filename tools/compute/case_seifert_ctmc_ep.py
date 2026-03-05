"""Computable evidence for Seifert CTMC entropy-production positivity."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class CaseResult:
    sigma: float
    passed: bool


def _random_irreducible_generator(rng: random.Random, n_states: int) -> list[list[float]]:
    """Build W with off-diagonal positive rates and column sums equal to zero."""
    W = [[0.0 for _ in range(n_states)] for _ in range(n_states)]
    for i in range(n_states):
        for j in range(n_states):
            if i != j:
                W[i][j] = rng.uniform(0.1, 2.0)

    for j in range(n_states):
        outgoing = 0.0
        for i in range(n_states):
            if i != j:
                outgoing += W[i][j]
        W[j][j] = -outgoing
    return W


def _solve_linear_system(A: list[list[float]], b: list[float]) -> list[float]:
    n = len(A)
    aug = [row[:] + [rhs] for row, rhs in zip(A, b)]

    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < 1e-14:
            raise ValueError("Singular linear system while solving stationary distribution")
        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]

        pivot_val = aug[col][col]
        for j in range(col, n + 1):
            aug[col][j] /= pivot_val

        for r in range(n):
            if r == col:
                continue
            factor = aug[r][col]
            for j in range(col, n + 1):
                aug[r][j] -= factor * aug[col][j]

    return [aug[i][n] for i in range(n)]


def _stationary_distribution(generator: list[list[float]]) -> list[float]:
    n_states = len(generator)
    system = [row[:] for row in generator]
    system[-1] = [1.0] * n_states
    rhs = [0.0] * n_states
    rhs[-1] = 1.0

    stationary = _solve_linear_system(system, rhs)
    stationary = [max(0.0, x) for x in stationary]
    total = sum(stationary)
    if total <= 0.0:
        raise ValueError("Invalid stationary distribution normalization")
    return [x / total for x in stationary]


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
    return 0.5 * sigma


def _run_single(seed: int) -> CaseResult:
    rng = random.Random(seed)
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
