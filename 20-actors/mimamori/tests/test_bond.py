#!/usr/bin/env python3
"""mimamori gate tests — every NEVER clause is asserted as a raised exception."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "methods"))
from bond import Mishmeret, GateViolation, validate_attr, load_seed, replay  # noqa: E402

A = "did:web:etzhayyim.com:member:fictional:aleph"
B = "did:web:etzhayyim.com:member:fictional:bet"
C = "did:web:etzhayyim.com:member:fictional:gimel"
PASS = []


def t(name, fn):
    fn()
    PASS.append(name)
    print(f"  ok  {name}")


def expect_raise(fn, frag):
    try:
        fn()
    except GateViolation as e:
        assert frag in str(e), f"expected '{frag}' in '{e}'"
        return
    raise AssertionError(f"expected GateViolation containing '{frag}'")


def test_lifecycle():
    m = Mishmeret()
    m.offer(A, B)
    m.consent(A, B)
    m.heartbeat(A, B)
    assert any(d[1] == ":mishmeret.keep/act" and d[2] == ":reached-out" for d in m.datoms)


def test_no_keep_without_consent():  # G3
    m = Mishmeret()
    m.offer(A, B)
    expect_raise(lambda: m.heartbeat(A, B), "G3")


def test_decline_and_unilateral_exit():  # G3
    m = Mishmeret()
    m.offer(A, B)
    m.decline(A, B)
    expect_raise(lambda: m.offer(A, B), "cooldown")  # anti-pestering
    m.offer(A, C)
    m.consent(A, C)
    m.exit_bond(A, C)  # unconditional, no penalty — just succeeds
    assert m.bonds_of(C)[0]["state"] == ":exited"


def test_g1_care_whitelist_only():
    m = Mishmeret()
    m.offer(A, B)
    m.consent(A, B)
    m.route_care(A, B, ":kokoro", kept_consents=True)  # ok
    expect_raise(lambda: m.route_care(A, B, ":police", kept_consents=True), "G1")
    expect_raise(lambda: m.route_care(A, B, ":authority", kept_consents=True), "G1")
    expect_raise(lambda: m.route_care(A, B, ":council", kept_consents=True), "G1")


def test_g1b_route_needs_per_act_consent():  # G3
    m = Mishmeret()
    m.offer(A, B)
    m.consent(A, B)
    expect_raise(lambda: m.route_care(A, B, ":kokoro", kept_consents=False), "G3")


def test_g2_no_score_of_soul():
    expect_raise(lambda: validate_attr(":mishmeret.person/risk-score"), "G2")
    expect_raise(lambda: validate_attr(":mishmeret.person/anything"), "G2")
    expect_raise(lambda: validate_attr(":mishmeret.bond/isolation-index"), "G2")
    m = Mishmeret()
    expect_raise(lambda: m._add("x", ":mishmeret.bond/danger-rating", 1, 1), "G2")


def test_g4_symmetric_visibility():
    m = Mishmeret()
    m.offer(A, B)
    m.consent(A, B)
    kept_view = m.bonds_of(B)     # the kept always sees who keeps them
    keeper_view = m.bonds_of(A)
    assert kept_view and kept_view[0]["keeper"] == A
    assert keeper_view and keeper_view[0]["kept"] == B
    assert m.bonds_of(C) == []    # a non-party sees nothing (G5: own-DID-only)


def test_g5_relay_no_sleepless_center():
    m = Mishmeret()
    m.offer(A, B)
    m.consent(A, B)
    m.handoff(A, B, C)
    states = {b["bond"]: b["state"] for b in m.bonds_of(B)}
    assert ":handed-off" in states.values() and ":active" in states.values()
    m.heartbeat(C, B)  # the relay keeper keeps


def test_g7_synthetic_only():
    m = Mishmeret()
    expect_raise(lambda: m.offer("did:web:etzhayyim.com:member:real-person", B), "G7")


def test_append_only_and_determinism():
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = load_seed(here / "data" / "seed-mimamori-bonds.json")
    m1, m2 = replay(seed), replay(seed)
    assert m1.emit() == m2.emit()                       # deterministic
    assert all(d[4] == ":add" for d in m1.datoms)       # append-only, :add only
    n = len(m1.datoms)
    m1.exit_bond("did:web:etzhayyim.com:member:fictional:vav",
                 "did:web:etzhayyim.com:member:fictional:he")
    assert len(m1.datoms) == n + 1                      # exit appends, never removes


if __name__ == "__main__":
    t("lifecycle offer→consent→keep", test_lifecycle)
    t("G3 no keeping without consent", test_no_keep_without_consent)
    t("G3 decline+cooldown / unilateral exit", test_decline_and_unilateral_exit)
    t("G1 care whitelist only (no denunciation rail)", test_g1_care_whitelist_only)
    t("G3 per-act routing consent", test_g1b_route_needs_per_act_consent)
    t("G2 score-of-soul unrepresentable", test_g2_no_score_of_soul)
    t("G4 symmetric visibility / G5 own-DID-only", test_g4_symmetric_visibility)
    t("G5 relay — no sleepless center", test_g5_relay_no_sleepless_center)
    t("G7 synthetic DIDs only at R0", test_g7_synthetic_only)
    t("append-only + deterministic emit", test_append_only_and_determinism)
    print(f"test_bond: {len(PASS)}/10 green")
