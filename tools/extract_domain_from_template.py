from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract a domain YAML draft from a template")
    parser.add_argument("--template", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--set", dest="sets", action="append", default=[])
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


def parse_set(value: str) -> tuple[list[str], str]:
    if "=" not in value:
        raise ValueError(f"Invalid --set value '{value}', expected path=value")
    dotted, raw = value.split("=", 1)
    path_parts = [part for part in dotted.split(".") if part]
    if not path_parts:
        raise ValueError(f"Invalid --set path in '{value}'")
    return path_parts, raw


def coerce_value(raw: str):
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def apply_path(target, path_parts: list[str], value) -> None:
    cursor = target
    for index, part in enumerate(path_parts[:-1]):
        next_part = path_parts[index + 1]
        is_next_index = next_part.isdigit()

        if isinstance(cursor, list):
            if not part.isdigit():
                raise ValueError(f"Expected list index at '{part}' in path {'.'.join(path_parts)}")
            item_index = int(part)
            if item_index < 0:
                raise ValueError("List index cannot be negative")
            while len(cursor) <= item_index:
                cursor.append({} if not is_next_index else [])
            if not isinstance(cursor[item_index], (dict, list)):
                cursor[item_index] = {} if not is_next_index else []
            cursor = cursor[item_index]
            continue

        if not isinstance(cursor, dict):
            raise ValueError(f"Cannot descend into non-container for path {'.'.join(path_parts)}")

        if part not in cursor or cursor[part] is None:
            cursor[part] = [] if is_next_index else {}
        elif not isinstance(cursor[part], (dict, list)):
            cursor[part] = [] if is_next_index else {}

        cursor = cursor[part]

    final = path_parts[-1]
    if isinstance(cursor, list):
        if not final.isdigit():
            raise ValueError(f"Expected list index at final segment '{final}'")
        final_index = int(final)
        if final_index < 0:
            raise ValueError("List index cannot be negative")
        while len(cursor) <= final_index:
            cursor.append(None)
        cursor[final_index] = value
        return

    if not isinstance(cursor, dict):
        raise ValueError(f"Cannot assign into non-dict at path {'.'.join(path_parts)}")
    cursor[final] = value


def load_template(path: Path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Template must be a YAML object")
    return data


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    template_path = Path(args.template)
    out_path = Path(args.out)

    if out_path.exists() and not args.force:
        print(f"Refusing to overwrite existing file: {out_path}")
        return 1

    try:
        payload = load_template(template_path)
        for assignment in args.sets:
            path_parts, raw_value = parse_set(assignment)
            apply_path(payload, path_parts, coerce_value(raw_value))
    except (OSError, yaml.YAMLError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    print(f"Wrote draft: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
