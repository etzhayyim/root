"""moyai 舫い — end-to-end demonstration of the give-to-get reciprocity loop.

Runnable: `python3 analyze.py` (from this dir). Walks the full lifecycle over a
`:representative` seed and prints a transparency report:

  1. three honest contributors do VERIFIED inference work for the commons → mint credit
  2. one SYBIL submits fabricated work → fails the honeypot gate → mints ZERO
  3. members draw inference back from the commons:
       - within the subsistence floor → FREE for everyone (information-as-BHI)
       - surplus while the mesh is idle → FREE for everyone
       - surplus under contention → contributors burn credit; a freeloader is DEFERRED
         (never denied essentials)
  4. asserts the charter invariants hold on every entry: cash≡0, non-transferable,
     conservation, Basic-High-Income untouched.
"""

from __future__ import annotations

from fair_share import (SUBSISTENCE_FLOOR_UNITS, Decision, affects_basic_high_income,
                        evaluate_draw)
from ledger import MoyaiLedger, redeemable_usd_micros
from proof_of_contribution import (Job, mint_from_verified, period_mint_totals,
                                   verify_batch)


def _frozen_oracle(prompt: str) -> str:
    """Stand-in for a pinned core Murakumo node running the frozen edge model
    deterministically. Same input ⇒ same output (so honeypots are exact)."""
    return f"answer::{prompt}"


def _honest_batch(node: str, n: int, honeypots: int):
    jobs = []
    for i in range(n):
        prompt = f"{node}-q{i}"
        jobs.append(Job(node, f"nonce-{node}-{i}", prompt, _frozen_oracle(prompt),
                        is_honeypot=(i < honeypots)))
    return jobs


def _sybil_batch(node: str, n: int, honeypots: int):
    jobs = []
    for i in range(n):
        prompt = f"{node}-q{i}"
        jobs.append(Job(node, f"nonce-{node}-{i}", prompt, "FABRICATED",  # wrong on purpose
                        is_honeypot=(i < honeypots)))
    return jobs


def run() -> dict:
    ledger = MoyaiLedger()
    report: dict = {"mints": {}, "draws": [], "invariants": {}}
    epoch = 0
    seen: set = set()

    # 1+2. contribution round ------------------------------------------------------------
    contributors = {
        "did:key:abel": _honest_batch("did:key:abel", 60, honeypots=8),   # honest
        "did:key:seth": _honest_batch("did:key:seth", 40, honeypots=6),   # honest
        "did:key:noah": _honest_batch("did:key:noah", 20, honeypots=4),   # honest, small
        "did:key:cain": _sybil_batch("did:key:cain", 50, honeypots=8),    # sybil / fabricated
    }
    minted_totals: dict = {}
    for did, jobs in contributors.items():
        res = verify_batch(jobs, _frozen_oracle,
                           already_minted_this_period=minted_totals.get(did, 0),
                           seen_hashes=seen)
        got = mint_from_verified(ledger, res, epoch=epoch, attestation_id=f"att-{did}")
        minted_totals[did] = minted_totals.get(did, 0) + got
        report["mints"][did] = {"submitted": res.submitted, "minted": got,
                                "accepted": res.accepted, "pass_rate": res.pass_rate}

    assert report["mints"]["did:key:cain"]["minted"] == 0, "sybil must mint nothing"
    assert report["mints"]["did:key:abel"]["minted"] > 0, "honest contributor must mint"

    # 3. draw round (later epoch; some decay has elapsed) --------------------------------
    epoch = 5
    scenarios = [
        # (who, requested, floor_used, mesh_load) -> expected decision family
        ("did:key:abel", 50, 0, 0.95),    # within floor → free (BHI)
        ("did:key:abel", 150, 0, 0.30),   # surplus but idle → free
        ("did:key:abel", 150, 0, 0.95),   # surplus + congested + has credit → charge
        ("did:key:freeloader", 150, 0, 0.95),  # surplus + congested + NO credit → deferred
        ("did:key:freeloader", 80, 0, 0.95),   # within floor → free even with no credit (BHI!)
    ]
    for who, req, used, load in scenarios:
        bal = ledger.balance(who, epoch)
        v = evaluate_draw(requested_units=req, floor_used_this_period=used,
                          mesh_load=load, credit_balance=bal)
        if v.decision is Decision.CHARGE_SURPLUS:
            ledger.burn(who, v.credit_to_burn, epoch, ref=f"draw-{who}-{req}")
        report["draws"].append({
            "who": who, "requested": req, "mesh_load": load,
            "balance": round(bal, 2), "decision": v.decision.value,
            "burned": v.credit_to_burn, "essential_guaranteed": v.essential_guaranteed,
        })

    # 4. charter invariants --------------------------------------------------------------
    ledger.assert_conservation()
    report["invariants"]["cash_zero"] = all(redeemable_usd_micros(e) == 0 for e in ledger.log)
    report["invariants"]["affects_bhi"] = affects_basic_high_income()           # must be False
    report["invariants"]["conservation_minted>=burned"] = (
        ledger.total_minted() >= ledger.total_burned())
    # BHI isolation: the freeloader (zero credit) and abel (credit-rich) get the IDENTICAL
    # essential floor — proof that credit does not touch Basic High Income.
    report["invariants"]["floor_equal_for_all"] = (
        evaluate_draw(requested_units=80, floor_used_this_period=0, mesh_load=0.99,
                      credit_balance=0.0).decision is Decision.FREE_SUBSISTENCE
        and evaluate_draw(requested_units=80, floor_used_this_period=0, mesh_load=0.99,
                          credit_balance=9999.0).decision is Decision.FREE_SUBSISTENCE)
    report["invariants"]["subsistence_floor_units"] = SUBSISTENCE_FLOOR_UNITS

    return report


def main() -> None:
    r = run()
    print("=== moyai 舫い — give-to-get reciprocity report ===\n")
    print("contribution round (mint = verified-work-only):")
    for did, m in r["mints"].items():
        tag = "SYBIL→0" if m["minted"] == 0 and not m["accepted"] else "ok"
        print(f"  {did:<22} submitted={m['submitted']:>3} minted={m['minted']:>4} "
              f"pass_rate={m['pass_rate']:.2f}  [{tag}]")
    print("\ndraw round (free floor + surplus reciprocity under contention):")
    for d in r["draws"]:
        print(f"  {d['who']:<22} req={d['requested']:>3} load={d['mesh_load']:.2f} "
              f"bal={d['balance']:>6} -> {d['decision']:<16} burned={d['burned']}")
    print("\ninvariants:")
    for k, v in r["invariants"].items():
        print(f"  {k} = {v}")
    assert r["invariants"]["affects_bhi"] is False
    assert r["invariants"]["cash_zero"] is True
    assert r["invariants"]["floor_equal_for_all"] is True
    print("\nOK — reward kept, cash≡0, Basic High Income untouched.")


if __name__ == "__main__":
    main()
