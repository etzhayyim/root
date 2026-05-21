"""Fixture argparse app for the yorishiro source-repo extractor tests.

Run the extractor against this directory to produce a kami manifest:

    python3 70-tools/etzhayyim-cli/yorishiro/scripts/extract-click.py \\
        70-tools/etzhayyim-cli/yorishiro/fixtures/source-repo-argparse \\
        --kami-id bin:argparse-demo --binary argparse-demo --framework argparse
"""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="argparse-demo",
        description="Demo argparse CLI used by the yorishiro source-repo fixture.",
    )
    parser.add_argument("source_path", help="Path to read from.")
    parser.add_argument("output_path", nargs="?", default="-", help="Output path; '-' for stdout.")
    parser.add_argument(
        "--max-rows",
        type=int,
        default=100,
        help="Maximum rows to emit.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Output encoding.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan without writing.",
    )
    args = parser.parse_args()
    if args.verbose:
        print(f"reading {args.source_path}; writing {args.output_path} (max {args.max_rows} rows)")
    if args.dry_run:
        print("[dry-run] (no output produced)")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
