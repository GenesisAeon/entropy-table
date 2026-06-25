from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
PACKAGE_DIR = Path(__file__).resolve().parents[1]

# When installed from a wheel, atlas/ data is bundled inside the package
# (see setup.py); in a source checkout it lives at the repo root instead.
_BUNDLED_ATLAS = PACKAGE_DIR / "atlas"
ATLAS = _BUNDLED_ATLAS if _BUNDLED_ATLAS.is_dir() else ROOT / "atlas"

_BUNDLED_TEMPLATES = PACKAGE_DIR / "templates"
TEMPLATES = _BUNDLED_TEMPLATES if _BUNDLED_TEMPLATES.is_dir() else ROOT / "templates"
DOMAINS_DIR = ATLAS / "domains"
RELATIONS_DIR = ATLAS / "relations"
DOMAIN_SCHEMA_PATH = ATLAS / "schema" / "domain.schema.json"
RELATION_SCHEMA_PATH = ATLAS / "schema" / "relation.schema.json"


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML object at the top level")
    return data


def domain_files() -> list[Path]:
    return sorted(DOMAINS_DIR.glob("**/*.yaml"))


def relation_files() -> list[Path]:
    return sorted(RELATIONS_DIR.glob("**/*.yaml"))
