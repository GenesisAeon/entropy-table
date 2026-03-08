"""Run entropy-production calculator cases from YAML specs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import yaml


from entropy_table.core.bindings import parse_claim_ids_from_case_yaml

REPO_ROOT = Path(__file__).resolve().parents[3]


class CaseError(ValueError):
    """Raised when a case spec is invalid."""


def _validate_required(data: dict[str, Any], keys: list[str], where: str) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise CaseError(f"Missing keys in {where}: {', '.join(missing)}")


def _load_case_input(case_dict: dict[str, Any]) -> dict[str, Any]:
    input_spec = case_dict["input"]
    _validate_required(input_spec, ["format"], "input")
    input_format = input_spec["format"]

    if input_format == "json-inline":
        if "data" not in input_spec:
            raise CaseError("Missing keys in input: data")
        if not isinstance(input_spec["data"], dict):
            raise CaseError("input.data must be a JSON object")
        return input_spec["data"]

    if input_format == "json-file":
        if "path" not in input_spec:
            raise CaseError("Missing keys in input: path")
        raw_path = Path(str(input_spec["path"]))
        file_path = raw_path if raw_path.is_absolute() else REPO_ROOT / raw_path
        if not file_path.exists():
            raise CaseError(f"JSON input file does not exist: {file_path}")
        try:
            with file_path.open("r", encoding="utf-8") as fh:
                loaded = json.load(fh)
        except json.JSONDecodeError as exc:
            raise CaseError(f"Invalid JSON in {file_path}: {exc}") from exc
        if not isinstance(loaded, dict):
            raise CaseError("JSON input must be an object")
        return loaded

    raise CaseError(f"Unsupported input.format: {input_format}")


def _compute_ctmc_ep(input_data: dict[str, Any]) -> dict[str, Any]:
    _validate_required(input_data, ["rates", "pi"], "ctmc input")
    rates = input_data["rates"]
    pi = input_data["pi"]
    if not isinstance(rates, list) or not all(isinstance(row, list) for row in rates):
        raise CaseError("ctmc input.rates must be a 2D list")
    if not isinstance(pi, list):
        raise CaseError("ctmc input.pi must be a list")

    n = len(rates)
    if n == 0:
        raise CaseError("ctmc input.rates cannot be empty")
    if len(pi) != n:
        raise CaseError("ctmc input.pi length must match rates size")
    if any(len(row) != n for row in rates):
        raise CaseError("ctmc input.rates must be square")

    sigma = 0.0
    detailed_balance = True
    tol = 1e-10
    for i in range(n):
        for j in range(i + 1, n):
            forward = float(pi[i]) * float(rates[i][j])
            backward = float(pi[j]) * float(rates[j][i])
            if forward > 0.0 and backward > 0.0:
                sigma += (forward - backward) * math.log(forward / backward)
            if abs(forward - backward) > tol:
                detailed_balance = False

    return {"sigma": float(sigma), "detailed_balance": detailed_balance}


def _compute_diffusion_ep_1d(input_data: dict[str, Any]) -> dict[str, Any]:
    _validate_required(input_data, ["mobility", "force", "temperature"], "diffusion input")
    mobility = float(input_data["mobility"])
    force = float(input_data["force"])
    temperature = float(input_data["temperature"])
    if temperature <= 0:
        raise CaseError("diffusion temperature must be > 0")
    sigma = mobility * (force**2) / temperature
    return {"sigma": float(sigma)}


def _compute(calculator: str, input_data: dict[str, Any]) -> dict[str, Any]:
    if calculator == "ctmc-ep":
        return _compute_ctmc_ep(input_data)
    if calculator == "diffusion-ep-1d":
        return _compute_diffusion_ep_1d(input_data)
    raise CaseError(f"Unsupported calculator: {calculator}")


def _evaluate_expected(result: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    sigma = result["sigma"]
    if "sigma_min" in expected and sigma < float(expected["sigma_min"]):
        errors.append(f"sigma {sigma} < sigma_min {expected['sigma_min']}")
    if "sigma_max" in expected and sigma > float(expected["sigma_max"]):
        errors.append(f"sigma {sigma} > sigma_max {expected['sigma_max']}")
    if "sigma_close" in expected:
        close_spec = expected["sigma_close"]
        if not isinstance(close_spec, dict) or "value" not in close_spec:
            errors.append("expected.sigma_close must be {value, tol?}")
        else:
            target = float(close_spec["value"])
            tol = float(close_spec.get("tol", 1e-9))
            if abs(sigma - target) > tol:
                errors.append(f"sigma {sigma} not within {tol} of {target}")
    return errors


def _input_digest(input_data: dict[str, Any]) -> str:
    canonical = json.dumps(input_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:8]


def load_case(path: str | Path) -> dict[str, Any]:
    case_path = Path(path)
    with case_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise CaseError("Case spec must be a mapping")
    _validate_required(data, ["id", "calculator", "input"], "case")
    return data


def run_case(case_dict: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    case_id = str(case_dict.get("id", "<unknown>"))
    calculator = str(case_dict.get("calculator", "<unknown>"))

    try:
        _validate_required(case_dict, ["id", "calculator", "input"], "case")
        input_data = _load_case_input(case_dict)
        computed = _compute(calculator, input_data)
        errors.extend(_evaluate_expected(computed, case_dict.get("expected", {})))
        status = "pass" if not errors else "fail"
        return {
            "case_id": case_id,
            "calculator": calculator,
            "sigma": computed["sigma"],
            "detailed_balance": computed.get("detailed_balance"),
            "status": status,
            "errors": errors,
            "input_digest": _input_digest(input_data),
            "notes": case_dict.get("notes"),
            "citations": case_dict.get("citations", []),
            "claims": parse_claim_ids_from_case_yaml(case_dict),
        }
    except CaseError as exc:
        errors.append(str(exc))
        return {
            "case_id": case_id,
            "calculator": calculator,
            "sigma": float("nan"),
            "detailed_balance": None,
            "status": "fail",
            "errors": errors,
            "input_digest": "",
            "notes": case_dict.get("notes"),
            "citations": case_dict.get("citations", []),
            "claims": parse_claim_ids_from_case_yaml(case_dict),
        }


def run_cases(list_of_paths: list[str | Path]) -> list[dict[str, Any]]:
    return [run_case(load_case(path)) for path in list_of_paths]


def discover_cases(root_dir: str | Path, *, pattern: str = "*.yaml") -> list[Path]:
    """Discover case files under ``root_dir`` with deterministic ordering."""
    root = Path(root_dir)
    if not root.exists() or not root.is_dir():
        return []

    discovered: list[Path] = []
    for path in root.rglob(pattern):
        if not path.is_file():
            continue
        rel_path = path.relative_to(root)
        if path.name.startswith(".") or any(part.startswith(".") for part in rel_path.parts):
            continue
        discovered.append(path)

    return sorted(
        discovered,
        key=lambda path: (str(path.relative_to(root).parent), path.name),
    )


def resolve_case_paths(
    explicit_cases: list[str | Path] | None,
    scan_dir: str | Path | None,
) -> list[Path]:
    """Union explicit and scanned case paths using deterministic ordering."""
    combined: dict[Path, Path] = {}

    for item in explicit_cases or []:
        path = Path(item)
        combined[path.resolve()] = path

    if scan_dir:
        for item in discover_cases(scan_dir):
            combined[item.resolve()] = item

    return [combined[key] for key in sorted(combined)]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run compute cases")
    parser.add_argument("--case", action="append", dest="cases", help="Path to case YAML")
    parser.add_argument(
        "--scan-dir",
        default="staging/cases/",
        help="Directory of case YAML files to scan (default: staging/cases/)",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    case_paths = resolve_case_paths(args.cases, args.scan_dir)
    results = run_cases(case_paths)
    for item in results:
        print(f"{item['case_id']}: sigma={item['sigma']:.12g} status={item['status']}")
    return 0 if all(item["status"] == "pass" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
