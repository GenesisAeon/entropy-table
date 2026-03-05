from __future__ import annotations

import re
from typing import Any

CLAIM_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CASE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:-v[0-9]+)?$")


def parse_case_ids_from_claim_yaml(claim: dict[str, Any]) -> list[str]:
    evidence = claim.get("evidence")
    if not isinstance(evidence, dict):
        return []
    raw = evidence.get("cases")
    if not isinstance(raw, list):
        return []
    case_ids: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            case_ids.append(item)
        elif isinstance(item, dict):
            case_id = item.get("id")
            if isinstance(case_id, str) and case_id.strip():
                case_ids.append(case_id)
    return case_ids


def parse_claim_ids_from_case_yaml(case: dict[str, Any]) -> list[str]:
    raw = case.get("claims")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, str) and item.strip()]
