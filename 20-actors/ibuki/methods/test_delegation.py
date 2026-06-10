"""test_delegation.py — 息吹 (ibuki) the revocable leash: scoped, expiring capability. ADR-2606101200 §委任."""
from __future__ import annotations

import json
import pathlib
import tempfile

import delegation as dg
from _t import expect_raises, run

ACTOR = "did:web:etzhayyim.com:actor:ibuki"
MEMBER = "did:key:zMemberExample"


def _bundle(**over):
    b = {"cacao_b64": "bWVtYmVyLXNpZ25lZC1jYm9y", "aud": ACTOR, "capability": "datom:transact",
         "graph": "ibuki", "exp": 2000, "nonce": "deadbeef"}
    b.update(over)
    return b


def _write(dr, bundle):
    p = pathlib.Path(dr) / "deleg.json"
    p.write_text(json.dumps(bundle), encoding="utf-8")
    return p


def test_load_absent_is_none_not_error():
    assert dg.load(pathlib.Path("/nonexistent/deleg.json")) is None   # fail-open


def test_load_rejects_missing_keys():
    with tempfile.TemporaryDirectory() as dr:
        b = _bundle(); del b["exp"]
        expect_raises(lambda: dg.load(_write(dr, b)), contains="missing keys")


def test_load_rejects_wrong_capability():
    with tempfile.TemporaryDirectory() as dr:
        expect_raises(lambda: dg.load(_write(dr, _bundle(capability="datom:read"))),
                      contains="datom:transact")


def test_load_requires_did_audience_and_nonce():
    with tempfile.TemporaryDirectory() as dr:
        expect_raises(lambda: dg.load(_write(dr, _bundle(aud="ibuki"))), contains="DID")
        expect_raises(lambda: dg.load(_write(dr, _bundle(nonce=""))), contains="nonce")


def test_usable_within_scope_and_window():
    ok, why = dg.is_usable(_bundle(exp=2000), now_epoch=1999, graph="ibuki")
    assert ok and "usable" in why


def test_unusable_when_expired():
    ok, why = dg.is_usable(_bundle(exp=2000), now_epoch=2000, graph="ibuki")
    assert not ok and "expired" in why                  # consent must be renewed


def test_unusable_off_scope_graph():
    ok, why = dg.is_usable(_bundle(graph="ibuki"), now_epoch=1, graph="ibuki-prod")
    assert not ok and "scoped to graph" in why          # never used outside its resource


def test_none_bundle_unusable_failopen():
    ok, why = dg.is_usable(None, now_epoch=1, graph="ibuki")
    assert not ok and "no delegation" in why


def test_actor_did_is_the_audience():
    assert dg.actor_did(_bundle()) == ACTOR


def test_issuance_template_is_member_signed_shape_only():
    """The template is the payload the MEMBER signs in their own runtime — ibuki never signs."""
    t = dg.issuance_template(member_did=MEMBER, actor_did=ACTOR, graph_cid="bafyibuki",
                             exp_epoch=2000, nonce_hex="deadbeef")
    assert t["iss"] == MEMBER and t["aud"] == ACTOR
    assert "datom:transact" in t["resources"][0] and "bafyibuki" in t["resources"][0]
    assert "never signs" in t["_note"]


def test_module_does_no_crypto_stdlib_only():
    src = pathlib.Path(dg.__file__).read_text(encoding="utf-8")
    for needle in ("ed25519", "nacl", "cryptography", "hashlib", "sign(", "private"):
        assert needle not in src, f"delegation must be present-only, no crypto: {needle}"


if __name__ == "__main__":
    run("delegation", [(n, f) for n, f in sorted(globals().items())
                       if n.startswith("test_") and callable(f)])
