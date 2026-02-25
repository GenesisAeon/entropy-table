from __future__ import annotations

from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from compute.diffusion_ep_1d import diffusion_ep_rate_1d


def test_diffusion_zero_current_has_zero_ep() -> None:
    sigma = diffusion_ep_rate_1d(p=[1.0, 2.0], J=[0.0, 0.0], D=1.0, dx=0.5)
    assert sigma == 0.0


def test_diffusion_simple_positive_case() -> None:
    sigma = diffusion_ep_rate_1d(p=[1.0, 1.0, 1.0], J=[1.0, 1.0, 1.0], D=1.0, dx=1.0)
    assert sigma == 3.0
