from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import ROOT, load_yaml

DEFAULT_REPORT_PATH = Path("outputs/atlas_health.md")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze atlas graph health and coverage gaps")
    parser.add_argument("--atlas-root", default="atlas", help="Atlas root directory")
    parser.add_argument("--out", default=str(DEFAULT_REPORT_PATH), help="Markdown report output path")
    parser.add_argument(
        "--ci-check",
        action="store_true",
        help="Exit with code 1 when stable claims are unfalsifiable or uncited",
    )
    return parser.parse_args(argv)


def _resolve_path(path_arg: str, *, base: Path) -> Path:
    path = Path(path_arg)
    if path.is_absolute():
        return path
    return base / path


def _yaml_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.glob("**/*.yaml"))


def _load_items(paths: list[Path]) -> list[dict]:
    return [load_yaml(path) for path in paths]


def analyze_health(atlas_root: Path) -> dict:
    domain_paths = _yaml_files(atlas_root / "domains")
    relation_paths = _yaml_files(atlas_root / "relations")
    claim_paths = _yaml_files(atlas_root / "claims")

    domains = _load_items(domain_paths)
    relations = _load_items(relation_paths)
    claims = _load_items(claim_paths)

    domain_ids_to_paths: dict[str, Path] = {}
    for path, domain in zip(domain_paths, domains):
        domain_id = domain.get("id")
        if isinstance(domain_id, str) and domain_id:
            domain_ids_to_paths[domain_id] = path

    connected_domain_ids: set[str] = set()
    regime_shift_connected_ids: set[str] = set()
    for relation in relations:
        src = relation.get("source_domain_id")
        tgt = relation.get("target_domain_id")
        if isinstance(src, str) and src:
            connected_domain_ids.add(src)
        if isinstance(tgt, str) and tgt:
            connected_domain_ids.add(tgt)

        if relation.get("relation_type") == "regime_shift":
            if isinstance(src, str) and src:
                regime_shift_connected_ids.add(src)
            if isinstance(tgt, str) and tgt:
                regime_shift_connected_ids.add(tgt)

    orphaned_domains: list[dict] = []
    missing_regime_shifts: list[dict] = []

    for domain in domains:
        domain_id = domain.get("id")
        if not isinstance(domain_id, str) or not domain_id:
            continue

        domain_path = domain_ids_to_paths.get(domain_id)
        limitations = domain.get("limitations")
        assumptions = domain.get("assumptions")
        has_limits_or_assumptions = (
            isinstance(limitations, list)
            and len([item for item in limitations if isinstance(item, str) and item.strip()]) > 0
        ) or (
            isinstance(assumptions, list)
            and len([item for item in assumptions if isinstance(item, str) and item.strip()]) > 0
        )

        if domain_id not in connected_domain_ids:
            orphaned_domains.append({"id": domain_id, "path": domain_path})

        if has_limits_or_assumptions and domain_id not in regime_shift_connected_ids:
            missing_regime_shifts.append({"id": domain_id, "path": domain_path})

    unfalsifiable_stable_claims: list[dict] = []
    uncited_stable_claims: list[dict] = []

    for path, claim in zip(claim_paths, claims):
        if claim.get("status") != "stable":
            continue

        evidence = claim.get("evidence")
        cases: list[str] = []
        citations: list[str] = []
        if isinstance(evidence, dict):
            raw_cases = evidence.get("cases")
            if isinstance(raw_cases, list):
                cases = [case for case in raw_cases if isinstance(case, str) and case.strip()]

            raw_citations = evidence.get("citations")
            if isinstance(raw_citations, list):
                citations = [citation for citation in raw_citations if isinstance(citation, str) and citation.strip()]

        row = {"id": claim.get("id", "<missing-id>"), "path": path}

        if len(cases) == 0:
            unfalsifiable_stable_claims.append(row)
        if len(citations) == 0:
            uncited_stable_claims.append(row)

    return {
        "total_domains": len(domain_ids_to_paths),
        "total_relations": len(relations),
        "total_claims": len(claims),
        "orphaned_domains": sorted(orphaned_domains, key=lambda item: item["id"]),
        "missing_regime_shifts": sorted(missing_regime_shifts, key=lambda item: item["id"]),
        "unfalsifiable_stable_claims": sorted(unfalsifiable_stable_claims, key=lambda item: str(item["id"])),
        "uncited_stable_claims": sorted(uncited_stable_claims, key=lambda item: str(item["id"])),
    }


def _render_table(rows: list[dict]) -> list[str]:
    if not rows:
        return ["_None._", ""]
    lines = ["| ID | File |", "| --- | --- |"]
    for row in rows:
        path = row.get("path")
        lines.append(f"| `{row.get('id', '<missing-id>')}` | `{path}` |")
    lines.append("")
    return lines


def render_markdown(report: dict) -> str:
    lines = [
        "# Atlas Graph Health & Coverage Report",
        "",
        "## Summary",
        "",
        f"- Total Domains: {report['total_domains']}",
        f"- Total Relations: {report['total_relations']}",
        f"- Total Claims: {report['total_claims']}",
        f"- Orphaned Domains: {len(report['orphaned_domains'])}",
        f"- Missing Regime Shifts: {len(report['missing_regime_shifts'])}",
        f"- Unfalsifiable Stable Claims: {len(report['unfalsifiable_stable_claims'])}",
        f"- Uncited Stable Claims: {len(report['uncited_stable_claims'])}",
        "",
        "## Orphaned Domains",
        "",
        "Domains not referenced as `source_domain_id` or `target_domain_id` in any relation.",
        "",
    ]
    lines.extend(_render_table(report["orphaned_domains"]))
    lines.extend(
        [
            "## Missing Regime Shifts",
            "",
            "Domains with listed `limitations` or `assumptions` but no connected `regime_shift` relation.",
            "",
        ]
    )
    lines.extend(_render_table(report["missing_regime_shifts"]))
    lines.extend(
        [
            "## Unfalsifiable Stable Claims",
            "",
            "Stable claims with no linked `evidence.cases` entries.",
            "",
        ]
    )
    lines.extend(_render_table(report["unfalsifiable_stable_claims"]))
    lines.extend(
        [
            "## Uncited Stable Claims",
            "",
            "Stable claims with missing or empty `evidence.citations`.",
            "",
        ]
    )
    lines.extend(_render_table(report["uncited_stable_claims"]))
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    atlas_root = _resolve_path(args.atlas_root, base=ROOT)
    output_path = _resolve_path(args.out, base=ROOT)

    report = analyze_health(atlas_root)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"Wrote atlas health report: {output_path}")

    ci_failures = len(report["unfalsifiable_stable_claims"]) + len(report["uncited_stable_claims"])
    if args.ci_check and ci_failures > 0:
        print("CI check failed: stable claim integrity issues detected.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
