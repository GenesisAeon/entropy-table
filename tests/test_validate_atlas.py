from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator


def load_schema(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_yaml(path: str) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def test_synthetic_domains_pass_schema() -> None:
    validator = Draft202012Validator(load_schema("atlas/schema/domain.schema.json"))
    for rel in [
        "atlas/domains/00_synthetic/langevin.yaml",
        "atlas/domains/00_synthetic/markov.yaml",
        "atlas/domains/00_synthetic/generic.yaml",
    ]:
        errors = list(validator.iter_errors(load_yaml(rel)))
        assert errors == [], f"{rel} had schema errors: {[e.message for e in errors]}"


def test_synthetic_relations_pass_schema() -> None:
    validator = Draft202012Validator(load_schema("atlas/schema/relation.schema.json"))
    for rel in [
        "atlas/relations/00_synthetic/underdamped_to_overdamped.yaml",
        "atlas/relations/00_synthetic/micro_to_macro_coarsegrain.yaml",
    ]:
        errors = list(validator.iter_errors(load_yaml(rel)))
        assert errors == [], f"{rel} had schema errors: {[e.message for e in errors]}"


def test_domain_requires_entropy_quantity_kind() -> None:
    validator = Draft202012Validator(load_schema("atlas/schema/domain.schema.json"))
    payload = load_yaml("atlas/domains/00_synthetic/generic.yaml")
    payload.pop("entropy_quantity_kind")
    errors = list(validator.iter_errors(payload))
    assert errors


def test_domain_id_pattern_enforced() -> None:
    validator = Draft202012Validator(load_schema("atlas/schema/domain.schema.json"))
    payload = load_yaml("atlas/domains/00_synthetic/generic.yaml")
    payload["id"] = "Not_kebab"
    errors = list(validator.iter_errors(payload))
    assert any("does not match" in e.message for e in errors)


def test_relation_requires_expected_effect() -> None:
    validator = Draft202012Validator(load_schema("atlas/schema/relation.schema.json"))
    payload = load_yaml("atlas/relations/00_synthetic/micro_to_macro_coarsegrain.yaml")
    payload.pop("expected_effect_on_entropy_measure")
    errors = list(validator.iter_errors(payload))
    assert errors


def test_relation_must_fail_tests_min_length_enforced() -> None:
    validator = Draft202012Validator(load_schema("atlas/schema/relation.schema.json"))
    payload = load_yaml("atlas/relations/00_synthetic/micro_to_macro_coarsegrain.yaml")
    payload["must_fail_tests"] = []
    errors = list(validator.iter_errors(payload))
    assert any("should be non-empty" in e.message or "is too short" in e.message for e in errors)
