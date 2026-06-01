#!/usr/bin/env python3
"""Production kotoba py-WASM migration — namespace runner (gemini, ADR-2605312100).

Migrates every LangGraph cell in one or more actor namespaces 1-by-1 with the
SELECTED model (Gemini CLI), then verifies each port:
  gemini agent  ->  agent.py (StateGraph(dict))  ->  build agent.wasm
   ->  deploy+invoke on :8077  ->  invoke-equivalence vs the host-CPython original.

Reuses the bake-off machinery (bakeoff_cli.run_gemini/task_prompt/build) and the
invoke-equivalence gate (invoke_equiv.host_reference/invoke_wasm). Writes a ledger
so a large migration is resumable and never silently drops a cell.

Usage:
  migrate_namespace.py gov-municipality infra-utility-connect
  migrate_namespace.py --only service_request,meter_install infra-utility-connect
Output:
  runs/<cell>/gemini/agent.py|.wasm   (ports)
  production/ledger.json              (per-cell status, resumable)
"""
from __future__ import annotations
import json, sys, shutil, subprocess, argparse
from pathlib import Path

import bakeoff_cli as B
import invoke_equiv as E

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LEDGER = HERE / "production" / "ledger.json"
GREEN, RED, YEL, DIM, RST = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"


def discover(namespaces, only=None):
    cells = []
    for ns in namespaces:
        base = ROOT / "20-actors" / ns / "cells"
        for cellpy in sorted(base.glob("**/cell.py")):
            if "from langgraph.graph import StateGraph" not in cellpy.read_text():
                continue
            name = cellpy.parent.name
            if only and name not in only:
                continue
            cells.append({"id": f"{ns}-{name}", "name": name, "ns": ns,
                          "src": str(cellpy.relative_to(ROOT)), "ref_input": {}})
    return cells


def verify_equiv(cell):
    """invoke-equivalence vs host-CPython original. Returns (verdict, detail)."""
    wasm = HERE / "runs" / cell["id"] / "gemini" / "agent.wasm"
    if not wasm.exists():
        return "no-wasm", None
    try:
        gold = E.host_reference(cell)
    except Exception as e:
        # R0 scaffolds raise on execution (gated pre-ratification) -> no runtime gold
        return "no-gold", str(e)[:120]
    try:
        out, err = E.invoke_wasm(wasm, cell["ref_input"])
    except Exception as e:
        return "invoke-error", str(e)[:120]
    if err:
        return "invoke-error", err
    strict = E.norm(out) == E.norm(gold)
    extra = set(out) - set(gold)
    gold_ok = all(k in out and E.norm(out[k]) == E.norm(gold[k]) for k in gold)
    if strict:
        return "strict", None
    if gold_ok and extra <= set(cell["ref_input"]):
        return "modulo-input", sorted(extra)
    return "mismatch", {"extra": sorted(extra), "missing": sorted(set(gold) - set(out))}


MAX_EQUIV_RETRIES = 2


def _correction_prompt(cell, detail, example_text):
    src = ROOT / cell["src"]
    return (B.task_prompt(cell, B.BUILD, example_text)
            + f"\n\nIMPORTANT — your PREVIOUS port built but is RUNTIME-WRONG. Invoking it produced an "
              f"output state dict that differs from the original `solve()`:\n  missing keys: {detail.get('missing')}\n"
              f"  extra keys: {detail.get('extra')}\nThe output state MUST match the original EXACTLY. Make sure "
              f"every node that writes an output channel is present and writes the same keys/shapes as the "
              f"original cell (`{cell['src']}`). Re-output agent.py and rebuild with: "
              f"bash {B.BUILD} agent.py agent.wasm.")


