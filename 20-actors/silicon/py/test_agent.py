#!/usr/bin/env python3
"""silicon 珪 — agent gate tests (offline, no kotoba host, no network, no LLM).

ADR-2605242500 / 2605242545. Exercises the §2(a)(c) force-review gate (G1),
append-only lot traceability (G8), and chip inalienability (G2).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_litho_requires_force_review() -> bool:
    g = agent.force_review_gate("litho", None)
    return _check("litho without force-review is blocked (G1)", g["allowed"] is False)


def test_implant_denied_verdict_blocks() -> bool:
    g = agent.force_review_gate("implant", {"verdict": "deny"})
    return _check("implant with deny verdict blocked (G1)", g["allowed"] is False)


def test_litho_approve_clears() -> bool:
    g = agent.force_review_gate("litho", {"verdict": "approve-with-conditions"})
    return _check("litho with approve-with-conditions clears (G1)", g["allowed"] is True)


def test_nongated_step_runs() -> bool:
    g = agent.force_review_gate("etch", None)
    return _check("non-§2(a)(c) step needs no review", g["allowed"] is True)


def test_record_step_blocked_without_review() -> bool:
    out = agent.record_process_step({"id": "L", "history": []}, "implant",
                                    "equip/x", "2026-06-02T00:00:00Z", review=None)
    return _check("record implant blocked without review (G1)", out.get("blocked") is True)


def test_record_step_monotonic_index() -> bool:
    lot = {"id": "L", "history": []}
    rev = {"id": "fr.l", "verdict": "approve"}
    lot = agent.record_process_step(lot, "litho", "e1", "t0", rev)
    lot = agent.record_process_step(lot, "deposition", "e2", "t1")
    lot = agent.record_process_step(lot, "etch", "e3", "t2")
    return _check("monotonic gap-free step chain (G8)",
                  [s["stepIndex"] for s in lot["history"]] == [0, 1, 2]
                  and agent.lot_traceable(lot))


def test_packaging_marks_verified() -> bool:
    lot = agent.record_process_step({"id": "L", "history": []}, "packaging",
                                    "e", "t", outcome="ok")
    return _check("packaging ok → lot verified", lot["state"] == "verified")


def test_scrap_outcome_sets_state() -> bool:
    lot = agent.record_process_step({"id": "L", "history": []}, "etch",
                                    "e", "t", outcome="scrapped")
    return _check("scrapped outcome propagates to lot state", lot["state"] == "scrapped")


def test_lease_requires_force_review() -> bool:
    out = agent.lease_chip({"id": "c"}, "did:web:lessee", force_review_uri=None)
    return _check("lease/ship requires force-review (G1)", out.get("blocked") is True)


def test_lease_sets_lessee_not_owner() -> bool:
    out = agent.lease_chip({"id": "c"}, "did:web:lessee", force_review_uri="fr.x")
    return _check("lease sets lessee, no owner attribute (G2)",
                  out.get("leasedToDid") == "did:web:lessee" and "owner" not in out)


def test_sale_is_rejected() -> bool:
    for act in ("sell", "transfer", "burn", "set-owner", "gift"):
        if agent.assert_no_transfer(act)["allowed"]:
            return _check(f"{act} must be rejected (G2)", False)
    return _check("sell/transfer/burn/set-owner/gift all rejected (G2)", True)


def test_lease_is_permitted() -> bool:
    return _check("lease is the only permitted disposition (G2)",
                  agent.assert_no_transfer("lease")["allowed"] is True)


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"silicon agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
