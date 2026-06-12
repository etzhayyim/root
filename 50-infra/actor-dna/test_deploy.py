"""test_deploy.py — the deploy descriptor binds every step to the single DNA CID."""
from __future__ import annotations

import cid as cidlib
import deploy
import dna
import integrity as ig
from _t import expect_raises, run

WASM = cidlib.cidv1_raw(b"\x00asm\x01\x00\x00\x00 fake wasm")
RULES = {":integrity/spec": "kotoba-integrity/v0", ":integrity/graph": "ibuki",
         ":integrity/append-only": True}
VAL = ig.validation_cid(RULES)
LEX = cidlib.cidv1_raw(b"{:lexicon \"ibuki\"}")
DID = "did:web:etzhayyim.com:actor:ibuki"


def _m():
    return dna.build(actor_did=DID, wasm_cid=WASM, graph="ibuki", validation_cid=VAL, lexicon_cid=LEX)


def test_plan_is_ordered_content_before_identity():
    steps = deploy.plan(_m())
    ops = [s["op"] for s in steps]
    assert ops == ["pin", "pin", "pin", "pin", "graph-genesis", "did-link"]
    # content (code/validation/lexicon) + the manifest are pinned BEFORE the did link
    assert ops.index("did-link") == len(ops) - 1


def test_every_step_carries_the_one_dna_cid():
    m = _m()
    d = dna.dna_cid(m)
    assert all(s["dna"] == d for s in deploy.plan(m))


def test_pins_cover_exactly_the_manifest_content_set():
    m = _m()
    steps = deploy.plan(m)
    pins = {s["cid"] for s in steps if s["op"] == "pin"}
    assert pins == {WASM, VAL, LEX, dna.dna_cid(m)}   # code + rules + lexicon + the manifest itself


def test_descriptor_and_deploy_cid_are_deterministic():
    m = _m()
    assert deploy.deploy_cid(m) == deploy.deploy_cid(_m())
    assert deploy.deploy_cid(m).startswith("bafkrei")


def test_verify_descriptor_accepts_the_matching_descriptor():
    m = _m()
    ok, why = deploy.verify_descriptor(deploy.descriptor(m), m)
    assert ok and "ok" in why


def test_verify_descriptor_rejects_a_tampered_dna_cid():
    m = _m()
    desc = deploy.descriptor(m)
    desc[":deploy/dna-cid"] = cidlib.cidv1_raw(b"a lie")
    ok, why = deploy.verify_descriptor(desc, m)
    assert not ok and "dna-cid" in why


def test_plan_refuses_an_unverified_dna():
    bad = _m()
    bad[":dna/graph-cid"] = cidlib.graph_cid("mismatch")   # broken binding
    expect_raises(lambda: deploy.plan(bad), contains="unverified DNA")


def test_did_link_step_carries_the_single_dna_service_entry():
    m = _m()
    link = [s for s in deploy.plan(m) if s["op"] == "did-link"][0]
    assert link["service"]["dnaCid"] == dna.dna_cid(m)


if __name__ == "__main__":
    run("deploy", [(n, f) for n, f in sorted(globals().items())
                   if n.startswith("test_") and callable(f)])
