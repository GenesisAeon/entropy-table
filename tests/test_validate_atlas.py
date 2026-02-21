from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def load_schema() -> dict:
    path = Path("atlas/schema/domain.schema.json")
    return json.loads(path.read_text(encoding="utf-8"))


def load_domain(path: str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def test_synthetic_domains_pass_schema() -> None:
    validator = Draft202012Validator(load_schema())
    for rel in [
        "atlas/domains/00_synthetic/langevin.yaml",
        "atlas/domains/00_synthetic/markov.yaml",
        "atlas/domains/00_synthetic/generic.yaml",
    ]:
        errors = list(validator.iter_errors(load_domain(rel)))
        assert errors == [], f"{rel} had schema errors: {[e.message for e in errors]}"


def test_missing_required_field_fails() -> None:
    validator = Draft202012Validator(load_schema())
    payload = load_domain("atlas/domains/00_synthetic/generic.yaml")
    payload.pop("entropy_proxy")
    errors = list(validator.iter_errors(payload))
    assert errors


def test_must_fail_tests_min_length_enforced() -> None:
    validator = Draft202012Validator(load_schema())
    payload = load_domain("atlas/domains/00_synthetic/generic.yaml")
    payload["must_fail_tests"] = ["only_one"]
    errors = list(validator.iter_errors(payload))
    assert any("is too short" in e.message for e in errors)
