"""entropy-table – Contract-first scientific entropy atlas CLI."""
from __future__ import annotations

import sys

import typer

app = typer.Typer(
    name="entropy-table",
    help="Contract-first scientific entropy atlas CLI",
    rich_markup_mode="markdown",
    no_args_is_help=True,
)


# ── Validation ────────────────────────────────────────────────────────────────

@app.command()
def validate(
    json_out: bool = typer.Option(False, "--json", help="Machine-readable JSON output"),
) -> None:
    """Validate domain/relation schemas and cross-references."""
    from entropy_table.commands.validate import main
    argv = ["--json"] if json_out else []
    raise SystemExit(main(argv))


@app.command("validate-all")
def validate_all() -> None:
    """Run ALL validation checks (schema + claims + composition + bibliography + math)."""
    from entropy_table.commands.validate import main as validate_main
    from entropy_table.commands.validate_claims import main as claims_main
    from entropy_table.commands.validate_composition import main as comp_main
    from entropy_table.commands.validate_bibliography import main as bib_main
    from entropy_table.commands.manage_cases import main as cases_main
    from entropy_table.commands.validate_math import main as math_main

    rc = 0
    rc |= validate_main([]) or 0
    rc |= claims_main([]) or 0
    rc |= comp_main([]) or 0
    rc |= bib_main([]) or 0
    rc |= cases_main(["validate"]) or 0
    rc |= math_main([]) or 0
    raise SystemExit(rc)


@app.command("validate-math")
def validate_math() -> None:
    """Validate mathematical expressions in atlas domains (SymPy-assisted)."""
    from entropy_table.commands.validate_math import main
    raise SystemExit(main([]))


@app.command("validate-cases")
def validate_cases() -> None:
    """Validate claim↔case cross-references (dangling + orphaned)."""
    from entropy_table.commands.manage_cases import main
    raise SystemExit(main(["validate"]))


# ── Visualisation ─────────────────────────────────────────────────────────────

@app.command()
def visualize(
    format: str = typer.Option("mermaid", "--format", help="mermaid | dot"),
    output: str = typer.Option("docs/atlas_graph.mmd", "--output", help="Output file path"),
    filter_status: list[str] = typer.Option([], "--filter-status", help="Filter by status"),
    exclude_group: list[str] = typer.Option([], "--exclude-group", help="Exclude group"),
) -> None:
    """Generate Mermaid or Graphviz DOT graph."""
    from entropy_table.commands.visualize import main
    argv = ["--format", format, "--output", output]
    for s in filter_status:
        argv += ["--filter-status", s]
    for g in exclude_group:
        argv += ["--exclude-group", g]
    raise SystemExit(main(argv))


# ── Rendering ─────────────────────────────────────────────────────────────────

@app.command()
def render() -> None:
    """Render atlas to atlas.md + atlas.tex."""
    from entropy_table.commands.render import main
    raise SystemExit(main())


# ── Scaffolding ───────────────────────────────────────────────────────────────

@app.command()
def scaffold(
    kind: str = typer.Argument(..., help="domain | case"),
    id: str = typer.Argument(..., help="kebab-case ID"),
    category: str = typer.Option("01_physics", "--category", help="Target category"),
) -> None:
    """Scaffold a new domain or case."""
    from entropy_table.commands.scaffold import main
    argv = [kind, id, "--category", category]
    raise SystemExit(main(argv))


# ── Analysis & Metrics ────────────────────────────────────────────────────────

@app.command()
def health(
    ci_check: bool = typer.Option(False, "--ci-check", help="Exit 1 on integrity issues"),
    out: str = typer.Option("outputs/atlas_health.md", "--out"),
) -> None:
    """Atlas health analysis (orphaned domains, unfalsifiable claims, …)."""
    from entropy_table.commands.analyze_health import main
    argv = ["--out", out]
    if ci_check:
        argv.append("--ci-check")
    raise SystemExit(main(argv))


@app.command()
def metrics(
    format: str = typer.Option("markdown", "--format", help="markdown | json"),
) -> None:
    """Compute operational atlas metrics."""
    from entropy_table.commands.metrics import main
    raise SystemExit(main(["--format", format]))


# ── Index & Release ───────────────────────────────────────────────────────────

@app.command("build-index")
def build_index() -> None:
    """Build the domain/relation search index."""
    from entropy_table.commands.build_index import main
    raise SystemExit(main([]))


@app.command()
def release(
    version: str = typer.Option("dev", "--version", help="Release version, e.g. v1.2.3"),
) -> None:
    """Build a release pack."""
    from entropy_table.commands.release import main
    raise SystemExit(main(["--version", version]))


if __name__ == "__main__":
    app()
