from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import domain_files, load_yaml, relation_files

DOMAIN_CLOSURE_TYPES = {"effectively_closed", "closed", "open", "unknown"}
EXCHANGE_CHANNELS = {"heat", "work", "matter", "radiation", "information", "chemical", "other"}
RELATION_TYPES = {
    "approximation_limit",
    "coarse_graining",
    "regime_shift",
    "model_reduction",
    "measurement_mapping",
    "equivalence_mapping",
    "composition",
    "coupling",
    "aggregation_rule",
}


def load_domains() -> list[dict]:
    return sorted([load_yaml(path) for path in domain_files()], key=lambda d: d.get("id", ""))


def load_relations() -> list[dict]:
    return sorted([load_yaml(path) for path in relation_files()], key=lambda r: r.get("id", ""))


def validate_choice(value: str | None, valid: set[str], flag: str) -> int:
    if value is None:
        return 0
    if value not in valid:
        print(f"Error: invalid value for {flag}: {value}", file=sys.stderr)
        print(f"Valid values: {', '.join(sorted(valid))}", file=sys.stderr)
        return 1
    return 0


def cmd_list_domains(args: argparse.Namespace) -> int:
    if validate_choice(args.closure_type, DOMAIN_CLOSURE_TYPES, "--closure-type"):
        return 1
    if validate_choice(args.exchange_channel, EXCHANGE_CHANNELS, "--exchange-channel"):
        return 1

    matched = []
    for domain in load_domains():
        boundary = domain.get("boundary", {}) or {}
        system_type = domain.get("system_type", {}) or {}
        context = domain.get("context", {}) or {}

        domain_tags = set(system_type.get("tags", []) or []) | set(context.get("tags", []) or [])
        channels = set(boundary.get("exchange_channels", []) or [])

        if args.closure_type and boundary.get("closure_type") != args.closure_type:
            continue
        if args.system_primary and system_type.get("primary") != args.system_primary:
            continue
        if args.tag and args.tag not in domain_tags:
            continue
        if args.exchange_channel and args.exchange_channel not in channels:
            continue
        matched.append(domain)

    print(f"Domains ({len(matched)}):")
    for domain in matched:
        boundary = domain.get("boundary", {}) or {}
        system_type = domain.get("system_type", {}) or {}
        print(
            f"  - {domain.get('id', '<missing-id>')} "
            f"(closure_type={boundary.get('closure_type', 'unknown')}, "
            f"system_primary={system_type.get('primary', 'unknown')})"
        )
    return 0


def cmd_list_relations(args: argparse.Namespace) -> int:
    if validate_choice(args.type, RELATION_TYPES, "--type"):
        return 1

    matched = []
    for relation in load_relations():
        if args.type and relation.get("relation_type") != args.type:
            continue
        if args.source and relation.get("source_domain_id") != args.source:
            continue
        if args.target and relation.get("target_domain_id") != args.target:
            continue
        matched.append(relation)

    print(f"Relations ({len(matched)}):")
    for relation in matched:
        print(
            f"  - {relation.get('id', '<missing-id>')} "
            f"[{relation.get('relation_type', 'unknown')}] "
            f"{relation.get('source_domain_id', '?')} -> {relation.get('target_domain_id', '?')}"
        )
    return 0


def iter_must_fail_rows(item: dict) -> list[tuple[str, str, str]]:
    rows = []
    for test in item.get("must_fail_tests", []) or []:
        for citation_id in test.get("citations", []) or []:
            rows.append((citation_id, test.get("id", "<missing-test-id>"), test.get("severity", "unknown")))
    return rows


def cmd_find_must_fail_by_citation(args: argparse.Namespace) -> int:
    results = []
    for domain in load_domains():
        for citation_id, test_id, severity in iter_must_fail_rows(domain):
            if citation_id == args.citation_id:
                results.append((domain.get("id", "<missing-id>"), test_id, severity, "domain"))

    for relation in load_relations():
        for citation_id, test_id, severity in iter_must_fail_rows(relation):
            if citation_id == args.citation_id:
                results.append((relation.get("id", "<missing-id>"), test_id, severity, "relation"))

    results.sort(key=lambda x: (x[3], x[0], x[1]))

    print(f"Matches for citation '{args.citation_id}' ({len(results)}):")
    for item_id, test_id, severity, kind in results:
        print(f"  - {kind}_id: {item_id}")
        print(f"    test_id: {test_id}")
        print(f"    severity: {severity}")
    return 0


def print_composition_tree(relations: list[dict]) -> None:
    composition = [r for r in relations if r.get("relation_type") == "composition"]
    if not composition:
        print("  none")
        return

    children = defaultdict(list)
    parents = {}
    for rel in composition:
        source = rel.get("source_domain_id", "?")
        target = rel.get("target_domain_id", "?")
        children[target].append(source)
        parents[source] = target

    for node in children:
        children[node].sort()

    roots = sorted(set(children.keys()) - set(parents.keys()))

    def walk(node: str, depth: int, seen: set[str]) -> None:
        print(f"  {'  ' * depth}- {node}")
        if node in seen:
            print(f"  {'  ' * (depth + 1)}- [cycle]")
            return
        next_seen = set(seen)
        next_seen.add(node)
        for child in children.get(node, []):
            walk(child, depth + 1, next_seen)

    for root in roots:
        walk(root, 0, set())


def cmd_graph_summary(_: argparse.Namespace) -> int:
    domains = load_domains()
    relations = load_relations()

    relation_counts = Counter(r.get("relation_type", "unknown") for r in relations)
    closure_counts = Counter((d.get("boundary", {}) or {}).get("closure_type", "unknown") for d in domains)

    print("Graph summary:")
    print(f"  total_domains: {len(domains)}")
    print(f"  total_relations: {len(relations)}")
    print("  relation_counts_by_type:")
    for relation_type in sorted(relation_counts):
        print(f"    - {relation_type}: {relation_counts[relation_type]}")
    print("  domains_by_closure_type:")
    for closure_type in sorted(closure_counts):
        print(f"    - {closure_type}: {closure_counts[closure_type]}")
    print("  composition_tree:")
    print_composition_tree(relations)
    return 0


def command_help() -> str:
    return (
        "usage: python tools/query.py <command> [options]\n\n"
        "commands:\n"
        "  list-domains [--closure-type ...] [--system-primary ...] [--tag ...] [--exchange-channel ...]\n"
        "  list-relations [--type ...] [--source ...] [--target ...]\n"
        "  find-must-fail-by-citation --citation-id <id>\n"
        "  graph-summary"
    )


def build_command_parser(command: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=f"python tools/query.py {command}")
    if command == "list-domains":
        parser.add_argument("--closure-type")
        parser.add_argument("--system-primary")
        parser.add_argument("--tag")
        parser.add_argument("--exchange-channel")
    elif command == "list-relations":
        parser.add_argument("--type")
        parser.add_argument("--source")
        parser.add_argument("--target")
    elif command == "find-must-fail-by-citation":
        parser.add_argument("--citation-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    commands = {
        "list-domains": cmd_list_domains,
        "list-relations": cmd_list_relations,
        "find-must-fail-by-citation": cmd_find_must_fail_by_citation,
        "graph-summary": cmd_graph_summary,
    }

    if not args:
        print(command_help())
        return 1

    command = args[0]
    if command not in commands:
        print(command_help())
        return 1

    parser = build_command_parser(command)
    parsed = parser.parse_args(args[1:])
    return commands[command](parsed)


if __name__ == "__main__":
    raise SystemExit(main())
