#!/usr/bin/env python3
"""engi ingest — floor-enforcement verification harness.

ADR-2606011000 §D7.1 + ADR-2605310100 §4(2). Mirrors the haraedo/transparency-guard
pytest-invariant precedent. Run: python3 test_engi_ingest.py  (or pytest).
"""
from __future__ import annotations

import engi_ingest as ei
from engi_ingest import Follow

MEMBERS = {"did:plc:alice", "did:plc:bob"}
FOLLOWS = [
    Follow("did:plc:alice", "did:plc:bob"),
    Follow("did:plc:alice", "did:plc:carol"),     # carol = latent non-member
    Follow("did:plc:carol", "did:plc:bob"),
    Follow("did:plc:dave", "did:plc:bob"),         # dave = latent non-member
    Follow("did:plc:bob", "did:plc:alice", "depends-on"),
]


def _run():
    res = ei.ingest(FOLLOWS, MEMBERS)
    return res, ei.to_edn(res)


def test_only_members_emitted_as_organisms():
    res, _ = _run()
    dids = {o[":organism/did"] for o in res.organisms.values()}
    assert dids == MEMBERS, f"non-member organism leaked: {dids - MEMBERS}"


def test_edges_only_between_members():
    res, _ = _run()
    # alice→bob (follows) and bob→alice (depends-on) qualify; the 3 latent-touching drop.
    kinds = sorted((e[":en/kind"], e[":en/from"], e[":en/to"]) for e in res.edges)
    assert len(res.edges) == 2, f"expected 2 member-member edges, got {len(res.edges)}"
    assert all(":follows" == k or ":depends-on" == k for k, *_ in kinds)


def test_floor_F2_no_latent_identity_in_output():
    res, edn = _run()
    for latent in ("carol", "dave"):
        assert latent not in edn, f"F2 breach: latent id {latent} leaked into EDN"


def test_floor_F1_no_ownership_keyword():
    _, edn = _run()
    for kw in ei.FORBIDDEN_KEYWORDS:
        assert kw not in edn, f"F1 breach: {kw} present"


def test_grasping_load_present_and_positive():
    res, _ = _run()
    for e in res.edges:
        assert e[":en/grasping-load"] > 0.0
        assert e[":en/source"].startswith(":atproto")


def test_grasp_concentration_counts_latent_anonymously():
    """bob has in-degree 3 (alice, carol, dave) → concentration 3.0, but carol/dave
    are never named — the §4(2) aggregate-first guarantee."""
    res, edn = _run()
    bob = res.grasp["did:plc:bob"]
    assert bob[":grasp/concentration"] == 3.0
    assert res.latent_aggregate["latent-organism-count"] == 2     # carol, dave
    assert res.latent_aggregate["latent-incident-edges"] == 3
    assert "carol" not in edn and "dave" not in edn


def test_validate_floor_clean_on_good_output():
    res, edn = _run()
    assert ei.validate_floor(edn, res, MEMBERS) == []


def test_validate_floor_catches_injected_owns():
    res, edn = _run()
    poisoned = edn + "\n  {:owns \"org.x\"}"
    v = ei.validate_floor(poisoned, res, MEMBERS)
    assert any("F1" in x for x in v), "guard failed to catch injected :owns"


def test_validate_floor_catches_leaked_latent_id():
    res, edn = _run()
    poisoned = edn + "\n  {:organism/did \"did:plc:carol\"}"
    v = ei.validate_floor(poisoned, res, MEMBERS)
    assert any("F2" in x for x in v), "guard failed to catch leaked latent id"


def test_edn_bracket_balance():
    _, edn = _run()
    # strip strings, then count
    out, instr = [], False
    for ch in edn:
        if ch == '"':
            instr = not instr
            continue
        if not instr and ch != ";":
            out.append(ch)
    t = "".join(out)
    for o, c in (("[", "]"), ("{", "}"), ("(", ")")):
        assert t.count(o) == t.count(c), f"{o}{c} imbalance"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} engi-ingest floor tests passed")
