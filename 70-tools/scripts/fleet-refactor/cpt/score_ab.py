#!/usr/bin/env python3
"""Score heldout-gen.jsonl: gate base_out vs cpt_out through the SAME unit gate
unit_refactor.py uses (extract clojure → balance repair → clj-kondo error + bb load).
A unit 'passes' if its single form, wrapped in a unit-scratch ns with the standard
prelude requires, both clj-kondo-clean (error level) AND bb-loads."""
import json, sys, re
sys.path.insert(0, ".")
from fleet_refactor import extract_clojure, balance_repair
from unit_refactor import bb_compile, lint_text

NS_PRELUDE = ("(ns unit.scratch\n  (:require [clojure.string]\n"
              "            [clojure.set]\n            [clojure.edn]))\n\n")

def gate(raw):
    code = extract_clojure(raw)
    if not code: return False, "no-clojure-block"
    code = balance_repair(code) or code
    full = NS_PRELUDE + code
    import shutil
    if shutil.which("clj-kondo"):
        ok_lint, lout = lint_text(full)
        if not ok_lint: return False, "clj-kondo:" + lout[:80]
    ok_bb, bout = bb_compile(full, "unit.scratch")
    if not ok_bb: return False, "bb:" + bout[:80]
    return True, "ok"

def main():
    recs = [json.loads(l) for l in open("heldout-gen.jsonl")]
    bp = cp = 0
    flips_gain = []; flips_loss = []
    for r in recs:
        b_ok,_ = gate(r["base_out"])
        c_ok,_ = gate(r["cpt_out"])
        bp += b_ok; cp += c_ok
        if c_ok and not b_ok: flips_gain.append(f'{r["actor"]}/{r["name"]}')
        if b_ok and not c_ok: flips_loss.append(f'{r["actor"]}/{r["name"]}')
    n = len(recs)
    print(f"held-out units: {n}")
    print(f"BASE  pass: {bp}/{n} = {bp/n*100:.1f}%")
    print(f"CPT   pass: {cp}/{n} = {cp/n*100:.1f}%")
    print(f"delta: {(cp-bp)/n*100:+.1f}pp ({cp-bp:+d} units)")
    print(f"CPT-gained ({len(flips_gain)}): {', '.join(flips_gain[:12])}")
    print(f"CPT-lost   ({len(flips_loss)}): {', '.join(flips_loss[:12])}")

if __name__ == "__main__":
    sys.exit(main())
