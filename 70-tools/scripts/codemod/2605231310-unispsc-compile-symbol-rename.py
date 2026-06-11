"""
Rename trailing ``compiled_graph = graph.compile()`` → ``graph = graph.compile()``.

Gemini-emitted ~1,887 agents that assign the compiled output to a fresh
``compiled_graph`` symbol while leaving the module-level ``graph`` bound to
the uncompiled ``StateGraph`` builder. The executor then calls ``graph.
invoke(...)`` and trips ``AttributeError: 'StateGraph' object has no
attribute 'invoke'``.

The fix is exactly the same line — just rebind to ``graph``.

Usage::

    cd 40-engine/kotoba/crates/kotoba-kotodama/py
    uv run python ../../../70-tools/scripts/codemod/2605231310-unispsc-compile-symbol-rename.py
    uv run python ../../../70-tools/scripts/codemod/2605231310-unispsc-compile-symbol-rename.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
AGENTS_DIR = (
    REPO_ROOT
    / "20-actors"
    / "kotodama"
    / "py"
    / "src"
    / "kotodama"
    / "langgraph_graphs"
    / "unispsc_agents"
)

# Match the symptom: the file's final non-empty statement is
#   <name> = graph.compile()
# where <name> != "graph". Allow leading whitespace + trailing whitespace.
RE_COMPILE = re.compile(
    r"(?P<lead>\n)\s*(?P<lhs>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*graph\.compile\(\)\s*$"
)


def patch_text(text: str) -> tuple[str, bool]:
    stripped = text.rstrip()
    m = RE_COMPILE.search(stripped)
    if not m:
        return text, False
    lhs = m.group("lhs")
    if lhs == "graph":
        return text, False
    # Replace just the LHS in the matched line.
    new = stripped[: m.start("lhs")] + "graph" + stripped[m.end("lhs"):]
    # Preserve a single trailing newline.
    return new + "\n", True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--manifest", default="/tmp/etz-broken-agents.jsonl")
    args = parser.parse_args()

    # Build target set from the manifest: codes where the symptom was
    # AttributeError "has no attribute" (uncompiled StateGraph). Falls back
    # to "scan all files matching the regex" if the manifest is absent.
    targets: set[str] | None = None
    mf = Path(args.manifest)
    if mf.exists():
        targets = set()
        for line in mf.read_text().splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("etype") == "AttributeError" and "has no attribute" in rec.get(
                "msg", ""
            ):
                targets.add(rec["code"])
        print(f"manifest target set = {len(targets)} codes")

    rewritten = 0
    skipped_no_match = 0
    samples = []
    t0 = time.time()
    files = sorted(p for p in AGENTS_DIR.iterdir() if p.name.startswith("c") and p.suffix == ".py")
    for p in files:
        code = p.stem[1:]
        if targets is not None and code not in targets:
            continue
        original = p.read_text()
        new, changed = patch_text(original)
        if not changed:
            skipped_no_match += 1
            continue
        if args.dry_run:
            rewritten += 1
            if len(samples) < 5:
                samples.append(code)
            continue
        p.write_text(new)
        rewritten += 1
        if len(samples) < 5:
            samples.append(code)

    print(f"rewritten        = {rewritten}")
    print(f"target unmatched = {skipped_no_match}")
    print(f"samples          = {samples}")
    print(f"elapsed          = {time.time() - t0:.2f}s")
    if args.dry_run:
        print("(dry-run, no files written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
