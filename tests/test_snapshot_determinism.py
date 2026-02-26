from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "tools"))

from snapshot import build_bundle


def test_bundle_determinism() -> None:
    bundle_a, bytes_a, sha_a = build_bundle("determinism-check", atlas_root=ROOT / "atlas", repo_root=ROOT)
    bundle_b, bytes_b, sha_b = build_bundle("determinism-check", atlas_root=ROOT / "atlas", repo_root=ROOT)

    assert sha_a == sha_b
    assert bytes_a == bytes_b
    assert bundle_a == bundle_b


def test_snapshot_verify_passes(tmp_path: Path) -> None:
    snapshot_id = "20990101-000000Z"
    out_root = tmp_path / "snapshots"

    snapshot = subprocess.run(
        [sys.executable, "tools/release.py", "snapshot", "--id", snapshot_id, "--out", str(out_root)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert snapshot.returncode == 0, snapshot.stderr

    verify = subprocess.run(
        [sys.executable, "tools/release.py", "verify", "--path", str(out_root / snapshot_id)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert verify.returncode == 0, verify.stderr
    assert "Snapshot verification passed" in verify.stdout


def test_sorting_by_id_in_bundle(tmp_path: Path) -> None:
    atlas_root = tmp_path / "atlas"
    (atlas_root / "domains" / "x").mkdir(parents=True)
    (atlas_root / "relations" / "x").mkdir(parents=True)
    (atlas_root / "claims" / "x").mkdir(parents=True)
    (atlas_root / "schema").mkdir(parents=True)

    (atlas_root / "domains" / "x" / "b.yaml").write_text('id: b-domain\nstatus: draft\n', encoding="utf-8")
    (atlas_root / "domains" / "x" / "a.yaml").write_text('id: a-domain\nstatus: draft\n', encoding="utf-8")
    (atlas_root / "relations" / "x" / "b.yaml").write_text('id: b-relation\nstatus: draft\n', encoding="utf-8")
    (atlas_root / "relations" / "x" / "a.yaml").write_text('id: a-relation\nstatus: draft\n', encoding="utf-8")
    (atlas_root / "claims" / "x" / "b.yaml").write_text('id: b-claim\nstatus: draft\n', encoding="utf-8")
    (atlas_root / "claims" / "x" / "a.yaml").write_text('id: a-claim\nstatus: draft\n', encoding="utf-8")

    (atlas_root / "schema" / "domain.schema.json").write_text('{"type":"object"}', encoding="utf-8")
    (atlas_root / "schema" / "relation.schema.json").write_text('{"type":"object"}', encoding="utf-8")

    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    (docs_root / "claims.md").write_text("claim contract", encoding="utf-8")

    bundle, bundle_bytes, _ = build_bundle("sort-check", atlas_root=atlas_root, repo_root=tmp_path)
    parsed = json.loads(bundle_bytes)

    assert [item["id"] for item in bundle["domains"]] == ["a-domain", "b-domain"]
    assert [item["id"] for item in bundle["relations"]] == ["a-relation", "b-relation"]
    assert [item["id"] for item in bundle["claims"]] == ["a-claim", "b-claim"]
    assert [item["id"] for item in parsed["domains"]] == ["a-domain", "b-domain"]
