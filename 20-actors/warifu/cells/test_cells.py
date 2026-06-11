"""warifu cell tests — happy + negative paths over InMemorySubstrate.

Runnable standalone (no pytest required, and the dir name `20-actors` is not import-safe):
    python 20-actors/warifu/cells/test_cells.py

Loads the `cells` dir as a synthetic package so the relative imports resolve.
"""

from __future__ import annotations

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

AuthRequest = wc.authorize.__globals__["AuthRequest"]
Funding = wc.authorize.__globals__["Funding"]
Decision = wc.authorize.__globals__["Decision"]
CapReq = wc.capture.__globals__["CaptureRequest"]
SettleReq = wc.settle.__globals__["CaptureRequest"]
RefundReq = wc.refund.__globals__["RefundRequest"]
DisputeReq = wc.dispute.__globals__["DisputeRequest"]


def _fresh():
    s = wc.InMemorySubstrate()
    s.add_card("tok-debit", "acct-A", balance=1_000_000)        # 1.0 USDC
    s.add_card("tok-credit", "acct-B", credit=500_000)          # 0.5 USDC 0% line
    s.add_card("tok-broke", "acct-C", balance=0)
    return s


PASS = 0


def check(name, cond):
    global PASS
    assert cond, f"FAIL: {name}"
    PASS += 1
    print(f"  ok {name}")


def run():
    # --- authorize: purpose gate ---------------------------------------------------------
    s = _fresh()
    r = wc.authorize(AuthRequest("tok-debit", 100, Funding.DEBIT, "purchase", "did:m", "k"), s)
    check("external purchase GATED before phase2", r.decision is Decision.GATED)
    r = wc.authorize(AuthRequest("tok-debit", 100, Funding.DEBIT, "purchase", "did:m", "k"), s, phase2_enabled=True)
    check("external purchase APPROVE after phase2", r.decision is Decision.APPROVE)
    r = wc.authorize(AuthRequest("tok-debit", 100, Funding.DEBIT, "tip", "did:m", "k"), s)
    check("unknown purpose DECLINE", r.decision is Decision.DECLINE)

    # --- authorize: balance / credit / card edges ---------------------------------------
    s = _fresh()
    r = wc.authorize(AuthRequest("tok-broke", 100, Funding.DEBIT, "internal-purchase", "did:m", "k"), s)
    check("insufficient debit balance DECLINE", r.decision is Decision.DECLINE)
    r = wc.authorize(AuthRequest("tok-credit", 600_000, Funding.CREDIT, "internal-purchase", "did:m", "k"), s)
    check("credit over-limit DECLINE", r.decision is Decision.DECLINE)
    r = wc.authorize(AuthRequest("tok-missing", 100, Funding.DEBIT, "internal-purchase", "did:m", "k"), s)
    check("unknown card DECLINE", r.decision is Decision.DECLINE)

    # --- authorize happy + zero-fee fact -------------------------------------------------
    s = _fresh()
    a = wc.authorize(AuthRequest("tok-debit", 300_000, Funding.DEBIT, "internal-purchase", "did:m", "k"), s)
    check("authorize APPROVE", a.decision is Decision.APPROVE and a.auth_id)
    check("zero-fee fact present", (a.auth_id, "warifu/fee_usdc", 0, a.auth_id) in a.eavt_facts)
    check("EAVT facts persisted", any(f[1] == "warifu/kind" for f in s.facts))

    # --- settle happy + money moved (fee 0) ---------------------------------------------
    sr = wc.settle(SettleReq(a.auth_id), s)
    check("settle settled", sr.settled and sr.fee_usdc == 0 and sr.finality == "T+0")
    check("holder debited exactly amount", s.balances["acct-A"] == 700_000)
    check("merchant credited exactly amount", s.balances["did:m"] == 300_000)
    check("settle unknown auth -> not settled", not wc.settle(SettleReq("auth-nope"), s).settled)

    # --- capture partial then remaining, then over-capture rejected ----------------------
    s = _fresh()
    a = wc.authorize(AuthRequest("tok-debit", 400_000, Funding.DEBIT, "internal-purchase", "did:m", "k"), s)
    c1 = wc.capture(CapReq(a.auth_id, 150_000), s)
    check("partial capture", c1.captured and c1.remaining_usdc == 250_000)
    c2 = wc.capture(CapReq(a.auth_id, 250_000), s)
    check("remaining capture", c2.captured and c2.remaining_usdc == 0)
    c3 = wc.capture(CapReq(a.auth_id, 1), s)
    check("over-capture rejected", not c3.captured)

    # --- refund happy + over-refund rejected --------------------------------------------
    s = _fresh()
    a = wc.authorize(AuthRequest("tok-debit", 200_000, Funding.DEBIT, "internal-purchase", "did:m", "k"), s)
    sr = wc.settle(SettleReq(a.auth_id), s)
    rf = wc.refund(RefundReq(sr.settlement_id, 50_000), s)
    check("partial refund (fee 0)", rf.refunded and rf.fee_usdc == 0)
    check("refund returned to holder", s.balances["acct-A"] == 850_000)
    over = wc.refund(RefundReq(sr.settlement_id, 200_000), s)
    check("over-refund rejected", not over.refunded)
    check("refund unknown settlement rejected", not wc.refund(RefundReq("settle-nope"), s).refunded)

    # --- credit settle draws 0% line, refund repays it ----------------------------------
    s = _fresh()
    a = wc.authorize(AuthRequest("tok-credit", 200_000, Funding.CREDIT, "internal-purchase", "did:m", "k"), s)
    sr = wc.settle(SettleReq(a.auth_id), s)
    check("credit draw reduces 0% line", s.credit["acct-B"] == 300_000)
    wc.refund(RefundReq(sr.settlement_id), s)
    check("credit refund repays 0% line", s.credit["acct-B"] == 500_000)

    # --- dispute: invalid reason + happy (encrypted-CID evidence) ------------------------
    s = _fresh()
    a = wc.authorize(AuthRequest("tok-debit", 100_000, Funding.DEBIT, "internal-purchase", "did:m", "k"), s)
    sr = wc.settle(SettleReq(a.auth_id), s)
    bad = wc.dispute(DisputeReq(sr.settlement_id, "bogus", "did:u", 100_000), s)
    check("invalid reason_code rejected", not bad.opened)
    d = wc.dispute(DisputeReq(sr.settlement_id, "fraud", "did:u", 100_000, ["bafyEncCID"]), s)
    check("dispute opened", d.opened and d.status.value == "open")
    check("evidence stored as CID fact", any(f[1] == "warifu/evidence_cid" for f in d.eavt_facts))
    nf = wc.dispute(DisputeReq("settle-nope", "fraud", "did:u", 1), s)
    check("dispute on unknown settlement rejected", not nf.opened)

    print(f"warifu cells: {PASS} checks passed")


if __name__ == "__main__":
    run()
