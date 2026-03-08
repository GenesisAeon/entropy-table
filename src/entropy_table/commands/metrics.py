from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import yaml

import sys

from entropy_table.core.common import domain_files, load_yaml, relation_files

INDEX_PATH = Path("cache/index.json")
DEFAULT_JSON_OUT = Path("cache/metrics.json")
DEFAULT_MD_OUT = Path("outputs/metrics.md")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute operational atlas metrics")
    parser.add_argument("--json-out", default=str(DEFAULT_JSON_OUT))
    parser.add_argument("--md-out", default=str(DEFAULT_MD_OUT))
    return parser.parse_args(argv)


def load_index() -> dict | None:
    if not INDEX_PATH.exists():
        return None
    try:
        data = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def load_domains_and_relations() -> tuple[list[dict], list[dict]]:
    domains = sorted([load_yaml(path) for path in domain_files()], key=lambda item: item.get("id", ""))
    relations = sorted([load_yaml(path) for path in relation_files()], key=lambda item: item.get("id", ""))
    return domains, relations


def _relation_type_counts_for_domain(domain_id: str, relations: list[dict]) -> tuple[Counter, int, int]:
    relation_type_counts: Counter = Counter()
    outgoing = 0
    incoming = 0

    for relation in relations:
        relation_type = relation.get("relation_type", "unknown")
        if relation.get("source_domain_id") == domain_id:
            outgoing += 1
            relation_type_counts[relation_type] += 1
        if relation.get("target_domain_id") == domain_id:
            incoming += 1
            relation_type_counts[relation_type] += 1

    return relation_type_counts, outgoing, incoming


def _closure_risk(domain: dict, relation_type_counts: Counter) -> tuple[int, str]:
    score = 0
    reasons: list[str] = []

    closure_type = ((domain.get("boundary") or {}).get("closure_type"))
    if closure_type == "effectively_closed":
        score += 2
        reasons.append("closure_type=effectively_closed (+2)")

    exchange_channels = set(((domain.get("boundary") or {}).get("exchange_channels") or []))
    if "information" in exchange_channels:
        score += 1
        reasons.append("information exchange channel present (+1)")

    limitations = domain.get("limitations") or []
    if isinstance(limitations, list) and len(limitations) >= 2:
        score += 1
        reasons.append("limitations count >= 2 (+1)")

    if relation_type_counts.get("regime_shift", 0) > 0 or relation_type_counts.get("coarse_graining", 0) > 0:
        score += 1
        reasons.append("regime_shift or coarse_graining relation present (+1)")

    if not reasons:
        reasons.append("no heuristic risk triggers")

    return score, "; ".join(reasons)


def compute_metrics(domains: list[dict], relations: list[dict]) -> dict:
    per_domain: dict[str, dict] = {}

    for domain in domains:
        domain_id = domain.get("id")
        if not isinstance(domain_id, str) or not domain_id:
            continue

        tests = [item for item in (domain.get("must_fail_tests") or []) if isinstance(item, dict)]
        hard_test_count = sum(1 for test in tests if test.get("severity") == "hard")
        soft_test_count = sum(1 for test in tests if test.get("severity") == "soft")

        citation_count = len(
            [citation for citation in (domain.get("citations") or []) if isinstance(citation, dict) and citation.get("id")]
        )

        relation_type_counts, outgoing_count, incoming_count = _relation_type_counts_for_domain(domain_id, relations)

        closure_risk_score, closure_risk_explanation = _closure_risk(domain, relation_type_counts)

        per_domain[domain_id] = {
            "hard_test_count": hard_test_count,
            "soft_test_count": soft_test_count,
            "citation_count": citation_count,
            "outgoing_relation_count": outgoing_count,
            "incoming_relation_count": incoming_count,
            "relation_type_counts": {
                relation_type: relation_type_counts[relation_type]
                for relation_type in sorted(relation_type_counts)
            },
            "closure_risk": {
                "score": closure_risk_score,
                "explanation": closure_risk_explanation,
            },
            "coverage": {
                "has_boundary": isinstance(domain.get("boundary"), dict),
                "has_entropy_accounting": isinstance(domain.get("entropy_accounting"), dict),
                "has_entropy_definition": isinstance(domain.get("entropy_definition"), dict),
                "has_operators": isinstance(domain.get("operators"), dict),
            },
        }

    return {
        "disclaimer": "Operational heuristics only; these metrics are reporting aids and not physics truth claims.",
        "domain_count": len(per_domain),
        "domains": {domain_id: per_domain[domain_id] for domain_id in sorted(per_domain)},
    }


def render_markdown(metrics: dict, used_index: bool) -> str:
    lines = [
        "# Atlas Metrics",
        "",
        "_Disclaimer: metrics are operational heuristics for analysis/reporting and not physics truth claims._",
        "",
        f"- Domains: {metrics.get('domain_count', 0)}",
        f"- Index cache observed: {'yes' if used_index else 'no'}",
        "",
        "## Per-domain metrics",
        "",
    ]

    for domain_id, row in (metrics.get("domains") or {}).items():
        lines.append(f"### `{domain_id}`")
        lines.append(f"- hard_test_count: {row.get('hard_test_count', 0)}")
        lines.append(f"- soft_test_count: {row.get('soft_test_count', 0)}")
        lines.append(f"- citation_count: {row.get('citation_count', 0)}")
        lines.append(f"- outgoing_relation_count: {row.get('outgoing_relation_count', 0)}")
        lines.append(f"- incoming_relation_count: {row.get('incoming_relation_count', 0)}")
        lines.append("- relation_type_counts:")
        relation_type_counts = row.get("relation_type_counts") or {}
        if relation_type_counts:
            for relation_type in sorted(relation_type_counts):
                lines.append(f"  - {relation_type}: {relation_type_counts[relation_type]}")
        else:
            lines.append("  - none")

        closure_risk = row.get("closure_risk") or {}
        lines.append(
            f"- closure_risk: {closure_risk.get('score', 0)} ({closure_risk.get('explanation', 'no explanation')})"
        )

        coverage = row.get("coverage") or {}
        lines.append("- coverage:")
        for key in ["has_boundary", "has_entropy_accounting", "has_entropy_definition", "has_operators"]:
            lines.append(f"  - {key}: {bool(coverage.get(key, False))}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # Optional index use signal for reproducibility diagnostics.
    index = load_index()
    used_index = index is not None

    try:
        domains, relations = load_domains_and_relations()
    except (yaml.YAMLError, OSError, ValueError) as exc:
        print(f"Error loading atlas data: {exc}", file=sys.stderr)
        return 1

    metrics = compute_metrics(domains, relations)

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)

    json_out.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_out.write_text(render_markdown(metrics, used_index), encoding="utf-8")

    print(f"Wrote metrics JSON: {json_out}")
    print(f"Wrote metrics Markdown: {md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
