.PHONY: help validate validate-all validate-ci test health render visualize visualize-dot metrics release clean

PYTHON := python
TOOLS  := tools
VERSION ?= dev

help:
	@echo "entropy-table — available targets:"
	@echo ""
	@echo "  validate      Validate domain/relation schemas and cross-references"
	@echo "  validate-all  Run all validation checks (schema + claims + composition + bibliography)"
	@echo "  validate-ci   validate-all + live DOI resolution checks (requires network)"
	@echo "  test          Run the full pytest test suite"
	@echo "  health        Analyse atlas health (orphaned domains, unfalsifiable claims, …)"
	@echo "  render        Render atlas to atlas.md and atlas.tex"
	@echo "  visualize     Generate Mermaid graph (docs/atlas_graph.mmd)"
	@echo "  visualize-dot Generate Graphviz DOT graph (docs/atlas_graph.dot)"
	@echo "  metrics       Compute operational atlas metrics (JSON + Markdown)"
	@echo "  release       Build a release pack  (set VERSION=vX.Y.Z)"
	@echo "  clean         Remove generated artefacts"

# ── Validation ────────────────────────────────────────────────────────────────

validate:
	$(PYTHON) $(TOOLS)/validate.py

validate-all: validate
	$(PYTHON) $(TOOLS)/validate_claims.py
	$(PYTHON) $(TOOLS)/validate_composition.py
	$(PYTHON) $(TOOLS)/validate_bibliography.py

# validate-ci extends validate-all with live network checks (DOI resolution).
# Intended for CI pipelines with network access; not required for local dev.
validate-ci: validate-all
	$(PYTHON) $(TOOLS)/validate_bibliography.py --verify-dois

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

# ── Cleanup ───────────────────────────────────────────────────────────────────

clean:
	rm -f atlas.md atlas.tex docs/atlas_graph.mmd docs/atlas_graph.dot
	rm -rf dist/packs/* dist/snapshots/*
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
