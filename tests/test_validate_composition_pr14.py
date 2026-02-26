from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "validate_composition.py"


def write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def domain_payload(domain_id: str, exchange_channels: list[str] | None = None) -> dict:
    payload = {
        "id": domain_id,
        "title": f"{domain_id} title",
        "system_type": {"primary": "stochastic_thermodynamics", "tags": ["synthetic"]},
        "entropy_quantity_kind": "production_rate",
        "epistemic_status": "numerical",
        "scope": {"applies_to": ["test"], "does_not_apply": ["none"]},
        "boundary": {
            "closure_type": "effectively_closed",
            "closure_notes": "modeled as effectively closed over selected scale",
            "external_entities": [{"id": "env", "role": "environment", "notes": "test entity"}],
        },
        "entropy_accounting": {
            "storage_term": {"symbol": "S", "latex": "S", "units": "J/K", "notes": "test"},
            "production_term": {"symbol": "Sigmadot", "latex": "\\dot{\\Sigma}", "units": "J/(Ks)", "notes": "test"},
            "flux_term": {"symbol": "Phidot", "latex": "\\dot{\\Phi}", "units": "J/(Ks)", "notes": "test"},
            "accounting_status": "approximate",
        },
        "entropy_definition": {
            "symbol": "S",
            "latex": "S = -k_B \\sum p \\ln p",
            "units": "J/K",
            "assumptions": [{"id": "a1", "statement": "assume", "epistemic_status": "heuristic", "citations": ["c1"]}],
            "zero_conditions": [{"id": "z1", "statement": "eq", "citations": ["c1"]}],
        },
        "operators": {
            "triggers": [
                {
                    "id": "tr1",
                    "name": "trigger",
                    "definition": "def",
                    "params": ["p"],
                    "observables": ["o"],
                    "notes": "n",
                    "epistemic_status": "heuristic",
                    "citations": ["c1"],
                }
            ],
            "dampers": [
                {
                    "id": "da1",
                    "name": "damper",
                    "definition": "def",
                    "params": ["p"],
                    "observables": ["o"],
                    "notes": "n",
                    "epistemic_status": "heuristic",
                    "citations": ["c1"],
                }
            ],
        },
        "spectral": {"method": "none", "phi_semantics": "none", "phi_definition": {"latex": "0", "notes": "none"}, "bands": []},
        "parameter_bands": {
            "beta": {"id": "b1", "name": "beta", "spec_type": "none", "value": None, "units": "none", "notes": "n"},
            "theta": {"id": "t1", "name": "theta", "spec_type": "none", "value": None, "units": "none", "notes": "n"},
            "zeta": {"id": "z2", "name": "zeta", "spec_type": "none", "value": None, "units": "none", "notes": "n"},
        },
        "must_fail_tests": [
            {"id": "mf1", "statement": "s", "expected_outcome": "reject", "rationale": "r", "citations": ["c1"], "severity": "hard"},
            {"id": "mf2", "statement": "s2", "expected_outcome": "reject", "rationale": "r2", "citations": ["c1"], "severity": "soft"},
        ],
        "citations": [{"id": "c1", "type": "note", "ref": "test"}],
        "status": "draft",
        "synthetic": True,
    }
    if exchange_channels is not None:
        payload["boundary"]["exchange_channels"] = exchange_channels
    return payload


def explicit_composition_relation(rel_id: str, source: str, target: str) -> dict:
    return {
        "id": rel_id,
        "source_domain_id": source,
        "target_domain_id": target,
        "relation_type": "composition",
        "conditions": {"text": "test", "params": {}},
        "preserved": ["x"],
        "lost": ["y"],
        "expected_effect": {"direction": "context_dependent", "description": "test"},
        "must_fail_tests": [
            {
                "id": "mf1",
                "statement": "s",
                "expected_outcome": "reject",
                "rationale": "r",
                "citations": ["c1"],
                "severity": "hard",
            }
        ],
        "citations": [{"id": "c1", "type": "note", "ref": "test"}],
        "status": "draft",
        "composition": {
            "kind": "subsystem_of",
            "parts": [{"domain_ref": source, "role": "subsystem", "weight": 1.0}],
        },
    }


def legacy_relation(rel_id: str, source: str, target: str) -> dict:
    relation = explicit_composition_relation(rel_id, source, target)
    relation["relation_type"] = "coupling"
    relation.pop("composition")
    relation["parts"] = [source]
    return relation


def run_validator(atlas_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--atlas-root", str(atlas_root)],
        check=False,
        text=True,
        capture_output=True,
    )


def test_explicit_composition_relation_passes(tmp_path: Path) -> None:
    atlas = tmp_path / "atlas"
    write_yaml(atlas / "domains" / "a.yaml", domain_payload("a", exchange_channels=["heat", "work"]))
    write_yaml(atlas / "domains" / "b.yaml", domain_payload("b", exchange_channels=["heat", "work"]))
    relation = explicit_composition_relation("a-to-b", "a", "b")
    relation["channels"] = ["heat"]
    write_yaml(atlas / "relations" / "a-to-b.yaml", relation)

    result = run_validator(atlas)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "cycle_found: no" in result.stdout


def test_legacy_heuristic_emits_warning_but_passes(tmp_path: Path) -> None:
    atlas = tmp_path / "atlas"
    write_yaml(atlas / "domains" / "a.yaml", domain_payload("a", exchange_channels=["heat"]))
    write_yaml(atlas / "domains" / "b.yaml", domain_payload("b", exchange_channels=["heat"]))
    write_yaml(atlas / "relations" / "a-to-b.yaml", legacy_relation("a-to-b", "a", "b"))

    result = run_validator(atlas)

    assert result.returncode == 0
    assert "legacy composition signal detected" in result.stdout


def test_channels_missing_domain_exchange_channels_warns(tmp_path: Path) -> None:
    atlas = tmp_path / "atlas"
    write_yaml(atlas / "domains" / "a.yaml", domain_payload("a", exchange_channels=None))
    write_yaml(atlas / "domains" / "b.yaml", domain_payload("b", exchange_channels=["heat"]))
    relation = explicit_composition_relation("a-to-b", "a", "b")
    relation["channels"] = ["heat"]
    write_yaml(atlas / "relations" / "a-to-b.yaml", relation)

    result = run_validator(atlas)

    assert result.returncode == 0
    assert "one or both domains do not declare boundary.exchange_channels" in result.stdout


def test_channels_mismatch_with_both_domains_declared_fails(tmp_path: Path) -> None:
    atlas = tmp_path / "atlas"
    write_yaml(atlas / "domains" / "a.yaml", domain_payload("a", exchange_channels=["heat", "work"]))
    write_yaml(atlas / "domains" / "b.yaml", domain_payload("b", exchange_channels=["heat"]))
    relation = explicit_composition_relation("a-to-b", "a", "b")
    relation["channels"] = ["work"]
    write_yaml(atlas / "relations" / "a-to-b.yaml", relation)

    result = run_validator(atlas)

    assert result.returncode == 1
    assert "must be declared in both" in result.stdout
