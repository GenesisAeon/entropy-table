# Developer Guide

## Setup

```bash
git clone https://github.com/GenesisAeon/entropy-table.git
cd entropy-table
uv sync --extra dev --extra docs
uv run pre-commit install
```

## CLI Reference

All commands via `uv run entropy-table <command>`:

| Command | Description |
|---|---|
| `validate-all` | Full validation: schema + claims + composition + bibliography |
| `scaffold domain <id>` | Create a new domain YAML scaffold |
| `scaffold case <id>` | Create a new compute case scaffold |
| `validate-cases` | Validate claim↔case cross-references |
| `visualize --format mermaid` | Regenerate `docs/atlas_graph.mmd` |
| `visualize --format dot` | Regenerate `docs/atlas_graph.dot` |
| `health --ci-check` | Strict health check (exits non-zero on issues) |
| `metrics --format markdown` | Compute and print atlas metrics |
| `render` | Render atlas to `atlas.md` and `atlas.tex` |
| `release --version vX.Y.Z` | Build release pack |

## Makefile targets (still supported)

```bash
make validate       # schema validation only
make validate-all   # all checks
make test           # pytest
make visualize      # regenerate Mermaid graph
make health         # atlas health report
make docs           # uv run mkdocs serve (new in Sprint 2)
make docs-build     # uv run mkdocs build
make docs-deploy    # gh-pages deploy
```

## pre-commit hooks

After `uv run pre-commit install`, every commit automatically runs:

- **Ruff** — linting and auto-fix
- **Black** — code formatting
- **mypy** — type checking

Run manually on all files:

```bash
uv run pre-commit run --all-files
```

## Adding a new CLI command

1. Create `src/entropy_table/commands/my_command.py` with a Typer app or function
2. Import and register it in `src/entropy_table/cli.py`:

```python
from entropy_table.commands import my_command
app.add_typer(my_command.app, name="my-command")
# or for a simple command:
@app.command()
def my_command(...): ...
```

## Docs development

```bash
uv run mkdocs serve      # live-reload at http://127.0.0.1:8000
uv run mkdocs build      # static build → site/
uv run mkdocs gh-deploy --force  # deploy to GitHub Pages
```

New doc pages go in `docs/` as Markdown files. Add them to `nav:` in `mkdocs.yml`.
