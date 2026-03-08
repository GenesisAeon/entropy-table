"""Toy 1D diffusion entropy-production helper."""

from __future__ import annotations


def diffusion_ep_rate_1d(
    p: list[float],
    J: list[float],
    D: float | list[float],
    dx: float,
    *,
    eps: float = 1e-15,
) -> float:
    """Compute a discrete approximation of sigma = ∫ J^2/(D p) dx."""
    if eps <= 0.0:
        raise ValueError("eps must be > 0")
    if dx <= 0.0:
        raise ValueError("dx must be > 0")
    if len(p) == 0:
        raise ValueError("p must not be empty")
    if len(J) != len(p):
        raise ValueError("J length must match p length")

    p_values = [float(v) for v in p]
    J_values = [float(v) for v in J]
    if any(v < 0.0 for v in p_values):
        raise ValueError("p must contain nonnegative entries")

    if isinstance(D, list):
        if len(D) != len(p):
            raise ValueError("D length must match p length")
        D_values = [float(v) for v in D]
    else:
        D_values = [float(D)] * len(p)

    if any(v < 0.0 for v in D_values):
        raise ValueError("D must be nonnegative")

    sigma = 0.0
    for pk, jk, dk in zip(p_values, J_values, D_values, strict=True):
        denom = max(dk, eps) * max(pk, eps)
        sigma += (jk * jk) / denom
    sigma *= dx

    if sigma < 0.0 and abs(sigma) <= 1e-12:
        return 0.0
    return float(sigma)
