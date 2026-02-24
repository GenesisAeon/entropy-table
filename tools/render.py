from __future__ import annotations

from common import ROOT, domain_files, load_yaml, relation_files

OUTPUT_DIR = ROOT / "outputs"


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
    out.extend(["## Relations", "", "| id | type | source | target |", "|---|---|---|---|"])
    for r in relations:
        suffix = " (composition)" if r["relation_type"] == "composition" else ""
        out.append(f"| {r['id']} | {r['relation_type']}{suffix} | {r['source_domain_id']} | {r['target_domain_id']} |")
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
        out.append(f"\\item {r['id']}: {r['source_domain_id']} $\\to$ {r['target_domain_id']} ({r['relation_type']})")
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
