from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def test_release_pack_generates_zip_with_required_files(tmp_path: Path) -> None:
    out_dir = tmp_path / "packs"

    completed = subprocess.run(
        [sys.executable, "tools/release.py", "--version", "v9.9.9-test", "--out", str(out_dir)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr

    archive = out_dir / "entropy-table-pack-v9.9.9-test.zip"
    assert archive.exists()

    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())

    assert "bundle.json" in names
    assert "MANIFEST.txt" in names
