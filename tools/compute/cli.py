from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.compute.ctmc_ep import is_detailed_balance, schnakenberg_ep_rate
from tools.compute.diffusion_ep_1d import diffusion_ep_rate_1d


def _load_json(path: str) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object")
    return data


def cmd_ctmc_ep(args: argparse.Namespace) -> int:
    data = _load_json(args.input_path)
    sigma = schnakenberg_ep_rate(data["p"], data["W"])
    detailed_balance = is_detailed_balance(data["p"], data["W"])
    print(f"sigma={sigma}")
    print(f"detailed_balance={str(detailed_balance).lower()}")
    return 0


def cmd_diffusion_ep_1d(args: argparse.Namespace) -> int:
    data = _load_json(args.input_path)
    sigma = diffusion_ep_rate_1d(data["p"], data["J"], data["D"], data["dx"])
    print(f"sigma={sigma}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Toy entropy production calculators")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ctmc = subparsers.add_parser("ctmc-ep", help="Compute CTMC Schnakenberg EP rate")
    ctmc.add_argument("--in", dest="input_path", required=True, help="Input JSON file path")
    ctmc.set_defaults(func=cmd_ctmc_ep)

    diffusion = subparsers.add_parser("diffusion-ep-1d", help="Compute 1D diffusion EP rate")
    diffusion.add_argument("--in", dest="input_path", required=True, help="Input JSON file path")
    diffusion.set_defaults(func=cmd_diffusion_ep_1d)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
