"""Generate a deterministic markdown report for compute cases."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from tools.compute.case_runner import run_cases

REPORT_PATH = Path("outputs/compute_report.md")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run compute cases and emit markdown report")
    parser.add_argument("--case", action="append", dest="cases", required=True, help="Path to case YAML")
    return parser


def write_report(case_paths: list[str]) -> Path:
    results = sorted(run_cases(case_paths), key=lambda item: item["case_id"])
    pass_count = sum(1 for item in results if item["status"] == "pass")
    fail_count = len(results) - pass_count
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
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
    for item in results:
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
        ]
    )

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return REPORT_PATH


def main() -> int:
    args = _build_parser().parse_args()
    report_path = write_report(args.cases)
    print(f"wrote {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
