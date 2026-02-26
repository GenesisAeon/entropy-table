from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from query_claims import load_claims
from bindings import parse_case_ids_from_claim_yaml

OUTPUT_PATH = Path("outputs/claims_report.md")


def build_report() -> str:
    claims = load_claims()
    by_kind = Counter(str(claim.get("claim_kind", "unknown")) for claim in claims)
    by_status = Counter(str(claim.get("status", "unknown")) for claim in claims)

    stable_claims = [claim for claim in claims if claim.get("status") == "stable"]
    review_claims = [claim for claim in claims if claim.get("status") == "review"]
    stable_with_cases = [claim for claim in stable_claims if len(parse_case_ids_from_claim_yaml(claim)) > 0]
    stable_without_cases = [claim for claim in stable_claims if len(parse_case_ids_from_claim_yaml(claim)) == 0]
    review_with_cases = [claim for claim in review_claims if len(parse_case_ids_from_claim_yaml(claim)) > 0]

    grouped: dict[str, list[dict]] = defaultdict(list)
    for claim in claims:
        grouped[str(claim.get("domain_ref", "unknown"))].append(claim)

    for domain_ref in grouped:
        grouped[domain_ref].sort(key=lambda c: str(c.get("id", "")))

    stable_without_falsification_refs = [
        claim
        for claim in claims
        if claim.get("status") == "stable"
        and len(((claim.get("falsification") or {}).get("must_fail_refs") or [])) == 0
    ]
    stable_without_citations = [
        claim
        for claim in claims
        if claim.get("status") == "stable"
        and len(((claim.get("evidence") or {}).get("citations") or [])) == 0
    ]

    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lines: list[str] = [
        "# Claims Report",
        "",
        f"Generated at: `{timestamp}`",
        "",
        "## Summary",
        "",
        f"- Total claims: **{len(claims)}**",
        f"- Stable claims total: **{len(stable_claims)}**",
        f"- Stable claims with >=1 cases: **{len(stable_with_cases)}**",
        f"- Stable claims with 0 cases: **{len(stable_without_cases)}**",
        f"- Review claims with >=1 cases: **{len(review_with_cases)}**",
        "",
        "### Claims by kind",
        "",
        "| Kind | Count |",
        "|---|---:|",
    ]

    for kind in sorted(by_kind):
        lines.append(f"| {kind} | {by_kind[kind]} |")

    lines.extend(["", "### Claims by status", "", "| Status | Count |", "|---|---:|"])
    for status in sorted(by_status):
        lines.append(f"| {status} | {by_status[status]} |")

    lines.extend(["", "## Per-domain claims", ""])

    for domain_ref in sorted(grouped):
        lines.append(f"### {domain_ref}")
        lines.append("")
        lines.append("| Claim ID | Title | Kind | Status | cases_count | cases_preview |")
        lines.append("|---|---|---|---|---:|---|")
        for claim in grouped[domain_ref]:
            case_ids = parse_case_ids_from_claim_yaml(claim)
            case_preview = ", ".join(case_ids[:3]) if case_ids else ""
            lines.append(
                f"| {claim.get('id', '')} | {claim.get('title', '')} | "
                f"{claim.get('claim_kind', '')} | {claim.get('status', '')} | "
                f"{len(case_ids)} | {case_preview} |"
            )
        lines.append("")

    lines.extend(["## Stability sanity checks", ""])
    if stable_without_falsification_refs:
        lines.append("Stable claims with no `must_fail_refs` (should be empty):")
        lines.append("")
        for claim in sorted(stable_without_falsification_refs, key=lambda c: str(c.get("id", ""))):
            lines.append(f"- {claim.get('id', '<missing-id>')} ({claim.get('domain_ref', 'unknown')})")
    else:
        lines.append("No stable claims without `must_fail_refs` found.")

    lines.extend(["", "## Coverage Warnings", ""])
    if stable_without_cases:
        lines.append("Stable claims with no `evidence.cases`:")
        lines.append("")
        for claim in sorted(stable_without_cases, key=lambda c: str(c.get("id", ""))):
            lines.append(f"- {claim.get('id', '<missing-id>')} ({claim.get('domain_ref', 'unknown')})")
    else:
        lines.append("No stable claims without `evidence.cases` found.")

    lines.append("")
    if stable_without_citations:
        lines.append("Stable claims with no `evidence.citations` (sanity check):")
        lines.append("")
        for claim in sorted(stable_without_citations, key=lambda c: str(c.get("id", ""))):
            lines.append(f"- {claim.get('id', '<missing-id>')} ({claim.get('domain_ref', 'unknown')})")
    else:
        lines.append("No stable claims without `evidence.citations` found.")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_report(), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
