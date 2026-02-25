from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import ROOT, load_yaml

CLAIMS_ROOT = ROOT / "atlas" / "claims"


def load_claims(claims_root: Path = CLAIMS_ROOT) -> list[dict]:
    claims: list[dict] = []
    for path in sorted(claims_root.glob("**/*.yaml")):
        claim = load_yaml(path)
        claim["_path"] = path
        claims.append(claim)
    claims.sort(key=lambda c: (str(c.get("domain_ref", "")), str(c.get("id", ""))))
    return claims


def cmd_list_claims(args: argparse.Namespace) -> int:
    claims = []
    for claim in load_claims():
        if args.domain and claim.get("domain_ref") != args.domain:
            continue
        if args.kind and claim.get("claim_kind") != args.kind:
            continue
        if args.status and claim.get("status") != args.status:
            continue
        if args.tag and args.tag not in (claim.get("tags") or []):
            continue
        claims.append(claim)

    print(f"Claims ({len(claims)}):")
    for claim in claims:
        print(
            f"  - {claim.get('id', '<missing-id>')} "
            f"[{claim.get('claim_kind', 'unknown')}] "
            f"domain={claim.get('domain_ref', 'unknown')} "
            f"status={claim.get('status', 'unknown')}"
        )
    return 0


def cmd_find_claims_by_citation(args: argparse.Namespace) -> int:
    matches: list[dict] = []
    for claim in load_claims():
        citations = ((claim.get("evidence") or {}).get("citations") or [])
        if args.citation_id in citations:
            matches.append(claim)

    matches.sort(key=lambda c: (str(c.get("domain_ref", "")), str(c.get("id", ""))))

    print(f"Matches for citation '{args.citation_id}' ({len(matches)}):")
    for claim in matches:
        print(
            f"  - {claim.get('id', '<missing-id>')} "
            f"[{claim.get('claim_kind', 'unknown')}] "
            f"domain={claim.get('domain_ref', 'unknown')}"
        )
    return 0


def cmd_graph_summary(_: argparse.Namespace) -> int:
    claims = load_claims()
    by_kind = Counter(str(claim.get("claim_kind", "unknown")) for claim in claims)
    by_status = Counter(str(claim.get("status", "unknown")) for claim in claims)
    by_domain = Counter(str(claim.get("domain_ref", "unknown")) for claim in claims)

    print("Claim graph summary:")
    print(f"  total_claims: {len(claims)}")
    print("  claims_by_kind:")
    for kind in sorted(by_kind):
        print(f"    - {kind}: {by_kind[kind]}")
    print("  claims_by_status:")
    for status in sorted(by_status):
        print(f"    - {status}: {by_status[status]}")
    print("  top_domains_by_claim_count:")
    for domain, count in sorted(by_domain.items(), key=lambda row: (-row[1], row[0])):
        print(f"    - {domain}: {count}")
    return 0


def command_help() -> str:
    return (
        "usage: python tools/query_claims.py <command> [options]\n\n"
        "commands:\n"
        "  list-claims [--domain <domain_id>] [--kind <claim_kind>] [--status <status>] [--tag <tag>]\n"
        "  find-claims-by-citation --citation-id <id>\n"
        "  graph-summary"
    )


def build_parser(command: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=f"python tools/query_claims.py {command}")
    if command == "list-claims":
        parser.add_argument("--domain")
        parser.add_argument("--kind")
        parser.add_argument("--status")
        parser.add_argument("--tag")
    elif command == "find-claims-by-citation":
        parser.add_argument("--citation-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    commands = {
        "list-claims": cmd_list_claims,
        "find-claims-by-citation": cmd_find_claims_by_citation,
        "graph-summary": cmd_graph_summary,
    }

    if not args:
        print(command_help())
        return 1

    command = args[0]
    if command not in commands:
        print(command_help())
        return 1

    parser = build_parser(command)
    parsed = parser.parse_args(args[1:])
    return commands[command](parsed)


if __name__ == "__main__":
    raise SystemExit(main())
