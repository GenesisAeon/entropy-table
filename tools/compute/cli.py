"""CLI wrappers for toy entropy-production calculators."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .ctmc_ep import is_detailed_balance, schnakenberg_ep_rate
from .diffusion_ep_1d import diffusion_ep_rate_1d


def _load_json(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("input JSON must be an object")
    return payload


def _cmd_ctmc_ep(path: str) -> int:
    payload = _load_json(path)
    if "p" not in payload or "W" not in payload:
        raise ValueError("ctmc-ep input requires keys: p, W")

    sigma = schnakenberg_ep_rate(payload["p"], payload["W"])
    db = is_detailed_balance(payload["p"], payload["W"])
    print(f"sigma={sigma}")
    print(f"detailed_balance={str(db).lower()}")
    return 0


def _cmd_diffusion_ep_1d(path: str) -> int:
    payload = _load_json(path)
    required = {"p", "J", "D", "dx"}
    missing = sorted(required - payload.keys())
    if missing:
        raise ValueError(f"diffusion-ep-1d input missing keys: {', '.join(missing)}")

    sigma = diffusion_ep_rate_1d(payload["p"], payload["J"], payload["D"], payload["dx"])
    print(f"sigma={sigma}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Toy entropy-production calculators")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ctmc = subparsers.add_parser("ctmc-ep", help="Compute CTMC Schnakenberg EP rate")
    ctmc.add_argument("--in", dest="input_path", required=True, help="Input JSON file")

    diffusion = subparsers.add_parser("diffusion-ep-1d", help="Compute 1D diffusion EP rate")
    diffusion.add_argument("--in", dest="input_path", required=True, help="Input JSON file")

    return parser


def main() -> int:
    args = _build_parser().parse_args()
    if args.command == "ctmc-ep":
        return _cmd_ctmc_ep(args.input_path)
    if args.command == "diffusion-ep-1d":
        return _cmd_diffusion_ep_1d(args.input_path)
    raise ValueError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
