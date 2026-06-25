"""Build-time hook: bundle atlas/ and templates/ data into the installable package.

The atlas/ and templates/ directories live at the repo root (where tests and
dev tooling expect them). For pip-installable wheels/sdists, setuptools can
only ship files that live inside the package tree, so we copy them into
src/entropy_table/ before packaging. entropy_table.core.common picks whichever
copy exists at runtime.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py
from setuptools.command.sdist import sdist as _sdist

REPO_ROOT = Path(__file__).resolve().parent
PACKAGE_DIR = REPO_ROOT / "src" / "entropy_table"
BUNDLED_DIRS = ("atlas", "templates")


def _bundle_data() -> None:
    for name in BUNDLED_DIRS:
        src = REPO_ROOT / name
        dst = PACKAGE_DIR / name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)


class build_py(_build_py):
    def run(self) -> None:
        _bundle_data()
        super().run()


class sdist(_sdist):
    def run(self) -> None:
        _bundle_data()
        super().run()


setup(cmdclass={"build_py": build_py, "sdist": sdist})
