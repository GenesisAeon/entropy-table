from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def run_validate_claims(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/validate_claims.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def make_valid_claim() -> dict:
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
            "provenance": "Temporary test fixture.",
        },
        "status": "review",
    }


def test_validate_claims_passes_for_repo_claims() -> None:
    result = run_validate_claims()
    assert result.returncode == 0
    assert "Claim validation passed" in result.stdout


def test_validate_claims_fails_missing_domain_ref(tmp_path: Path) -> None:
    claims_dir = tmp_path / "claims" / "01_physics" / "ctmc-schnakenberg"
    claims_dir.mkdir(parents=True)
    payload = make_valid_claim()
    payload.pop("domain_ref")
    (claims_dir / "claim-tmp-valid-claim.yaml").write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = run_validate_claims("--claims-root", str(claims_dir.parents[2]))
    assert result.returncode != 0
    assert "domain_ref" in result.stdout


def test_validate_claims_fails_invalid_claim_kind(tmp_path: Path) -> None:
    claims_dir = tmp_path / "claims" / "01_physics" / "ctmc-schnakenberg"
    claims_dir.mkdir(parents=True)
    payload = make_valid_claim()
    payload["claim_kind"] = "speculation"
    (claims_dir / "claim-tmp-valid-claim.yaml").write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = run_validate_claims("--claims-root", str(claims_dir.parents[2]))
    assert result.returncode != 0
    assert "claim_kind" in result.stdout


def test_validate_claims_fails_stable_without_citations(tmp_path: Path) -> None:
    claims_dir = tmp_path / "claims" / "01_physics" / "ctmc-schnakenberg"
    claims_dir.mkdir(parents=True)
    payload = make_valid_claim()
    payload["status"] = "stable"
    payload["evidence"]["citations"] = []
    (claims_dir / "claim-tmp-valid-claim.yaml").write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = run_validate_claims("--claims-root", str(claims_dir.parents[2]))
    assert result.returncode != 0
    assert "status=stable" in result.stdout


def test_validate_claims_supports_structured_case_objects(tmp_path: Path) -> None:
    claims_dir = tmp_path / "claims" / "01_physics" / "ctmc-schnakenberg"
    claims_dir.mkdir(parents=True)
    payload = make_valid_claim()
    payload["evidence"]["cases"] = [
        {
            "id": "case-seifert-ctmc-ep-positivity",
            "compute_ref": "tools/compute/case_seifert_ctmc_ep.py",
        }
    ]
    (claims_dir / "claim-tmp-valid-claim.yaml").write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = run_validate_claims("--claims-root", str(claims_dir.parents[2]))
    assert result.returncode == 0
    assert "Claim validation passed" in result.stdout
