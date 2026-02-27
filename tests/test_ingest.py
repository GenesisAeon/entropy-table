from __future__ import annotations

from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from ingest import ingest_draft


def _build_temp_atlas(tmp_path: Path) -> Path:
    atlas = tmp_path / "atlas"
    (atlas / "domains" / "01_physics").mkdir(parents=True)
    (atlas / "relations" / "01_physics").mkdir(parents=True)
    (atlas / "claims").mkdir()
    (atlas / "schema").mkdir()
    (atlas / "bibliography").mkdir()

    (atlas / "schema" / "domain.schema.json").write_text(
        (ROOT / "atlas" / "schema" / "domain.schema.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (atlas / "schema" / "relation.schema.json").write_text(
        (ROOT / "atlas" / "schema" / "relation.schema.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    refs = {
        "c1": {
            "type": "misc",
            "title": "Fixture citation",
            "authors": ["Atlas Team"],
            "year": 2024,
            "doi": "10.0000/c1",
        }
    }
    (atlas / "bibliography" / "refs.yaml").write_text(yaml.safe_dump(refs, sort_keys=True), encoding="utf-8")
    return atlas


def test_invalid_draft_fails_and_not_copied(tmp_path: Path) -> None:
    atlas = _build_temp_atlas(tmp_path)
    draft = tmp_path / "invalid-domain.yaml"
    draft.write_text("id: only-id\n", encoding="utf-8")

    ok, message, target = ingest_draft(draft, "domain", "01_physics", atlas_root=atlas)

    assert not ok
    assert "failed" in message.lower()
    assert target is None
    assert not (atlas / "domains" / "01_physics" / draft.name).exists()


def test_valid_draft_succeeds_and_is_copied(tmp_path: Path) -> None:
    atlas = _build_temp_atlas(tmp_path)
    draft = tmp_path / "domain-valid.yaml"
    draft.write_text((ROOT / "tests" / "fixtures" / "pass" / "domain_valid.yaml").read_text(encoding="utf-8"), encoding="utf-8")

    ok, message, target = ingest_draft(draft, "domain", "01_physics", atlas_root=atlas)

    assert ok
    assert "successful" in message.lower()
    assert target == atlas / "domains" / "01_physics" / draft.name
    assert target.exists()


def test_existing_target_fails_without_force(tmp_path: Path) -> None:
    atlas = _build_temp_atlas(tmp_path)
    draft = tmp_path / "domain-valid.yaml"
    draft.write_text((ROOT / "tests" / "fixtures" / "pass" / "domain_valid.yaml").read_text(encoding="utf-8"), encoding="utf-8")

    existing_target = atlas / "domains" / "01_physics" / draft.name
    existing_target.write_text("id: existing\n", encoding="utf-8")

    ok, message, target = ingest_draft(draft, "domain", "01_physics", atlas_root=atlas)

    assert not ok
    assert "already exists" in message.lower()
    assert target == existing_target
