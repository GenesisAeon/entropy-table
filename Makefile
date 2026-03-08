.PHONY: help validate validate-all test health render visualize visualize-dot metrics release new-domain new-case validate-cases clean

PYTHON := uv run python
CLI    := uv run entropy-table
TOOLS  := tools
VERSION ?= dev

help:
	@echo "entropy-table — available targets:"
	@echo ""
	@echo "  validate       Validate domain/relation schemas and cross-references"
	@echo "  validate-all   Run all validation checks (schema + claims + composition + bibliography)"
	@echo "  test           Run the full pytest test suite"
	@echo "  health         Analyse atlas health (orphaned domains, unfalsifiable claims, …)"
	@echo "  render         Render atlas to atlas.md and atlas.tex"
	@echo "  visualize      Generate Mermaid graph (docs/atlas_graph.mmd)"
	@echo "  visualize-dot  Generate Graphviz DOT graph (docs/atlas_graph.dot)"
	@echo "  metrics        Compute operational atlas metrics (JSON + Markdown)"
	@echo "  release        Build a release pack  (set VERSION=vX.Y.Z)"
	@echo "  new-domain     Scaffold a new domain file  (set ID=my-domain)"
	@echo "  new-case       Scaffold a new case file   (set ID=my-case-v01; optional CLAIM= CALCULATOR=)"
	@echo "  validate-cases Validate claim↔case cross-references (dangling + orphaned)"
	@echo "  clean          Remove generated artefacts"
	@echo ""
	@echo "  Or use the CLI directly:"
	@echo "    uv run entropy-table --help"

# ── Validation ────────────────────────────────────────────────────────────────

validate:
	$(PYTHON) $(TOOLS)/validate.py

validate-all: validate
	$(PYTHON) $(TOOLS)/validate_claims.py
	$(PYTHON) $(TOOLS)/validate_composition.py
	$(PYTHON) $(TOOLS)/validate_bibliography.py
	$(CLI) validate-cases

# ── Testing ───────────────────────────────────────────────────────────────────

test:
	$(PYTHON) -m pytest

# ── Atlas health & metrics ────────────────────────────────────────────────────

health:
	$(CLI) health

metrics:
	$(CLI) metrics --format markdown

# ── Rendering ─────────────────────────────────────────────────────────────────

render:
	$(CLI) render

# ── Visualisation ─────────────────────────────────────────────────────────────

visualize:
	$(PYTHON) -m entropy_table.commands.visualize --format mermaid --output docs/atlas_graph.mmd
	@echo "Mermaid graph written to docs/atlas_graph.mmd"

visualize-dot:
	$(PYTHON) -m entropy_table.commands.visualize --format dot --output docs/atlas_graph.dot
	@echo "Graphviz DOT graph written to docs/atlas_graph.dot"

# ── Release ───────────────────────────────────────────────────────────────────

release:
	$(CLI) release --version $(VERSION)

# ── Scaffolding ───────────────────────────────────────────────────────────────

new-domain:
	@if [ -z "$(ID)" ]; then \
		read -p "Domain ID (kebab-case, e.g. my-new-system): " _id; \
		$(PYTHON) $(TOOLS)/scaffold.py domain "$$_id" --category "$(or $(CATEGORY),01_physics)"; \
	else \
		$(PYTHON) $(TOOLS)/scaffold.py domain "$(ID)" --category "$(or $(CATEGORY),01_physics)"; \
	fi

new-case:
	@if [ -z "$(ID)" ]; then \
		read -p "Case ID (kebab-case with optional -vNN, e.g. ctmc-3cycle-v01): " _id; \
		$(CLI) scaffold case "$$_id" --category "$(or $(CATEGORY),01_physics)"; \
	else \
		$(CLI) scaffold case "$(ID)" --category "$(or $(CATEGORY),01_physics)"; \
	fi

validate-cases:
	$(CLI) validate-cases

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean:
	rm -f atlas.md atlas.tex docs/atlas_graph.mmd docs/atlas_graph.dot
	rm -rf dist/packs/* dist/snapshots/*
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
