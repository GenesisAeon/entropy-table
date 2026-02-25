from __future__ import annotations

from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from metrics import compute_metrics
from common import domain_files, load_yaml, relation_files


def load_atlas_data() -> tuple[list[dict], list[dict]]:
    domains = sorted([load_yaml(path) for path in domain_files()], key=lambda d: d.get("id", ""))
    relations = sorted([load_yaml(path) for path in relation_files()], key=lambda r: r.get("id", ""))
    return domains, relations


def test_compute_metrics_returns_dict() -> None:
    domains, relations = load_atlas_data()
    result = compute_metrics(domains, relations)
    assert isinstance(result, dict)
    assert "domains" in result


def test_overdamped_domain_has_counts() -> None:
    domains, relations = load_atlas_data()
    result = compute_metrics(domains, relations)
    overdamped = result["domains"]["overdamped-langevin-st"]
    assert overdamped["hard_test_count"] >= 1
    assert overdamped["citation_count"] >= 1
