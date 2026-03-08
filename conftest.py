"""Root conftest.py – makes entropy_table importable during pytest runs.

Adds src/ to sys.path so that `import entropy_table` works without an
editable install.  Also exposes the commands/ and core/ sub-packages at the
top level so that legacy test flat-imports (e.g. `from analyze_health import
...`, `from compute.case_runner import ...`) continue to resolve.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"

# Make `import entropy_table` work
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Flat-import compat: `from analyze_health import ...`
_COMMANDS = str(SRC / "entropy_table" / "commands")
if _COMMANDS not in sys.path:
    sys.path.insert(0, _COMMANDS)

# Flat-import compat: `from compute.xxx import ...`
_ET = str(SRC / "entropy_table")
if _ET not in sys.path:
    sys.path.insert(0, _ET)

# Flat-import compat: `from common import ...`, `from bindings import ...`
_CORE = str(SRC / "entropy_table" / "core")
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)
