from __future__ import annotations

from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from compute.ctmc_ep import schnakenberg_ep_rate


def test_ctmc_detailed_balance_has_zero_ep() -> None:
    p = [0.5, 0.5]
    W = [[-1.0, 1.0], [1.0, -1.0]]
    sigma = schnakenberg_ep_rate(p, W)
    assert sigma == 0.0


def test_ctmc_cycle_ness_has_positive_ep() -> None:
    p = [1 / 3, 1 / 3, 1 / 3]
    W = [
        [-3.0, 2.0, 1.0],
        [1.0, -3.0, 2.0],
        [2.0, 1.0, -3.0],
    ]
    sigma = schnakenberg_ep_rate(p, W)
    assert sigma > 0.0
