from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "atlas"
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
