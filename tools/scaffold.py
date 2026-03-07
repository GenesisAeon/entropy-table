from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "templates"
ATLAS_DIR = ROOT / "atlas"

_KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# Category dirs follow the repo convention: optional digits + underscore prefix, e.g. 01_physics
_CATEGORY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

# Map entity type -> (template filename, atlas sub-directory)
_ENTITY_CONFIG: dict[str, tuple[str, str]] = {
    "domain": ("domain_template.yaml", "domains"),
}


def _validate_kebab(value: str) -> None:
    if not _KEBAB_RE.match(value):
        print(f"error: '{value}' is not valid kebab-case (e.g. 'my-new-system')", file=sys.stderr)
        sys.exit(1)


def _validate_category(value: str) -> None:
    if not _CATEGORY_RE.match(value):
        print(f"error: '{value}' is not a valid category name (e.g. '01_physics')", file=sys.stderr)
        sys.exit(1)


def scaffold(entity: str, entity_id: str, category: str) -> Path:
    _validate_kebab(entity_id)
    _validate_category(category)

    template_name, atlas_subdir = _ENTITY_CONFIG[entity]
    template_path = TEMPLATES_DIR / template_name
    if not template_path.exists():
        print(f"error: template not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    target_dir = ATLAS_DIR / atlas_subdir / category
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / f"{entity_id}.yaml"
    if target_path.exists():
        print(f"error: file already exists: {target_path}", file=sys.stderr)
        sys.exit(1)

    content = template_path.read_text(encoding="utf-8")

    # Replace the placeholder id field (handles quoted and unquoted values)
    content = re.sub(
        r'^id:\s*.*$',
        f'id: "{entity_id}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )

    target_path.write_text(content, encoding="utf-8")
    return target_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a new atlas entity from a template.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join([
            "examples:",
            "  python tools/scaffold.py domain my-new-system",
            "  python tools/scaffold.py domain my-new-system --category 01_physics",
        ]),
    )
    subparsers = parser.add_subparsers(dest="entity", required=True)

    domain_parser = subparsers.add_parser("domain", help="Create a new domain from the template.")
    domain_parser.add_argument("id", help="Domain ID in kebab-case, e.g. 'my-new-system'.")
    domain_parser.add_argument(
        "--category",
        default="01_physics",
        help="Target subdirectory under atlas/domains/ (default: 01_physics).",
    )

    args = parser.parse_args(argv)

    try:
        path = scaffold(args.entity, args.id, args.category)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"created: {path.relative_to(ROOT)}")
    print("fill in every <TODO:...> field before committing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
