"""Tests for tools/visualize.py — atlas graph visualiser."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def run_viz(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tools.visualize", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


# ── Smoke tests ───────────────────────────────────────────────────────────────

def test_mermaid_default_runs() -> None:
    result = run_viz()
    assert result.returncode == 0, result.stderr
    assert "flowchart LR" in result.stdout


def test_dot_format_runs() -> None:
    result = run_viz("--format", "dot")
    assert result.returncode == 0, result.stderr
    assert "digraph entropy_atlas" in result.stdout


# ── Mermaid output content ────────────────────────────────────────────────────

def test_mermaid_contains_known_domain() -> None:
    result = run_viz("--exclude-group", "00_golden")
    assert result.returncode == 0
    # ctmc-schnakenberg must appear as a sanitised node ID
    assert "ctmc_schnakenberg" in result.stdout


def test_mermaid_contains_classdefs() -> None:
    result = run_viz()
    assert "classDef stable" in result.stdout
    assert "classDef review" in result.stdout
    assert "classDef draft" in result.stdout


def test_mermaid_edge_label_approximation() -> None:
    # underdamped → overdamped is an approximation_limit relation
    result = run_viz("--exclude-group", "00_golden")
    assert result.returncode == 0
    assert "approx" in result.stdout


def test_mermaid_edge_label_regime() -> None:
    result = run_viz("--exclude-group", "00_golden")
    assert result.returncode == 0
    assert "regime" in result.stdout


# ── DOT output content ────────────────────────────────────────────────────────

def test_dot_contains_known_domain() -> None:
    result = run_viz("--format", "dot", "--exclude-group", "00_golden")
    assert result.returncode == 0
    assert "ctmc-schnakenberg" in result.stdout


def test_dot_contains_legend() -> None:
    result = run_viz("--format", "dot")
    assert "cluster_legend" in result.stdout


def test_dot_edge_styles_present() -> None:
    result = run_viz("--format", "dot", "--exclude-group", "00_golden")
    assert result.returncode == 0
    # At least one edge with a label should appear
    assert "approx" in result.stdout or "coarse" in result.stdout or "regime" in result.stdout


# ── Filtering ─────────────────────────────────────────────────────────────────

def test_filter_status_stable_only() -> None:
    result = run_viz("--filter-status", "stable")
    assert result.returncode == 0
    # No draft or review class assignments should appear for nodes
    # (classDef lines are always present; only class *assignments* must be absent)
    lines = [l for l in result.stdout.splitlines() if l.strip().startswith("class ")]
    for line in lines:
        assert "draft" not in line
        assert "review" not in line


def test_filter_status_draft_review() -> None:
    result = run_viz("--filter-status", "draft", "review")
    assert result.returncode == 0
    lines = [l for l in result.stdout.splitlines() if l.strip().startswith("class ")]
    for line in lines:
        assert "stable" not in line


def test_exclude_golden_group() -> None:
    result = run_viz("--exclude-group", "00_golden")
    assert result.returncode == 0
    # Golden-only ids like subsystem-langevin / supersystem-network must be absent
    assert "subsystem_langevin" not in result.stdout
    assert "supersystem_network" not in result.stdout


def test_exclude_all_groups_gives_empty_graph() -> None:
    result = run_viz("--exclude-group", "00_golden", "01_physics")
    # Should exit 0 but warn
    assert result.returncode == 0
    assert "warning" in result.stderr.lower()


# ── Output file writing ───────────────────────────────────────────────────────

def test_output_to_file(tmp_path: Path) -> None:
    out = tmp_path / "graph.mmd"
    result = run_viz("--output", str(out))
    assert result.returncode == 0
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "flowchart LR" in content


def test_dot_output_to_file(tmp_path: Path) -> None:
    out = tmp_path / "graph.dot"
    result = run_viz("--format", "dot", "--output", str(out))
    assert result.returncode == 0
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "digraph entropy_atlas" in content


# ── Unit tests for renderers (import directly) ────────────────────────────────

from tools.visualize import (
    DomainNode,
    RelationEdge,
    render_dot,
    render_mermaid,
)


def _make_nodes() -> list[DomainNode]:
    return [
        DomainNode("sys-a", "System A", "effectively_closed", "stable", "01_physics"),
        DomainNode("sys-b", "System B", "open", "draft", "01_physics"),
    ]


def _make_edges() -> list[RelationEdge]:
    return [
        RelationEdge("rel-1", "sys-a", "sys-b", "approximation_limit", "draft", "01_physics"),
    ]


def test_render_mermaid_node_shapes() -> None:
    out = render_mermaid(_make_nodes(), [])
    # effectively_closed → stadium shape ([( )])
    assert "sys_a([" in out
    # open → circle shape ((  ))
    assert "sys_b((" in out


def test_render_mermaid_edge_arrow() -> None:
    out = render_mermaid(_make_nodes(), _make_edges())
    assert "-->|approx|" in out


def test_render_mermaid_class_assignment_stable() -> None:
    out = render_mermaid(_make_nodes(), [])
    assert "class sys_a stable" in out


def test_render_mermaid_class_assignment_draft() -> None:
    out = render_mermaid(_make_nodes(), [])
    assert "class sys_b draft" in out


def test_render_dot_node_shape_effectively_closed() -> None:
    out = render_dot(_make_nodes(), [])
    assert 'shape="box"' in out


def test_render_dot_node_fill_stable() -> None:
    out = render_dot(_make_nodes(), [])
    assert '#c8e6c9' in out  # stable fill


def test_render_dot_edge_label() -> None:
    out = render_dot(_make_nodes(), _make_edges())
    assert 'label="approx"' in out


def test_render_dot_edge_color_approximation() -> None:
    out = render_dot(_make_nodes(), _make_edges())
    assert '#1565c0' in out  # approximation_limit edge color


def test_long_title_truncated_in_mermaid() -> None:
    long_title = "A" * 50
    nodes = [DomainNode("x", long_title, "unknown", "draft", "grp")]
    out = render_mermaid(nodes, [])
    # Label in output must be ≤ 40 chars + quotes + ellipsis
    assert "…" in out
