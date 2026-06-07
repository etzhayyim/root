"""
Rewrite broken UNSPSC agent modules into clean LangGraph placeholders.

Per the 2026-05-23 corpus health sweep: 9,985 of 18,342 ``cXXXXXXXX.py``
modules under ``kotodama.langgraph_graphs.unispsc_agents`` fail to import
— 9,882 of those are the Gemini-emitted one-liner where ``class Foo(Type-
dDict): a: str; b: int`` is on the same line (invalid Python class-body
form). The remaining ~110 are stray topology errors, line-continuation
glitches, missing `from import`, and unknown-node edges.

This codemod:
  1. Loads the registry (00-contracts/actor-registry/unispsc.json) so it
     knows the canonical (code, title, segment, did) per agent.
  2. Tries to import each ``c<code>``. If import succeeds AND the module
     exposes a ``graph`` attribute, the file is left alone (preserves
     Gemini's bespoke per-code logic where it actually works).
  3. Otherwise overwrites the file with a 40-LOC placeholder that
     compiles, exposes ``graph`` (with ``.builder`` for the executor's
     MstCheckpointSaver rebind path), embeds the registry metadata as
     module constants, and runs a deterministic 3-node compliance/
     process/emit pipeline.

Idempotent: re-runs only touch files that still fail. To force-rewrite a
healthy file, delete it first.

Usage::

    cd 40-engine/kotoba/crates/kotoba-kotodama/py
    uv run python ../../../70-tools/scripts/codemod/2605231300-unispsc-agent-placeholder-rewrite.py
    uv run python ../../../70-tools/scripts/codemod/2605231300-unispsc-agent-placeholder-rewrite.py --dry-run
    uv run python ../../../70-tools/scripts/codemod/2605231300-unispsc-agent-placeholder-rewrite.py --only 10101500,43211500

ADR: pending — corpus rebuild is interim; Gemini exec rebuild will
overwrite per-code logic in a later pass.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPO_ROOT / "00-contracts" / "actor-registry" / "unispsc.json"
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
AGENTS_PKG = "kotodama.langgraph_graphs.unispsc_agents"

PLACEHOLDER_MARKER = "# codemod:2605231300-unispsc-placeholder"


def render(code: str, title: str, segment: str, did: str) -> str:
    safe_title = title.replace('"', '\\"')
    return f'''{PLACEHOLDER_MARKER} v1
"""
Unispsc actor agent c{code} — {safe_title} (segment {segment}).

Placeholder graph emitted by the 2026-05-23 corpus rebuild codemod. The
upstream Gemini exec rebuild will overwrite this file with bespoke per-
code logic; until then this 3-node compliance/process/emit pipeline
ensures the agent is callable from UnispscAgentExecutorCell and exercises
the MstCheckpointSaver substrate path.

This module is regenerated automatically — hand-edit at your own risk.
"""

from __future__ import annotations

from operator import add
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph

UNISPSC_CODE = "{code}"
UNISPSC_TITLE = "{safe_title}"
UNISPSC_SEGMENT = "{segment}"
UNISPSC_DID = "{did}"


class State(TypedDict, total=False):
    input: dict[str, Any]
    compliance_check: bool
    log: Annotated[list[str], add]
    result: dict[str, Any]


def receive(state: State) -> dict[str, Any]:
    inp = state.get("input") or {{}}
    return {{
        "log": [f"{{UNISPSC_CODE}}:receive"],
        "compliance_check": bool(inp),
    }}


def process(state: State) -> dict[str, Any]:
    return {{"log": [f"{{UNISPSC_CODE}}:process"]}}


def emit(state: State) -> dict[str, Any]:
    return {{
        "log": [f"{{UNISPSC_CODE}}:emit"],
        "result": {{
            "code": UNISPSC_CODE,
            "title": UNISPSC_TITLE,
            "segment": UNISPSC_SEGMENT,
            "did": UNISPSC_DID,
            "ok": True,
        }},
    }}


_g = StateGraph(State)
_g.add_node("receive", receive)
_g.add_node("process", process)
_g.add_node("emit", emit)
_g.add_edge(START, "receive")
_g.add_edge("receive", "process")
_g.add_edge("process", "emit")
_g.add_edge("emit", END)

graph = _g.compile()
'''


def load_registry() -> dict[str, dict]:
    with REGISTRY_PATH.open("rb") as f:
        data = json.load(f)
    out: dict[str, dict] = {}
    for row in data.get("agents", []):
        code = row.get("code")
        if not code:
            continue
        out[code] = row
    return out


def health_of(code: str) -> tuple[bool, str]:
    """Return (is_healthy, reason). Healthy = imports + has `graph` attr."""
    mod_name = f"{AGENTS_PKG}.c{code}"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    try:
        mod = importlib.import_module(mod_name)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
    if not hasattr(mod, "graph"):
        return False, "no `graph` attribute"
    return True, "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="Don't write; just count what would change"
    )
    parser.add_argument(
        "--only",
        default=None,
        help="Comma-separated list of codes to consider (otherwise all 18,342)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite even healthy files (use to refresh all placeholders)",
    )
    parser.add_argument(
        "--max", type=int, default=0, help="Limit to N candidates (0 = no limit)"
    )
    args = parser.parse_args()

    if str(REPO_ROOT / "20-actors" / "kotodama" / "py" / "src") not in sys.path:
        sys.path.insert(0, str(REPO_ROOT / "20-actors" / "kotodama" / "py" / "src"))

    registry = load_registry()
    print(f"registry: {len(registry)} agents loaded")

    if args.only:
        candidates = [c.strip() for c in args.only.split(",") if c.strip()]
    else:
        candidates = sorted(registry.keys())
    if args.max > 0:
        candidates = candidates[: args.max]

    rewritten = 0
    skipped_healthy = 0
    skipped_no_registry = 0
    sampled = []
    t0 = time.time()
    for i, code in enumerate(candidates):
        row = registry.get(code)
        if not row:
            skipped_no_registry += 1
            continue
        path = AGENTS_DIR / f"c{code}.py"
        if not args.force:
            healthy, _ = health_of(code)
            if healthy:
                skipped_healthy += 1
                continue
        title = row.get("title", "")
        segment = row.get("segment", code[:2])
        did = row.get("did", f"did:web:etzhayyim.com:actor:c{code}")
        content = render(code, title, segment, did)
        if args.dry_run:
            rewritten += 1
            if len(sampled) < 3:
                sampled.append(code)
            continue
        path.write_text(content)
        rewritten += 1
        if len(sampled) < 3:
            sampled.append(code)
        if (i + 1) % 1000 == 0:
            print(
                f"  ... {i + 1}/{len(candidates)} processed "
                f"(rewritten={rewritten} healthy={skipped_healthy} elapsed={time.time() - t0:.1f}s)"
            )

    print()
    print(f"rewritten          = {rewritten}")
    print(f"skipped (healthy)  = {skipped_healthy}")
    print(f"skipped (no row)   = {skipped_no_registry}")
    print(f"samples            = {sampled}")
    print(f"elapsed            = {time.time() - t0:.2f}s")
    if args.dry_run:
        print("(dry-run, no files written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
