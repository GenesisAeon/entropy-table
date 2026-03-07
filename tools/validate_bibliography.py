from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import ROOT, load_yaml

TARGET_SUBDIRS = ("domains", "relations", "claims")
FAIL_STATUSES = {"stable", "review"}
WARN_STATUSES = {"draft"}

_DOI_USER_AGENT = "entropy-table-ci/1.0 (https://github.com/entropy-table/entropy-table)"


def verify_doi(doi: str, retries: int = 3) -> bool:
    """Return True if *doi* resolves successfully via doi.org HEAD request.

    Uses exponential backoff on transient errors (5xx, connection issues).
    Returns False immediately on a definitive 404.
    """
    url = f"https://doi.org/{doi}"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url,
                method="HEAD",
                headers={"User-Agent": _DOI_USER_AGENT},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                return resp.status in (200, 301, 302)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return False
            # 429 / 5xx — back off and retry
        except urllib.error.URLError:
            pass  # network error — retry
        if attempt < retries - 1:
            time.sleep(2 ** attempt)
    return False


def verify_dois_in_refs(refs: dict, *, verbose: bool = False) -> list[str]:
    """Return a list of error strings for every DOI in *refs* that cannot be resolved."""
    errors: list[str] = []
    total = sum(1 for v in refs.values() if isinstance(v, dict) and v.get("doi"))
    checked = 0
    for ref_id, data in refs.items():
        if not isinstance(data, dict):
            continue
        doi = data.get("doi")
        if not doi:
            continue
        checked += 1
        if verbose:
            print(f"  [{checked}/{total}] Checking DOI for '{ref_id}': {doi}", flush=True)
        if not verify_doi(str(doi)):
            errors.append(
                f"refs.yaml: citation '{ref_id}' has an unresolvable DOI: {doi}"
            )
    return errors


def load_bibliography_ids(refs_path: Path) -> set[str]:
    refs = load_yaml(refs_path)
    return set(refs.keys())


def discover_yaml_files(atlas_root: Path) -> list[Path]:
    files: list[Path] = []
    for subdir in TARGET_SUBDIRS:
        files.extend(sorted((atlas_root / subdir).glob("**/*.yaml")))
    return files


def collect_citation_refs(payload: Any) -> set[str]:
    refs: set[str] = set()

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "citations" and isinstance(value, list):
                    for item in value:
                        if isinstance(item, str) and item.strip():
                            refs.add(item)
                _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(payload)
    return refs


def validate_file(path: Path, known_refs: set[str]) -> tuple[list[str], list[str]]:
    payload = load_yaml(path)
    citations = collect_citation_refs(payload)
    missing = sorted(ref for ref in citations if ref not in known_refs)
    if not missing:
        return [], []

    status = payload.get("status")
    prefix = f"{path}: unknown citation id(s) {missing}"

    if status in FAIL_STATUSES:
        return [f"{prefix} (status={status})"], []
    if status in WARN_STATUSES:
        return [], [f"{prefix} (status={status})"]
    return [f"{prefix} (status={status!r}; expected one of draft/review/stable)"], []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate citation IDs against atlas bibliography SSOT")
    parser.add_argument("--atlas-root", default="atlas", help="Atlas root containing domains/relations/claims")
    parser.add_argument(
        "--refs",
        default="atlas/bibliography/refs.yaml",
        help="Bibliography YAML mapping citation IDs to metadata",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument(
        "--verify-dois",
        action="store_true",
        help="Perform live HTTP HEAD checks on every DOI in refs.yaml (requires network access)",
    )
    args = parser.parse_args(argv)

    atlas_root = Path(args.atlas_root)
    refs_path = Path(args.refs)
    if not atlas_root.is_absolute():
        atlas_root = ROOT / atlas_root
    if not refs_path.is_absolute():
        refs_path = ROOT / refs_path

    refs_data = load_yaml(refs_path)
    known_refs: set[str] = set(refs_data.keys())
    yaml_paths = discover_yaml_files(atlas_root)

    errors: list[str] = []
    warnings: list[str] = []

    # Optional live DOI verification (CI-only, behind flag)
    if args.verify_dois:
        if not args.json:
            print(f"Verifying DOIs for {sum(1 for v in refs_data.values() if isinstance(v, dict) and v.get('doi'))} entries in refs.yaml …")
        doi_errors = verify_dois_in_refs(refs_data, verbose=not args.json)
        errors.extend(doi_errors)

    for path in yaml_paths:
        path_errors, path_warnings = validate_file(path, known_refs)
        errors.extend(path_errors)
        warnings.extend(path_warnings)

    summary = {
        "files_scanned": len(yaml_paths),
        "known_citations": len(known_refs),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "valid": len(errors) == 0,
    }

    if args.json:
        output = {
            "summary": summary,
            "errors": errors,
            "warnings": warnings,
        }
        print(json.dumps(output, indent=2))
    else:
        if warnings:
            print(f"Bibliography validation warnings ({len(warnings)}):")
            for warning in warnings:
                print(f" - WARNING: {warning}")

        if errors:
            print(f"Bibliography validation failed with {len(errors)} error(s):")
            for error in errors:
                print(f" - {error}")
            return 1

        print(
            f"Bibliography validation passed: {len(yaml_paths)} files scanned, "
            f"{len(known_refs)} known citation id(s)."
        )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
