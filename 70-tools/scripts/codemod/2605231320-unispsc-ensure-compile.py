"""
Ensure each ``cXXXXXXXX.py`` ends with ``graph = <builder>.compile()``.

After codemod 2605231310 (compile-symbol-rename) some agents still expose
the bare ``StateGraph`` builder under ``graph`` because:

  (a) the file ends with no ``.compile()`` call at all — gemini forgot it
  (b) the file ends with ``graph.compile()`` (or ``<var>.compile()``) but
      discards the return value (compile() returns a NEW object — the
      builder is not mutated in place)

Both cases trip ``AttributeError: 'StateGraph' object has no attribute
'invoke'`` at runtime. Mechanical patch:

  case (a): append a trailing ``graph = graph.compile()`` (using whichever
            builder variable was last seen) — preserves all gemini logic.
  case (b): rewrite the orphaned compile() line to ``graph = <var>.compile()``.

Usage::

    cd 40-engine/kotoba/crates/kotoba-kotodama/py
    uv run python ../../../70-tools/scripts/codemod/2605231320-unispsc-ensure-compile.py --dry-run
    uv run python ../../../70-tools/scripts/codemod/2605231320-unispsc-ensure-compile.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
AGENTS_DIR = (
    REPO_ROOT / "20-actors" / "kotodama" / "py" / "src"
    / "kotodama" / "langgraph_graphs" / "unispsc_agents"
)

RE_STATEGRAPH_VAR = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*StateGraph\b", re.MULTILINE
)
RE_BARE_COMPILE = re.compile(
    r"(?P<lead>\n)(?P<indent>[ \t]*)([A-Za-z_][A-Za-z0-9_]*)\.compile\(\s*\)\s*$"
)
RE_LAST_GRAPH_ASSIGN = re.compile(
    r"^\s*graph\s*=\s*[A-Za-z_][A-Za-z0-9_]*\.compile\(\)", re.MULTILINE
)


def patch_text(text: str) -> tuple[str, str]:
    """Return (new_text, action). action ∈ {'append', 'rewrite_bare', 'noop'}."""
    stripped = text.rstrip()
    # Case (a/b): does the file already have `graph = <something>.compile()`?
    if RE_LAST_GRAPH_ASSIGN.search(stripped):
        # Already correct symbol — but maybe followed by a stray bare compile?
        # Either way no-op.
        return text, "noop"

    # Case (b): orphan bare compile() call (e.g. `graph.compile()` discarded).
    m = RE_BARE_COMPILE.search(stripped)
    if m:
        # Determine which variable the compile() is being called on.
        # The matched text is `<lead><indent><var>.compile()`. Extract var.
        chunk = stripped[m.start():m.end()]
        m_var = re.search(r"([A-Za-z_][A-Za-z0-9_]*)\.compile\(\)\s*$", chunk)
        if m_var:
            var = m_var.group(1)
            new = stripped[: m.start()] + m.group("lead") + m.group("indent") + (
                f"graph = {var}.compile()"
            )
            return new + "\n", "rewrite_bare"

    # Case (a): no `.compile()` anywhere. Append one. Determine builder
    # variable from the last `<var> = StateGraph(...)` assignment.
    builder = "graph"  # default fallback
    matches = list(RE_STATEGRAPH_VAR.finditer(stripped))
    if matches:
        builder = matches[-1].group(1)
    return stripped + "\n\n" + f"graph = {builder}.compile()\n", "append"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--manifest", default="/tmp/etz-broken-agents.jsonl")
    args = parser.parse_args()

    targets: set[str] | None = None
    mf = Path(args.manifest)
    if mf.exists():
        targets = set()
        for line in mf.read_text().splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("etype") == "AttributeError" and "StateGraph" in rec.get("msg", "") and "invoke" in rec.get("msg", ""):
                targets.add(rec["code"])
        print(f"manifest target set = {len(targets)} codes")

    counts = {"append": 0, "rewrite_bare": 0, "noop": 0}
    samples = {"append": [], "rewrite_bare": []}
    t0 = time.time()
    files = sorted(p for p in AGENTS_DIR.iterdir() if p.name.startswith("c") and p.suffix == ".py")
    for p in files:
        code = p.stem[1:]
        if targets is not None and code not in targets:
            continue
        original = p.read_text()
        new, action = patch_text(original)
        counts[action] += 1
        if action == "noop":
            continue
        if len(samples[action]) < 3:
            samples[action].append(code)
        if not args.dry_run:
            p.write_text(new)

    for action, n in counts.items():
        print(f"  {action:>14}  {n:>5}   {samples.get(action, '')}")
    print(f"elapsed = {time.time() - t0:.2f}s")
    if args.dry_run:
        print("(dry-run)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
