#!/usr/bin/env python3
"""shakai.py — keeper-side social-capital mint bridge (ADR-2606082100 Part A reuse).

The mishmar storage covenant defines social capital as minted by two value-acts:
information disclosure and **wellbecoming intervention** — and mandates that it
REUSE the moyai 舫い ledger primitive verbatim (non-monetary, non-transferable,
decaying, conservation-bound; ADR-2606062100). Keeping (見守り) is the purest
form of wellbecoming intervention, so mimamori is the first actor to close that
loop in code:

    keeping act (content-free heartbeat on a consented bond)
        → mint 1 unit of social capital TO THE KEEPER (capped per epoch)
        → decays (a flow, never a store) — keeping must be lived, not banked

Invariants carried over from the moyai family, enforced by the imported ledger
(reuse, NOT reimplementation — 50-infra/etzhayyim-moyai-credit/methods/ledger.py):
no transfer/gift/pool verb exists · redeemable_usd_micros ≡ 0 (cash≡0, BHI
firewall) · burn ≤ decayed balance (conservation) · half-life decay.

mimamori-specific invariants enforced HERE:
  - mints go to the KEEPER only — there is no path that writes anything about
    the kept (G2 no-score: the kept's side of a keeping act is not a record)
  - provenance refs are sha256-opaque — a ledger entry never carries a kept DID
  - per-keeper per-epoch earn cap (moyai anti-sybil pattern): keeping is
    covenant, not a mining surface (G8 no-gamification)
  - grants_governance_weight() / grants_benefit_or_stage() are const-False —
    social capital never buys votes or 救済 stage (moyai invariants verbatim)

Offline-only at R1: the synthetic engine's own validator (G3 consent) is the
verification layer; the witness-quorum + KaizenObserver wellbecoming-Δ mint
path of ADR-2606082100 is the G7-gated live leg. Stdlib + moyai reuse only.
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve()
sys.path.insert(0, str(_HERE.parent))
# verbatim reuse of the moyai-family ledger (ADR-2606082100 Part A: "social capital
# MUST reuse that ledger primitive verbatim" — vendored into the wasm build at R2+)
sys.path.insert(0, str(_HERE.parents[3] / "50-infra" / "etzhayyim-moyai-credit" / "methods"))
from ledger import HALF_LIFE_EPOCHS, MoyaiLedger, redeemable_usd_micros  # noqa: E402,F401

MINT_PER_ACT = 1        # one keeping act = one unit (integer, implied units)
EARN_CAP_PER_EPOCH = 3  # per-keeper cap: keeping is covenant, not a mining surface


def grants_governance_weight() -> bool:
    """INVARIANT (moyai-family verbatim): social capital never weighs a vote. 1 SBT = 1 vote."""
    return False


def grants_benefit_or_stage() -> bool:
    """INVARIANT (moyai-family verbatim): social capital never gates 救済/benefit/stage.
    The BHI subsistence floor is unconditional (ADR-2606062100 firewall)."""
    return False


def _opaque_ref(keep_entity: str) -> str:
    """Provenance ref with NO DID inside — linkable by the parties who hold the keep
    entity id, opaque to everyone else (the ledger never becomes a who-keeps-whom registry)."""
    return "keep:" + hashlib.sha256(keep_entity.encode("utf-8")).hexdigest()[:16]


def keeping_acts(engine) -> list[tuple[str, str]]:
    """(keeper_did, keep_entity) per content-free heartbeat. Consent is guaranteed by
    construction: the bond engine refuses a heartbeat on any non-consented bond (G3)."""
    keep_bond = {e: v for (e, a, v, _t, _o) in engine.datoms if a == ":mishmeret.keep/bond"}
    acts = []
    for (e, a, v, _t, _o) in engine.datoms:
        if a == ":mishmeret.keep/act" and v == ":reached-out":
            bid = keep_bond[e]
            acts.append((engine._keeper[bid], e))
    return acts


def mint_from_keeping(engine, ledger: MoyaiLedger, epoch: int) -> dict:
    """Mint social capital to keepers for this engine's keeping acts (capped). Returns an
    aggregate summary; the per-keeper balances live in the ledger, DID-bound (Soulbound)."""
    minted = capped = 0
    per_keeper: dict[str, int] = {}
    for keeper, keep_entity in keeping_acts(engine):
        if per_keeper.get(keeper, 0) >= EARN_CAP_PER_EPOCH:
            capped += 1
            continue
        ledger.mint(keeper, MINT_PER_ACT, epoch, _opaque_ref(keep_entity))
        per_keeper[keeper] = per_keeper.get(keeper, 0) + 1
        minted += 1
    ledger.assert_conservation()
    return {  # aggregate-only counts (G5); balances are queried per-DID by their holder
        "acts": minted + capped,
        "minted_units": minted * MINT_PER_ACT,
        "capped_acts": capped,
        "keepers_minted": len(per_keeper),
    }


def social_capital_datoms(ledger: MoyaiLedger, epoch: int) -> list[list]:
    """EAVT assertions for the epoch's mint entries (Soulbound: holder DID is the
    keeper's own earned credit; refs are opaque — no kept DID anywhere)."""
    out = []
    for i, e in enumerate(ledger._log):
        if e.epoch != epoch:
            continue
        eid = f"shakai.{epoch}.{i}"
        out.append([":db/add", eid, ":social.capital/holder", e.holder_did])
        out.append([":db/add", eid, ":social.capital/op", ":" + e.op])
        out.append([":db/add", eid, ":social.capital/units", e.units])
        out.append([":db/add", eid, ":social.capital/epoch", e.epoch])
        out.append([":db/add", eid, ":social.capital/ref", e.ref])
    return out
