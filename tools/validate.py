from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from common import DOMAIN_SCHEMA_PATH, RELATION_SCHEMA_PATH, domain_files, load_yaml, relation_files

TAG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def format_schema_errors(path: Path, validator: Draft202012Validator) -> list[dict]:
    payload = load_yaml(path)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    return [
        {
            "file": str(path),
            "error_type": "SchemaValidationError",
            "location": ".".join(str(p) for p in err.path) or "<root>",
            "message": err.message
        }
        for err in errors
    ]


def gather_citation_refs_domain(domain: dict) -> set[str]:
    refs: set[str] = set()
    for assumption in domain["entropy_definition"]["assumptions"]:
        refs.update(assumption.get("citations", []))
    for zero_condition in domain["entropy_definition"]["zero_conditions"]:
        refs.update(zero_condition.get("citations", []))
    for operator_group in ("triggers", "dampers"):
        for operator in domain["operators"][operator_group]:
            refs.update(operator.get("citations", []))
    for test in domain.get("must_fail_tests", []):
        refs.update(test.get("citations", []))
    for limitation in domain.get("limitations", []):
        refs.update(limitation.get("citations", []))
    return refs


def gather_citation_refs_relation(relation: dict) -> set[str]:
    refs: set[str] = set()
    for test in relation.get("must_fail_tests", []):
        refs.update(test.get("citations", []))
    return refs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Atlas schema and cross-references.")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args(argv)

    domain_validator = Draft202012Validator(json.loads(DOMAIN_SCHEMA_PATH.read_text(encoding="utf-8")))
    relation_validator = Draft202012Validator(json.loads(RELATION_SCHEMA_PATH.read_text(encoding="utf-8")))

    domain_paths = domain_files()
    relation_paths = relation_files()

    errors: list[dict] = []
    domain_ids: set[str] = set()

    # 1. Schema Validation
    for path in domain_paths:
        errors.extend(format_schema_errors(path, domain_validator))

    for path in relation_paths:
        errors.extend(format_schema_errors(path, relation_validator))

    # 2. Domain Cross-References & Custom Validation
    for path in domain_paths:
        d = load_yaml(path)
        domain_id = d.get("id")
        if domain_id in domain_ids:
            errors.append({"file": str(path), "error_type": "CrossReferenceError", "message": f"duplicate domain id '{domain_id}'"})
        domain_ids.add(domain_id)

        stype = d.get("system_type", {})
        tags = stype.get("tags", []) if isinstance(stype, dict) else []
        for t in tags:
            if not TAG_RE.match(str(t)):
                errors.append({"file": str(path), "error_type": "ValidationError", "message": f"system_type.tags contains invalid tag '{t}'"})
        if stype.get("primary") == "other" and len(tags) < 1:
            errors.append({"file": str(path), "error_type": "ValidationError", "message": "system_type.primary=other requires at least one system_type.tags entry"})

        boundary = d.get("boundary", {})
        if boundary.get("closure_type") == "effectively_closed" and not str(boundary.get("closure_notes", "")).strip():
            errors.append({"file": str(path), "error_type": "ValidationError", "message": "boundary.closure_notes is required when closure_type=effectively_closed"})

        citation_ids = {c.get("id") for c in d.get("citations", []) if isinstance(c, dict)}
        if len(citation_ids) != len(d.get("citations", [])):
            errors.append({"file": str(path), "error_type": "ValidationError", "message": "duplicate citation id(s) in citations"})
        for ref in gather_citation_refs_domain(d):
            if ref not in citation_ids:
                errors.append({"file": str(path), "error_type": "CrossReferenceError", "message": f"citation reference '{ref}' not found in citations"})

    # 3. Relation Cross-References & Custom Validation
    relation_ids: set[str] = set()
    for path in relation_paths:
        r = load_yaml(path)
        rel_id = r.get("id")
        if rel_id in relation_ids:
            errors.append({"file": str(path), "error_type": "CrossReferenceError", "message": f"duplicate relation id '{rel_id}'"})
        relation_ids.add(rel_id)

        if r.get("source_domain_id") not in domain_ids:
            errors.append({"file": str(path), "error_type": "CrossReferenceError", "message": f"source_domain_id '{r.get('source_domain_id')}' does not exist"})
        if r.get("target_domain_id") not in domain_ids:
            errors.append({"file": str(path), "error_type": "CrossReferenceError", "message": f"target_domain_id '{r.get('target_domain_id')}' does not exist"})

        if r.get("relation_type") == "composition":
            for part in r.get("parts", []):
                if part not in domain_ids:
                    errors.append({"file": str(path), "error_type": "CrossReferenceError", "message": f"composition part '{part}' does not exist"})

        context_tags = r.get("context", {}).get("tags", []) if isinstance(r.get("context"), dict) else []
        for t in context_tags:
            if not TAG_RE.match(str(t)):
                errors.append({"file": str(path), "error_type": "ValidationError", "message": f"context.tags contains invalid tag '{t}'"})

        citation_ids = {c.get("id") for c in r.get("citations", []) if isinstance(c, dict)}
        if len(citation_ids) != len(r.get("citations", [])):
            errors.append({"file": str(path), "error_type": "ValidationError", "message": "duplicate citation id(s) in citations"})
        for ref in gather_citation_refs_relation(r):
            if ref not in citation_ids:
                errors.append({"file": str(path), "error_type": "CrossReferenceError", "message": f"citation reference '{ref}' not found in citations"})

    # 4. Output Generation
    summary = {
        "total_domains": len(domain_paths),
        "total_relations": len(relation_paths),
        "valid": len(errors) == 0,
        "error_count": len(errors)
    }

    if args.json:
        print(json.dumps({"summary": summary, "errors": errors}, indent=2))
    else:
        if errors:
            print(f"Validation failed with {len(errors)} error(s):")
            for err in errors:
                loc = f" at {err['location']}" if "location" in err else ""
                print(f" - {err['file']}{loc}: [{err['error_type']}] {err['message']}")
        else:
            print(f"Validation passed: {summary['total_domains']} domains, {summary['total_relations']} relations.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
