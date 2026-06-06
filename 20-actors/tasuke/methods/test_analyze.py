#!/usr/bin/env python3
"""End-to-end membrane tests for 助 (tasuke) — every case journey costs the victim ¥0."""
from __future__ import annotations

import analyze


def test_run_over_seed_is_all_free():
    res = analyze.run()
    assert res["total_cost"] == 0
    assert res["rows"]
    for r in res["rows"]:
        assert r["cost"] == 0
        assert r["paid_referral"] is False


def test_every_case_generates_member_authored_docs():
    res = analyze.run()
    for r in res["rows"]:
        assert r["docs"]  # at least the police core set
        assert "damage-report" in r["docs"]


def test_unauthorized_transfer_gets_bank_request():
    res = analyze.run()
    fund = next(r for r in res["rows"] if r["kind"] == "unauthorized-transfer")
    assert "bank-freeze-request" in fund["docs"]
    assert fund["severity"] == "critical"


def test_takeover_gets_recovery_plan():
    res = analyze.run()
    to = next(r for r in res["rows"] if r["kind"] == "account-takeover")
    assert "recovery-plan" in to["docs"] and "platform-request" in to["docs"]


def test_report_renders_and_is_free():
    res = analyze.run()
    report = analyze._report(res)
    assert "¥0" in report and "FREE — G1 holds" in report


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"{len(fns) - failed}/{len(fns)} passed in test_analyze.py")
    sys.exit(1 if failed else 0)
