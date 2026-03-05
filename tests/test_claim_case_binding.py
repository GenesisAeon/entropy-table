from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import report_claims


def run_validate_claims(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/validate_claims.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def make_claim(case_items: list[object]) -> dict:
    return {
        "id": "tmp-valid-claim",
        "title": "Temporary valid claim",
        "domain_ref": "ctmc-schnakenberg",
        "claim_kind": "theorem",
        "statement": {"text": "Temporary statement."},
        "assumptions": ["Markov assumptions hold."],
        "falsification": {"must_fail_refs": ["detailed-balance-implies-zero-ep"]},
        "evidence": {
            "citations": ["schnakenberg1976-rmp"],
            "cases": case_items,
            "provenance": "Temporary test fixture.",
        },
        "status": "review",
    }


def test_validate_claims_accepts_valid_case_id_format(tmp_path: Path) -> None:
    claims_dir = tmp_path / "claims" / "01_physics" / "ctmc-schnakenberg"
    claims_dir.mkdir(parents=True)
    payload = make_claim(["ctmc-3cycle-nonzero-v1", "diffusion-ep-zero-current-v1"])
    (claims_dir / "claim-tmp-valid-claim.yaml").write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = run_validate_claims("--claims-root", str(claims_dir.parents[2]))
    assert result.returncode == 0
    assert "Claim validation passed" in result.stdout


def test_validate_claims_accepts_structured_case_item(tmp_path: Path) -> None:
    claims_dir = tmp_path / "claims" / "01_physics" / "ctmc-schnakenberg"
    claims_dir.mkdir(parents=True)
    payload = make_claim(
        [
            {
                "id": "ctmc-3cycle-nonzero-v1",
                "description": "Structured case payload",
            }
        ]
    )
    (claims_dir / "claim-tmp-valid-claim.yaml").write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = run_validate_claims("--claims-root", str(claims_dir.parents[2]))
    assert result.returncode == 0
    assert "Claim validation passed" in result.stdout


def test_validate_claims_rejects_invalid_case_id_format(tmp_path: Path) -> None:
    claims_dir = tmp_path / "claims" / "01_physics" / "ctmc-schnakenberg"
    claims_dir.mkdir(parents=True)
    payload = make_claim(["Bad/Case/Path.yaml"])
    (claims_dir / "claim-tmp-valid-claim.yaml").write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = run_validate_claims("--claims-root", str(claims_dir.parents[2]))
    assert result.returncode != 0
    assert "evidence.cases contains invalid case id" in result.stdout


def test_validate_claims_rejects_invalid_structured_case_shape(tmp_path: Path) -> None:
    claims_dir = tmp_path / "claims" / "01_physics" / "ctmc-schnakenberg"
    claims_dir.mkdir(parents=True)
    payload = make_claim([{"description": "missing id"}])
    (claims_dir / "claim-tmp-valid-claim.yaml").write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = run_validate_claims("--claims-root", str(claims_dir.parents[2]))
    assert result.returncode != 0
    assert "evidence.cases must be a list of non-empty strings or objects with non-empty string id" in result.stdout


def test_report_claims_includes_cases_count(monkeypatch) -> None:
    monkeypatch.setattr(
        report_claims,
        "load_claims",
        lambda: [
            {
                "id": "stable-linked-claim",
                "title": "Stable linked",
                "domain_ref": "ctmc-schnakenberg",
                "claim_kind": "theorem",
                "status": "stable",
                "falsification": {"must_fail_refs": ["x"]},
                "evidence": {
                    "citations": ["schnakenberg1976-rmp"],
                    "cases": ["ctmc-3cycle-nonzero-v1", "ctmc-3cycle-zero-v1"],
                },
            }
        ],
    )

    report = report_claims.build_report()

    assert "| Claim ID | Title | Kind | Status | cases_count | cases_preview |" in report
    assert "| stable-linked-claim | Stable linked | theorem | stable | 2 | ctmc-3cycle-nonzero-v1, ctmc-3cycle-zero-v1 |" in report
