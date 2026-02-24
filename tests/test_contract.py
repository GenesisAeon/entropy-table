from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: str) -> dict:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def load_schema(path: str) -> Draft202012Validator:
    schema = json.loads((ROOT / path).read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def test_golden_domains_pass_schema() -> None:
    validator = load_schema("atlas/schema/domain.schema.json")
    for path in (ROOT / "atlas/domains/00_golden").glob("*.yaml"):
        errors = list(validator.iter_errors(load_yaml(path.relative_to(ROOT).as_posix())))
        assert errors == [], f"{path} failed: {[e.message for e in errors]}"


def test_golden_relations_pass_schema() -> None:
    validator = load_schema("atlas/schema/relation.schema.json")
    for path in (ROOT / "atlas/relations/00_golden").glob("*.yaml"):
        errors = list(validator.iter_errors(load_yaml(path.relative_to(ROOT).as_posix())))
        assert errors == [], f"{path} failed: {[e.message for e in errors]}"


def test_fail_missing_closure_notes() -> None:
    validator = load_schema("atlas/schema/domain.schema.json")
    errors = list(validator.iter_errors(load_yaml("tests/fixtures/fail/domain_missing_closure_notes.yaml")))
    assert errors


def test_fail_missing_must_fail_tests() -> None:
    validator = load_schema("atlas/schema/domain.schema.json")
    errors = list(validator.iter_errors(load_yaml("tests/fixtures/fail/domain_missing_must_fail_tests.yaml")))
    assert errors


def test_fail_invalid_enum() -> None:
    validator = load_schema("atlas/schema/domain.schema.json")
    errors = list(validator.iter_errors(load_yaml("tests/fixtures/fail/domain_invalid_enum.yaml")))
    assert errors


def test_fail_dangling_relation_endpoint() -> None:
    domain_ids = {d["id"] for d in [load_yaml(p.relative_to(ROOT).as_posix()) for p in (ROOT / "atlas/domains/00_golden").glob("*.yaml")]}
    relation = load_yaml("tests/fixtures/fail/relation_dangling_endpoint.yaml")
    assert relation["target_domain_id"] not in domain_ids
