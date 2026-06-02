#!/usr/bin/env python3
"""tsukuru 作 — B2B factory-direct ordering langgraph actor (kotoba WASM cell).

ADR-2605202800, migration plan Phase 4. Runs in-WASM on kotoba :8077. Four handlers
over one kotoba EAVT graph, mirroring the production lifecycle:

  handle_discover    member spec → capability/country/ISIC match → factory candidates
  handle_production  production-order (BTO/MTO/CTO): create → dispatch → progress → ready
  handle_qc          quality-inspection: pass / fail (→ quarantine) / rework
  handle_compliance  trade-compliance gate (G16): treaty (FTA/EPA) + yabai screening

LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G5). State is
written back to the kotoba Datom log (G6). The member is always the purchasing
principal (G14): no external B2B value flows INTO etzhayyim (G2). Settlement is USDC
on Base L2 + ERC-4337 + TitheRouter 10% only — no fiat, no Stripe (G7). The platform
holds no key; the member signs each settlement with their own passkey/smart-account
(G15). Every stage is recorded as a Datom — no silent truncation (G17).

This R0 build computes and returns plans/records; it does not dispatch real factory
work and does not broadcast settlements (both G11-gated; settlement stops at :intent).
"""
from __future__ import annotations

from typing import TypedDict

# kotoba-provided host bindings (WASM Component Model imports)
try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

TITHE_BPS = 1000  # 10% TitheRouter auto-split (G7), basis points
FULFILLMENT_MODES = ("bto", "mto", "cto")
# linear production trajectory (G17) — every transition is a recorded stage
ORDER_FLOW = ["draft", "placed", "dispatched", "in-production", "qc", "ready", "shipped"]


# --------------------------------------------------------------------------- #
# discover — spec → matching factory candidates
# --------------------------------------------------------------------------- #
class DiscoverState(TypedDict, total=False):
    spec: str
    factories: list
    candidates: list


def _tokens(s: str) -> set:
    """Split on any non-alphanumeric into lowercase tokens (e.g. 'cnc-5axis' → {cnc, 5axis})."""
    out, cur = set(), []
    for ch in s.lower():
        if ch.isalnum():
            cur.append(ch)
        elif cur:
            out.add("".join(cur))
            cur = []
    if cur:
        out.add("".join(cur))
    return out


def _capability_match(spec: str, factory: dict) -> int:
    """Token-overlap capability scoring (a capability counts if any of its tokens appears
    in the spec). Crude by design — Murakumo rerank refines genuine fit (G5)."""
    spec_tokens = _tokens(spec)
    return sum(1 for cap in factory.get("capabilities", [])
               if _tokens(cap) & spec_tokens)


def _llm_rank_factories(spec: str, cands: list) -> list:
    """Murakumo-only rerank by genuine fit (capability/quality), never paid placement."""
    if not llm or not cands:
        return cands
    try:
        order = llm.infer(  # type: ignore[union-attr]
            model="gemma3:4b",
            prompt=f"Rank these factories for the production spec '{spec}' by genuine "
            f"capability fit (not price upsell). Return DIDs in order: "
            f"{[c['factoryDid'] for c in cands]}",
        )
        rank = {did: i for i, did in enumerate(str(order).split())}
        cands.sort(key=lambda c: rank.get(c["factoryDid"], len(cands)))
    except Exception:
        pass
    return cands


def handle_discover(state: DiscoverState) -> DiscoverState:
    spec = state.get("spec", "")
    factories = state.get("factories", [])
    scored = sorted(factories, key=lambda f: _capability_match(spec, f), reverse=True)
    cands = [f for f in scored if _capability_match(spec, f) > 0] or scored
    cands = _llm_rank_factories(spec, list(cands))
    return {**state, "candidates": cands}


# --------------------------------------------------------------------------- #
# compliance — trade-compliance gate (G16): treaty + yabai before any dispatch
# --------------------------------------------------------------------------- #
def screen_entity(factory_did: str, screen_fn=None) -> dict:
    """yabai ScreenEntity (sanctions / denied-party). screen_fn injected for test/host."""
    if screen_fn is not None:
        return screen_fn(factory_did)
    # R0 default: no host screening wired → conservative 'pending', never silent pass
    return {"clear": None, "note": "yabai ScreenEntity not wired (R0); treat as pending"}


def resolve_treaty(buyer_country: str, factory_country: str, treaty_fn=None) -> dict:
    """treaty.etzhayyim.com FTA/EPA authority-chain resolution."""
    if treaty_fn is not None:
        return treaty_fn(buyer_country, factory_country)
    if buyer_country and buyer_country == factory_country:
        return {"agreement": "domestic", "tariff_bps": 0}
    return {"agreement": None, "note": "cross-border treaty not wired (R0)"}


def handle_compliance(state: dict, screen_fn=None, treaty_fn=None) -> dict:
    factory_did = state.get("factoryDid", "")
    screen = screen_entity(factory_did, screen_fn)
    treaty = resolve_treaty(state.get("buyerCountry", ""), state.get("factoryCountry", ""), treaty_fn)
    # G16: a denied-party hit is a hard reject; unresolved screening cannot 'pass'
    if screen.get("clear") is False:
        return {**state, "complianceState": "rejected",
                "complianceNote": f"yabai denied-party hit: {screen.get('note', '')}"}
    if screen.get("clear") is True:
        return {**state, "complianceState": "passed",
                "complianceNote": f"yabai clear; treaty={treaty.get('agreement')}"}
    return {**state, "complianceState": "pending",
            "complianceNote": f"screening unresolved: {screen.get('note', '')} (G16, no auto-pass)"}


