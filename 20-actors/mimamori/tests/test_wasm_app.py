#!/usr/bin/env python3
"""mimamori wasm export-body tests — dev-mode verification of the exact component surface."""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "wasm"))
sys.path.insert(0, str(HERE / "methods"))
import app  # noqa: E402

A = "did:web:etzhayyim.com:member:fictional:aleph"
B = "did:web:etzhayyim.com:member:fictional:bet"
PASS = []


def t(name, fn):
    fn()
    PASS.append(name)
    print(f"  ok  {name}")


def test_heartbeat_stateless_deterministic():
    r1 = json.loads(app.heartbeat(1, ""))
    r2 = json.loads(app.heartbeat(1, ""))
    assert r1["cid"] == r2["cid"]                       # same (cycle, prev) → same CID
    r3 = json.loads(app.heartbeat(2, r1["cid"]))
    assert r3["cid"] != r1["cid"]                       # prev-linked chain
    assert r1["txEdn"].startswith("{:tx/id 1 ")
    assert "did:" not in json.dumps(r1["summary"])      # summary counts-only (G5)


def test_host_side_chain_verifies():
    from kotoba import tx_cid
    r1 = json.loads(app.heartbeat(1, ""))
    r2 = json.loads(app.heartbeat(2, r1["cid"]))
    # the host can recompute both CIDs from the returned datoms via read_log parity:
    from _edn import _parse, _tokens
    tx1 = _parse(_tokens(r1["txEdn"]))
    tx2 = _parse(_tokens(r2["txEdn"]))
    assert tx_cid(tx1[":tx/datoms"], "") == r1["cid"]
    assert tx_cid(tx2[":tx/datoms"], r1["cid"]) == r2["cid"]


def test_bonds_of_own_did_only():
    mine = json.loads(app.bonds_of(B))
    assert mine and all(B in (b["keeper"], b["kept"]) for b in mine)   # G4
    assert json.loads(app.bonds_of("did:web:etzhayyim.com:member:fictional:nobody")) == []  # G5


def test_coverage_and_vow():
    cov = app.coverage()
    assert "did:" not in cov and "unkept" in cov        # aggregate-only
    v = app.vow()
    assert "私は弟の保持者でしょうか" in v and "継ぐ者が見守ります" in v


if __name__ == "__main__":
    t("heartbeat stateless + deterministic + prev-linked", test_heartbeat_stateless_deterministic)
    t("host can recompute + verify both CIDs", test_host_side_chain_verifies)
    t("bonds-of is own-DID-only (G4/G5)", test_bonds_of_own_did_only)
    t("coverage aggregate-only + vow intact", test_coverage_and_vow)
    print(f"test_wasm_app: {len(PASS)}/4 green")
