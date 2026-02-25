from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_build_index(out_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "tools/build_index.py",
            "--out",
            str(out_path),
            "--domains-root",
            "atlas/domains",
            "--relations-root",
            "atlas/relations",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def test_build_index_creates_index(tmp_path: Path) -> None:
    out_path = tmp_path / "index.json"
    result = run_build_index(out_path)
    assert result.returncode == 0, result.stderr
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert "domains" in payload
    assert "relations" in payload
    assert "reverse" in payload
    assert "graph" in payload
    assert "meta" in payload


def test_reverse_map_contains_celani(tmp_path: Path) -> None:
    out_path = tmp_path / "index.json"
    result = run_build_index(out_path)
    assert result.returncode == 0, result.stderr
    payload = json.loads(out_path.read_text(encoding="utf-8"))

    reverse = payload["reverse"]
    domain_hits = reverse["citation_to_domains"].get("celani2012-prl", [])
    relation_hits = reverse["citation_to_relations"].get("celani2012-prl", [])
    assert len(domain_hits) + len(relation_hits) >= 1
