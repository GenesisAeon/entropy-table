from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build deterministic atlas metadata index")
    parser.add_argument("--out", default="cache/index.json")
    parser.add_argument("--domains-root", default="atlas/domains")
    parser.add_argument("--relations-root", default="atlas/relations")
    return parser.parse_args(argv)


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML object")
    return data


def iter_yaml_files(root: Path) -> list[Path]:
    return sorted(root.glob("**/*.yaml"))


def build_index(domains_root: Path, relations_root: Path) -> dict:
    domains: dict[str, dict] = {}
    relations: dict[str, dict] = {}
    citation_to_domains: dict[str, set[str]] = defaultdict(set)
    citation_to_relations: dict[str, set[str]] = defaultdict(set)
    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, list[str]] = defaultdict(list)

    for path in iter_yaml_files(domains_root):
        data = load_yaml(path)
        domain_id = data.get("id")
        if not isinstance(domain_id, str) or not domain_id:
            raise ValueError(f"{path} missing required 'id'")

        boundary = data.get("boundary") or {}
        system_type = data.get("system_type") or {}
        context = data.get("context") or {}
        domain_tags = sorted(set((system_type.get("tags") or []) + (context.get("tags") or [])))
        citation_ids = sorted(c.get("id") for c in (data.get("citations") or []) if isinstance(c, dict) and c.get("id"))

        must_fail_rows = []
        for test in data.get("must_fail_tests") or []:
            if not isinstance(test, dict):
                continue
            test_id = test.get("id", "<missing-test-id>")
            severity = test.get("severity", "unknown")
            for citation_id in test.get("citations") or []:
                citation_to_domains[citation_id].add(domain_id)
                must_fail_rows.append(
                    {
                        "citation_id": citation_id,
                        "test_id": test_id,
                        "severity": severity,
                    }
                )

        domains[domain_id] = {
            "path": str(path.as_posix()),
            "title": data.get("title", ""),
            "system_primary": system_type.get("primary", ""),
            "tags": domain_tags,
            "closure_type": boundary.get("closure_type", "unknown"),
            "exchange_channels": sorted(boundary.get("exchange_channels") or []),
            "citation_ids": citation_ids,
            "must_fail_rows": sorted(
                must_fail_rows,
                key=lambda row: (row["citation_id"], row["test_id"], row["severity"]),
            ),
        }

    for path in iter_yaml_files(relations_root):
        data = load_yaml(path)
        relation_id = data.get("id")
        if not isinstance(relation_id, str) or not relation_id:
            raise ValueError(f"{path} missing required 'id'")

        source = data.get("source_domain_id", "")
        target = data.get("target_domain_id", "")
        citation_ids = sorted(c.get("id") for c in (data.get("citations") or []) if isinstance(c, dict) and c.get("id"))

        must_fail_rows = []
        for test in data.get("must_fail_tests") or []:
            if not isinstance(test, dict):
                continue
            test_id = test.get("id", "<missing-test-id>")
            severity = test.get("severity", "unknown")
            for citation_id in test.get("citations") or []:
                citation_to_relations[citation_id].add(relation_id)
                must_fail_rows.append(
                    {
                        "citation_id": citation_id,
                        "test_id": test_id,
                        "severity": severity,
                    }
                )

        relations[relation_id] = {
            "path": str(path.as_posix()),
            "relation_type": data.get("relation_type", "unknown"),
            "source": source,
            "target": target,
            "citation_ids": citation_ids,
            "must_fail_rows": sorted(
                must_fail_rows,
                key=lambda row: (row["citation_id"], row["test_id"], row["severity"]),
            ),
        }
        outgoing[source].append(relation_id)
        incoming[target].append(relation_id)

    return {
        "domains": {key: domains[key] for key in sorted(domains)},
        "relations": {key: relations[key] for key in sorted(relations)},
        "reverse": {
            "citation_to_domains": {
                citation_id: sorted(domain_ids)
                for citation_id, domain_ids in sorted(citation_to_domains.items())
            },
            "citation_to_relations": {
                citation_id: sorted(relation_ids)
                for citation_id, relation_ids in sorted(citation_to_relations.items())
            },
        },
        "graph": {
            "outgoing": {
                domain_id: sorted(relation_ids)
                for domain_id, relation_ids in sorted(outgoing.items())
            },
            "incoming": {
                domain_id: sorted(relation_ids)
                for domain_id, relation_ids in sorted(incoming.items())
            },
        },
        "meta": {
            "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "domain_count": len(domains),
            "relation_count": len(relations),
        },
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        index = build_index(Path(args.domains_root), Path(args.relations_root))
    except (yaml.YAMLError, OSError, ValueError) as exc:
        print(f"Error building index: {exc}", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote index: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
