"""Fixture argparse-with-subparsers app for the yorishiro extractor tests.

Run the extractor against this directory to produce a kami manifest:

    python3 70-tools/etzhayyim-cli/yorishiro/scripts/extract-click.py \\
        70-tools/etzhayyim-cli/yorishiro/fixtures/source-repo-argparse-subparsers \\
        --kami-id bin:argparse-sub --binary argparse-sub --framework argparse
"""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="argparse-sub",
        description="Demo argparse subparser CLI used by the yorishiro fixture.",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging across all subcommands.")
    parser.add_argument("--config", default="/etc/sub.conf", help="Path to config file.")

    subparsers = parser.add_subparsers(dest="cmd", required=True)

    encode = subparsers.add_parser("encode", help="Encode an input file.")
    encode.add_argument("input_path", help="Source path.")
    encode.add_argument("--output", default="-", help="Output file; '-' for stdout.")
    encode.add_argument("--bitrate", type=int, default=128, help="Output bitrate (kbps).")
    encode.add_argument("--lossless", action="store_true", help="Use lossless encoding.")

    decode = subparsers.add_parser("decode", help="Decode an input file.")
    decode.add_argument("input_path", help="Source path.")
    decode.add_argument("output_path", nargs="?", default="-", help="Output file; '-' for stdout.")
    decode.add_argument("--sample-rate", "sample_rate", type=int, default=44100, help="Sample rate (Hz).")

    inspect = subparsers.add_parser("inspect", help="Print metadata only.")
    inspect.add_argument("input_path", help="Source path.")

    args = parser.parse_args()
    if args.verbose:
        print(f"[cmd={args.cmd}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
