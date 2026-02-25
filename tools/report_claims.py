from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from query_claims import load_claims

OUTPUT_PATH = Path("outputs/claims_report.md")


def build_report() -> str:
    claims = load_claims()
    by_kind = Counter(str(claim.get("claim_kind", "unknown")) for claim in claims)
    by_status = Counter(str(claim.get("status", "unknown")) for claim in claims)

    grouped: dict[str, list[dict]] = defaultdict(list)
    for claim in claims:
        grouped[str(claim.get("domain_ref", "unknown"))].append(claim)

    for domain_ref in grouped:
        grouped[domain_ref].sort(key=lambda c: str(c.get("id", "")))

    stable_without_refs = [
        claim
        for claim in claims
        if claim.get("status") == "stable"
        and len(((claim.get("falsification") or {}).get("must_fail_refs") or [])) == 0
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
        lines.append("| Claim ID | Title | Kind | Status |")
        lines.append("|---|---|---|---|")
        for claim in grouped[domain_ref]:
            lines.append(
                f"| {claim.get('id', '')} | {claim.get('title', '')} | "
                f"{claim.get('claim_kind', '')} | {claim.get('status', '')} |"
            )
        lines.append("")

    lines.extend(["## Stability sanity checks", ""])
    if stable_without_refs:
        lines.append("Stable claims with no `must_fail_refs` (should be empty):")
        lines.append("")
        for claim in sorted(stable_without_refs, key=lambda c: str(c.get("id", ""))):
            lines.append(f"- {claim.get('id', '<missing-id>')} ({claim.get('domain_ref', 'unknown')})")
    else:
        lines.append("No stable claims without `must_fail_refs` found.")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_report(), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
