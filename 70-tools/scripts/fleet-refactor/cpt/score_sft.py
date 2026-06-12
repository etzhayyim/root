#!/usr/bin/env python3
"""3-way: base (from heldout-gen.jsonl) vs CPT (same) vs SFT (heldout-gen-sft.jsonl).
Same bb-load gate, applied identically. Run from fleet-refactor/."""
import json, sys
sys.path.insert(0,".")
from fleet_refactor import extract_clojure, balance_repair
from unit_refactor import bb_compile, lint_text
import shutil
NS=("(ns unit.scratch\n  (:require [clojure.string]\n            [clojure.set]\n            [clojure.edn]))\n\n")
def gate(raw):
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
    base={}; cpt={}
    for l in open("heldout-gen.jsonl"):
        d=json.loads(l); k=(d["actor"],d["name"]); base[k]=d["base_out"]; cpt[k]=d["cpt_out"]
    sft={}
    for l in open("heldout-gen-sft.jsonl"):
        d=json.loads(l); sft[(d["actor"],d["name"])]=d["sft_out"]
    keys=[k for k in base if k in sft]
    bg=[gate(base[k]) for k in keys]; cg=[gate(cpt[k]) for k in keys]; sg=[gate(sft[k]) for k in keys]
    n=len(keys)
    bp,cp,sp=sum(bg),sum(cg),sum(sg)
    print(f"held-out units: {n}")
    print(f"BASE pass: {bp}/{n} = {bp/n*100:.1f}%")
    print(f"CPT  pass: {cp}/{n} = {cp/n*100:.1f}%  ({(cp-bp)/n*100:+.1f}pp)")
    print(f"SFT  pass: {sp}/{n} = {sp/n*100:.1f}%  ({(sp-bp)/n*100:+.1f}pp vs base)")
    gain=[f"{keys[i][0]}/{keys[i][1]}" for i in range(n) if sg[i] and not bg[i]]
    loss=[f"{keys[i][0]}/{keys[i][1]}" for i in range(n) if bg[i] and not sg[i]]
    print(f"SFT-gained ({len(gain)}): {', '.join(gain[:14])}")
    print(f"SFT-lost   ({len(loss)}): {', '.join(loss[:14])}")
if __name__=="__main__": sys.exit(main())
