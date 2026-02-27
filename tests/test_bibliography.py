from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def run_validate_bibliography(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/validate_bibliography.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


@pytest.fixture
def atlas_root(tmp_path: Path) -> Path:
    atlas = tmp_path / "atlas"
    (atlas / "domains" / "01_physics").mkdir(parents=True)
    (atlas / "relations").mkdir()
    (atlas / "claims").mkdir()
    (atlas / "bibliography").mkdir()

    refs = {
        "known-citation": {
            "type": "article",
            "title": "Known citation",
            "authors": ["Example Author"],
            "year": 2024,
            "doi": "10.0000/known",
        }
    }
    (atlas / "bibliography" / "refs.yaml").write_text(yaml.safe_dump(refs, sort_keys=True), encoding="utf-8")
    return atlas


def _write_domain(path: Path, status: str, citations: list[str]) -> None:
    payload = {
        "id": "test-domain",
        "status": status,
        "entropy_definition": {
            "assumptions": [
                {
                    "id": "a1",
                    "statement": "placeholder",
                    "citations": citations,
                }
            ]
        },
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_draft_with_unknown_citation_warns_only(atlas_root: Path) -> None:
    _write_domain(
        atlas_root / "domains" / "01_physics" / "draft-domain.yaml",
        status="draft",
        citations=["missing-citation"],
    )

    result = run_validate_bibliography("--atlas-root", str(atlas_root), "--refs", str(atlas_root / "bibliography" / "refs.yaml"))
    assert result.returncode == 0
    assert "WARNING" in result.stdout
    assert "missing-citation" in result.stdout


def test_stable_with_unknown_citation_fails(atlas_root: Path) -> None:
    _write_domain(
        atlas_root / "domains" / "01_physics" / "stable-domain.yaml",
        status="stable",
        citations=["missing-citation"],
    )

    result = run_validate_bibliography("--atlas-root", str(atlas_root), "--refs", str(atlas_root / "bibliography" / "refs.yaml"))
    assert result.returncode != 0
    assert "failed" in result.stdout.lower()
    assert "missing-citation" in result.stdout
