#!/usr/bin/env python3
"""Fleet A/B score: gemma4:e4b-it-qat vs gemma4:12b-it-qat (heldout-gen-fleet.jsonl),
bb-load gate applied identically. Run from fleet-refactor/."""
import json, sys, shutil
sys.path.insert(0,".")
from fleet_refactor import extract_clojure, balance_repair
from unit_refactor import bb_compile, lint_text
NS=("(ns unit.scratch\n  (:require [clojure.string]\n            [clojure.set]\n            [clojure.edn]))\n\n")
def gate(raw):
    if not raw or raw.startswith("ERROR:"): return False
    code=extract_clojure(raw)
    if not code: return False
    code=balance_repair(code) or code
    full=NS+code
    if shutil.which("clj-kondo"):
        ok,_=lint_text(full)
        if not ok: return False
    ok,_=bb_compile(full,"unit.scratch")
    return ok
def main():
    recs=[json.loads(l) for l in open("heldout-gen-fleet.jsonl")]
    eg=[gate(r["e4b_out"]) for r in recs]; tg=[gate(r["12b_out"]) for r in recs]
    n=len(recs); ep=sum(eg); tp=sum(tg)
    print(f"held-out units: {n}  (fleet Ollama, 20-stream, native /api/chat think:false)")
    print(f"e4b-it-qat pass: {ep}/{n} = {ep/n*100:.1f}%")
    print(f"12b-it-qat pass: {tp}/{n} = {tp/n*100:.1f}%  ({(tp-ep)/n*100:+.1f}pp vs e4b)")
    gain=[f'{recs[i]["actor"]}/{recs[i]["name"]}' for i in range(n) if tg[i] and not eg[i]]
    loss=[f'{recs[i]["actor"]}/{recs[i]["name"]}' for i in range(n) if eg[i] and not tg[i]]
    print(f"12b-gained ({len(gain)}): {', '.join(gain[:16])}")
    print(f"12b-lost   ({len(loss)}): {', '.join(loss[:16])}")
if __name__=="__main__": sys.exit(main())
