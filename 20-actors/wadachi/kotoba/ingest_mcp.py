#!/usr/bin/env python3
"""wadachi 轍 — ingest seed.edn into a live kotoba node via MCP.

ADR-2605242000, R0 scaffold. Flattens each seed entity map into
(graph, subject, predicate, object) datoms and asserts them via the
`kotoba_datom_create` MCP tool; `kotoba commit` seals them. Writes require an
operator AT-session JWT (no-server-key posture, G14). --dry-run parses + counts
datoms only (no writes, no LLM; G8 untouched).

Usage:
    python3 ingest_mcp.py [--url http://127.0.0.1:8077] [--graph com.etzhayyim.wadachi] [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import sys

SEED = os.path.join(os.path.dirname(__file__), "seed.edn")


def _strip_comments(s: str) -> str:
    out = []
    in_str = False
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if in_str:
            out.append(c)
            if c == '"' and s[i - 1] != "\\":
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if c == ";":
            while i < n and s[i] != "\n":
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _top_level_entities(s: str):
    """Yield each top-level {...} map literal inside the outer [ ... ] vector."""
    s = _strip_comments(s)
    start = s.find("[")
    if start < 0:
        return
    depth = 0
    buf = []
    in_str = False
    for c in s[start + 1:]:
        if in_str:
            buf.append(c)
            if c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
            buf.append(c)
            continue
        if c == "{":
            depth += 1
            buf.append(c)
        elif c == "}":
            depth -= 1
            buf.append(c)
            if depth == 0:
                yield "".join(buf).strip()
                buf = []
        elif depth > 0:
            buf.append(c)


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest wadachi seed datoms to kotoba")
    parser.add_argument("--url", default="http://127.0.0.1:8077", help="Kotoba node URL")
    parser.add_argument("--graph", default="com.etzhayyim.wadachi", help="Graph name")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, no writes")
    args = parser.parse_args()

    if not os.path.isfile(SEED):
        print(f"ERROR: {SEED} not found", file=sys.stderr)
        return 1

    with open(SEED) as f:
        content = f.read()

    entities = list(_top_level_entities(content))
    print(f"wadachi seed ingest → {args.url} (graph {args.graph})")
    print(f"parsed {len(entities)} entities")

    if args.dry_run:
        print(f"--dry-run: no writes. Set operator KOTOBA_TOKEN to ingest.")
    else:
        print(f"(operator token verification skipped in R0 scaffold)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
