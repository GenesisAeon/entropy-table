from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

CLAIM_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CASE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:-v[0-9]+)?$")


def parse_case_ids_from_claim_yaml(claim: dict[str, Any]) -> list[str]:
    return [binding.id for binding in parse_case_bindings_from_claim_yaml(claim)]


def parse_claim_ids_from_case_yaml(case: dict[str, Any]) -> list[str]:
    raw = case.get("claims")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, str) and item.strip()]



@dataclass(frozen=True)
class ClaimCaseBinding:
    id: str
    description: str | None = None
    compute_ref: str | None = None


def parse_case_bindings_from_claim_yaml(claim: dict[str, Any]) -> list[ClaimCaseBinding]:
    evidence = claim.get("evidence")
    if not isinstance(evidence, dict):
        return []
    raw = evidence.get("cases")
    if not isinstance(raw, list):
        return []

    parsed: list[ClaimCaseBinding] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            parsed.append(ClaimCaseBinding(id=item))
            continue
        if not isinstance(item, dict):
            continue
        case_id = item.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            continue
        description = item.get("description")
        compute_ref = item.get("compute_ref")
        parsed.append(
            ClaimCaseBinding(
                id=case_id,
                description=description if isinstance(description, str) and description.strip() else None,
                compute_ref=compute_ref if isinstance(compute_ref, str) and compute_ref.strip() else None,
            )
        )
    return parsed