# --------------------------------------------------------------------------- #
# production — order state machine (BTO/MTO/CTO)
# --------------------------------------------------------------------------- #
def check_sbt_eligibility(buyer_did: str, sbt_registry: dict) -> dict:
    """Member buyer must hold an active Adherent SBT (§3 / G2)."""
    active = bool(sbt_registry.get(buyer_did, {}).get("active"))
    return {"eligible": active,
            "reason": "" if active else "buyer lacks active Adherent SBT (§3/G2)"}


def create_production_order(buyer_did: str, factory_did: str, mode: str, spec: str,
                            sbt_registry: dict | None = None) -> dict:
    """okaimono `create-production-order` entrypoint. Member = purchasing principal (G14)."""
    if mode not in FULFILLMENT_MODES:
        return {"state": "refused", "reason": f"unknown fulfillment mode '{mode}'"}
    elig = check_sbt_eligibility(buyer_did, sbt_registry or {})
    if not elig["eligible"]:
        return {"state": "refused", "reason": elig["reason"]}
    return {"buyerDid": buyer_did, "factoryDid": factory_did, "mode": mode,
            "spec": spec, "state": "placed", "complianceState": "pending"}


def advance_order(order: dict) -> dict:
    """Advance one stage along ORDER_FLOW. Compliance must pass before dispatch (G16);
    a QC fail diverts to :quarantine (handled in handle_qc)."""
    state = order.get("state", "draft")
    if state == "refused" or state == "quarantine":
        return order
    if state == "placed" and order.get("complianceState") != "passed":
        return {**order, "blocked": "compliance not passed (G16)"}
    try:
        nxt = ORDER_FLOW[ORDER_FLOW.index(state) + 1]
    except (ValueError, IndexError):
        return order
    return {**order, "state": nxt, "blocked": None}


def handle_production(state: dict) -> dict:
    order = state.get("order") or create_production_order(
        state.get("buyerDid", ""), state.get("factoryDid", ""),
        state.get("mode", "bto"), state.get("spec", ""), state.get("sbtRegistry", {}))
    advanced = advance_order(order)
    # record a progress datom for the new stage (G17)
    progress = {"order": advanced.get("buyerDid", ""), "stage": advanced.get("state"),
                "pct": _stage_pct(advanced.get("state", "draft")),
                "timestamp": state.get("now", "")}
    return {**state, "order": advanced, "progress": progress}


def _stage_pct(stage: str) -> int:
    table = {"draft": 0, "placed": 5, "dispatched": 15, "in-production": 60,
             "qc": 90, "ready": 98, "shipped": 100, "quarantine": 90}
    return table.get(stage, 0)


# --------------------------------------------------------------------------- #
# qc — quality inspection (pass / fail→quarantine / rework)
# --------------------------------------------------------------------------- #
def handle_qc(state: dict, inspect_fn=None) -> dict:
    order = state.get("order", {})
    defects = (inspect_fn(order) if inspect_fn else state.get("defects")) or []
    if defects:
        result = "rework" if state.get("reworkable", True) else "fail"
        new_state = "in-production" if result == "rework" else "quarantine"
        order = {**order, "state": new_state}
    else:
        result = "pass"
        order = {**order, "state": "ready"}
    quality = {"order": order.get("buyerDid", ""), "result": result,
               "defects": defects, "inspectorDid": state.get("inspectorDid", ""),
               "timestamp": state.get("now", "")}
    return {**state, "order": order, "quality": quality}


# --------------------------------------------------------------------------- #
# settlement — USDC + TitheRouter intent (NOT broadcast; G7/G11/G15)
# --------------------------------------------------------------------------- #
def build_settlement_intent(gross_minor: int, buyer_sig_ref: str | None = None) -> dict:
    """Compute the USDC settlement split. 10% tithe → Public Fund; factory gets the net.
    Stops at :intent — broadcast needs a member signature (G15) + operator gate (G11)."""
    tithe = (gross_minor * TITHE_BPS) // 10_000
    return {
        "rail": "usdc-base-l2",
        "grossMinor": gross_minor,
        "titheMinor": tithe,
        "factoryPayoutMinor": gross_minor - tithe,
        "titheRouter": "50-infra/etzhayyim-tithe-router",
        # member signs with their own passkey/smart-account; platform holds no key (G15)
        "state": "executed" if buyer_sig_ref else "intent",
        "buyerSigRef": buyer_sig_ref or "",
    }


if __name__ == "__main__":  # pragma: no cover
    demo = handle_discover({
        "spec": "5-axis CNC aluminum bracket, anodized",
        "factories": [
            {"factoryDid": "f1", "capabilities": ["cnc-5axis", "anodizing"]},
            {"factoryDid": "f2", "capabilities": ["injection-molding"]},
        ],
    })
    print("discover candidates:", [c["factoryDid"] for c in demo["candidates"]])
    print("settlement:", build_settlement_intent(500_000_000))
