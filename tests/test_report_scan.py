from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from compute.case_runner import discover_cases
from compute.report import main as report_main
from compute.report import write_report


def _write_case(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def test_discover_cases_is_deterministic_and_ignores_hidden(tmp_path) -> None:
    _write_case(
        tmp_path / "b" / "z-case.yaml",
        """
id: z-case
calculator: diffusion-ep-1d
input:
  format: json-inline
  data: {mobility: 1.0, force: 1.0, temperature: 1.0}
""",
    )
    _write_case(
        tmp_path / "a" / "a-case.yaml",
        """
id: a-case
calculator: diffusion-ep-1d
input:
  format: json-inline
  data: {mobility: 1.0, force: 1.0, temperature: 1.0}
""",
    )
    _write_case(
        tmp_path / ".hidden" / "skip.yaml",
        """
id: skip-hidden
calculator: diffusion-ep-1d
input:
  format: json-inline
  data: {mobility: 1.0, force: 1.0, temperature: 1.0}
""",
    )
    (tmp_path / "a" / "not-a-case.txt").write_text("ignore", encoding="utf-8")

    discovered = discover_cases(tmp_path)

    assert [p.relative_to(tmp_path).as_posix() for p in discovered] == [
        "a/a-case.yaml",
        "b/z-case.yaml",
    ]


def test_report_scan_only_failures_writes_expected_content(tmp_path) -> None:
    pass_case = tmp_path / "01-pass.yaml"
    fail_case = tmp_path / "02-fail.yaml"

    _write_case(
        pass_case,
        """
id: diffusion-pass-v01
calculator: diffusion-ep-1d
input:
  format: json-inline
  data:
    mobility: 2.0
    force: 2.0
    temperature: 2.0
expected:
  sigma_close:
    value: 4.0
    tol: 1e-12
citations: [ref-pass]
""",
    )
    _write_case(
        fail_case,
        """
id: diffusion-fail-v01
calculator: diffusion-ep-1d
input:
  format: json-inline
  data:
    mobility: 1.0
    force: 1.0
    temperature: 1.0
expected:
  sigma_close:
    value: 2.0
    tol: 1e-12
citations: [ref-fail]
""",
    )

    out_path = tmp_path / "report.md"
    report_path = write_report(
        [pass_case, fail_case],
        out_path=out_path,
        only_failures=True,
    )
    content = report_path.read_text(encoding="utf-8")

    assert report_path.exists()
    assert "| diffusion-fail-v01 |" in content
    assert "| diffusion-pass-v01 |" not in content
    assert "- Total cases: **2**" in content
    assert "- Pass: **1**" in content
    assert "- Fail: **1**" in content
    assert "- sigma_close failures: **1**" in content


def test_report_main_with_scan_dir_only_failures(tmp_path, monkeypatch) -> None:
    _write_case(
        tmp_path / "pass.yaml",
        """
id: pass-case-v01
calculator: diffusion-ep-1d
input:
  format: json-inline
  data: {mobility: 1.0, force: 1.0, temperature: 1.0}
expected:
  sigma_close:
    value: 1.0
    tol: 1e-12
""",
    )
    _write_case(
        tmp_path / "fail.yaml",
        """
id: fail-case-v01
calculator: diffusion-ep-1d
input:
  format: json-inline
  data: {mobility: 1.0, force: 1.0, temperature: 1.0}
expected:
  sigma_close:
    value: 3.0
    tol: 1e-12
""",
    )
    out_path = tmp_path / "from_main.md"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "report",
            "--scan-dir",
            str(tmp_path),
            "--only-failures",
            "--out",
            str(out_path),
        ],
    )

    rc = report_main()
    content = out_path.read_text(encoding="utf-8")

    assert rc == 0
    assert "| fail-case-v01 |" in content
    assert "| pass-case-v01 |" not in content
