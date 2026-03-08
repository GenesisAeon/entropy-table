"""Toy CTMC entropy-production helpers."""

from __future__ import annotations

import math


_DIAG_TOL = 1e-12


def _normalize_probabilities(p: list[float]) -> list[float]:
    if not p:
        raise ValueError("p must not be empty")

    values = [float(x) for x in p]
    if any(x < 0.0 for x in values):
        raise ValueError("p must contain nonnegative entries")

    total = sum(values)
    if total <= 0.0:
        raise ValueError("sum(p) must be > 0")

    return [x / total for x in values]


def _validated_generator(W: list[list[float]]) -> list[list[float]]:
    if not W:
        raise ValueError("W must not be empty")
    if not all(isinstance(row, list) for row in W):
        raise ValueError("W must be a 2D list")

    n = len(W)
    if any(len(row) != n for row in W):
        raise ValueError("W must be square")

    matrix = [[float(value) for value in row] for row in W]
    for i in range(n):
        off_diag_sum = 0.0
        for j in range(n):
            if i == j:
                continue
            if matrix[i][j] < 0.0:
                raise ValueError("off-diagonal rates must be nonnegative")
            off_diag_sum += matrix[i][j]

        expected_diag = -off_diag_sum
        if abs(matrix[i][i] - expected_diag) <= _DIAG_TOL:
            matrix[i][i] = expected_diag
            continue

        if abs(matrix[i][i]) <= _DIAG_TOL:
            matrix[i][i] = expected_diag
            continue

        raise ValueError(
            f"invalid generator diagonal at row {i}: expected {expected_diag}, got {matrix[i][i]}"
        )

    return matrix


def is_detailed_balance(p: list[float], W: list[list[float]], tol: float = 1e-10) -> bool:
    """Return True when p_i W_ij ~= p_j W_ji for all i != j."""
    probabilities = _normalize_probabilities(p)
    generator = _validated_generator(W)

    n = len(probabilities)
    if len(generator) != n:
        raise ValueError("p and W dimension mismatch")

    for i in range(n):
        for j in range(i + 1, n):
            forward = probabilities[i] * generator[i][j]
            backward = probabilities[j] * generator[j][i]
            if abs(forward - backward) > tol:
                return False
    return True


def schnakenberg_ep_rate(
    p: list[float],
    W: list[list[float]],
    *,
    eps: float = 1e-15,
) -> float:
    """Compute Schnakenberg entropy production rate for a CTMC state."""
    if eps <= 0.0:
        raise ValueError("eps must be > 0")

    probabilities = _normalize_probabilities(p)
    generator = _validated_generator(W)

    n = len(probabilities)
    if len(generator) != n:
        raise ValueError("p and W dimension mismatch")

    sigma = 0.0
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            forward = probabilities[i] * generator[i][j]
            backward = probabilities[j] * generator[j][i]
            current = forward - backward
            ratio = (forward + eps) / (backward + eps)
            sigma += current * math.log(ratio)

    sigma *= 0.5
    if sigma < 0.0 and abs(sigma) <= 1e-12:
        return 0.0
    return float(sigma)
