"""Generate a deterministic markdown report for compute cases."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


from .case_runner import load_case, resolve_case_paths, run_case
from entropy_table.core.bindings import CLAIM_ID_RE, parse_claim_ids_from_case_yaml

DEFAULT_REPORT_PATH = Path("outputs/compute_report.md")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run compute cases and emit markdown report")
    parser.add_argument("--case", action="append", dest="cases", help="Path to case YAML")
    parser.add_argument(
        "--scan-dir",
        default="staging/cases/",
        help="Directory of case YAML files to scan (default: staging/cases/)",
    )
    parser.add_argument("--only-failures", action="store_true", help="Show only failing cases in table")
    parser.add_argument("--fail-fast", action="store_true", help="Stop execution after first failing case")
    parser.add_argument("--out", default=str(DEFAULT_REPORT_PATH), help="Report output path")
    return parser


def _sorted_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(results, key=lambda item: (item["case_id"], item["calculator"]))


def _count_constraint_failures(results: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"sigma_min": 0, "sigma_max": 0, "sigma_close": 0}
    for item in results:
        if item["status"] != "fail":
            continue
        for error in item.get("errors", []):
            if "sigma_min" in error:
                counts["sigma_min"] += 1
            elif "sigma_max" in error:
                counts["sigma_max"] += 1
            elif "within" in error:
                counts["sigma_close"] += 1
    return counts


def _citation_ids(case_dicts: list[dict[str, Any]]) -> list[str]:
    citations: set[str] = set()
    for case in case_dicts:
        raw = case.get("citations", [])
        if isinstance(raw, list):
            citations.update(str(item) for item in raw)
    return sorted(citations)


def _claim_reference_counts(case_dicts: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for case in case_dicts:
        for claim_id in parse_claim_ids_from_case_yaml(case):
            counts[claim_id] = counts.get(claim_id, 0) + 1
    return counts


def _discover_atlas_claim_ids() -> set[str]:
    claims_root = Path("atlas/claims")
    if not claims_root.exists() or not claims_root.is_dir():
        return set()
    ids: set[str] = set()
    for path in sorted(claims_root.glob("**/*.yaml")):
        try:
            claim = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(claim, dict):
            continue
        claim_id = claim.get("id")
        if isinstance(claim_id, str) and claim_id:
            ids.add(claim_id)
    return ids


def write_report(
    case_paths: list[str | Path],
    *,
    out_path: str | Path = DEFAULT_REPORT_PATH,
    only_failures: bool = False,
    fail_fast: bool = False,
) -> Path:
    run_items: list[dict[str, Any]] = []
    case_dicts: list[dict[str, Any]] = []
    for path in case_paths:
        case_data = load_case(path)
        case_dicts.append(case_data)
        result = run_case(case_data)
        run_items.append(result)
        if fail_fast and result["status"] == "fail":
            break

    results = _sorted_results(run_items)
    displayed = [item for item in results if item["status"] == "fail"] if only_failures else results
    pass_count = sum(1 for item in results if item["status"] == "pass")
    fail_count = len(results) - pass_count
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    by_calculator: dict[str, dict[str, int]] = {}
    for item in results:
        calc = item["calculator"]
        bucket = by_calculator.setdefault(calc, {"total": 0, "pass": 0, "fail": 0})
        bucket["total"] += 1
        bucket[item["status"]] += 1

    constraint_counts = _count_constraint_failures(results)
    citation_ids = _citation_ids(case_dicts)
    claim_reference_counts = _claim_reference_counts(case_dicts)
    invalid_claim_ids = sorted(claim_id for claim_id in claim_reference_counts if not CLAIM_ID_RE.match(claim_id))
    atlas_claim_ids = _discover_atlas_claim_ids()

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Compute Case Report",
        "",
        f"Generated (UTC): `{timestamp}`",
        "",
        "## Cases",
        "",
        "| case_id | calculator | sigma | status | input_digest | notes |",
        "|---|---|---:|---|---|---|",
    ]
    for item in displayed:
        notes = (item.get("notes") or "").replace("|", "\\|")
        lines.append(
            "| {case_id} | {calculator} | {sigma:.12g} | {status} | `{digest}` | {notes} |".format(
                case_id=item["case_id"],
                calculator=item["calculator"],
                sigma=item["sigma"],
                status=item["status"],
                digest=item["input_digest"],
                notes=notes,
            )
        )

    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Total cases: **{len(results)}**",
            f"- Pass: **{pass_count}**",
            f"- Fail: **{fail_count}**",
            "",
            "### Cases by calculator",
            "",
            "| calculator | total | pass | fail |",
            "|---|---:|---:|---:|",
        ]
    )
    for calculator in sorted(by_calculator):
        counts = by_calculator[calculator]
        lines.append(
            f"| {calculator} | {counts['total']} | {counts['pass']} | {counts['fail']} |"
        )

    lines.extend(
        [
            "",
            "### Constraint types hit",
            "",
            f"- sigma_min failures: **{constraint_counts['sigma_min']}**",
            f"- sigma_max failures: **{constraint_counts['sigma_max']}**",
            f"- sigma_close failures: **{constraint_counts['sigma_close']}**",
            "",
            "### Citation IDs referenced by cases",
            "",
        ]
    )
    if citation_ids:
        lines.extend([f"- `{citation}`" for citation in citation_ids])
    else:
        lines.append("- _(none)_")

    lines.extend(["", "### Claims referenced by cases", ""])
    if claim_reference_counts:
        lines.extend(["| claim_id | cases |", "|---|---:|"])
        for claim_id in sorted(claim_reference_counts):
            lines.append(f"| {claim_id} | {claim_reference_counts[claim_id]} |")
    else:
        lines.append("- _(none)_")

    if invalid_claim_ids:
        lines.extend(["", "Claim linkage warnings:", ""])
        for claim_id in invalid_claim_ids:
            lines.append(f"- invalid claim_id syntax in case linkage: `{claim_id}`")

    if claim_reference_counts and atlas_claim_ids:
        missing_from_atlas = sorted(claim_id for claim_id in claim_reference_counts if claim_id not in atlas_claim_ids)
        if missing_from_atlas:
            lines.extend(["", "Atlas existence warnings:", ""])
            for claim_id in missing_from_atlas:
                lines.append(f"- claim_id referenced by cases but not found in atlas/claims: `{claim_id}`")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> int:
    args = _build_parser().parse_args()
    case_paths = resolve_case_paths(args.cases, args.scan_dir)
    report_path = write_report(
        case_paths,
        out_path=args.out,
        only_failures=args.only_failures,
        fail_fast=args.fail_fast,
    )
    print(f"wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
