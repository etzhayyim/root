"""warifu EAVT datom conformance — every fact a full lifecycle emits matches the schema.

Runnable standalone:
    python 20-actors/warifu/cells/test_eavt_schema.py

Runs authorize -> capture -> settle -> refund -> dispute on one InMemorySubstrate and asserts the
accumulated `warifu/*` facts all conform to cells/eavt_schema.py (the kotoba write contract),
including the zero-fee and T+0 invariants. This is the guard the real @etzhayyim/sdk adapter runs
before writing to kotoba.
"""

from __future__ import annotations

import importlib
import importlib.util
import pathlib
import sys

_CELLS = pathlib.Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "warifu_cells", _CELLS / "__init__.py", submodule_search_locations=[str(_CELLS)]
)
wc = importlib.util.module_from_spec(_spec)
sys.modules["warifu_cells"] = wc
_spec.loader.exec_module(wc)
es = importlib.import_module("warifu_cells.eavt_schema")

AuthRequest = wc.authorize.__globals__["AuthRequest"]
Funding = wc.authorize.__globals__["Funding"]
Decision = wc.authorize.__globals__["Decision"]
CapReq = wc.capture.__globals__["CaptureRequest"]
SettleReq = wc.settle.__globals__["CaptureRequest"]
RefundReq = wc.refund.__globals__["RefundRequest"]
DisputeReq = wc.dispute.__globals__["DisputeRequest"]

PASS = 0
def check(name, cond):
    global PASS
    assert cond, f"FAIL: {name}"
    PASS += 1
    print(f"  ok {name}")


def run():
    s = wc.InMemorySubstrate()
    s.add_card("tok", "acct", balance=1_000_000)

    a = wc.authorize(AuthRequest("tok", 400_000, Funding.DEBIT, "internal-purchase", "did:m", "k"), s)
    check("authorize approved", a.decision is Decision.APPROVE)
    cap = wc.capture(CapReq(a.auth_id, 100_000), s)
    check("partial capture", cap.captured)
    st = wc.settle(SettleReq(a.auth_id), s)
    check("settle settled", st.settled)
    rf = wc.refund(RefundReq(st.settlement_id, 100_000), s)
    check("refund ok", rf.refunded)
    dp = wc.dispute(DisputeReq(st.settlement_id, "fraud", "did:u", 300_000, ["bafyCID"]), s)
    check("dispute opened", dp.opened)

    # --- the core assertion: every emitted fact conforms to the kotoba schema ---
    violations = es.validate_facts(s.facts)
    check(f"all {len(s.facts)} EAVT facts conform to schema", violations == [])

    kinds = {v for (e, attr, v, t) in s.facts if attr == "warifu/kind"}
    check("all 5 entity kinds emitted", kinds == {"auth_hold", "capture", "settlement", "refund", "dispute"})

    fee_facts = [v for (e, attr, v, t) in s.facts if attr == "warifu/fee_usdc"]
    check("fee facts present and all zero", len(fee_facts) >= 3 and all(v == 0 for v in fee_facts))

    check("finality T+0 emitted", any(attr == "warifu/finality" and v == "T+0" for (e, attr, v, t) in s.facts))
    check("evidence stored as CID", any(attr == "warifu/evidence_cid" for (e, attr, v, t) in s.facts))

    # --- negative: assert_valid must reject a malformed/fee-leaking fact ---
    bad = [("e", "warifu/fee_usdc", 1, "t")]  # nonzero fee
    try:
        es.assert_valid(bad)
        raise SystemExit("assert_valid accepted a fee-leaking fact")
    except AssertionError:
        check("assert_valid rejects nonzero fee fact", True)

    unknown = [("e", "warifu/bogus", "x", "t")]
    check("validator flags unknown attribute", es.validate_facts(unknown) != [])

    print(f"warifu eavt-schema: {PASS} checks passed")


if __name__ == "__main__":
    run()
