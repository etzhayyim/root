"""test_dna.py — the Actor DNA manifest binds code+data into ONE content-addressed identity."""
from __future__ import annotations

import cid as cidlib
import dna
from _t import expect_raises, run

WASM = cidlib.cidv1_raw(b"\x00asm\x01\x00\x00\x00 fake wasm")
VAL = cidlib.cidv1_raw(b"{:integrity/spec \"kotoba-integrity/v0\"}")
LEX = cidlib.cidv1_raw(b"{:lexicon \"ibuki\"}")
DID = "did:web:etzhayyim.com:actor:ibuki"


def _m(**over):
    m = dna.build(actor_did=DID, wasm_cid=WASM, graph="ibuki", validation_cid=VAL, lexicon_cid=LEX)
    m.update(over)
    return m


def test_build_derives_the_graph_binding():
    m = _m()
    assert m[":dna/graph-cid"] == cidlib.graph_cid("ibuki")   # ASSERTED, not implied
    assert m[":dna/spec"] == dna.SPEC and m[":dna/capability"] == "datom:transact"


def test_dna_cid_is_deterministic_and_raw():
    m = _m()
    assert dna.dna_cid(m) == dna.dna_cid(_m())                # same manifest → same identity
    assert dna.dna_cid(m).startswith("bafkrei")               # CIDv1 raw sha256 prefix


def test_any_part_change_changes_the_identity():
    base = dna.dna_cid(_m())
    # recompile the wasm → new code CID → different actor
    assert dna.dna_cid(_m(**{":dna/wasm-cid": cidlib.cidv1_raw(b"other wasm")})) != base
    # edit the rules → new validation CID → different actor
    assert dna.dna_cid(_m(**{":dna/validation-cid": cidlib.cidv1_raw(b"other rules")})) != base
    # retarget the graph → new graph + graph-cid → different actor
    other = dna.build(actor_did=DID, wasm_cid=WASM, graph="ibuki-2", validation_cid=VAL, lexicon_cid=LEX)
    assert dna.dna_cid(other) != base


def test_verify_accepts_a_well_formed_manifest():
    ok, why = dna.verify(_m())
    assert ok and "ok" in why


def test_verify_rejects_a_broken_graph_binding():
    bad = _m(**{":dna/graph-cid": cidlib.graph_cid("some-other-graph")})
    ok, why = dna.verify(bad)
    assert not ok and "graph binding broken" in why


def test_verify_blob_reverify_catches_a_swapped_program():
    m = _m()
    ok, why = dna.verify(m, blobs={":dna/wasm-cid": b"\x00asm\x01\x00\x00\x00 fake wasm"})
    assert ok, why
    ok2, why2 = dna.verify(m, blobs={":dna/wasm-cid": b"a DIFFERENT program"})
    assert not ok2 and "content mismatch" in why2


def test_build_rejects_a_non_cid_part():
    expect_raises(lambda: dna.build(actor_did=DID, wasm_cid="not-a-cid", graph="ibuki",
                                    validation_cid=VAL, lexicon_cid=LEX), contains="not a CIDv1")


def test_build_rejects_a_non_did_actor():
    expect_raises(lambda: dna.build(actor_did="ibuki", wasm_cid=WASM, graph="ibuki",
                                    validation_cid=VAL, lexicon_cid=LEX), contains="must be a DID")


def test_manifest_edn_rejects_unknown_fields():
    expect_raises(lambda: dna.manifest_edn(_m(**{":dna/rogue": "x"})), contains="unknown fields")


def test_did_service_entry_points_at_the_single_dna_cid():
    m = _m()
    svc = dna.did_service_entry(m)
    assert svc["type"] == "EtzhayyimActorDna"
    assert svc["serviceEndpoint"] == f"ipfs://{dna.dna_cid(m)}"
    assert svc["dnaCid"] == dna.dna_cid(m)


if __name__ == "__main__":
    run("dna", [(n, f) for n, f in sorted(globals().items())
                if n.startswith("test_") and callable(f)])
