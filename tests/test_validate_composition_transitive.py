"""Tests for the transitive channel-consistency check (Option A).

Every subsystem's boundary.exchange_channels must be a subset of the
corresponding supersystem's boundary.exchange_channels.  Violations should be
reported as hard errors together with a full hierarchical path string.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "validate_composition.py"


# ---------------------------------------------------------------------------
# Helpers (minimal duplicates of the shared helpers in test_validate_composition.py)
# ---------------------------------------------------------------------------

def write_yaml(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def domain_payload(domain_id: str, exchange_channels: list[str] | None = None) -> dict:
    channels = ["heat"] if exchange_channels is None else exchange_channels
    return {
        "id": domain_id,
        "title": f"{domain_id} title",
        "system_type": {"primary": "stochastic_thermodynamics", "tags": ["synthetic"]},
        "entropy_quantity_kind": "production_rate",
        "epistemic_status": "numerical",
        "scope": {"applies_to": ["test"], "does_not_apply": ["none"]},
        "boundary": {
            "closure_type": "effectively_closed",
            "closure_notes": "modeled as effectively closed over selected scale",
            "exchange_channels": channels,
            "external_entities": [{"id": "env", "role": "environment", "notes": "test"}],
        },
        "entropy_accounting": {
            "storage_term": {"symbol": "S", "latex": "S", "units": "J/K", "notes": "test"},
            "production_term": {"symbol": "Sigmadot", "latex": r"\dot{\Sigma}", "units": "J/(Ks)", "notes": "test"},
            "flux_term": {"symbol": "Phidot", "latex": r"\dot{\Phi}", "units": "J/(Ks)", "notes": "test"},
            "accounting_status": "approximate",
        },
        "entropy_definition": {
            "symbol": "S",
            "latex": r"S = -k_B \sum p \ln p",
            "units": "J/K",
            "assumptions": [{"id": "a1", "statement": "assume", "epistemic_status": "heuristic", "citations": ["c1"]}],
            "zero_conditions": [{"id": "z1", "statement": "eq", "citations": ["c1"]}],
        },
        "operators": {
            "triggers": [{"id": "tr1", "name": "trigger", "definition": "def", "params": ["p"],
                          "observables": ["o"], "notes": "n", "epistemic_status": "heuristic", "citations": ["c1"]}],
            "dampers": [{"id": "da1", "name": "damper", "definition": "def", "params": ["p"],
                         "observables": ["o"], "notes": "n", "epistemic_status": "heuristic", "citations": ["c1"]}],
        },
        "spectral": {"method": "none", "phi_semantics": "none",
                     "phi_definition": {"latex": "0", "notes": "none"}, "bands": []},
        "parameter_bands": {
            "beta":  {"id": "b1", "name": "beta",  "spec_type": "none", "value": None, "units": "none", "notes": "n"},
            "theta": {"id": "t1", "name": "theta", "spec_type": "none", "value": None, "units": "none", "notes": "n"},
            "zeta":  {"id": "z2", "name": "zeta",  "spec_type": "none", "value": None, "units": "none", "notes": "n"},
        },
        "must_fail_tests": [
            {"id": "mf1", "statement": "s",  "expected_outcome": "reject", "rationale": "r",  "citations": ["c1"], "severity": "hard"},
            {"id": "mf2", "statement": "s2", "expected_outcome": "reject", "rationale": "r2", "citations": ["c1"], "severity": "soft"},
        ],
        "citations": [{"id": "c1", "type": "note", "ref": "test"}],
        "status": "draft",
        "synthetic": True,
    }


def composition_relation(rel_id: str, source: str, target: str) -> dict:
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
            {"id": "mf1", "statement": "s", "expected_outcome": "reject",
             "rationale": "r", "citations": ["c1"], "severity": "hard"}
        ],
        "citations": [{"id": "c1", "type": "note", "ref": "test"}],
        "status": "draft",
        "composition": {"kind": "subsystem_of", "parts": [{"domain_ref": source}]},
    }


def run_validator(atlas_root: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--atlas-root", str(atlas_root), *extra_args],
        check=False,
        text=True,
        capture_output=True,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_transitive_channels_flat_superset_passes(tmp_path: Path) -> None:
    """Subsystem channels ⊆ supersystem channels — no violation."""
    atlas = tmp_path / "atlas"
    write_yaml(atlas / "domains" / "sub.yaml",   domain_payload("sub",   exchange_channels=["heat", "work"]))
    write_yaml(atlas / "domains" / "super.yaml",  domain_payload("super", exchange_channels=["heat", "work", "information"]))
    write_yaml(atlas / "relations" / "r.yaml", composition_relation("r", "sub", "super"))

    result = run_validator(atlas)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Transitive channel integrity" not in result.stdout


def test_transitive_channels_exact_match_passes(tmp_path: Path) -> None:
    """sub.channels == super.channels — a superset (equality) is fine."""
    atlas = tmp_path / "atlas"
    write_yaml(atlas / "domains" / "sub.yaml",   domain_payload("sub",   exchange_channels=["heat", "information"]))
    write_yaml(atlas / "domains" / "super.yaml",  domain_payload("super", exchange_channels=["heat", "information"]))
    write_yaml(atlas / "relations" / "r.yaml", composition_relation("r", "sub", "super"))

    result = run_validator(atlas)

    assert result.returncode == 0, result.stdout + result.stderr


def test_transitive_channels_missing_channel_fails(tmp_path: Path) -> None:
    """Subsystem declares 'information'; supersystem only has 'heat' → error."""
    atlas = tmp_path / "atlas"
    write_yaml(atlas / "domains" / "sub.yaml",   domain_payload("sub",   exchange_channels=["heat", "information"]))
    write_yaml(atlas / "domains" / "super.yaml",  domain_payload("super", exchange_channels=["heat"]))
    write_yaml(atlas / "relations" / "r.yaml", composition_relation("r", "sub", "super"))

    result = run_validator(atlas)

    assert result.returncode == 1
    assert "Transitive channel integrity violation" in result.stdout
    assert "information" in result.stdout
    assert "super" in result.stdout
    assert "sub" in result.stdout


def test_transitive_channels_error_contains_path(tmp_path: Path) -> None:
    """Error message must include a path string showing the chain of domains."""
    atlas = tmp_path / "atlas"
    write_yaml(atlas / "domains" / "sub.yaml",   domain_payload("sub",   exchange_channels=["heat", "information"]))
    write_yaml(atlas / "domains" / "super.yaml",  domain_payload("super", exchange_channels=["heat"]))
    write_yaml(atlas / "relations" / "r.yaml", composition_relation("r", "sub", "super"))

    result = run_validator(atlas)

    assert result.returncode == 1
    # The error must contain a "Path:" section with an arrow-separated chain
    assert "Path:" in result.stdout
    assert "sub -> super" in result.stdout


def test_transitive_channels_deep_hierarchy_path_in_error(tmp_path: Path) -> None:
    """3-level hierarchy: sub-sub → sub → super.

    sub-sub declares [heat, information]; sub also declares [heat, information];
    super only declares [heat].  The failing edge is sub→super and the reported
    path must show all three levels: sub-sub -> sub -> super.
    """
    atlas = tmp_path / "atlas"
    write_yaml(atlas / "domains" / "sub-sub.yaml", domain_payload("sub-sub", exchange_channels=["heat", "information"]))
    write_yaml(atlas / "domains" / "sub.yaml",     domain_payload("sub",     exchange_channels=["heat", "information"]))
    write_yaml(atlas / "domains" / "super.yaml",   domain_payload("super",   exchange_channels=["heat"]))
    write_yaml(atlas / "relations" / "r1.yaml", composition_relation("r1", "sub-sub", "sub"))
    write_yaml(atlas / "relations" / "r2.yaml", composition_relation("r2", "sub",     "super"))

    result = run_validator(atlas)

    assert result.returncode == 1
    assert "Transitive channel integrity violation" in result.stdout
    # Full path must be visible in the error output
    assert "sub-sub -> sub -> super" in result.stdout


def test_transitive_channels_deep_hierarchy_broken_at_middle(tmp_path: Path) -> None:
    """3-level hierarchy where the channel is lost at the middle level.

    sub-sub: [heat, information], sub: [heat] (loses 'information'), super: [heat, information].
    The failing edge is sub-sub→sub; the error must mention 'information' and show that edge.
    """
    atlas = tmp_path / "atlas"
    write_yaml(atlas / "domains" / "sub-sub.yaml", domain_payload("sub-sub", exchange_channels=["heat", "information"]))
    write_yaml(atlas / "domains" / "sub.yaml",     domain_payload("sub",     exchange_channels=["heat"]))
    write_yaml(atlas / "domains" / "super.yaml",   domain_payload("super",   exchange_channels=["heat", "information"]))
    write_yaml(atlas / "relations" / "r1.yaml", composition_relation("r1", "sub-sub", "sub"))
    write_yaml(atlas / "relations" / "r2.yaml", composition_relation("r2", "sub",     "super"))

    result = run_validator(atlas)

    assert result.returncode == 1
    assert "information" in result.stdout
    assert "sub-sub" in result.stdout
    assert "sub" in result.stdout


def test_transitive_channels_no_exchange_channels_skipped(tmp_path: Path) -> None:
    """Domains without exchange_channels declared should not trigger transitive errors."""
    atlas = tmp_path / "atlas"
    # Use empty lists — the existing logic already handles missing-channel warnings;
    # the transitive check must not double-fire when channels are absent.
    write_yaml(atlas / "domains" / "sub.yaml",   domain_payload("sub",   exchange_channels=[]))
    write_yaml(atlas / "domains" / "super.yaml",  domain_payload("super", exchange_channels=["heat"]))
    write_yaml(atlas / "relations" / "r.yaml", composition_relation("r", "sub", "super"))

    result = run_validator(atlas)

    # Empty sub-channels: {} - {} = {} → no transitive error
    assert "Transitive channel integrity violation" not in result.stdout


def test_transitive_channels_json_output(tmp_path: Path) -> None:
    """Transitive violation is surfaced in JSON output under 'errors'."""
    atlas = tmp_path / "atlas"
    write_yaml(atlas / "domains" / "sub.yaml",   domain_payload("sub",   exchange_channels=["heat", "information"]))
    write_yaml(atlas / "domains" / "super.yaml",  domain_payload("super", exchange_channels=["heat"]))
    write_yaml(atlas / "relations" / "r.yaml", composition_relation("r", "sub", "super"))

    result = run_validator(atlas, "--json")

    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data["summary"]["valid"] is False
    assert any("Transitive channel integrity" in e for e in data["errors"])
    assert any("information" in e for e in data["errors"])
