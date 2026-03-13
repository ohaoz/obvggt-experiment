#!/usr/bin/env python3
"""
Print experiment preflight context from Trellis config.
"""

from __future__ import annotations

import argparse
import json

from common.experiment_ops import (
    get_experiment_preflight,
    get_experiment_preflight_banner,
    get_experiment_preflight_lines,
)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Show experiment preflight context")
    parser.add_argument(
        "--mode",
        choices=["full", "banner"],
        default="full",
        help="Output mode",
    )
    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Output JSON instead of text",
    )
    args = parser.parse_args()

    if args.json:
        print(json.dumps(get_experiment_preflight() or {}, indent=2, ensure_ascii=False))
        return

    if args.mode == "banner":
        banner = get_experiment_preflight_banner()
        if banner:
            print(banner)
        return

    lines = get_experiment_preflight_lines()
    if lines:
        print("\n".join(lines))


if __name__ == "__main__":
    main()
