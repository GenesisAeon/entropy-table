"""Case management tool: scaffold new cases and validate claim↔case bindings.

Subcommands
-----------
create
    Scaffold a new compute-case YAML from the template, optionally linked to
    an existing claim.  The file is placed at:
        atlas/cases/<category>/<domain_ref>/<case-id>.yaml

validate
    Cross-check every claim's ``evidence.cases`` list against the case files
    actually present in ``atlas/cases/``.  Reports two issue classes:

    Dangling references  – a claim's evidence.cases entry has no corresponding
                          file in atlas/cases/  (always a hard error).
    Orphaned cases       – a case file in atlas/cases/ is not referenced by any
                          claim  (soft warning; promoted to error with --strict).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
ATLAS = ROOT / "atlas"
CLAIMS_DIR = ATLAS / "claims"
CASES_DIR = ATLAS / "cases"
TEMPLATES_DIR = ROOT / "templates"

_CASE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:-v[0-9]+)?$")
_CATEGORY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

SUPPORTED_CALCULATORS = ("ctmc-ep", "diffusion-ep-1d")


# ── helpers ──────────────────────────────────────────────────────────────────


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping at the top level")
    return data


def _claim_files(claims_root: Path) -> list[Path]:
    if not claims_root.exists():
        return []
    return sorted(claims_root.glob("**/*.yaml"))


def _case_files(cases_root: Path) -> list[Path]:
    if not cases_root.exists():
        return []
    return sorted(cases_root.glob("**/*.yaml"))


def _case_ids_from_claim(claim: dict[str, Any]) -> list[str]:
    """Return the list of case IDs referenced in *claim.evidence.cases*."""
    evidence = claim.get("evidence")
    if not isinstance(evidence, dict):
        return []
    raw = evidence.get("cases")
    if not isinstance(raw, list):
        return []
    result: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
        elif isinstance(item, dict):
            cid = item.get("id")
            if isinstance(cid, str) and cid.strip():
                result.append(cid.strip())
    return result


# ── create ───────────────────────────────────────────────────────────────────


def cmd_create(args: argparse.Namespace) -> int:
    case_id: str = args.id
    if not _CASE_ID_RE.match(case_id):
        print(
            f"error: '{case_id}' is not a valid case ID "
            "(kebab-case with optional -vNN suffix, e.g. 'ctmc-3cycle-v01')",
            file=sys.stderr,
        )
        return 1

    calculator: str = args.calculator
    if calculator not in SUPPORTED_CALCULATORS:
        print(
            f"error: unsupported calculator '{calculator}'. "
            f"Choose from: {', '.join(SUPPORTED_CALCULATORS)}",
            file=sys.stderr,
        )
        return 1

    # ── resolve category + domain_ref ──
    if args.claim_file:
        claim_path = Path(args.claim_file)
        if not claim_path.exists():
            print(f"error: claim file not found: {claim_path}", file=sys.stderr)
            return 1
        try:
            claim_data = _load_yaml(claim_path)
        except Exception as exc:
            print(f"error: could not parse claim file: {exc}", file=sys.stderr)
            return 1
        domain_ref: str = str(claim_data.get("domain_ref", "")).strip()
        if not domain_ref:
            print(
                f"error: claim file has no 'domain_ref' field: {claim_path}",
                file=sys.stderr,
            )
            return 1
        # Infer category from file path relative to CLAIMS_DIR
        try:
            rel = claim_path.resolve().relative_to(CLAIMS_DIR.resolve())
            category: str = rel.parts[0]
        except ValueError:
            category = args.category
    else:
        if not args.domain:
            print(
                "error: --domain is required when --claim-file is not provided",
                file=sys.stderr,
            )
            return 1
        domain_ref = args.domain
        category = args.category
        claim_data = None

    if not _CATEGORY_RE.match(category):
        print(
            f"error: '{category}' is not a valid category name (e.g. '01_physics')",
            file=sys.stderr,
        )
        return 1

    template_path = TEMPLATES_DIR / "case_template.yaml"
    if not template_path.exists():
        print(f"error: case template not found: {template_path}", file=sys.stderr)
        return 1

    target_dir = CASES_DIR / category / domain_ref
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / f"{case_id}.yaml"
    if target_path.exists():
        print(f"error: case file already exists: {target_path}", file=sys.stderr)
        return 1

    content = template_path.read_text(encoding="utf-8")

    # Replace the id placeholder (matches quoted and unquoted values)
    content = re.sub(
        r"^id:\s*.*$",
        f'id: "{case_id}"',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    # Replace the calculator placeholder
    content = re.sub(
        r"^calculator:\s*.*$",
        f"calculator: {calculator}",
        content,
        count=1,
        flags=re.MULTILINE,
    )

    target_path.write_text(content, encoding="utf-8")

    try:
        display_path = target_path.relative_to(ROOT)
    except ValueError:
        display_path = target_path
    print(f"created: {display_path}")
    print("fill in every <TODO:...> field before committing.")

    if args.claim_file and claim_data is not None:
        claim_id = str(claim_data.get("id", "")).strip()
        print(
            f"\nTo link this case to the claim, add the case ID to\n"
            f"  evidence.cases in {args.claim_file}"
        )
        if claim_id:
            print(
                f"\nTo add the back-reference in the case file:\n"
                f"  claims: [{claim_id}]"
            )

    return 0


# ── validate ─────────────────────────────────────────────────────────────────


def cmd_validate(args: argparse.Namespace) -> int:
    claims_root = Path(args.claims_root)
    cases_root = Path(args.cases_root)

    # Collect every case ID referenced by any claim
    # claim_refs: case_id -> [list of claim file paths that reference it]
    claim_refs: dict[str, list[str]] = {}
    for claim_path in _claim_files(claims_root):
        try:
            claim_data = _load_yaml(claim_path)
        except Exception as exc:
            print(f"warning: could not parse {claim_path}: {exc}", file=sys.stderr)
            continue
        for cid in _case_ids_from_claim(claim_data):
            claim_refs.setdefault(cid, []).append(str(claim_path))

    # Collect every case ID present as a file in atlas/cases/
    # file_cases: case_id -> Path of the case file
    file_cases: dict[str, Path] = {}
    for case_path in _case_files(cases_root):
        try:
            case_data = _load_yaml(case_path)
            cid = case_data.get("id")
            if isinstance(cid, str) and cid.strip():
                file_cases[cid.strip()] = case_path
            else:
                print(f"warning: {case_path} has no valid 'id' field", file=sys.stderr)
        except Exception as exc:
            print(f"warning: could not parse {case_path}: {exc}", file=sys.stderr)

    # ── classify issues ──
    dangling: list[tuple[str, list[str]]] = [
        (cid, refs)
        for cid, refs in sorted(claim_refs.items())
        if cid not in file_cases
    ]
    orphaned: list[tuple[str, Path]] = [
        (cid, path)
        for cid, path in sorted(file_cases.items())
        if cid not in claim_refs
    ]

    if dangling:
        print(f"DANGLING CASE REFERENCES ({len(dangling)} found):")
        for cid, refs in dangling:
            print(f"  {cid}")
            for ref in refs:
                print(f"    <- {ref}")

    if orphaned:
        print(f"ORPHANED CASES ({len(orphaned)} found):")
        for cid, path in orphaned:
            try:
                display = path.relative_to(ROOT)
            except ValueError:
                display = path
            print(f"  {cid}  ({display})")

    if not dangling and not orphaned:
        print(
            f"Case validation passed: "
            f"{len(file_cases)} case(s), {len(claim_refs)} reference(s), no issues."
        )
        return 0

    exit_code = 0
    summary: list[str] = []

    if dangling:
        summary.append(f"{len(dangling)} dangling reference(s)")
        exit_code = 1

    if orphaned:
        summary.append(f"{len(orphaned)} orphaned case(s)")
        if args.strict:
            exit_code = 1

    verdict = "failed" if exit_code else "passed with warnings"
    print(f"\nCase validation {verdict}: {', '.join(summary)}.")
    return exit_code


# ── CLI ──────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Manage compute cases: scaffold new cases and validate claim↔case bindings.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join([
            "examples:",
            "  python tools/manage_cases.py create ctmc-3cycle-v01 \\",
            "      --claim-file atlas/claims/01_physics/ctmc-schnakenberg/claim-schnakenberg-ep-rate-definition.yaml",
            "  python tools/manage_cases.py create ctmc-3cycle-v01 --domain ctmc-schnakenberg",
            "  python tools/manage_cases.py validate",
            "  python tools/manage_cases.py validate --strict",
        ]),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── create ──
    create_p = subparsers.add_parser(
        "create",
        help="Scaffold a new case YAML from the template.",
    )
    create_p.add_argument(
        "id",
        help="Case ID in kebab-case with optional -vNN suffix, e.g. 'ctmc-3cycle-v01'.",
    )
    create_p.add_argument(
        "--claim-file",
        metavar="PATH",
        help="Path to an existing claim YAML; infers category and domain_ref from it.",
    )
    create_p.add_argument(
        "--domain",
        metavar="DOMAIN",
        help="Domain ID (required when --claim-file is not provided).",
    )
    create_p.add_argument(
        "--category",
        default="01_physics",
        help="Category subdirectory under atlas/cases/ (default: 01_physics).",
    )
    create_p.add_argument(
        "--calculator",
        default="ctmc-ep",
        choices=list(SUPPORTED_CALCULATORS),
        help="Calculator type (default: ctmc-ep).",
    )
    create_p.set_defaults(func=cmd_create)

    # ── validate ──
    validate_p = subparsers.add_parser(
        "validate",
        help="Cross-check claim evidence.cases references against atlas/cases/ files.",
    )
    validate_p.add_argument(
        "--claims-root",
        default=str(CLAIMS_DIR),
        metavar="PATH",
        help=f"Root directory for claim YAML files (default: atlas/claims).",
    )
    validate_p.add_argument(
        "--cases-root",
        default=str(CASES_DIR),
        metavar="PATH",
        help=f"Root directory for case YAML files (default: atlas/cases).",
    )
    validate_p.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero for orphaned cases (no claim reference) in addition to dangling references.",
    )
    validate_p.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
