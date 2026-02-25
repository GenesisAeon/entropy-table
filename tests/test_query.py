from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_query(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/query.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def test_list_domains_runs() -> None:
    result = run_query("list-domains")
    assert result.returncode == 0
    assert "Domains (" in result.stdout


def test_list_domains_filter_closure_type() -> None:
    result = run_query("list-domains", "--closure-type", "effectively_closed")
    assert result.returncode == 0
    lines = [line for line in result.stdout.splitlines() if line.strip().startswith("-")]
    assert lines
    assert all("closure_type=effectively_closed" in line for line in lines)


def test_find_must_fail_by_citation_known_entry() -> None:
    result = run_query("find-must-fail-by-citation", "--citation-id", "celani2012-prl")
    assert result.returncode == 0
    assert "test_id: missing-anomalous-correction" in result.stdout


def test_invalid_command_non_zero() -> None:
    result = run_query("bad-command")
    assert result.returncode != 0
