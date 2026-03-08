.PHONY: help validate validate-all test health render visualize visualize-dot metrics release new-domain new-case validate-cases clean

PYTHON := python
TOOLS  := tools
VERSION ?= dev

help:
	@echo "entropy-table — available targets:"
	@echo ""
	@echo "  validate      Validate domain/relation schemas and cross-references"
	@echo "  validate-all  Run all validation checks (schema + claims + composition + bibliography)"
	@echo "  test          Run the full pytest test suite"
	@echo "  health        Analyse atlas health (orphaned domains, unfalsifiable claims, …)"
	@echo "  render        Render atlas to atlas.md and atlas.tex"
	@echo "  visualize     Generate Mermaid graph (docs/atlas_graph.mmd)"
	@echo "  visualize-dot Generate Graphviz DOT graph (docs/atlas_graph.dot)"
	@echo "  metrics       Compute operational atlas metrics (JSON + Markdown)"
	@echo "  release       Build a release pack  (set VERSION=vX.Y.Z)"
	@echo "  new-domain    Scaffold a new domain file  (set ID=my-domain)"
	@echo "  new-case      Scaffold a new case file   (set ID=my-case-v01; optional CLAIM= CALCULATOR=)"
	@echo "  validate-cases Validate claim↔case cross-references (dangling + orphaned)"
	@echo "  clean         Remove generated artefacts"

# ── Validation ────────────────────────────────────────────────────────────────

validate:
	$(PYTHON) $(TOOLS)/validate.py

validate-all: validate
	$(PYTHON) $(TOOLS)/validate_claims.py
	$(PYTHON) $(TOOLS)/validate_composition.py
	$(PYTHON) $(TOOLS)/validate_bibliography.py
	$(PYTHON) $(TOOLS)/manage_cases.py validate

# ── Testing ───────────────────────────────────────────────────────────────────

test:
	$(PYTHON) -m pytest

# ── Atlas health & metrics ────────────────────────────────────────────────────

health:
	$(PYTHON) $(TOOLS)/analyze_health.py

metrics:
	$(PYTHON) $(TOOLS)/metrics.py --format markdown

# ── Rendering ─────────────────────────────────────────────────────────────────

render:
	$(PYTHON) $(TOOLS)/render.py

# ── Visualisation ─────────────────────────────────────────────────────────────

visualize:
	$(PYTHON) -m tools.visualize --format mermaid --output docs/atlas_graph.mmd
	@echo "Mermaid graph written to docs/atlas_graph.mmd"

visualize-dot:
	$(PYTHON) -m tools.visualize --format dot --output docs/atlas_graph.dot
	@echo "Graphviz DOT graph written to docs/atlas_graph.dot"

# ── Release ───────────────────────────────────────────────────────────────────

release:
	$(PYTHON) $(TOOLS)/release.py --version $(VERSION)

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
		$(PYTHON) $(TOOLS)/manage_cases.py create "$$_id" \
			--category "$(or $(CATEGORY),01_physics)" \
			$(if $(CLAIM),--claim-file "$(CLAIM)") \
			$(if $(DOMAIN),--domain "$(DOMAIN)") \
			$(if $(CALCULATOR),--calculator "$(CALCULATOR)"); \
	else \
		$(PYTHON) $(TOOLS)/manage_cases.py create "$(ID)" \
			--category "$(or $(CATEGORY),01_physics)" \
			$(if $(CLAIM),--claim-file "$(CLAIM)") \
			$(if $(DOMAIN),--domain "$(DOMAIN)") \
			$(if $(CALCULATOR),--calculator "$(CALCULATOR)"); \
	fi

validate-cases:
	$(PYTHON) $(TOOLS)/manage_cases.py validate

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean:
	rm -f atlas.md atlas.tex docs/atlas_graph.mmd docs/atlas_graph.dot
	rm -rf dist/packs/* dist/snapshots/*
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
