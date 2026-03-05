"""Computable evidence for Seifert CTMC entropy-production positivity."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

try:  # optional dependency; validator environments may not have numpy installed
    import numpy as np
except Exception:  # pragma: no cover - fallback path exercised in subprocess validation
    np = None


@dataclass(frozen=True)
class CaseResult:
    sigma: float
    passed: bool


def _random_irreducible_generator(seed: int, n_states: int) -> list[list[float]]:
    rng = random.Random(seed)
    rates = [[rng.uniform(0.1, 2.0) for _ in range(n_states)] for _ in range(n_states)]
    for i in range(n_states):
        rates[i][i] = 0.0
    generator = [row[:] for row in rates]
    for i in range(n_states):
        generator[i][i] = -sum(rates[i][j] for j in range(n_states) if j != i)
    return generator


def _solve_linear(system: list[list[float]], rhs: list[float]) -> list[float]:
    n = len(rhs)
    a = [row[:] + [rhs_i] for row, rhs_i in zip(system, rhs)]
    for i in range(n):
        pivot = max(range(i, n), key=lambda r: abs(a[r][i]))
        if abs(a[pivot][i]) < 1e-15:
            raise ValueError("Singular system while solving for stationary distribution")
        a[i], a[pivot] = a[pivot], a[i]

        factor = a[i][i]
        for k in range(i, n + 1):
            a[i][k] /= factor

        for r in range(n):
            if r == i:
                continue
            f = a[r][i]
            for k in range(i, n + 1):
                a[r][k] -= f * a[i][k]

    return [a[i][n] for i in range(n)]


def _stationary_distribution(generator: list[list[float]]) -> list[float]:
    n_states = len(generator)

    if np is not None:
        system = np.array(generator, dtype=float).T
        system[-1, :] = 1.0
        rhs = np.zeros(n_states, dtype=float)
        rhs[-1] = 1.0
        stationary = np.linalg.solve(system, rhs)
        stationary = np.clip(stationary, 0.0, None)
        total = float(stationary.sum())
        return [float(x / total) for x in stationary]

    system = [[generator[row][col] for row in range(n_states)] for col in range(n_states)]
    system[-1] = [1.0] * n_states
    rhs = [0.0] * n_states
    rhs[-1] = 1.0
    stationary = _solve_linear(system, rhs)
    stationary = [max(0.0, x) for x in stationary]
    total = sum(stationary)
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
    return 0.5 * float(sigma)


def _run_single(seed: int) -> CaseResult:
    generator = _random_irreducible_generator(seed, n_states=3)
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
