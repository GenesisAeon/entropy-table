from __future__ import annotations

from entropy_table.core.common import ROOT, domain_files, load_yaml, relation_files

OUTPUT_DIR = ROOT / "outputs"


def _relation_marker(relation: dict) -> str:
    relation_type = relation["relation_type"]
    if relation_type == "composition":
        composition = relation.get("composition", {})
        kind = composition.get("kind", "?") if isinstance(composition, dict) else "?"
        parts = composition.get("parts", []) if isinstance(composition, dict) else []
        refs = [p.get("domain_ref", "?") for p in parts if isinstance(p, dict)] if isinstance(parts, list) else []
        return f"composition:{kind} [{', '.join(refs) or 'none'}]"
    if relation_type == "aggregation_rule":
        aggregation = relation.get("aggregation", {})
        rule_kind = aggregation.get("rule_kind", "?") if isinstance(aggregation, dict) else "?"
        statement = aggregation.get("statement", {}) if isinstance(aggregation, dict) else {}
        statement_text = statement.get("text", "") if isinstance(statement, dict) else ""
        short = (statement_text[:48] + "...") if len(statement_text) > 48 else statement_text
        return f"aggregation:{rule_kind} {short}".strip()
    if relation_type == "regime_shift":
        regime = relation.get("regime", {})
        breaks = regime.get("breaks_assumptions", []) if isinstance(regime, dict) else []
        count = len(breaks) if isinstance(breaks, list) else 0
        return f"regime_shift:breaks={count}"
    return relation_type


def render_md(domains: list[dict], relations: list[dict]) -> str:
    out = ["# Entropy Atlas", "", "## Domains", ""]
    for d in domains:
        out.extend(
            [
                f"### {d['title']} (`{d['id']}`)",
                f"- system_type.primary: `{d['system_type']['primary']}`",
                f"- system_type.tags: {', '.join(d['system_type'].get('tags', [])) or '(none)'}",
                f"- closure_type: `{d['boundary']['closure_type']}`",
                f"- entropy_quantity_kind: `{d['entropy_quantity_kind']}`",
                "",
            ]
        )
    out.extend(["## Relations", "", "| id | type | source | target | marker |", "|---|---|---|---|---|"])
    for r in relations:
        out.append(
            f"| {r['id']} | {r['relation_type']} | {r['source_domain_id']} | {r['target_domain_id']} | {_relation_marker(r)} |"
        )
    out.append("")
    return "\n".join(out)


def render_tex(domains: list[dict], relations: list[dict]) -> str:
    out = ["\\section*{Entropy Atlas}", "\\subsection*{Domains}"]
    for d in domains:
        out.extend(
            [
                f"\\paragraph{{{d['title']} ({d['id']})}}",
                f"Primary type: {d['system_type']['primary']}\\\\",
                f"Closure: {d['boundary']['closure_type']}\\\\",
            ]
        )
    out.extend(["\\subsection*{Relations}", "\\begin{itemize}"])
    for r in relations:
        out.append(
            f"\\item {r['id']}: {r['source_domain_id']} $\\to$ {r['target_domain_id']} ({r['relation_type']}; {_relation_marker(r)})"
        )
    out.extend(["\\end{itemize}", ""])
    return "\n".join(out)


def main() -> int:
    domains = [load_yaml(p) for p in domain_files()]
    relations = [load_yaml(p) for p in relation_files()]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "atlas.md").write_text(render_md(domains, relations), encoding="utf-8")
    (OUTPUT_DIR / "atlas.tex").write_text(render_tex(domains, relations), encoding="utf-8")
    print("Rendered outputs/atlas.md and outputs/atlas.tex")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
