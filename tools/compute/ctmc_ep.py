from __future__ import annotations

import math


def _normalize_probabilities(p: list[float]) -> list[float]:
    if not p:
        raise ValueError("p must be a non-empty probability vector")
    if any(pi < 0 for pi in p):
        raise ValueError("p entries must be nonnegative")

    total = sum(p)
    if total <= 0:
        raise ValueError("sum(p) must be positive")

    return [pi / total for pi in p]


def _validate_and_reconstruct_generator(W: list[list[float]], n: int, tol: float = 1e-12) -> list[list[float]]:
    if len(W) != n or any(len(row) != n for row in W):
        raise ValueError("W must be an n x n matrix matching len(p)")

    reconstructed = [row[:] for row in W]
    for i in range(n):
        off_diag_sum = 0.0
        for j in range(n):
            value = reconstructed[i][j]
            if i == j:
                continue
            if value < 0:
                raise ValueError("off-diagonal generator entries must be nonnegative")
            off_diag_sum += value

        expected_diag = -off_diag_sum
        diag = reconstructed[i][i]
        if abs(diag - expected_diag) <= tol:
            reconstructed[i][i] = expected_diag
            continue

        if abs(diag) <= tol:
            reconstructed[i][i] = expected_diag
            continue

        raise ValueError(f"invalid diagonal entry W[{i}][{i}]: expected {expected_diag}, got {diag}")

    return reconstructed


def schnakenberg_ep_rate(p: list[float], W: list[list[float]], *, eps: float = 1e-15) -> float:
    """Compute Schnakenberg entropy production rate for a finite CTMC."""
    if eps <= 0:
        raise ValueError("eps must be positive")

    p_norm = _normalize_probabilities(p)
    W_gen = _validate_and_reconstruct_generator(W, len(p_norm))

    sigma = 0.0
    n = len(p_norm)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            forward = p_norm[i] * W_gen[i][j]
            backward = p_norm[j] * W_gen[j][i]
            current = forward - backward
            sigma += 0.5 * current * math.log((forward + eps) / (backward + eps))

    if sigma < 0 and sigma > -1e-12:
        return 0.0
    return sigma


def is_detailed_balance(p: list[float], W: list[list[float]], tol: float = 1e-10) -> bool:
    if tol < 0:
        raise ValueError("tol must be nonnegative")

    p_norm = _normalize_probabilities(p)
    W_gen = _validate_and_reconstruct_generator(W, len(p_norm))

    n = len(p_norm)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if abs(p_norm[i] * W_gen[i][j] - p_norm[j] * W_gen[j][i]) > tol:
                return False
    return True
