#!/usr/bin/env python3
"""Conformance tests for the civil-registry module (matsurigoto 政, ADR-2606062300).

Standalone-runnable AND pytest-compatible.
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import civil_registry as C  # noqa: E402

NOW = "2026-06-05T00:00:00Z"


def test_no_server_authority_certificates_unsigned():
    """G1 — every certificate is unsigned; the module signs nothing."""
    assert C.SERVER_HELD_AUTHORITY is False
    b = C.register_birth("b1", "child:a", ["parent:p"], "place", "2026-01-01T00:00:00Z", NOW)
    assert b["certificate"]["proof"] is None
    assert b["certificate"]["server_held_authority"] is False
    assert b["certificate"]["status"] == "issued-unsigned"


def test_birth_requires_child_and_parent():
    for bad in [("", ["p"]), ("c", [])]:
        try:
            C.register_birth("b", bad[0], bad[1], "place", "2026-01-01T00:00:00Z", NOW)
        except ValueError:
            continue
        raise AssertionError(f"birth should reject {bad}")


def test_birth_rejects_future_occurrence():
    try:
        C.register_birth("b", "c", ["p"], "place", "2027-01-01T00:00:00Z", NOW)
    except ValueError:
        return
    raise AssertionError("future birth must raise")


def test_birth_record_is_immutable_and_minimized():
    b = C.register_birth("b1", "child:aoi", ["parent:rin"], "tokyo", "2026-06-01T00:00:00Z", NOW)
    rec = b["record"]
    assert rec["immutable"] is True
    assert rec["vital_kind"] == "birth"
    assert set(rec["fields"]) == {"child", "parents", "place"}  # G6 minimization


def test_death_registration():
    d = C.register_death("d1", "person:x", "osaka", "2026-05-01T00:00:00Z", NOW, cause="ICD-11:XX")
    assert d["record"]["fields"]["cause"] == "ICD-11:XX"
    assert d["certificate"]["type"][1] == "DeathCertificate"


def test_marriage_requires_distinct_partners():
    try:
        C.register_marriage("m", "a", "a", "place", "2026-01-01T00:00:00Z", NOW)
    except ValueError:
        return
    raise AssertionError("same-person marriage must raise")


def test_marriage_rejects_bigamy():
    existing = [("a", "z")]
    try:
        C.register_marriage("m", "a", "b", "place", "2026-01-01T00:00:00Z", NOW, existing_marriages=existing)
    except ValueError:
        return
    raise AssertionError("already-married partner must raise")


def test_marriage_partners_sorted_deterministic():
    m1 = C.register_marriage("m1", "rin", "aoi", "place", "2026-01-01T00:00:00Z", NOW)
    m2 = C.register_marriage("m2", "aoi", "rin", "place", "2026-01-01T00:00:00Z", NOW)
    assert m1["record"]["fields"]["partners"] == m2["record"]["fields"]["partners"]


def test_append_is_non_destructive_g5():
    hist = []
    b = C.register_birth("b1", "c", ["p"], "place", "2026-01-01T00:00:00Z", NOW)
    hist2 = C.append(hist, b)
    assert hist == []           # original untouched
    assert len(hist2) == 1      # new list returned


def test_residency_latest_is_current_address():
    hist = []
    hist = C.append(hist, C.register_residency("r1", "person:x", "addr-A", "2026-01-01T00:00:00Z", NOW))
    hist = C.append(hist, C.register_residency("r2", "person:x", "addr-B", "2026-03-01T00:00:00Z", NOW))
    # both fixes retained (非終末論); latest = current
    assert len(hist) == 2
    assert C.current_address(hist, "person:x") == "addr-B"


def test_solve_is_gated_at_r0():
    try:
        C.solve()
    except RuntimeError:
        return
    raise AssertionError("solve() must raise at R0")


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
