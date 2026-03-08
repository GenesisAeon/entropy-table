# Contributing to Entropy Table

Please read [docs/contribution.md](docs/contribution.md) first — all rules still apply.

## New workflow (Sprint 1+2)

```bash
# Setup
uv sync --extra dev --extra docs
uv run pre-commit install

# Add a new domain
uv run entropy-table scaffold domain my-new-domain
# ... edit atlas/domains/my-new-domain.yaml ...
uv run entropy-table validate-all

# Check code quality
uv run pre-commit run --all-files

# Preview docs locally
uv run mkdocs serve
```

## What needs a PR?

- New or modified domain/relation YAMLs → always requires `validate-all` to pass
- New CLI commands → add tests in `tests/`
- Doc changes → `uv run mkdocs build` must succeed

## CI

Every push runs: `make test` + `make validate-all` + `entropy-table health --ci-check`.
Docs are automatically deployed to GitHub Pages on every merge to `main`.
