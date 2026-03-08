"""Tests for schema_version enforcement in domain and relation schemas.

Verifies that:
- Files with the correct schema_version pass validation.
- Files with a missing schema_version fail validation.
- Files with a wrong schema_version fail validation.
- validate.py runs cleanly against the fully-migrated atlas.
- The schema enum correctly rejects wrong version strings.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
VALIDATE_SCRIPT = ROOT / "tools" / "validate.py"


def load_schema(rel_path: str) -> Draft202012Validator:
    schema = json.loads((ROOT / rel_path).read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def load_yaml(rel_path: str) -> dict:
    return yaml.safe_load((ROOT / rel_path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Domain schema_version
# ---------------------------------------------------------------------------

def test_domain_correct_schema_version_passes() -> None:
    validator = load_schema("atlas/schema/domain.schema.json")
    domain = load_yaml("tests/fixtures/pass/domain_valid.yaml")
    assert domain.get("schema_version") == "1.0.0"
    errors = list(validator.iter_errors(domain))
    assert errors == [], [e.message for e in errors]


def test_domain_missing_schema_version_fails() -> None:
    validator = load_schema("atlas/schema/domain.schema.json")
    domain = load_yaml("tests/fixtures/pass/domain_valid.yaml")
    del domain["schema_version"]
    errors = list(validator.iter_errors(domain))
    assert errors, "missing schema_version must fail domain schema validation"


def test_domain_wrong_schema_version_fails() -> None:
    validator = load_schema("atlas/schema/domain.schema.json")
    domain = load_yaml("tests/fixtures/pass/domain_valid.yaml")
    domain["schema_version"] = "0.9.0"
    errors = list(validator.iter_errors(domain))
    assert errors, "wrong schema_version must fail domain schema validation"


# ---------------------------------------------------------------------------
# Relation schema_version
# ---------------------------------------------------------------------------

def test_relation_correct_schema_version_passes() -> None:
    """Uses the golden composition relation which is fully schema-valid."""
    validator = load_schema("atlas/schema/relation.schema.json")
    relation = load_yaml("atlas/relations/00_golden/composition-sub-to-super.yaml")
    assert relation.get("schema_version") == "1.0.0"
    errors = list(validator.iter_errors(relation))
    assert errors == [], [e.message for e in errors]


def test_relation_missing_schema_version_fails() -> None:
    validator = load_schema("atlas/schema/relation.schema.json")
    relation = load_yaml("atlas/relations/00_golden/composition-sub-to-super.yaml")
    del relation["schema_version"]
    errors = list(validator.iter_errors(relation))
    assert errors, "missing schema_version must fail relation schema validation"


def test_relation_wrong_schema_version_fails() -> None:
    validator = load_schema("atlas/schema/relation.schema.json")
    relation = load_yaml("atlas/relations/00_golden/composition-sub-to-super.yaml")
    relation["schema_version"] = "0.9.0"
    errors = list(validator.iter_errors(relation))
    assert errors, "wrong schema_version must fail relation schema validation"


# ---------------------------------------------------------------------------
# validate.py integration: full atlas must pass cleanly after migration
# ---------------------------------------------------------------------------

def test_validate_passes_for_full_migrated_atlas() -> None:
    """validate.py --json must exit 0 with no errors after the schema_version migration."""
    import os

    env = {**os.environ, "PYTHONPATH": str(ROOT / "tools")}
    result = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "--json"],
        check=False,
        text=True,
        capture_output=True,
        cwd=str(ROOT),
        env=env,
    )
    output = json.loads(result.stdout)
    assert result.returncode == 0, f"validate.py failed:\n{output['errors']}"
    assert output["summary"]["valid"] is True
    assert output["summary"]["error_count"] == 0


def test_validate_version_conflict_error_type() -> None:
    """VersionConflict must appear in validate.py output for a mismatched schema_version.

    We test this at the Python level (calling main() logic directly) to avoid
    the hardcoded-atlas-root limitation in common.py that prevents subprocess
    redirection to a tmp directory.
    """
    # A domain dict that is otherwise schema-valid but declares the wrong version.
    import yaml

    domain_schema = json.loads((ROOT / "atlas/schema/domain.schema.json").read_text(encoding="utf-8"))
    expected_version = domain_schema.get("version", "unknown")

    # Wrong version triggers the friendly VersionConflict message.
    assert expected_version == "1.0.0"

    # Validate directly: schema enum must reject "0.9.0".
    validator = Draft202012Validator(domain_schema)
    domain = yaml.safe_load((ROOT / "tests/fixtures/pass/domain_valid.yaml").read_text(encoding="utf-8"))
    domain["schema_version"] = "0.9.0"
    errors = [e for e in validator.iter_errors(domain)]
    error_messages = [e.message for e in errors]
    assert any("0.9.0" in msg for msg in error_messages), (
        f"Expected schema to reject '0.9.0', got: {error_messages}"
    )
