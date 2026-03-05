from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    ATLAS,
    ROOT,
    load_yaml,
)
from validate import (  # noqa: E402
    format_schema_errors,
    gather_citation_refs_domain,
    gather_citation_refs_relation,
)
from validate_bibliography import collect_citation_refs, load_bibliography_ids  # noqa: E402
from validate_claims import validate_claim_file  # noqa: E402

ENTRY_TYPES = ("domain", "relation", "claim")


def _discover_domain_ids(atlas_root: Path) -> set[str]:
    ids: set[str] = set()
    for path in sorted((atlas_root / "domains").glob("**/*.yaml")):
        domain_id = load_yaml(path).get("id")
        if isinstance(domain_id, str):
            ids.add(domain_id)
    return ids


def _discover_relation_ids(atlas_root: Path) -> set[str]:
    ids: set[str] = set()
    for path in sorted((atlas_root / "relations").glob("**/*.yaml")):
        relation_id = load_yaml(path).get("id")
        if isinstance(relation_id, str):
            ids.add(relation_id)
    return ids


def _validate_domain_or_relation(path: Path, entry_type: str, atlas_root: Path) -> list[str]:
    errors: list[str] = []
    payload = load_yaml(path)

    if entry_type == "domain":
        schema_path = atlas_root / "schema" / "domain.schema.json"
        validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
        errors.extend(format_schema_errors(path, validator))

        citation_ids = {c.get("id") for c in payload.get("citations", []) if isinstance(c, dict)}
        if len(citation_ids) != len(payload.get("citations", [])):
            errors.append(f"{path}: duplicate citation id(s) in citations")
        try:
            refs = gather_citation_refs_domain(payload)
        except (KeyError, TypeError):
            refs = set()
        for ref in refs:
            if ref not in citation_ids:
                errors.append(f"{path}: citation reference '{ref}' not found in citations")

    if entry_type == "relation":
        schema_path = atlas_root / "schema" / "relation.schema.json"
        validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
        errors.extend(format_schema_errors(path, validator))

        domain_ids = _discover_domain_ids(atlas_root)
        if payload.get("source_domain_id") not in domain_ids:
            errors.append(f"{path}: source_domain_id '{payload.get('source_domain_id')}' does not exist")
        if payload.get("target_domain_id") not in domain_ids:
            errors.append(f"{path}: target_domain_id '{payload.get('target_domain_id')}' does not exist")
        if payload.get("relation_type") == "composition":
            for part in payload.get("parts", []):
                if part not in domain_ids:
                    errors.append(f"{path}: composition part '{part}' does not exist")

        citation_ids = {c.get("id") for c in payload.get("citations", []) if isinstance(c, dict)}
        if len(citation_ids) != len(payload.get("citations", [])):
            errors.append(f"{path}: duplicate citation id(s) in citations")
        try:
            refs = gather_citation_refs_relation(payload)
        except (KeyError, TypeError):
            refs = set()
        for ref in refs:
            if ref not in citation_ids:
                errors.append(f"{path}: citation reference '{ref}' not found in citations")

    return errors


def _validate_claim(path: Path, target_dir: str, atlas_root: Path) -> list[str]:
    domain_ids = _discover_domain_ids(atlas_root)
    relation_ids = _discover_relation_ids(atlas_root)
    payload = load_yaml(path)
    domain_ref = payload.get("domain_ref") if isinstance(payload, dict) else None

    with tempfile.TemporaryDirectory() as tmp:
        if isinstance(domain_ref, str) and domain_ref.strip():
            temp_path = Path(tmp) / target_dir / domain_ref / path.name
        else:
            temp_path = Path(tmp) / target_dir / path.name
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        _, errors, _warnings = validate_claim_file(temp_path, domain_ids, relation_ids)
        return errors


def _validate_bibliography(path: Path, refs_path: Path) -> list[str]:
    payload = load_yaml(path)
    known_refs = load_bibliography_ids(refs_path)
    missing = sorted(ref for ref in collect_citation_refs(payload) if ref not in known_refs)
    if missing:
        return [f"{path}: unknown citation id(s) {missing}"]
    return []


def ingest_draft(
    input_file: Path,
    entry_type: str,
    target_dir: str,
    force: bool = False,
    atlas_root: Path = ATLAS,
    refs_path: Path | None = None,
) -> tuple[bool, str, Path | None]:
    refs = refs_path if refs_path is not None else atlas_root / "bibliography" / "refs.yaml"

    if not input_file.exists():
        return False, f"Input file not found: {input_file}", None

    try:
        load_yaml(input_file)
    except Exception as exc:
        return False, f"Failed to parse YAML: {exc}", None

    errors: list[str] = []
    if entry_type in {"domain", "relation"}:
        errors.extend(_validate_domain_or_relation(input_file, entry_type, atlas_root))
    else:
        errors.extend(_validate_claim(input_file, target_dir, atlas_root))

    errors.extend(_validate_bibliography(input_file, refs))

    if errors:
        joined = "\n".join(f" - {err}" for err in errors)
        return False, f"Ingestion failed with {len(errors)} error(s):\n{joined}", None

    if entry_type == "claim":
        payload = load_yaml(input_file)
        domain_ref = payload.get("domain_ref") if isinstance(payload, dict) else None
        if isinstance(domain_ref, str) and domain_ref.strip():
            target_path = atlas_root / f"{entry_type}s" / target_dir / domain_ref / input_file.name
        else:
            target_path = atlas_root / f"{entry_type}s" / target_dir / input_file.name
    else:
        target_path = atlas_root / f"{entry_type}s" / target_dir / input_file.name
    if target_path.exists() and not force:
        return False, f"Target already exists: {target_path} (use --force to overwrite)", target_path

    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(input_file, target_path)
    return True, f"Ingestion successful: {input_file} -> {target_path}", target_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest a staged draft into atlas after validation")
    parser.add_argument("input_file", help="Path to draft YAML file")
    parser.add_argument("--type", choices=ENTRY_TYPES, required=True, help="Entry type to ingest")
    parser.add_argument("--target-dir", required=True, help="Target atlas subdirectory (for example: 01_physics)")
    parser.add_argument("--force", action="store_true", help="Overwrite existing target file")
    parser.add_argument("--atlas-root", default=str(ATLAS), help=argparse.SUPPRESS)
    parser.add_argument("--refs", default=None, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    atlas_root = Path(args.atlas_root)
    if not atlas_root.is_absolute():
        atlas_root = ROOT / atlas_root

    refs_path = Path(args.refs) if args.refs else None
    if refs_path is not None and not refs_path.is_absolute():
        refs_path = ROOT / refs_path

    ok, message, _target = ingest_draft(
        input_file=Path(args.input_file),
        entry_type=args.type,
        target_dir=args.target_dir,
        force=args.force,
        atlas_root=atlas_root,
        refs_path=refs_path,
    )
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
