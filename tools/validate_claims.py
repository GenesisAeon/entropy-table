from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import ROOT, domain_files, load_yaml, relation_files
from bindings import CASE_ID_RE, CLAIM_ID_RE, parse_case_ids_from_claim_yaml

CLAIM_KINDS = {"definition", "theorem", "lemma", "heuristic", "empirical", "limitation"}
CLAIM_STATUS = {"draft", "review", "stable"}


def _is_valid_case_item(case: Any) -> bool:
    if isinstance(case, str):
        return bool(case.strip())
    if not isinstance(case, dict):
        return False

    case_id = case.get("id")
    if case_id is not None and (not isinstance(case_id, str) or not case_id.strip()):
        return False

    description = case.get("description")
    if description is not None and (not isinstance(description, str) or not description.strip()):
        return False

    compute_ref = case.get("compute_ref")
    if compute_ref is not None and (not isinstance(compute_ref, str) or not compute_ref.strip()):
        return False

    return True


def _load_module_from_path(module_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_compute_case_hooks(claim: dict[str, Any], errors: list[str], where: str) -> None:
    status = claim.get("status")
    if status not in {"review", "stable"}:
        return

    evidence = claim.get("evidence")
    if not isinstance(evidence, dict):
        return

    cases = evidence.get("cases")
    if not isinstance(cases, list):
        return

    for idx, case in enumerate(cases):
        if not isinstance(case, dict):
            continue

        compute_ref = case.get("compute_ref")
        if not isinstance(compute_ref, str) or not compute_ref.strip():
            continue

        case_label = case.get("id") if isinstance(case.get("id"), str) and case.get("id").strip() else f"index={idx}"

        try:
            module_path = ROOT / compute_ref
            if not module_path.exists():
                raise FileNotFoundError(f"compute_ref path does not exist: {compute_ref}")

            module = _load_module_from_path(module_path)
            verify = getattr(module, "verify_claim", None)
            if not callable(verify):
                raise AttributeError("verify_claim() function is missing or not callable")

            result = verify()
            if not isinstance(result, bool):
                raise TypeError("verify_claim() must return a bool")
            if not result:
                raise AssertionError("verify_claim() returned False")
        except Exception as exc:  # noqa: BLE001 - must never crash validation pipeline
            errors.append(
                f"{where}: compute evidence failed for case '{case_label}' via '{compute_ref}': {exc}"
            )


def discover_domain_ids() -> set[str]:
    ids: set[str] = set()
    for path in domain_files():
        domain_id = load_yaml(path).get("id")
        if isinstance(domain_id, str):
            ids.add(domain_id)
    return ids


def discover_relation_ids() -> set[str]:
    ids: set[str] = set()
    for path in relation_files():
        relation_id = load_yaml(path).get("id")
        if isinstance(relation_id, str):
            ids.add(relation_id)
    return ids


def expect_string(claim: dict, key: str, errors: list[str], where: str) -> str | None:
    value = claim.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{where}: '{key}' must be a non-empty string")
        return None
    return value


def validate_claim_file(
    path: Path,
    domain_ids: set[str],
    relation_ids: set[str],
) -> tuple[str | None, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    where = str(path)

    try:
        claim = load_yaml(path)
    except Exception as exc:  # pragma: no cover - defensive
        return None, [f"{where}: failed to parse YAML ({exc})"], []

    claim_id = expect_string(claim, "id", errors, where)
    if claim_id and not CLAIM_ID_RE.match(claim_id):
        errors.append(f"{where}: id '{claim_id}' does not match regex {CLAIM_ID_RE.pattern}")

    title = claim.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append(f"{where}: 'title' must be a non-empty string")

    domain_ref = claim.get("domain_ref")
    if not isinstance(domain_ref, str) or not domain_ref.strip():
        errors.append(f"{where}: 'domain_ref' must be a non-empty string")
    elif domain_ref not in domain_ids:
        errors.append(f"{where}: domain_ref '{domain_ref}' does not match any known domain id")

    kind = claim.get("claim_kind")
    if kind not in CLAIM_KINDS:
        errors.append(f"{where}: claim_kind must be one of {sorted(CLAIM_KINDS)}")

    statement = claim.get("statement")
    if not isinstance(statement, dict):
        errors.append(f"{where}: 'statement' must be an object")
    else:
        text = statement.get("text")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"{where}: statement.text must be a non-empty string")
        latex = statement.get("latex")
        if latex is not None and not isinstance(latex, str):
            errors.append(f"{where}: statement.latex must be a string when provided")

    assumptions = claim.get("assumptions")
    if not isinstance(assumptions, list) or not all(isinstance(item, str) and item.strip() for item in assumptions):
        errors.append(f"{where}: assumptions must be a list of non-empty strings")
    elif kind != "definition" and len(assumptions) < 1:
        errors.append(f"{where}: assumptions must contain at least one entry unless claim_kind=definition")

    falsification = claim.get("falsification")
    must_fail_refs: list[str] | None = None
    if not isinstance(falsification, dict):
        errors.append(f"{where}: 'falsification' must be an object")
    else:
        refs = falsification.get("must_fail_refs")
        if not isinstance(refs, list) or not all(isinstance(item, str) and item.strip() for item in refs):
            errors.append(f"{where}: falsification.must_fail_refs must be a list of non-empty strings")
        else:
            must_fail_refs = refs
            if kind != "definition" and len(refs) < 1:
                errors.append(
                    f"{where}: falsification.must_fail_refs must contain at least one entry unless claim_kind=definition"
                )
        notes = falsification.get("notes")
        if notes is not None and not isinstance(notes, str):
            errors.append(f"{where}: falsification.notes must be a string when provided")

    evidence = claim.get("evidence")
    citations: list[str] | None = None
    if not isinstance(evidence, dict):
        errors.append(f"{where}: 'evidence' must be an object")
    else:
        citation_refs = evidence.get("citations")
        if not isinstance(citation_refs, list) or not all(
            isinstance(item, str) and item.strip() for item in citation_refs
        ):
            errors.append(f"{where}: evidence.citations must be a list of non-empty strings")
        else:
            citations = citation_refs

        cases = evidence.get("cases")
        if cases is not None and (not isinstance(cases, list) or not all(_is_valid_case_item(item) for item in cases)):
            errors.append(
                f"{where}: evidence.cases must be a list of non-empty strings or case objects when provided"
            )
        else:
            for case_id in parse_case_ids_from_claim_yaml(claim):
                if not CASE_ID_RE.match(case_id):
                    errors.append(f"{where}: evidence.cases contains invalid case id '{case_id}'")

        provenance = evidence.get("provenance")
        if not isinstance(provenance, str) or not provenance.strip():
            errors.append(f"{where}: evidence.provenance must be a non-empty string")

    status = claim.get("status")
    if status not in CLAIM_STATUS:
        errors.append(f"{where}: status must be one of {sorted(CLAIM_STATUS)}")
    elif status in {"review", "stable"} and citations is not None and len(citations) < 1:
        errors.append(f"{where}: evidence.citations must contain at least one citation for status={status}")
    elif status in {"review", "stable"} and len(parse_case_ids_from_claim_yaml(claim)) < 1:
        warnings.append(f"{where}: review/stable claim has 0 evidence.cases")

    _run_compute_case_hooks(claim, errors, where)

    relations_touched = claim.get("relations_touched")
    if relations_touched is not None:
        if not isinstance(relations_touched, list) or not all(
            isinstance(item, str) and item.strip() for item in relations_touched
        ):
            errors.append(f"{where}: relations_touched must be a list of non-empty strings when provided")
        else:
            for relation_id in relations_touched:
                if relation_id not in relation_ids:
                    errors.append(f"{where}: relations_touched contains unknown relation id '{relation_id}'")

    tags = claim.get("tags")
    if tags is not None:
        if not isinstance(tags, list) or not all(isinstance(item, str) and item.strip() for item in tags):
            errors.append(f"{where}: tags must be a list of non-empty strings when provided")
        else:
            for tag in tags:
                if not CLAIM_ID_RE.match(tag):
                    errors.append(f"{where}: tags contains invalid kebab-case tag '{tag}'")

    notes = claim.get("notes")
    if notes is not None and not isinstance(notes, str):
        errors.append(f"{where}: notes must be a string when provided")

    if claim_id:
        expected_file = f"claim-{claim_id}.yaml"
        if path.name != expected_file:
            errors.append(f"{where}: file name must be '{expected_file}'")

    if isinstance(domain_ref, str) and domain_ref:
        if path.parent.name != domain_ref:
            errors.append(f"{where}: parent directory must match domain_ref '{domain_ref}'")

    return claim_id, errors, warnings


def iter_claim_files(claims_root: Path) -> list[Path]:
    if not claims_root.exists():
        return []
    return sorted(claims_root.glob("**/*.yaml"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate atlas claim files")
    parser.add_argument("--claims-root", default="atlas/claims", help="Path containing claim YAML files")
    parser.add_argument("--atlas-root", default="atlas", help="Atlas root containing domains and relations")
    args = parser.parse_args(argv)

    claims_root = Path(args.claims_root)
    atlas_root = Path(args.atlas_root)
    if not claims_root.is_absolute():
        claims_root = ROOT / claims_root
    if not atlas_root.is_absolute():
        atlas_root = ROOT / atlas_root

    # Keep discovery behavior aligned with existing tools by using common.py roots unless explicitly redirected.
    if atlas_root != ROOT / "atlas":
        domain_glob = sorted((atlas_root / "domains").glob("**/*.yaml"))
        relation_glob = sorted((atlas_root / "relations").glob("**/*.yaml"))
        domain_ids: set[str] = set()
        for path in domain_glob:
            domain_id = load_yaml(path).get("id")
            if isinstance(domain_id, str):
                domain_ids.add(domain_id)
        relation_ids: set[str] = set()
        for path in relation_glob:
            relation_id = load_yaml(path).get("id")
            if isinstance(relation_id, str):
                relation_ids.add(relation_id)
    else:
        domain_ids = discover_domain_ids()
        relation_ids = discover_relation_ids()

    claim_paths = iter_claim_files(claims_root)
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: dict[str, Path] = {}

    for path in claim_paths:
        claim_id, claim_errors, claim_warnings = validate_claim_file(path, domain_ids, relation_ids)
        errors.extend(claim_errors)
        warnings.extend(claim_warnings)
        if claim_id:
            prev = seen_ids.get(claim_id)
            if prev is not None:
                errors.append(f"{path}: duplicate claim id '{claim_id}' also found at {prev}")
            else:
                seen_ids[claim_id] = path

    if errors:
        print(f"Claim validation failed with {len(errors)} error(s):")
        for error in sorted(errors):
            print(f" - {error}")
        return 1

    if warnings:
        print(f"Claim validation warnings ({len(warnings)}):")
        for warning in sorted(warnings):
            print(f" - WARNING: {warning}")

    print(f"Claim validation passed: {len(claim_paths)} claim(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
