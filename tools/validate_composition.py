from __future__ import annotations

import argparse
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import yaml

DEFAULT_MAX_DEPTH_WARNING = 8


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected top-level mapping")
    return data


def domain_files(atlas_root: Path) -> list[Path]:
    return sorted((atlas_root / "domains").glob("**/*.yaml"))


def relation_files(atlas_root: Path) -> list[Path]:
    return sorted((atlas_root / "relations").glob("**/*.yaml"))


def relation_tags(relation: dict[str, Any]) -> list[str]:
    context = relation.get("context")
    if not isinstance(context, dict):
        return []
    tags = context.get("tags", [])
    if not isinstance(tags, list):
        return []
    return [str(tag) for tag in tags]


def relation_channels(relation: dict[str, Any]) -> tuple[list[str], bool]:
    for key in ("exchange_channels", "coupling_channels", "channels"):
        channels = relation.get(key)
        if channels is None:
            continue
        if isinstance(channels, list):
            return [str(channel) for channel in channels], True
        return [str(channels)], True
    return [], False


def is_composition_edge(relation: dict[str, Any]) -> bool:
    if relation.get("relation_type") == "composition":
        return True

    if relation.get("composition") is True:
        return True

    if isinstance(relation.get("composition_parts"), dict):
        return True

    if "composition" in {tag.lower() for tag in relation_tags(relation)}:
        return True

    parts = relation.get("parts")
    if isinstance(parts, list) and len(parts) > 0:
        return True

    return False


def find_cycle(adjacency: dict[str, list[str]]) -> list[str] | None:
    state: dict[str, int] = {}
    stack: list[str] = []
    stack_index: dict[str, int] = {}

    def dfs(node: str) -> list[str] | None:
        state[node] = 1
        stack_index[node] = len(stack)
        stack.append(node)

        for nxt in adjacency.get(node, []):
            nxt_state = state.get(nxt, 0)
            if nxt_state == 0:
                cycle = dfs(nxt)
                if cycle:
                    return cycle
            elif nxt_state == 1:
                start = stack_index[nxt]
                return stack[start:] + [nxt]

        stack.pop()
        stack_index.pop(node, None)
        state[node] = 2
        return None

    for node in adjacency:
        if state.get(node, 0) == 0:
            cycle = dfs(node)
            if cycle:
                return cycle

    return None


def max_depth(adjacency: dict[str, list[str]]) -> int:
    indegree: dict[str, int] = {node: 0 for node in adjacency}
    for source, targets in adjacency.items():
        indegree.setdefault(source, 0)
        for target in targets:
            indegree[target] = indegree.get(target, 0) + 1

    queue = deque(node for node, degree in indegree.items() if degree == 0)
    depth: dict[str, int] = {node: 0 for node in indegree}

    while queue:
        node = queue.popleft()
        for target in adjacency.get(node, []):
            depth[target] = max(depth.get(target, 0), depth[node] + 1)
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)

    return max(depth.values(), default=0)


def _format_cycle(cycle: list[str]) -> str:
    return " -> ".join(cycle)


