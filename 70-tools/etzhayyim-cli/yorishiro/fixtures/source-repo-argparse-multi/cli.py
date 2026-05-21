"""Multi-parser argparse fixture for Phase 2.5.2.1.

Two top-level ArgumentParser() in one module. Each emits its own
yorishiro op. Names derive from `prog=` when set; falls back to
`main` / `main_<n>` otherwise.
"""

from __future__ import annotations

import argparse


def build_encoder_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="encoder", description="Standalone encoder driver.")
    p.add_argument("input_path", help="Path to encode.")
    p.add_argument("--bitrate", type=int, default=192, help="kbps.")
    p.add_argument("--mono", action="store_true", help="Force mono output.")
    return p


def build_decoder_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="decoder", description="Standalone decoder driver.")
    p.add_argument("input_path", help="Path to decode.")
    p.add_argument("--sample-rate", type=int, default=48000, help="Hz.")
    return p


if __name__ == "__main__":
    raise SystemExit(0)
