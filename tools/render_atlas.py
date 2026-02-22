from __future__ import annotations

from common import ROOT, domain_files, load_yaml, relation_files

OUTPUTS_DIR = ROOT / "outputs"
MD_PATH = OUTPUTS_DIR / "atlas.md"
TEX_PATH = OUTPUTS_DIR / "atlas.tex"


def render_markdown(domains: list[dict], relations: list[dict]) -> str:
    lines = ["# Entropy Atlas", "", "## Domains", ""]
    for item in domains:
        lines.extend(
            [
                f"### {item['domain']} ({item['id']})",
                f"- **System type:** {item['system_type']}",
                f"- **Entropy quantity kind:** {item['entropy_quantity_kind']}",
                f"- **Epistemic status:** {item['epistemic_status']}",
                f"- **Status:** {item['status']}",
                f"- **Proxy:** ${item['entropy_proxy']['symbol']}$",
                f"- **Bands:** {', '.join(item['spectral_bands']['bands'])}",
                "",
            ]
        )

    lines.extend(
        [
            "## Relations",
            "",
            "| id | source | target | relation_type | entropy_effect | status |",
            "|---|---|---|---|---|---|",
        ]
    )
    for rel in relations:
        lines.append(
            "| "
            f"{rel['id']} | {rel['source_domain_ref']} | {rel['target_domain_ref']} | "
            f"{rel['relation_type']} | {rel['expected_effect_on_entropy_measure']['direction']} | {rel['status']} |"
        )
    lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_latex(domains: list[dict], relations: list[dict]) -> str:
    lines = [
        "\\section*{Entropy Atlas}",
        "\\subsection*{Domains}",
    ]
    for item in domains:
        lines.extend(
            [
                f"\\subsubsection*{{{item['domain']} ({item['id']})}}",
                f"System type: {item['system_type']}\\\\",
                f"Entropy quantity kind: {item['entropy_quantity_kind']}\\\\",
                f"Epistemic status: {item['epistemic_status']}\\\\",
                f"Status: {item['status']}\\\\",
                f"Proxy: ${item['entropy_proxy']['symbol']}$\\\\",
                f"Bands: {', '.join(item['spectral_bands']['bands'])}",
                "",
            ]
        )

    lines.extend(
        [
            "\\subsection*{Relations}",
            "\\begin{tabular}{llllll}",
            "id & source & target & type & effect & status \\\\",
            "\\hline",
        ]
    )
    for rel in relations:
        lines.append(
            f"{rel['id']} & {rel['source_domain_ref']} & {rel['target_domain_ref']} & "
            f"{rel['relation_type']} & {rel['expected_effect_on_entropy_measure']['direction']} & {rel['status']} \\\\"
        )
    lines.extend(["\\end{tabular}", ""])
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    domains = [load_yaml(f) for f in domain_files() if f.name != "registry.yaml"]
    relations = [load_yaml(f) for f in relation_files() if f.name != "registry.yaml"]
    MD_PATH.write_text(render_markdown(domains, relations), encoding="utf-8")
    TEX_PATH.write_text(render_latex(domains, relations), encoding="utf-8")
    print(
        f"Rendered {len(domains)} domain(s) and {len(relations)} relation(s) to {MD_PATH} and {TEX_PATH}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
