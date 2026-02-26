from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from snapshot import (  # noqa: E402
    ATLAS,
    ROOT,
    build_bundle,
    build_manifest,
    build_readme,
    canonical_json_bytes,
    compute_schema_hashes,
    generate_snapshot_id,
)

FREEZE_MANIFEST_PATH = ROOT / "dist" / "freeze" / "freeze_manifest.json"


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(data))


def cmd_snapshot(args: argparse.Namespace) -> int:
    snapshot_id = args.snapshot_id or generate_snapshot_id()
    out_root = Path(args.out)
    if not out_root.is_absolute():
        out_root = ROOT / out_root
    snapshot_dir = out_root / snapshot_id
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    bundle, bundle_bytes, bundle_sha256 = build_bundle(snapshot_id=snapshot_id, atlas_root=ATLAS, repo_root=ROOT)

    bundle_path = snapshot_dir / "bundle.json"
    readme_path = snapshot_dir / "README.md"
    manifest_path = snapshot_dir / "MANIFEST.json"

    bundle_path.write_bytes(bundle_bytes)

    readme_text = build_readme(
        snapshot_id=snapshot_id,
        bundle_sha256=bundle_sha256,
        counts=bundle["counts"],
        schema_hashes=bundle["schema"],
        bundle=bundle,
    )
    readme_path.write_text(readme_text, encoding="utf-8")

    manifest = build_manifest(
        snapshot_id=snapshot_id,
        bundle_sha256=bundle_sha256,
        counts=bundle["counts"],
        schema_hashes=bundle["schema"],
        bundle_path=bundle_path,
        readme_path=readme_path,
        manifest_path=manifest_path,
        repo_root=ROOT,
    )
    _write_json(manifest_path, manifest)

    print(f"snapshot_id={snapshot_id}")
    print(f"bundle_sha256={bundle_sha256}")
    print(f"path={snapshot_dir}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    snapshot_path = Path(args.path)
    if not snapshot_path.is_absolute():
        snapshot_path = ROOT / snapshot_path

    manifest_path = snapshot_path / "MANIFEST.json"
    bundle_path = snapshot_path / "bundle.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bundle_bytes = bundle_path.read_bytes()
    actual_bundle_hash = hashlib.sha256(bundle_bytes).hexdigest()
    expected_bundle_hash = manifest.get("bundle_sha256")

    if actual_bundle_hash != expected_bundle_hash:
        print("Bundle hash mismatch", file=sys.stderr)
        print(f"expected={expected_bundle_hash}", file=sys.stderr)
        print(f"actual={actual_bundle_hash}", file=sys.stderr)
        return 1

    bundle = json.loads(bundle_bytes)
    manifest_schema = manifest.get("schema", {})
    current_schema = compute_schema_hashes(atlas_root=ATLAS, repo_root=ROOT)
    for key, value in current_schema.items():
        if manifest_schema.get(key) != value:
            print(f"WARNING: schema hash mismatch for {key}: manifest={manifest_schema.get(key)} current={value}")

    if bundle.get("counts") != manifest.get("counts"):
        print("WARNING: manifest counts differ from bundle counts")

    print("Snapshot verification passed")
    return 0


def _stable_records() -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    for path in sorted((ATLAS / "domains").glob("**/*.yaml")) + sorted((ATLAS / "relations").glob("**/*.yaml")) + sorted(
        (ATLAS / "claims").glob("**/*.yaml")
    ):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("status") == "stable":
            file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            rel = path.relative_to(ROOT).as_posix()
            records.append((rel, file_hash))
    return sorted(records)


def _current_freeze_manifest() -> dict[str, Any]:
    records = _stable_records()
    return {
        "stable_entries": [{"path": path, "sha256": sha} for path, sha in records],
        "count": len(records),
    }


def _write_freeze_manifest() -> None:
    _write_json(FREEZE_MANIFEST_PATH, _current_freeze_manifest())


def cmd_freeze_init(_: argparse.Namespace) -> int:
    _write_freeze_manifest()
    print(f"Wrote freeze manifest: {FREEZE_MANIFEST_PATH}")
    return 0


def cmd_freeze_verify(_: argparse.Namespace) -> int:
    if not FREEZE_MANIFEST_PATH.exists():
        print("Freeze manifest not found. Run freeze-init first.", file=sys.stderr)
        return 1

    existing = json.loads(FREEZE_MANIFEST_PATH.read_text(encoding="utf-8"))
    current = _current_freeze_manifest()
    existing_map = {item["path"]: item["sha256"] for item in existing.get("stable_entries", [])}
    current_map = {item["path"]: item["sha256"] for item in current.get("stable_entries", [])}

    changed = [path for path in sorted(set(existing_map) & set(current_map)) if existing_map[path] != current_map[path]]
    removed = sorted(set(existing_map) - set(current_map))
    added = sorted(set(current_map) - set(existing_map))

    if changed or removed or added:
        print("Stable asset changes detected:", file=sys.stderr)
        for path in changed:
            print(f" - modified: {path}", file=sys.stderr)
        for path in removed:
            print(f" - removed: {path}", file=sys.stderr)
        for path in added:
            print(f" - added: {path}", file=sys.stderr)
        return 1

    print("Freeze verification passed")
    return 0


def cmd_freeze_update(args: argparse.Namespace) -> int:
    if not args.allow_stable_edits:
        print("freeze-update requires --allow-stable-edits", file=sys.stderr)
        return 1
    _write_freeze_manifest()
    print(f"Updated freeze manifest: {FREEZE_MANIFEST_PATH}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Release tooling for deterministic scientific snapshots")
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot_parser = subparsers.add_parser("snapshot", help="Build deterministic snapshot bundle")
    snapshot_parser.add_argument("--id", dest="snapshot_id", default=None, help="Snapshot identifier (UTC timestamp if omitted)")
    snapshot_parser.add_argument("--out", default="dist/snapshots", help="Output root directory")
    snapshot_parser.set_defaults(func=cmd_snapshot)

    verify_parser = subparsers.add_parser("verify", help="Verify snapshot manifest and hashes")
    verify_parser.add_argument("--path", required=True, help="Path to dist/snapshots/<snapshot_id>")
    verify_parser.set_defaults(func=cmd_verify)

    freeze_check_parser = subparsers.add_parser("freeze-check", help="Alias for freeze-verify")
    freeze_check_parser.set_defaults(func=cmd_freeze_verify)

    freeze_init_parser = subparsers.add_parser("freeze-init", help="Initialize freeze manifest")
    freeze_init_parser.set_defaults(func=cmd_freeze_init)

    freeze_verify_parser = subparsers.add_parser("freeze-verify", help="Verify stable assets against freeze manifest")
    freeze_verify_parser.set_defaults(func=cmd_freeze_verify)

    freeze_update_parser = subparsers.add_parser("freeze-update", help="Update freeze manifest when stable edits are intentional")
    freeze_update_parser.add_argument("--allow-stable-edits", action="store_true", help="Required acknowledgement")
    freeze_update_parser.set_defaults(func=cmd_freeze_update)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
