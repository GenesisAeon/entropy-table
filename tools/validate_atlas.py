from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from common import (
    DOMAIN_SCHEMA_PATH,
    RELATION_SCHEMA_PATH,
    domain_files,
    load_yaml,
    relation_files,
)


def validate_payload(path: Path, validator: Draft202012Validator) -> list[str]:
    data = load_yaml(path)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    out: list[str] = []
    for err in errors:
        rel = ".".join(str(p) for p in err.path) or "<root>"
        out.append(f"{path}: {rel}: {err.message}")
    return out


def main() -> int:
    domain_schema = json.loads(DOMAIN_SCHEMA_PATH.read_text(encoding="utf-8"))
    relation_schema = json.loads(RELATION_SCHEMA_PATH.read_text(encoding="utf-8"))
    domain_validator = Draft202012Validator(domain_schema)
    relation_validator = Draft202012Validator(relation_schema)

    domain_paths = [f for f in domain_files() if f.name != "registry.yaml"]
    relation_paths = [f for f in relation_files() if f.name != "registry.yaml"]

    all_errors: list[str] = []
    domain_ids: set[str] = set()

    for path in domain_paths:
        all_errors.extend(validate_payload(path, domain_validator))
        data = load_yaml(path)
        domain_id = data.get("id")
        if isinstance(domain_id, str):
            if domain_id in domain_ids:
                all_errors.append(f"{path}: id: duplicate domain id '{domain_id}'")
            domain_ids.add(domain_id)

    for path in relation_paths:
        all_errors.extend(validate_payload(path, relation_validator))
        data = load_yaml(path)
        source = data.get("source_domain_ref")
        target = data.get("target_domain_ref")
        if isinstance(source, str) and source not in domain_ids:
            all_errors.append(f"{path}: source_domain_ref: unknown domain id '{source}'")
        if isinstance(target, str) and target not in domain_ids:
            all_errors.append(f"{path}: target_domain_ref: unknown domain id '{target}'")

    if all_errors:
        print(
            "Validation failed for "
            f"{len(all_errors)} issue(s) across {len(domain_paths)} domain and {len(relation_paths)} relation file(s)."
        )
        for line in all_errors:
            print(f" - {line}")
        return 1

    print(
        "Validation passed for "
        f"{len(domain_paths)} domain file(s) and {len(relation_paths)} relation file(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
