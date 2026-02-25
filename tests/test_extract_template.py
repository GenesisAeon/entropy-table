from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_extract_template_generates_yaml(tmp_path: Path) -> None:
    out_path = tmp_path / "draft-domain.yaml"
    result = subprocess.run(
        [
            sys.executable,
            "tools/extract_domain_from_template.py",
            "--template",
            "templates/domain_template.yaml",
            "--out",
            str(out_path),
            "--set",
            "id=temp-domain",
            "--set",
            "title=Temp Domain",
            "--set",
            "system_type.primary=stochastic_thermodynamics",
            "--set",
            "status=review",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    payload = yaml.safe_load(out_path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    assert payload.get("id") == "temp-domain"
    assert payload.get("title") == "Temp Domain"
