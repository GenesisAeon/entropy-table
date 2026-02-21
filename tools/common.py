from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parents[1]
ATLAS_DIR = ROOT / "atlas"
SCHEMA_PATH = ATLAS_DIR / "schema" / "domain.schema.json"
DOMAINS_DIR = ATLAS_DIR / "domains"


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def domain_files() -> Iterable[Path]:
    return sorted(DOMAINS_DIR.glob("**/*.yaml"))
