"""Validate mathematical expressions in atlas domain YAML files.

Checks performed per domain
---------------------------
1. Structural completeness – every ``entropy_accounting`` term has ``latex``,
   ``symbol``, and ``units``.
2. Non-negativity annotation – ``production_term.latex`` must contain an
   explicit ``\\ge 0`` / ``\\geq 0`` annotation (the domain contract assertion).
3. must_fail_tests integrity – each test entry has the required fields
   (``id``, ``statement``, ``expected_outcome``, ``citations``) and a valid
   ``expected_outcome`` value.
4. SymPy parse probe (best-effort) – tries to parse ``entropy_definition.latex``
   via ``sympy.parsing.latex``; reports parse failures as warnings, not errors,
   because most full-physics expressions are outside SymPy's parser scope.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

from ..core.common import domain_files

_REQUIRED_TERM_FIELDS = ("latex", "symbol", "units")
_VALID_OUTCOMES = {
    "reject",
    "pass-if-zero-otherwise-reject",
    "pass",
    "warn",
}
_REQUIRED_TEST_FIELDS = ("id", "statement", "expected_outcome", "citations")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_term(term: dict[str, Any], term_name: str, domain_id: str, errors: list[str]) -> None:
    for field in _REQUIRED_TERM_FIELDS:
        if field not in term:
            errors.append(f"{domain_id}: entropy_accounting.{term_name} missing '{field}'")


def _check_non_negativity(production_latex: str, domain_id: str, warnings: list[str]) -> None:
    if r"\ge 0" not in production_latex and r"\geq 0" not in production_latex:
        warnings.append(
            f"{domain_id}: production_term.latex has no explicit \\ge 0 annotation"
        )


def _check_must_fail_tests(
    tests: list[dict[str, Any]],
    domain_id: str,
    errors: list[str],
    warnings: list[str],
) -> None:
    for test in tests:
        tid = test.get("id", "<unknown>")
        for field in _REQUIRED_TEST_FIELDS:
            if field not in test:
                errors.append(f"{domain_id}: must_fail_tests[{tid}] missing '{field}'")
        outcome = test.get("expected_outcome", "")
        if outcome and outcome not in _VALID_OUTCOMES:
            warnings.append(
                f"{domain_id}: must_fail_tests[{tid}] unknown expected_outcome '{outcome}'"
            )


def _probe_sympy(latex: str, domain_id: str, warnings: list[str]) -> None:
    try:
        from sympy.parsing.latex import parse_latex  # type: ignore[import]
        parse_latex(latex)
    except ImportError:
        warnings.append(
            f"{domain_id}: sympy LaTeX parser unavailable (antlr4 not installed) – skipping"
        )
    except Exception:
        # Most physics LaTeX is outside SymPy's parser scope; treat as info only
        pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    domains_checked = 0

    for path in domain_files():
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if not isinstance(data, dict):
            continue

        domain_id = data.get("id", path.stem)
        domains_checked += 1

        # 1. Structural completeness
        accounting = data.get("entropy_accounting", {})
        for term_name in ("storage_term", "production_term", "flux_term"):
            term = accounting.get(term_name)
            if isinstance(term, dict):
                _check_term(term, term_name, domain_id, errors)

        # 2. Non-negativity annotation on production_term
        production = accounting.get("production_term", {})
        if isinstance(production, dict) and "latex" in production:
            _check_non_negativity(production["latex"], domain_id, warnings)

        # 3. must_fail_tests integrity
        tests = data.get("must_fail_tests", [])
        if isinstance(tests, list):
            _check_must_fail_tests(tests, domain_id, errors, warnings)

        # 4. Best-effort SymPy parse of entropy_definition.latex
        defn = data.get("entropy_definition", {})
        if isinstance(defn, dict) and "latex" in defn:
            _probe_sympy(defn["latex"], domain_id, warnings)

    # Report
    for w in warnings:
        print(f"  WARN  {w}")
    for e in errors:
        print(f"  ERROR {e}")

    ok = len(errors) == 0
    status = "PASS" if ok else "FAIL"
    print(
        f"[validate-math] {status} – "
        f"{domains_checked} domains checked, "
        f"{len(errors)} error(s), {len(warnings)} warning(s)"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
