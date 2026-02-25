from __future__ import annotations


def _validate_density_and_current(p: list[float], J: list[float]) -> None:
    if not p or not J:
        raise ValueError("p and J must be non-empty")
    if len(p) != len(J):
        raise ValueError("p and J must have the same length")
    if any(pk < 0 for pk in p):
        raise ValueError("p entries must be nonnegative")


def _resolve_diffusion(D: float | list[float], n: int) -> list[float]:
    if isinstance(D, (int, float)):
        if D < 0:
            raise ValueError("D must be nonnegative")
        return [float(D)] * n

    if len(D) != n:
        raise ValueError("D must be a scalar or an array with len(D) == len(p)")
    if any(dk < 0 for dk in D):
        raise ValueError("D entries must be nonnegative")
    return [float(dk) for dk in D]


def diffusion_ep_rate_1d(
    p: list[float],
    J: list[float],
    D: float | list[float],
    dx: float,
    *,
    eps: float = 1e-15,
) -> float:
    """Compute a 1D discrete entropy production approximation sigma = sum J^2/(Dp)*dx."""
    if dx <= 0:
        raise ValueError("dx must be positive")
    if eps <= 0:
        raise ValueError("eps must be positive")

    _validate_density_and_current(p, J)
    D_vals = _resolve_diffusion(D, len(p))

    sigma = 0.0
    for pk, jk, dk in zip(p, J, D_vals):
        sigma += (jk * jk) / (max(dk, eps) * max(pk, eps)) * dx

    if sigma < 0 and sigma > -1e-12:
        return 0.0
    return sigma
