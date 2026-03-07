from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

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


try:
    import fcntl as _fcntl

    _HAS_FCNTL = True
except ImportError:
    _HAS_FCNTL = False


@contextmanager
def locked_atomic_write(target_path: Path) -> Generator[Path, None, None]:
    """Atomic, parallel-safe file write using a lock file and os.replace().

    Yields a temporary Path to write content into. On successful exit the
    temporary file is atomically renamed to *target_path*. The lock file
    serialises concurrent writers on Unix (fcntl); on Windows the atomic
    rename alone provides sufficient protection for typical CI scenarios.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = target_path.with_suffix(".lock")

    lock_fd = open(lock_path, "w")  # noqa: WPS515
    if _HAS_FCNTL:
        _fcntl.flock(lock_fd, _fcntl.LOCK_EX)

    fd, tmp_str = tempfile.mkstemp(dir=target_path.parent, prefix=".tmp_", suffix=target_path.suffix)
    tmp_path = Path(tmp_str)
    os.close(fd)

    try:
        yield tmp_path
        os.replace(tmp_path, target_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        if _HAS_FCNTL:
            _fcntl.flock(lock_fd, _fcntl.LOCK_UN)
        lock_fd.close()
        try:
            lock_path.unlink()
        except OSError:
            pass


def domain_files() -> list[Path]:
    return sorted(DOMAINS_DIR.glob("**/*.yaml"))


def relation_files() -> list[Path]:
    return sorted(RELATIONS_DIR.glob("**/*.yaml"))
