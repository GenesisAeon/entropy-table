from __future__ import annotations

from pathlib import Path
import textwrap

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from analyze_health import analyze_health, main


def _write_yaml(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).strip() + "\n", encoding="utf-8")


def test_analyze_health_detects_orphan_and_missing_regime_shift(tmp_path: Path) -> None:
    atlas_root = tmp_path / "atlas"

    _write_yaml(
        atlas_root / "domains" / "test" / "connected.yaml",
        """
        id: connected-domain
        assumptions: ["a1"]
        limitations: []
        """,
    )
    _write_yaml(
        atlas_root / "domains" / "test" / "orphan.yaml",
        """
        id: orphan-domain
        assumptions: ["a1"]
        limitations: ["l1"]
        """,
    )
    _write_yaml(
        atlas_root / "relations" / "test" / "edge.yaml",
        """
        id: relation-edge
        relation_type: coarse_graining
        source_domain_id: connected-domain
        target_domain_id: connected-domain
        """,
    )

    report = analyze_health(atlas_root)

    assert [row["id"] for row in report["orphaned_domains"]] == ["orphan-domain"]
    assert "orphan-domain" in [row["id"] for row in report["missing_regime_shifts"]]


def test_ci_check_fails_on_invalid_stable_claims(tmp_path: Path) -> None:
    atlas_root = tmp_path / "atlas"
    out_path = tmp_path / "outputs" / "atlas_health.md"

    _write_yaml(
        atlas_root / "domains" / "test" / "d1.yaml",
        """
        id: domain-a
        assumptions: []
        limitations: []
        """,
    )
    _write_yaml(
        atlas_root / "relations" / "test" / "r1.yaml",
        """
        id: relation-r1
        relation_type: regime_shift
        source_domain_id: domain-a
        target_domain_id: domain-a
        """,
    )
    _write_yaml(
        atlas_root / "claims" / "test" / "claim-bad-cases.yaml",
        """
        id: bad-cases
        status: stable
        evidence:
          citations: ["ref-a"]
          cases: []
        """,
    )
    _write_yaml(
        atlas_root / "claims" / "test" / "claim-bad-citations.yaml",
        """
        id: bad-citations
        status: stable
        evidence:
          citations: []
          cases: ["case-a"]
        """,
    )

    exit_code = main(["--atlas-root", str(atlas_root), "--out", str(out_path), "--ci-check"])

    assert out_path.exists()
    assert exit_code == 1
