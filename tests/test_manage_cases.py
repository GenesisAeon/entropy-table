"""Tests for tools/manage_cases.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import manage_cases


# ── helpers ──────────────────────────────────────────────────────────────────


def _write_claim(path: Path, domain_ref: str = "ctmc-schnakenberg", case_ids: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {
        "id": path.stem,
        "title": "Test claim",
        "domain_ref": domain_ref,
        "claim_kind": "theorem",
        "statement": {"text": "Test statement."},
        "assumptions": ["Test assumption."],
        "falsification": {"must_fail_refs": []},
        "evidence": {
            "citations": [],
            "provenance": "test",
        },
        "status": "draft",
    }
    if case_ids is not None:
        data["evidence"]["cases"] = case_ids
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _write_case(path: Path, case_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "id": case_id,
        "calculator": "ctmc-ep",
        "input": {"format": "json-inline", "data": {"rates": [[0.0, 1.0], [1.0, 0.0]], "pi": [0.5, 0.5]}},
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


# ── create: happy paths ───────────────────────────────────────────────────────


def test_create_with_domain_places_file_correctly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(manage_cases, "CASES_DIR", tmp_path / "cases")
    monkeypatch.setattr(manage_cases, "TEMPLATES_DIR", ROOT / "templates")

    ret = manage_cases.main(["create", "ctmc-3cycle-v01", "--domain", "ctmc-schnakenberg"])

    assert ret == 0
    out_path = tmp_path / "cases" / "01_physics" / "ctmc-schnakenberg" / "ctmc-3cycle-v01.yaml"
    assert out_path.exists()
    data = yaml.safe_load(out_path.read_text())
    assert data["id"] == "ctmc-3cycle-v01"
    assert data["calculator"] == "ctmc-ep"


def test_create_with_claim_file_infers_domain_and_category(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(manage_cases, "CASES_DIR", tmp_path / "cases")
    monkeypatch.setattr(manage_cases, "TEMPLATES_DIR", ROOT / "templates")
    monkeypatch.setattr(manage_cases, "CLAIMS_DIR", tmp_path / "claims")

    claim_path = tmp_path / "claims" / "01_physics" / "ctmc-schnakenberg" / "claim-foo.yaml"
    _write_claim(claim_path, domain_ref="ctmc-schnakenberg")

    ret = manage_cases.main(["create", "ctmc-schnakenberg-baseline-v01", "--claim-file", str(claim_path)])

    assert ret == 0
    out_path = tmp_path / "cases" / "01_physics" / "ctmc-schnakenberg" / "ctmc-schnakenberg-baseline-v01.yaml"
    assert out_path.exists()
    data = yaml.safe_load(out_path.read_text())
    assert data["id"] == "ctmc-schnakenberg-baseline-v01"


def test_create_custom_calculator(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(manage_cases, "CASES_DIR", tmp_path / "cases")
    monkeypatch.setattr(manage_cases, "TEMPLATES_DIR", ROOT / "templates")

    ret = manage_cases.main([
        "create", "diffusion-baseline-v01",
        "--domain", "overdamped-langevin-st",
        "--calculator", "diffusion-ep-1d",
    ])

    assert ret == 0
    out_path = tmp_path / "cases" / "01_physics" / "overdamped-langevin-st" / "diffusion-baseline-v01.yaml"
    data = yaml.safe_load(out_path.read_text())
    assert data["calculator"] == "diffusion-ep-1d"


def test_create_custom_category(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(manage_cases, "CASES_DIR", tmp_path / "cases")
    monkeypatch.setattr(manage_cases, "TEMPLATES_DIR", ROOT / "templates")

    ret = manage_cases.main([
        "create", "ctmc-golden-v01",
        "--domain", "ctmc-schnakenberg",
        "--category", "00_golden",
    ])

    assert ret == 0
    out_path = tmp_path / "cases" / "00_golden" / "ctmc-schnakenberg" / "ctmc-golden-v01.yaml"
    assert out_path.exists()


# ── create: error paths ───────────────────────────────────────────────────────


def test_create_rejects_invalid_case_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(manage_cases, "CASES_DIR", tmp_path / "cases")
    monkeypatch.setattr(manage_cases, "TEMPLATES_DIR", ROOT / "templates")

    ret = manage_cases.main(["create", "Bad/Case/ID", "--domain", "ctmc-schnakenberg"])

    assert ret != 0


def test_create_rejects_uppercase_in_case_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(manage_cases, "CASES_DIR", tmp_path / "cases")
    monkeypatch.setattr(manage_cases, "TEMPLATES_DIR", ROOT / "templates")

    ret = manage_cases.main(["create", "CTMC-Case-V01", "--domain", "ctmc-schnakenberg"])

    assert ret != 0


def test_create_rejects_duplicate_case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(manage_cases, "CASES_DIR", tmp_path / "cases")
    monkeypatch.setattr(manage_cases, "TEMPLATES_DIR", ROOT / "templates")

    manage_cases.main(["create", "ctmc-dup-v01", "--domain", "ctmc-schnakenberg"])
    ret = manage_cases.main(["create", "ctmc-dup-v01", "--domain", "ctmc-schnakenberg"])

    assert ret != 0


def test_create_requires_domain_without_claim_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(manage_cases, "CASES_DIR", tmp_path / "cases")
    monkeypatch.setattr(manage_cases, "TEMPLATES_DIR", ROOT / "templates")

    ret = manage_cases.main(["create", "ctmc-no-domain-v01"])

    assert ret != 0


def test_create_rejects_missing_claim_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(manage_cases, "CASES_DIR", tmp_path / "cases")
    monkeypatch.setattr(manage_cases, "TEMPLATES_DIR", ROOT / "templates")

    ret = manage_cases.main(["create", "ctmc-x-v01", "--claim-file", str(tmp_path / "nonexistent.yaml")])

    assert ret != 0


# ── validate: happy path ──────────────────────────────────────────────────────


def test_validate_passes_with_no_claims_and_no_cases(tmp_path: Path) -> None:
    claims_root = tmp_path / "claims"
    cases_root = tmp_path / "cases"
    claims_root.mkdir()
    cases_root.mkdir()

    ret = manage_cases.main([
        "validate",
        "--claims-root", str(claims_root),
        "--cases-root", str(cases_root),
    ])

    assert ret == 0


def test_validate_passes_with_matching_claim_and_case(tmp_path: Path) -> None:
    claims_root = tmp_path / "claims"
    cases_root = tmp_path / "cases"

    _write_claim(claims_root / "01_physics" / "ctmc-schnakenberg" / "claim-foo.yaml", case_ids=["ctmc-3cycle-v01"])
    _write_case(cases_root / "01_physics" / "ctmc-schnakenberg" / "ctmc-3cycle-v01.yaml", "ctmc-3cycle-v01")

    ret = manage_cases.main([
        "validate",
        "--claims-root", str(claims_root),
        "--cases-root", str(cases_root),
    ])

    assert ret == 0


# ── validate: dangling references ────────────────────────────────────────────


def test_validate_fails_on_dangling_claim_reference(tmp_path: Path) -> None:
    claims_root = tmp_path / "claims"
    cases_root = tmp_path / "cases"
    cases_root.mkdir(parents=True)

    _write_claim(
        claims_root / "01_physics" / "ctmc-schnakenberg" / "claim-foo.yaml",
        case_ids=["ctmc-missing-case-v01"],
    )

    ret = manage_cases.main([
        "validate",
        "--claims-root", str(claims_root),
        "--cases-root", str(cases_root),
    ])

    assert ret != 0


def test_validate_reports_all_dangling_references(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    claims_root = tmp_path / "claims"
    cases_root = tmp_path / "cases"
    cases_root.mkdir(parents=True)

    _write_claim(
        claims_root / "01_physics" / "ctmc-schnakenberg" / "claim-foo.yaml",
        case_ids=["ctmc-missing-v01", "ctmc-also-missing-v02"],
    )

    manage_cases.main([
        "validate",
        "--claims-root", str(claims_root),
        "--cases-root", str(cases_root),
    ])

    captured = capsys.readouterr()
    assert "ctmc-missing-v01" in captured.out
    assert "ctmc-also-missing-v02" in captured.out
    assert "DANGLING" in captured.out


# ── validate: orphaned cases ─────────────────────────────────────────────────


def test_validate_passes_on_orphaned_case_without_strict(tmp_path: Path) -> None:
    claims_root = tmp_path / "claims"
    cases_root = tmp_path / "cases"
    claims_root.mkdir(parents=True)

    # Case file with no claim referencing it
    _write_case(cases_root / "01_physics" / "ctmc-schnakenberg" / "ctmc-orphan-v01.yaml", "ctmc-orphan-v01")

    ret = manage_cases.main([
        "validate",
        "--claims-root", str(claims_root),
        "--cases-root", str(cases_root),
    ])

    assert ret == 0


def test_validate_fails_on_orphaned_case_with_strict(tmp_path: Path) -> None:
    claims_root = tmp_path / "claims"
    cases_root = tmp_path / "cases"
    claims_root.mkdir(parents=True)

    _write_case(cases_root / "01_physics" / "ctmc-schnakenberg" / "ctmc-orphan-v01.yaml", "ctmc-orphan-v01")

    ret = manage_cases.main([
        "validate",
        "--claims-root", str(claims_root),
        "--cases-root", str(cases_root),
        "--strict",
    ])

    assert ret != 0


def test_validate_reports_orphaned_case_id(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    claims_root = tmp_path / "claims"
    cases_root = tmp_path / "cases"
    claims_root.mkdir(parents=True)

    _write_case(cases_root / "01_physics" / "ctmc-schnakenberg" / "ctmc-orphan-v01.yaml", "ctmc-orphan-v01")

    manage_cases.main([
        "validate",
        "--claims-root", str(claims_root),
        "--cases-root", str(cases_root),
    ])

    captured = capsys.readouterr()
    assert "ctmc-orphan-v01" in captured.out
    assert "ORPHANED" in captured.out


# ── validate: real atlas (smoke test) ────────────────────────────────────────


def test_validate_passes_on_real_atlas() -> None:
    """The real atlas must validate cleanly (atlas/cases/ may be empty initially)."""
    ret = manage_cases.main(["validate"])
    assert ret == 0
