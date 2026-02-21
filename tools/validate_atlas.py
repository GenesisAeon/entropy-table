from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from common import SCHEMA_PATH, domain_files, load_yaml


def validate_domain(path: Path, validator: Draft202012Validator) -> list[str]:
    data = load_yaml(path)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
    out: list[str] = []
    for err in errors:
        rel = ".".join(str(p) for p in err.path) or "<root>"
        out.append(f"{path}: {rel}: {err.message}")
    return out


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    files = [f for f in domain_files() if f.name != "registry.yaml"]
    all_errors: list[str] = []
    for path in files:
        all_errors.extend(validate_domain(path, validator))

    if all_errors:
        print(f"Validation failed for {len(all_errors)} issue(s) across {len(files)} file(s).")
        for line in all_errors:
            print(f" - {line}")
        return 1

    print(f"Validation passed for {len(files)} domain file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