def validate_composition(atlas_root: Path, max_depth_warning: int = DEFAULT_MAX_DEPTH_WARNING) -> int:
    domains_by_id: dict[str, dict[str, Any]] = {}
    domain_path_by_id: dict[str, Path] = {}
    errors: list[str] = []
    warnings: list[str] = []
    infos: list[str] = []

    for path in domain_files(atlas_root):
        try:
            domain = load_yaml(path)
        except Exception as exc:
            errors.append(f"{path}: could not parse domain YAML ({exc})")
            continue

        domain_id = domain.get("id")
        if not isinstance(domain_id, str) or not domain_id:
            errors.append(f"{path}: missing/invalid domain id")
            continue

        if domain_id in domains_by_id:
            errors.append(f"{path}: duplicate domain id '{domain_id}'")
            continue

        domains_by_id[domain_id] = domain
        domain_path_by_id[domain_id] = path

    composition_edges: list[tuple[str, str, Path, str, list[str], bool]] = []

    for path in relation_files(atlas_root):
        try:
            relation = load_yaml(path)
        except Exception as exc:
            errors.append(f"{path}: could not parse relation YAML ({exc})")
            continue

        if not is_composition_edge(relation):
            continue

        source = relation.get("source_domain_id")
        target = relation.get("target_domain_id")
        relation_id = str(relation.get("id", "<unknown-relation-id>"))

        if source not in domains_by_id:
            errors.append(f"{path}: composition source_domain_id '{source}' does not exist")
        if target not in domains_by_id:
            errors.append(f"{path}: composition target_domain_id '{target}' does not exist")

        if isinstance(source, str) and isinstance(target, str) and source == target:
            errors.append(f"{path}: composition relation '{relation_id}' cannot be a self-loop ({source} -> {target})")

        channels, explicit_channels = relation_channels(relation)
        composition_edges.append((str(source), str(target), path, relation_id, channels, explicit_channels))

    adjacency: dict[str, list[str]] = defaultdict(list)
    edge_path_by_pair: dict[tuple[str, str], Path] = {}
    for source, target, path, _, _, _ in composition_edges:
        adjacency[source].append(target)
        adjacency.setdefault(target, [])
        edge_path_by_pair[(source, target)] = path

    cycle = find_cycle(adjacency)
    if cycle:
        cycle_edges = list(zip(cycle[:-1], cycle[1:]))
        cycle_edge_files = sorted({edge_path_by_pair.get(edge) for edge in cycle_edges if edge_path_by_pair.get(edge)})
        if cycle_edge_files:
            files_text = ", ".join(str(p) for p in cycle_edge_files)
            errors.append(f"composition cycle detected: {_format_cycle(cycle)} (relations: {files_text})")
        else:
            errors.append(f"composition cycle detected: {_format_cycle(cycle)}")

    depth = max_depth(adjacency) if not cycle else 0

    participating_subsystems = {source for source, _, _, _, _, _ in composition_edges if source in domains_by_id}
    for subsystem_id in sorted(participating_subsystems):
        domain = domains_by_id[subsystem_id]
        path = domain_path_by_id[subsystem_id]
        boundary = domain.get("boundary")
        if not isinstance(boundary, dict):
            errors.append(f"{path}: subsystem '{subsystem_id}' missing boundary object")
            continue

        closure_type = boundary.get("closure_type")
        if closure_type is None:
            errors.append(f"{path}: subsystem '{subsystem_id}' missing boundary.closure_type")
            continue

        closure_notes = str(boundary.get("closure_notes", "")).strip()
        if closure_type == "effectively_closed" and not closure_notes:
            errors.append(
                f"{path}: subsystem '{subsystem_id}' with closure_type=effectively_closed must declare non-empty boundary.closure_notes"
            )

        exchange_channels = boundary.get("exchange_channels")
        if closure_type == "effectively_closed" and (not isinstance(exchange_channels, list) or len(exchange_channels) == 0):
            warnings.append(
                f"{path}: subsystem '{subsystem_id}' is effectively_closed but declares no boundary.exchange_channels"
            )

    for source, target, path, relation_id, channels, explicit_channels in composition_edges:
        if not explicit_channels:
            infos.append(f"{path}: relation '{relation_id}' has implicit channels")
            continue

        source_channels = domains_by_id.get(source, {}).get("boundary", {}).get("exchange_channels", [])
        target_channels = domains_by_id.get(target, {}).get("boundary", {}).get("exchange_channels", [])
        source_channel_set = {str(channel) for channel in source_channels} if isinstance(source_channels, list) else set()
        target_channel_set = {str(channel) for channel in target_channels} if isinstance(target_channels, list) else set()

        for channel in channels:
            if channel not in source_channel_set or channel not in target_channel_set:
                errors.append(
                    f"{path}: relation '{relation_id}' channel '{channel}' must be declared in both "
                    f"source({source}).boundary.exchange_channels and target({target}).boundary.exchange_channels"
                )

    if depth > max_depth_warning:
        warnings.append(
            f"composition max depth is {depth}, above warning threshold {max_depth_warning}; consider whether systems are over-nested"
        )

    for error in errors:
        print(f"ERROR: {error}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for info in infos:
        print(f"INFO: {info}")

    print("Summary:")
    print(f"  composition_edges_count: {len(composition_edges)}")
    print(f"  max_depth: {depth}")
    print(f"  cycle_found: {'yes' if cycle else 'no'}")
    print(f"  warnings_count: {len(warnings)}")

    return 1 if errors else 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate composition/integrity rules for atlas relations")
    parser.add_argument(
        "--atlas-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "atlas",
        help="Path to atlas root (default: ./atlas)",
    )
    parser.add_argument(
        "--max-depth-warning",
        type=int,
        default=DEFAULT_MAX_DEPTH_WARNING,
        help=f"Warn when composition depth exceeds this threshold (default: {DEFAULT_MAX_DEPTH_WARNING})",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or [])
    return validate_composition(args.atlas_root, max_depth_warning=args.max_depth_warning)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