def migrate_one(cell, example_text):
    # gemini migrate + build (reuse bake-off; writes runs/<id>/gemini/agent.py|.wasm)
    src = ROOT / cell["src"]
    cls = next((l.split()[1].rstrip(":") for l in src.read_text().splitlines()
                if l.startswith("class ")), None)
    cell["class"] = cls
    cell["entry"] = "solve"
    row = B.migrate("gemini", cell, example_text)        # build + structural + judge
    verdict, detail = ("skip", None)
    if row.get("build_pass"):
        verdict, detail = verify_equiv(cell)

    # EQUIV-FEEDBACK: if the port built but is runtime-wrong, feed the diff back and retry.
    retries = 0
    workdir = B.RUNS / cell["id"] / "gemini"
    while verdict == "mismatch" and retries < MAX_EQUIV_RETRIES:
        retries += 1
        print(f"    {YEL}equiv-feedback retry {retries}{RST}: {detail}")
        B.run_gemini(str(workdir), _correction_prompt(cell, detail, example_text))
        if (workdir / "agent.wasm").exists():
            verdict, detail = verify_equiv(cell)

    out = {"cell": cell["id"], "src": cell["src"], "build": (B.RUNS / cell["id"] / "gemini" / "agent.wasm").exists(),
           "structural": bool(row.get("structural_ok")), "judge": row.get("judge_score"),
           "wall_s": row.get("wall_s"), "equiv_retries": retries, "equiv": verdict, "equiv_detail": detail}
    color = GREEN if verdict in ("strict", "modulo-input") else (YEL if verdict in ("no-gold",) else RED)
    print(f"  {color}{verdict:13s}{RST} build={out['build']} judge={out['judge']} {cell['id']}"
          + (f"  {DIM}{detail}{RST}" if detail else ""))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("namespaces", nargs="+")
    ap.add_argument("--only", default="", help="comma cell names to restrict to")
    ap.add_argument("--resume", action="store_true", help="skip cells already strict/modulo in ledger")
    args = ap.parse_args()
    only = set(args.only.split(",")) if args.only else None

    cells = discover(args.namespaces, only)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    # ledger MERGES across runs (keyed by cell id) so a later wave never clobbers an earlier one.
    ledger = {}
    if LEDGER.exists():
        ledger = {r["cell"]: r for r in json.loads(LEDGER.read_text())}
    example_text = B.GOLD_EXAMPLE.read_text()

    def flush():
        LEDGER.write_text(json.dumps(list(ledger.values()), indent=2, default=str))

    print(f"Wave: {len(cells)} cells across {args.namespaces} (model=gemini-3-flash-preview)\n")
    rows = []
    for cell in cells:
        if args.resume and ledger.get(cell["id"], {}).get("equiv") in ("strict", "modulo-input"):
            print(f"  {DIM}skip (done): {cell['id']}{RST}"); rows.append(ledger[cell["id"]]); continue
        try:
            r = migrate_one(cell, example_text)
        except Exception as e:
            print(f"  {RED}ERROR{RST} {cell['id']}: {e}")
            r = {"cell": cell["id"], "src": cell["src"], "build": False, "equiv": "error", "equiv_detail": str(e)[:150]}
        rows.append(r)
        ledger[cell["id"]] = r
        flush()   # checkpoint each cell (merged ledger)

    # rollup over THIS wave's cells
    from collections import Counter
    c = Counter(r["equiv"] for r in rows)
    nbuild = sum(bool(r.get("build")) for r in rows)
    print(f"\n{GREEN}=== Wave complete ==={RST}")
    print(f"  build-pass: {nbuild}/{len(rows)}")
    print(f"  equiv: " + "  ".join(f"{k}={v}" for k, v in sorted(c.items())))
    print(f"  ledger: {LEDGER.relative_to(ROOT)}")
    runtime_verifiable = [r for r in rows if r["equiv"] not in ("no-gold", "skip", "no-wasm")]
    good = sum(r["equiv"] in ("strict", "modulo-input") for r in runtime_verifiable)
    if runtime_verifiable:
        print(f"  runtime-verified equivalent: {good}/{len(runtime_verifiable)} "
              f"(rest are R0-scaffold no-gold, not runtime-testable)")


if __name__ == "__main__":
    main()
