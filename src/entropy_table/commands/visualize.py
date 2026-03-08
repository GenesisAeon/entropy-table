"""
tools/visualize.py — Atlas graph visualiser.

Reads all domains and relations from atlas/ and renders a graph in either
Mermaid.js (flowchart) or Graphviz DOT format.

Node appearance:
  - Shape / border encodes closure_type (effectively_closed / open / unknown)
  - Fill colour encodes epistemic status  (draft / review / stable)

Edge appearance:
  - Style and label encode relation_type
    (approximation_limit, coarse_graining, composition, regime_shift,
     coupling, aggregation_rule, equivalence_mapping, model_reduction,
     measurement_mapping)

Usage
-----
    python tools/visualize.py                         # Mermaid to stdout
    python tools/visualize.py --format dot            # Graphviz DOT to stdout
    python tools/visualize.py --format mermaid --output docs/atlas_graph.mmd
    python tools/visualize.py --format dot    --output docs/atlas_graph.dot
    python tools/visualize.py --filter-status stable review
    python tools/visualize.py --exclude-group 00_golden
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import NamedTuple

from entropy_table.core.common import domain_files, load_yaml, relation_files

# ── Data model ────────────────────────────────────────────────────────────────

class DomainNode(NamedTuple):
    id: str
    title: str
    closure_type: str   # effectively_closed | open | unknown | closed
    status: str         # draft | review | stable
    group: str          # directory name, e.g. 00_golden


class RelationEdge(NamedTuple):
    id: str
    source: str
    target: str
    relation_type: str
    status: str
    group: str


# ── Loading ───────────────────────────────────────────────────────────────────

def load_domains(exclude_groups: set[str]) -> list[DomainNode]:
    nodes: list[DomainNode] = []
    for path in domain_files():
        group = path.parent.name
        if group in exclude_groups:
            continue
        data = load_yaml(path)
        nodes.append(DomainNode(
            id=data.get("id", path.stem),
            title=data.get("title", data.get("id", path.stem)),
            closure_type=data.get("boundary", {}).get("closure_type", "unknown"),
            status=data.get("status", "draft"),
            group=group,
        ))
    return nodes


def load_relations(
    exclude_groups: set[str],
    known_ids: set[str],
) -> list[RelationEdge]:
    edges: list[RelationEdge] = []
    for path in relation_files():
        group = path.parent.name
        if group in exclude_groups:
            continue
        data = load_yaml(path)
        src = data.get("source_domain_id", "")
        tgt = data.get("target_domain_id", "")
        # Skip dangling edges silently (e.g. golden fixtures referencing test nodes)
        if src not in known_ids or tgt not in known_ids:
            continue
        edges.append(RelationEdge(
            id=data.get("id", path.stem),
            source=src,
            target=tgt,
            relation_type=data.get("relation_type", "unknown"),
            status=data.get("status", "draft"),
            group=group,
        ))
    return edges


# ── Mermaid renderer ──────────────────────────────────────────────────────────

# Mermaid node shape by closure_type
_MERMAID_SHAPE: dict[str, tuple[str, str]] = {
    "effectively_closed": ("([", "])"),   # stadium / rounded
    "closed":             ("[",  "]"),    # rectangle
    "open":               ("((", "))"),   # circle
    "unknown":            ("{",  "}"),    # diamond / rhombus
}
_MERMAID_SHAPE_DEFAULT = ("[", "]")

# Mermaid fill class by status
_MERMAID_CLASS: dict[str, str] = {
    "stable": "stable",
    "review": "review",
    "draft":  "draft",
}

# Mermaid edge style by relation_type
_MERMAID_EDGE: dict[str, tuple[str, str]] = {
    "approximation_limit":  ("-->|approx|",   ""),
    "coarse_graining":      ("-.->|coarse|",  ""),
    "composition":          ("--o|part-of|",   ""),
    "aggregation_rule":     ("--o|aggregate|", ""),
    "regime_shift":         ("==>|regime|",    ""),
    "coupling":             ("<-->|couple|",   ""),
    "equivalence_mapping":  ("-->|equiv|",     ""),
    "model_reduction":      ("-->|reduce|",    ""),
    "measurement_mapping":  ("-->|measure|",   ""),
}
_MERMAID_EDGE_DEFAULT = ("-->", "")


def _mermaid_node_id(domain_id: str) -> str:
    """Sanitise domain ID for use as a Mermaid node identifier."""
    return domain_id.replace("-", "_")


def render_mermaid(nodes: list[DomainNode], edges: list[RelationEdge]) -> str:
    lines: list[str] = [
        "%%{ init: { 'theme': 'base', 'themeVariables': {",
        "    'primaryColor': '#e8f4f8', 'edgeLabelBackground': '#ffffff'",
        "} } }%%",
        "flowchart LR",
        "",
        "    %% ── Node definitions ─────────────────────────────────────────",
    ]

    for node in nodes:
        nid = _mermaid_node_id(node.id)
        open_b, close_b = _MERMAID_SHAPE.get(node.closure_type, _MERMAID_SHAPE_DEFAULT)
        # Truncate long titles so the diagram stays readable
        label = node.title if len(node.title) <= 40 else node.title[:37] + "…"
        lines.append(f'    {nid}{open_b}"{label}"{close_b}')

    lines += [
        "",
        "    %% ── Edges ────────────────────────────────────────────────────",
    ]

    for edge in edges:
        src = _mermaid_node_id(edge.source)
        tgt = _mermaid_node_id(edge.target)
        arrow, _ = _MERMAID_EDGE.get(edge.relation_type, _MERMAID_EDGE_DEFAULT)
        lines.append(f"    {src} {arrow} {tgt}")

    lines += [
        "",
        "    %% ── Style classes ────────────────────────────────────────────",
        "    classDef stable fill:#c8e6c9,stroke:#388e3c,color:#1b5e20",
        "    classDef review fill:#fff9c4,stroke:#f9a825,color:#4e342e",
        "    classDef draft  fill:#fce4ec,stroke:#c62828,color:#4a148c",
        "",
        "    %% ── Node class assignments ───────────────────────────────────",
    ]

    for status in ("stable", "review", "draft"):
        ids = [_mermaid_node_id(n.id) for n in nodes if n.status == status]
        if ids:
            lines.append(f"    class {','.join(ids)} {status}")

    return "\n".join(lines) + "\n"


# ── Graphviz DOT renderer ─────────────────────────────────────────────────────

# DOT node shape by closure_type
_DOT_SHAPE: dict[str, str] = {
    "effectively_closed": "box",
    "closed":             "rectangle",
    "open":               "ellipse",
    "unknown":            "diamond",
}
_DOT_SHAPE_DEFAULT = "box"

# DOT fill colour by status
_DOT_FILL: dict[str, str] = {
    "stable": "#c8e6c9",
    "review": "#fff9c4",
    "draft":  "#fce4ec",
}
_DOT_FILL_DEFAULT = "#f5f5f5"

# DOT edge style by relation_type
_DOT_EDGE_STYLE: dict[str, dict[str, str]] = {
    "approximation_limit": {"style": "solid",  "arrowhead": "normal", "color": "#1565c0"},
    "coarse_graining":     {"style": "dashed", "arrowhead": "normal", "color": "#6a1b9a"},
    "composition":         {"style": "solid",  "arrowhead": "odiamond","color": "#2e7d32"},
    "aggregation_rule":    {"style": "solid",  "arrowhead": "odiamond","color": "#33691e"},
    "regime_shift":        {"style": "bold",   "arrowhead": "vee",    "color": "#e65100"},
    "coupling":            {"style": "dashed", "arrowhead": "none",   "color": "#37474f",
                            "dir": "both"},
    "equivalence_mapping": {"style": "dotted", "arrowhead": "normal", "color": "#00695c"},
    "model_reduction":     {"style": "solid",  "arrowhead": "normal", "color": "#4527a0"},
    "measurement_mapping": {"style": "dashed", "arrowhead": "open",   "color": "#558b2f"},
}
_DOT_EDGE_DEFAULT: dict[str, str] = {"style": "solid", "arrowhead": "normal", "color": "#555555"}

# Human-readable edge labels
_DOT_EDGE_LABEL: dict[str, str] = {
    "approximation_limit": "approx",
    "coarse_graining":     "coarse",
    "composition":         "part-of",
    "aggregation_rule":    "aggregate",
    "regime_shift":        "regime",
    "coupling":            "couple",
    "equivalence_mapping": "equiv",
    "model_reduction":     "reduce",
    "measurement_mapping": "measure",
}


def _dot_attr(attrs: dict[str, str]) -> str:
    return ", ".join(f'{k}="{v}"' for k, v in attrs.items())


def render_dot(nodes: list[DomainNode], edges: list[RelationEdge]) -> str:
    lines: list[str] = [
        "digraph entropy_atlas {",
        "    // Graph-level settings",
        '    graph [rankdir=LR, fontname="Helvetica", bgcolor="#fafafa",'
        '           label="Entropy Atlas — domain graph", labelloc=t, fontsize=14]',
        '    node  [fontname="Helvetica", fontsize=11, style=filled]',
        '    edge  [fontname="Helvetica", fontsize=9]',
        "",
        "    // ── Nodes ──────────────────────────────────────────────────",
    ]

    for node in nodes:
        shape = _DOT_SHAPE.get(node.closure_type, _DOT_SHAPE_DEFAULT)
        fill  = _DOT_FILL.get(node.status, _DOT_FILL_DEFAULT)
        # Escape quotes in titles
        title = node.title.replace('"', '\\"')
        tooltip = f"{node.id} | {node.closure_type} | {node.status}"
        attrs = {
            "label":   title,
            "shape":   shape,
            "fillcolor": fill,
            "tooltip": tooltip,
        }
        lines.append(f'    "{node.id}" [{_dot_attr(attrs)}]')

    lines += [
        "",
        "    // ── Edges ──────────────────────────────────────────────────",
    ]

    for edge in edges:
        style = dict(_DOT_EDGE_STYLE.get(edge.relation_type, _DOT_EDGE_DEFAULT))
        label = _DOT_EDGE_LABEL.get(edge.relation_type, edge.relation_type)
        style["label"] = label
        # coupling is bidirectional
        if edge.relation_type == "coupling":
            style.setdefault("dir", "both")
        lines.append(f'    "{edge.source}" -> "{edge.target}" [{_dot_attr(style)}]')

    lines += [
        "",
        "    // ── Legend (invisible helper nodes) ───────────────────────",
        '    subgraph cluster_legend {',
        '        label="Legend"; style=dashed; fontsize=10',
        '        l_stable [label="stable", shape=box, fillcolor="#c8e6c9", style=filled]',
        '        l_review [label="review", shape=box, fillcolor="#fff9c4", style=filled]',
        '        l_draft  [label="draft",  shape=box, fillcolor="#fce4ec", style=filled]',
        '    }',
        "}",
    ]

    return "\n".join(lines) + "\n"


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate a graph of the entropy atlas (Mermaid or Graphviz DOT).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--format", choices=["mermaid", "dot"], default="mermaid",
        help="Output format (default: mermaid)",
    )
    p.add_argument(
        "--output", "-o", metavar="FILE",
        help="Write output to FILE instead of stdout",
    )
    p.add_argument(
        "--filter-status", nargs="+",
        choices=["draft", "review", "stable"],
        metavar="STATUS",
        help="Only include nodes/edges with these statuses",
    )
    p.add_argument(
        "--exclude-group", nargs="+", default=[],
        metavar="GROUP",
        help="Exclude atlas sub-directories by name (e.g. 00_golden)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exclude = set(args.exclude_group)
    allowed_statuses: set[str] | None = set(args.filter_status) if args.filter_status else None

    nodes = load_domains(exclude)
    if allowed_statuses:
        nodes = [n for n in nodes if n.status in allowed_statuses]

    known_ids = {n.id for n in nodes}
    edges = load_relations(exclude, known_ids)
    if allowed_statuses:
        edges = [e for e in edges if e.status in allowed_statuses]

    if not nodes:
        print("warning: no domains found (check --exclude-group and --filter-status)", file=sys.stderr)

    if args.format == "mermaid":
        output = render_mermaid(nodes, edges)
    else:
        output = render_dot(nodes, edges)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
