from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from entropy_table.core.common import ROOT, domain_files, load_yaml, relation_files
from entropy_table.core.bindings import CASE_ID_RE, CLAIM_ID_RE, parse_case_ids_from_claim_yaml

CLAIM_KINDS = {"definition", "theorem", "lemma", "heuristic", "empirical", "limitation"}
CLAIM_STATUS = {"draft", "review", "stable"}


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


def expect_string(claim: dict, key: str, errors: list[dict], where: str) -> str | None:
    value = claim.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append({"file": where, "error_type": "ValidationError", "message": f"'{key}' must be a non-empty string"})
        return None
    return value


def validate_claim_file(
    path: Path,
    domain_ids: set[str],
    relation_ids: set[str],
) -> tuple[str | None, list[dict], list[dict]]:
    errors: list[dict] = []
    warnings: list[dict] = []
    where = str(path)

    def add_error(etype: str, msg: str):
        errors.append({"file": where, "error_type": etype, "message": msg})

    def add_warning(etype: str, msg: str):
        warnings.append({"file": where, "error_type": etype, "message": msg})

    try:
        claim = load_yaml(path)
    except Exception as exc:  # pragma: no cover - defensive
        add_error("ParseError", f"failed to parse YAML ({exc})")
        return None, errors, warnings

    claim_id = expect_string(claim, "id", errors, where)
    if claim_id and not CLAIM_ID_RE.match(claim_id):
        add_error("ValidationError", f"id '{claim_id}' does not match regex {CLAIM_ID_RE.pattern}")

    title = claim.get("title")
    if not isinstance(title, str) or not title.strip():
        add_error("ValidationError", "'title' must be a non-empty string")

    domain_ref = claim.get("domain_ref")
    if not isinstance(domain_ref, str) or not domain_ref.strip():
        add_error("ValidationError", "'domain_ref' must be a non-empty string")
    elif domain_ref not in domain_ids:
        add_error("CrossReferenceError", f"domain_ref '{domain_ref}' does not match any known domain id")

    kind = claim.get("claim_kind")
    if kind not in CLAIM_KINDS:
        add_error("ValidationError", f"claim_kind must be one of {sorted(CLAIM_KINDS)}")

    statement = claim.get("statement")
    if not isinstance(statement, dict):
        add_error("ValidationError", "'statement' must be an object")
    else:
        text = statement.get("text")
        if not isinstance(text, str) or not text.strip():
            add_error("ValidationError", "statement.text must be a non-empty string")
        latex = statement.get("latex")
        if latex is not None and not isinstance(latex, str):
            add_error("ValidationError", "statement.latex must be a string when provided")

    assumptions = claim.get("assumptions")
    if not isinstance(assumptions, list) or not all(isinstance(item, str) and item.strip() for item in assumptions):
        add_error("ValidationError", "assumptions must be a list of non-empty strings")
    elif kind != "definition" and len(assumptions) < 1:
        add_error("ValidationError", "assumptions must contain at least one entry unless claim_kind=definition")

    falsification = claim.get("falsification")
    must_fail_refs: list[str] | None = None
    if not isinstance(falsification, dict):
        add_error("ValidationError", "'falsification' must be an object")
    else:
        refs = falsification.get("must_fail_refs")
        if not isinstance(refs, list) or not all(isinstance(item, str) and item.strip() for item in refs):
            add_error("ValidationError", "falsification.must_fail_refs must be a list of non-empty strings")
        else:
            must_fail_refs = refs
            if kind != "definition" and len(refs) < 1:
                add_error("ValidationError", "falsification.must_fail_refs must contain at least one entry unless claim_kind=definition")
        notes = falsification.get("notes")
        if notes is not None and not isinstance(notes, str):
            add_error("ValidationError", "falsification.notes must be a string when provided")

    evidence = claim.get("evidence")
    citations: list[str] | None = None
    if not isinstance(evidence, dict):
        add_error("ValidationError", "'evidence' must be an object")
    else:
        citation_refs = evidence.get("citations")
        if not isinstance(citation_refs, list) or not all(
            isinstance(item, str) and item.strip() for item in citation_refs
        ):
            add_error("ValidationError", "evidence.citations must be a list of non-empty strings")
        else:
            citations = citation_refs

        cases = evidence.get("cases")
        if cases is not None and (
            not isinstance(cases, list) or not all(isinstance(item, str) and item.strip() for item in cases)
        ):
            add_error("ValidationError", "evidence.cases must be a list of non-empty strings when provided")
        else:
            for case_id in parse_case_ids_from_claim_yaml(claim):
                if not CASE_ID_RE.match(case_id):
                    add_error("ValidationError", f"evidence.cases contains invalid case id '{case_id}'")

        provenance = evidence.get("provenance")
        if not isinstance(provenance, str) or not provenance.strip():
            add_error("ValidationError", "evidence.provenance must be a non-empty string")

    status = claim.get("status")
    if status not in CLAIM_STATUS:
        add_error("ValidationError", f"status must be one of {sorted(CLAIM_STATUS)}")
    elif status in {"review", "stable"} and citations is not None and len(citations) < 1:
        add_error("ValidationError", f"evidence.citations must contain at least one citation for status={status}")
    elif status in {"review", "stable"} and len(parse_case_ids_from_claim_yaml(claim)) < 1:
        add_warning("ValidationWarning", "review/stable claim has 0 evidence.cases")

    relations_touched = claim.get("relations_touched")
    if relations_touched is not None:
        if not isinstance(relations_touched, list) or not all(
            isinstance(item, str) and item.strip() for item in relations_touched
        ):
            add_error("ValidationError", "relations_touched must be a list of non-empty strings when provided")
        else:
            for relation_id in relations_touched:
                if relation_id not in relation_ids:
                    add_error("CrossReferenceError", f"relations_touched contains unknown relation id '{relation_id}'")

    tags = claim.get("tags")
    if tags is not None:
        if not isinstance(tags, list) or not all(isinstance(item, str) and item.strip() for item in tags):
            add_error("ValidationError", "tags must be a list of non-empty strings when provided")
        else:
            for tag in tags:
                if not CLAIM_ID_RE.match(tag):
                    add_error("ValidationError", f"tags contains invalid kebab-case tag '{tag}'")

    notes = claim.get("notes")
    if notes is not None and not isinstance(notes, str):
        add_error("ValidationError", "notes must be a string when provided")

    if claim_id:
        expected_file = f"claim-{claim_id}.yaml"
        if path.name != expected_file:
            add_error("ValidationError", f"file name must be '{expected_file}'")

    if isinstance(domain_ref, str) and domain_ref:
        if path.parent.name != domain_ref:
            add_error("ValidationError", f"parent directory must match domain_ref '{domain_ref}'")

    return claim_id, errors, warnings


