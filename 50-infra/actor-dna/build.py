#!/usr/bin/env python3
"""build.py — build a REAL Actor DNA from an actor's on-disk artifacts.

Given an actor's committed WASM program, its lexicon/schema file, and an integrity ruleset,
this computes every CID from the real bytes and emits the canonical DNA manifest + deploy
descriptor. The `:dna/wasm-cid` is the byte-exact content-address of the deployed program (the
SAME CID the actor's did.json advertises and the WASM loader re-verifies) — so the manifest is
not a mock, it binds the actual code.

  python3 build.py --did did:web:etzhayyim.com:actor:tsumugi --graph tsumugi \
      --wasm ../../orgs/etzhayyim/com-etzhayyim-tsumugi/wasm/loader/tsumugi-core.wasm \
      --lexicon ../../00-contracts/schemas/engi-organism-ontology.kotoba.edn \
      --rules-out ../../orgs/etzhayyim/com-etzhayyim-tsumugi/dna/tsumugi.integrity.edn \
      --dna-out   ../../orgs/etzhayyim/com-etzhayyim-tsumugi/dna/tsumugi.dna.edn \
      --append-only --deny :person/name --deny :individual/handle

The ruleset is GENERATED canonically (integrity.rules_edn) so the committed file's raw CID IS
`:dna/validation-cid` by construction — no EDN parser needed to re-verify.
"""
from __future__ import annotations

import argparse
import pathlib

import cid as cidlib
import dna as dnalib
import deploy as deploylib
import integrity as ig


def build_actor_dna(*, did: str, graph: str, wasm_path: str, lexicon_path: str,
                    rules: dict, rules_out: str, dna_out: str,
                    capability: str = dnalib.DEFAULT_CAPABILITY) -> dict:
    wasm_bytes = pathlib.Path(wasm_path).read_bytes()
    if len(wasm_bytes) > cidlib.SINGLE_BLOCK_LIMIT:
        raise SystemExit(f"{wasm_path} is {len(wasm_bytes)}B > single-block limit "
                         f"{cidlib.SINGLE_BLOCK_LIMIT}B (dag-pb chunking out of scope)")
    wasm_cid = cidlib.cidv1_raw(wasm_bytes)

    lexicon_bytes = pathlib.Path(lexicon_path).read_bytes()
    lexicon_cid = cidlib.cidv1_raw(lexicon_bytes)

    # generate the ruleset canonically → its file bytes' raw CID IS the validation-cid
    rules_bytes = ig.rules_edn(rules)
    pathlib.Path(rules_out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(rules_out).write_bytes(rules_bytes + b"\n")  # trailing \n for git friendliness
    validation_cid = cidlib.cidv1_raw(rules_bytes)            # CID is of the canonical bytes (no \n)

    manifest = dnalib.build(actor_did=did, wasm_cid=wasm_cid, graph=graph,
                            validation_cid=validation_cid, lexicon_cid=lexicon_cid,
                            capability=capability)
    pathlib.Path(dna_out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(dna_out).write_bytes(dnalib.manifest_edn(manifest) + b"\n")

    ok, why = dnalib.verify(manifest, blobs={":dna/wasm-cid": wasm_bytes})
    if not ok:
        raise SystemExit(f"built an invalid DNA: {why}")
    return {"manifest": manifest, "dna_cid": dnalib.dna_cid(manifest),
            "deploy_cid": deploylib.deploy_cid(manifest), "verify": why}


def main() -> None:
    ap = argparse.ArgumentParser(description="build a real Actor DNA from on-disk artifacts")
    ap.add_argument("--did", required=True)
    ap.add_argument("--graph", required=True)
    ap.add_argument("--wasm", required=True)
    ap.add_argument("--lexicon", required=True)
    ap.add_argument("--rules-out", required=True)
    ap.add_argument("--dna-out", required=True)
    ap.add_argument("--capability", default=dnalib.DEFAULT_CAPABILITY)
    ap.add_argument("--append-only", action="store_true")
    ap.add_argument("--deny", action="append", default=[], metavar=":attr",
                    help="a structurally-forbidden attribute (repeatable)")
    a = ap.parse_args()

    rules = {":integrity/spec": ig.SPEC, ":integrity/graph": a.graph}
    if a.append_only:
        rules[":integrity/append-only"] = True
    if a.deny:
        rules[":integrity/deny-attrs"] = a.deny

    out = build_actor_dna(did=a.did, graph=a.graph, wasm_path=a.wasm, lexicon_path=a.lexicon,
                          rules=rules, rules_out=a.rules_out, dna_out=a.dna_out,
                          capability=a.capability)
    print(f"wrote {a.rules_out} + {a.dna_out}")
    print(f"  wasm-cid       : {out['manifest'][':dna/wasm-cid']}")
    print(f"  validation-cid : {out['manifest'][':dna/validation-cid']}")
    print(f"  lexicon-cid    : {out['manifest'][':dna/lexicon-cid']}")
    print(f"  >>> DNA CID    : {out['dna_cid']}")
    print(f"  deploy CID     : {out['deploy_cid']}")
    print(f"  verify         : {out['verify']}")


if __name__ == "__main__":
    main()
