from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


BASE_RELATION = {
    "id": "rel-test",
    "source_domain_id": "domain-a",
    "target_domain_id": "domain-b",
    "relation_type": "coupling",
    "conditions": {"text": "test", "params": {}},
    "preserved": ["a"],
    "lost": ["b"],
    "expected_effect": {"direction": "unknown", "description": "test"},
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
}


def validator() -> Draft202012Validator:
    schema = json.loads((ROOT / "atlas/schema/relation.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def errors(payload: dict) -> list[str]:
    return [e.message for e in validator().iter_errors(payload)]


def test_composition_requires_composition_block() -> None:
    relation = dict(BASE_RELATION)
    relation["relation_type"] = "composition"
    assert errors(relation)


def test_aggregation_rule_requires_aggregation_block() -> None:
    relation = dict(BASE_RELATION)
    relation["relation_type"] = "aggregation_rule"
    assert errors(relation)


def test_composition_block_requires_composition_relation_type() -> None:
    relation = dict(BASE_RELATION)
    relation["composition"] = {
        "kind": "subsystem_of",
        "parts": [{"domain_ref": "domain-a"}],
    }
    assert errors(relation)


def test_channels_enforces_kebab_case() -> None:
    relation = dict(BASE_RELATION)
    relation["channels"] = ["heat-flow", "BadChannel"]
    assert errors(relation)


def test_valid_explicit_composition_passes() -> None:
    relation = dict(BASE_RELATION)
    relation["relation_type"] = "composition"
    relation["composition"] = {
        "kind": "subsystem_of",
        "parts": [{"domain_ref": "domain-a", "role": "subsystem", "weight": 0.7}],
    }
    assert errors(relation) == []