def iter_claim_files(claims_root: Path) -> list[Path]:
    if not claims_root.exists():
        return []
    return sorted(claims_root.glob("**/*.yaml"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate atlas claim files")
    parser.add_argument("--claims-root", default="atlas/claims", help="Path containing claim YAML files")
    parser.add_argument("--atlas-root", default="atlas", help="Atlas root containing domains and relations")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args(argv)

    claims_root = Path(args.claims_root)
    atlas_root = Path(args.atlas_root)
    if not claims_root.is_absolute():
        claims_root = ROOT / claims_root
    if not atlas_root.is_absolute():
        atlas_root = ROOT / atlas_root

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
    errors: list[dict] = []
    warnings: list[dict] = []
    seen_ids: dict[str, Path] = {}

    for path in claim_paths:
        claim_id, claim_errors, claim_warnings = validate_claim_file(path, domain_ids, relation_ids)
        errors.extend(claim_errors)
        warnings.extend(claim_warnings)
        if claim_id:
            prev = seen_ids.get(claim_id)
            if prev is not None:
                errors.append({
                    "file": str(path),
                    "error_type": "CrossReferenceError",
                    "message": f"duplicate claim id '{claim_id}' also found at {prev}"
                })
            else:
                seen_ids[claim_id] = path

    summary = {
        "total_claims": len(claim_paths),
        "valid": len(errors) == 0,
        "error_count": len(errors),
        "warning_count": len(warnings)
    }

    if args.json:
        output = {
            "summary": summary,
            "errors": errors,
            "warnings": warnings
        }
        print(json.dumps(output, indent=2))
    else:
        if errors:
            print(f"Claim validation failed with {len(errors)} error(s):")
            for err in sorted(errors, key=lambda x: (x['file'], x['message'])):
                print(f" - {err['file']}: [{err['error_type']}] {err['message']}")

        if warnings:
            print(f"Claim validation warnings ({len(warnings)}):")
            for warn in sorted(warnings, key=lambda x: (x['file'], x['message'])):
                print(f" - WARNING: {warn['file']}: [{warn['error_type']}] {warn['message']}")

        if not errors:
            print(f"Claim validation passed: {summary['total_claims']} claim(s).")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
