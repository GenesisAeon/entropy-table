from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas"


def _load_yaml_object(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML object")
    return data


def _load_sorted_yaml(dir_path: Path) -> list[dict[str, Any]]:
    items = [_load_yaml_object(path) for path in sorted(dir_path.glob("**/*.yaml"))]
    return sorted(items, key=lambda item: str(item.get("id", "")))


def load_all_domains(atlas_root: Path = ATLAS) -> list[dict[str, Any]]:
    return _load_sorted_yaml(atlas_root / "domains")


def load_all_relations(atlas_root: Path = ATLAS) -> list[dict[str, Any]]:
    return _load_sorted_yaml(atlas_root / "relations")


def load_all_claims(atlas_root: Path = ATLAS) -> list[dict[str, Any]]:
    return _load_sorted_yaml(atlas_root / "claims")


def load_bibliography(atlas_root: Path = ATLAS) -> dict[str, Any]:
    return _load_yaml_object(atlas_root / "bibliography" / "refs.yaml")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_schema_hashes(atlas_root: Path = ATLAS, repo_root: Path = ROOT) -> dict[str, str]:
    schema_root = atlas_root / "schema"
    claim_contract_path = repo_root / "docs" / "claims.md"
    return {
        "domain_schema_sha256": sha256_file(schema_root / "domain.schema.json"),
        "relation_schema_sha256": sha256_file(schema_root / "relation.schema.json"),
        "claim_contract_sha256": sha256_file(claim_contract_path),
    }


def canonical_json_bytes(data: dict[str, Any]) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build_bundle(snapshot_id: str, atlas_root: Path = ATLAS, repo_root: Path = ROOT) -> tuple[dict[str, Any], bytes, str]:
    domains = load_all_domains(atlas_root)
    relations = load_all_relations(atlas_root)
    claims = load_all_claims(atlas_root)
    bibliography = load_bibliography(atlas_root)
    schema_hashes = compute_schema_hashes(atlas_root=atlas_root, repo_root=repo_root)

    bundle = {
        "snapshot_id": snapshot_id,
        "schema": schema_hashes,
        "counts": {"domains": len(domains), "relations": len(relations), "claims": len(claims)},
        "domains": domains,
        "relations": relations,
        "claims": claims,
        "bibliography": bibliography,
    }
    bundle_bytes = canonical_json_bytes(bundle)
    bundle_sha256 = hashlib.sha256(bundle_bytes).hexdigest()
    return bundle, bundle_bytes, bundle_sha256


def git_info(repo_root: Path = ROOT) -> dict[str, Any]:
    def _git(args: list[str]) -> str | None:
        try:
            completed = subprocess.run(
                ["git", *args],
                cwd=repo_root,
                check=True,
                capture_output=True,
                text=True,
            )
            return completed.stdout.strip()
        except Exception:
            return None

    commit = _git(["rev-parse", "HEAD"])
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"])
    status = _git(["status", "--porcelain"])

    if commit is None and branch is None:
        return {"commit": None, "branch": None, "dirty": None}

    return {"commit": commit, "branch": branch, "dirty": bool(status)}


def generate_snapshot_id(now: datetime | None = None) -> str:
    current = now or datetime.now(timezone.utc)
    return current.strftime("%Y%m%d-%H%M%SZ")


def build_manifest(
    snapshot_id: str,
    bundle_sha256: str,
    counts: dict[str, int],
    schema_hashes: dict[str, str],
    bundle_path: Path,
    readme_path: Path,
    manifest_path: Path,
    created_utc: str | None = None,
    repo_root: Path = ROOT,
) -> dict[str, Any]:
    created_value = created_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "snapshot_id": snapshot_id,
        "created_utc": created_value,
        "bundle_sha256": bundle_sha256,
        "schema": schema_hashes,
        "counts": counts,
        "git": git_info(repo_root=repo_root),
        "paths": {
            "bundle": str(bundle_path),
            "readme": str(readme_path),
            "manifest": str(manifest_path),
        },
    }


def build_readme(snapshot_id: str, bundle_sha256: str, counts: dict[str, int], schema_hashes: dict[str, str], bundle: dict[str, Any], top_n: int = 10) -> str:
    domains = [item.get("id", "") for item in bundle["domains"][:top_n]]
    relations = [item.get("id", "") for item in bundle["relations"][:top_n]]
    claims = [item.get("id", "") for item in bundle["claims"][:top_n]]

    def _fmt(items: list[str]) -> str:
        return "\n".join(f"- `{value}`" for value in items if value) or "- _(none)_"

    return (
        f"# Entropy Atlas Snapshot {snapshot_id}\n\n"
        "## Summary\n"
        f"- Domains: {counts['domains']}\n"
        f"- Relations: {counts['relations']}\n"
        f"- Claims: {counts['claims']}\n"
        f"- Bundle SHA256: `{bundle_sha256}`\n\n"
        "## Schema hashes\n"
        f"- domain.schema.json: `{schema_hashes['domain_schema_sha256']}`\n"
        f"- relation.schema.json: `{schema_hashes['relation_schema_sha256']}`\n"
        f"- claim contract (docs/claims.md): `{schema_hashes['claim_contract_sha256']}`\n\n"
        f"## Top-level IDs (first {top_n})\n"
        "### Domains\n"
        f"{_fmt(domains)}\n\n"
        "### Relations\n"
        f"{_fmt(relations)}\n\n"
        "### Claims\n"
        f"{_fmt(claims)}\n\n"
        "See `bundle.json` for full data.\n\n"
        "## Citation\n"
        f"Cite as: `Entropy Atlas Snapshot {snapshot_id}, bundle_sha256={bundle_sha256}`\n"
    )
