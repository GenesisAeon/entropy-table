from __future__ import annotations

from pathlib import Path

from common import ROOT, domain_files, load_yaml

OUTPUTS_DIR = ROOT / "outputs"
MD_PATH = OUTPUTS_DIR / "atlas.md"
TEX_PATH = OUTPUTS_DIR / "atlas.tex"


def render_markdown(items: list[dict]) -> str:
    lines = ["# Entropy Atlas", ""]
    for item in items:
        lines.extend(
            [
                f"## {item['domain']}",
                f"- **System type:** {item['system_type']}",
                f"- **Status:** {item['status']}",
                f"- **Proxy:** ${item['entropy_proxy']['symbol']}$",
                f"- **Bands:** {', '.join(item['spectral_bands']['bands'])}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def render_latex(items: list[dict]) -> str:
    lines = [
        "\\section*{Entropy Atlas}",
    ]
    for item in items:
        lines.extend(
            [
                f"\\subsection*{{{item['domain']}}}",
                f"System type: {item['system_type']}\\\\",
                f"Status: {item['status']}\\\\",
                f"Proxy: ${item['entropy_proxy']['symbol']}$\\\\",
                f"Bands: {', '.join(item['spectral_bands']['bands'])}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    items = [load_yaml(f) for f in domain_files() if f.name != "registry.yaml"]
    MD_PATH.write_text(render_markdown(items), encoding="utf-8")
    TEX_PATH.write_text(render_latex(items), encoding="utf-8")
    print(f"Rendered {len(items)} domain(s) to {MD_PATH} and {TEX_PATH}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
