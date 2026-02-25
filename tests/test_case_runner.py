from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from compute.case_runner import load_case, run_case


def test_run_case_json_inline_passes_sigma_close(tmp_path) -> None:
    case_path = tmp_path / "ctmc_case.yaml"
    case_path.write_text(
        """
id: ctmc-inline
calculator: ctmc-ep
input:
  format: json-inline
  data:
    pi: [0.5, 0.5]
    rates:
      - [0.0, 1.0]
      - [1.0, 0.0]
expected:
  sigma_close:
    value: 0.0
    tol: 1e-12
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = run_case(load_case(case_path))

    assert isinstance(result["sigma"], float)
    assert result["status"] == "pass"
    assert result["errors"] == []


def test_run_case_json_file_passes_bounds(tmp_path) -> None:
    json_path = tmp_path / "diff_input.json"
    json_path.write_text(
        json.dumps({"mobility": 2.0, "force": 2.0, "temperature": 2.0}),
        encoding="utf-8",
    )

    case_path = tmp_path / "diff_case.yaml"
    case_path.write_text(
        f"""
id: diffusion-file
calculator: diffusion-ep-1d
input:
  format: json-file
  path: {json_path}
expected:
  sigma_min: 3.9
  sigma_max: 4.1
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = run_case(load_case(case_path))

    assert isinstance(result["sigma"], float)
    assert result["status"] == "pass"
    assert result["errors"] == []


def test_run_case_fails_expected_constraint(tmp_path) -> None:
    case_path = tmp_path / "diff_fail.yaml"
    case_path.write_text(
        """
id: diffusion-fail
calculator: diffusion-ep-1d
input:
  format: json-inline
  data:
    mobility: 1.0
    force: 1.0
    temperature: 1.0
expected:
  sigma_max: 0.5
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = run_case(load_case(case_path))

    assert result["status"] == "fail"
    assert result["errors"]
