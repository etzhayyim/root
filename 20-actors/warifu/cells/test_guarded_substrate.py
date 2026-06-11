"""GuardedSubstrate tests — the production write guard enforces the EAVT schema at runtime.

Runnable standalone:
    python 20-actors/warifu/cells/test_guarded_substrate.py
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
gs = importlib.import_module("warifu_cells.guarded_substrate")

AuthRequest = wc.authorize.__globals__["AuthRequest"]
Funding = wc.authorize.__globals__["Funding"]
Decision = wc.authorize.__globals__["Decision"]
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
    backend = wc.InMemorySubstrate()
    backend.add_card("tok", "acct", balance=1_000_000)
    sub = gs.GuardedSubstrate(backend)

    # --- full lifecycle runs unchanged through the guard, writing to the backend ---
    a = wc.authorize(AuthRequest("tok", 300_000, Funding.DEBIT, "internal-purchase", "did:m", "k"), sub)
    check("authorize through guard approves", a.decision is Decision.APPROVE)
    st = wc.settle(SettleReq(a.auth_id), sub)
    check("settle through guard settles", st.settled)
    rf = wc.refund(RefundReq(st.settlement_id), sub)
    check("refund through guard ok", rf.refunded)
    dp = wc.dispute(DisputeReq(st.settlement_id, "fraud", "did:u", 300_000, ["bafyCID"]), sub)
    check("dispute through guard opens", dp.opened)
    check("facts landed in backend ledger", len(backend.facts) > 0)
    check("backend facts conform to schema", wc.validate_facts(backend.facts) == [])

    # --- reads/chain ops delegate transparently ---
    check("resolve_card delegates", sub.resolve_card("tok") == "acct")
    check("usdc_balance delegates", isinstance(sub.usdc_balance("acct"), int))

    # --- the guard REJECTS a fee-leaking write before it can reach the backend ---
    fresh_backend = wc.InMemorySubstrate()
    guarded = gs.GuardedSubstrate(fresh_backend)
    try:
        guarded.write_facts([("e", "warifu/fee_usdc", 1, "t")])  # nonzero fee
        raise SystemExit("guard accepted a fee-leaking fact")
    except AssertionError:
        check("guard rejects nonzero-fee write", True)
    check("rejected write never reached backend", fresh_backend.facts == [])

    # --- unknown attribute also rejected ---
    try:
        guarded.write_facts([("e", "warifu/bogus", "x", "t")])
        raise SystemExit("guard accepted unknown attribute")
    except AssertionError:
        check("guard rejects unknown attribute", True)

    print(f"warifu guarded-substrate: {PASS} checks passed")


if __name__ == "__main__":
    run()
