#!/usr/bin/env python3
"""okaimono 御買物 — provisioning-commons langgraph actor (kotoba WASM cell).

ADR-2606012100. Runs in-WASM on kotoba :8077. Six handlers over one kotoba EAVT
graph, organized as three concentric rings (commons → internal → external):

  handle_discover   need → Ring 0 commons-first → Ring 1 internal → Ring 2 external
  handle_compare    Wellbecoming-axis scoring (cost/durability/repairability/labor/carbon)
  handle_basket     multi-source / multi-gen landed-cost roll-up (+ tithe)
  handle_provision  checkout router (internal USDC+tithe / external handoff / proxy refused)
  handle_lifecycle  end-of-life route + Wellbecoming trajectory stamp

LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G5). State is
written back to the kotoba Datom log (G6). NO ads / affiliate / paid ranking (G3).
External `purchase` value never flows into etzhayyim (G2): Ring 2 R0 is a self-checkout
handoff; 代理-purchase is refused unless an explicit Council/operator gate-ref is present
(G11). All scoring optimizes sufficiency + durability + multi-gen, never engagement (G4).

This R0 build computes and returns plans/records; it does not execute real external
purchases and does not run live scraping ingest (both G11-gated).
"""
from __future__ import annotations

from typing import TypedDict
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

# kotoba-provided host bindings (WASM Component Model imports)
try:
    from kotoba import datalog, llm  # type: ignore
except ImportError:  # local dev fallback
    datalog = llm = None  # type: ignore

# Ring ordering is constitutional (G4): commons before internal before external.
RING_ORDER = ["commons", "internal", "external"]
TITHE_BPS = 1000  # 10% TitheRouter auto-split (G7), basis points


# --------------------------------------------------------------------------- #
# Wellbecoming comparison (G3/G4) — NO price-only ranking, NO paid placement.
# --------------------------------------------------------------------------- #
_LABOR_RANK = {"etzhayyim-dignity": 3, "verified-fair": 2, "disclosed": 1, "unknown": 0}


def _wellbecoming_score(p: dict) -> float:
    """Higher = better. Rewards durability + repairability + dignified labor; lightly
    penalizes embodied carbon and landed cost. Sufficiency-oriented, never engagement."""
    durability = float(p.get("durabilityYears", 0.0))
    repair = float(p.get("repairability", 0))
    labor = _LABOR_RANK.get(p.get("laborProvenance", "unknown"), 0)
    carbon = float(p.get("carbonKg", 0.0))
    price = float(p.get("priceMinor", 0)) / 1_000_000.0
    return (durability * 2.0) + (repair * 1.5) + (labor * 3.0) - (carbon * 0.1) - (price * 0.05)


# --------------------------------------------------------------------------- #
# discover — commons-first three-ring search
# --------------------------------------------------------------------------- #
class DiscoverState(TypedDict, total=False):
    need_text: str
    member_did: str
    household_scope: str
    candidates: list
    resolved_ring: str


def handle_discover(state: DiscoverState) -> DiscoverState:
    """need → intent → Ring 0 commons → Ring 1 internal → Ring 2 external.

    Returns the first ring that yields candidates as `resolved_ring` (commons-first,
    G4/G12), but always carries the full candidate set so the member can see the
    durable/repair/borrow alternatives even when an outer ring is chosen."""
    cands = _catalog_candidates(state.get("need_text", ""))
    by_ring = {r: [c for c in cands if c.get("ring") == r] for r in RING_ORDER}
    resolved = next((r for r in RING_ORDER if by_ring[r]), "unresolved")
    return {
        **state,
        "candidates": cands,
        "resolved_ring": resolved,
    }


def _catalog_candidates(need_text: str) -> list:
    """Query the kotoba catalog for products matching the need. R0: returns whatever
    the datalog cell holds; semantic ranking is Murakumo-only (G5) when available."""
    if datalog is None:
        return []
    rows = datalog.query(  # type: ignore[union-attr]
        "[:find ?id ?ring ?title :where [?p :product/id ?id] [?p :product/ring ?ring] [?p :product/title ?title]]"
    )
    cands = [{"productId": r[0], "ring": str(r[1]).lstrip(":"), "title": r[2]} for r in rows]
    if llm is not None and need_text:
        # semantic re-rank within ring (Murakumo-only; no external LLM, G5)
        cands = _llm_rerank(need_text, cands)
    return cands


def _llm_rerank(need_text: str, cands: list) -> list:
    try:
        order = llm.infer(  # type: ignore[union-attr]
            model="gemma3:4b",
            prompt=f"Rank these products for the need '{need_text}' by genuine fit "
            f"(sufficiency, not upsell). Return ids in order: "
            f"{[c['productId'] for c in cands]}",
        )
        rank = {pid: i for i, pid in enumerate(str(order).split())}
        cands.sort(key=lambda c: rank.get(c["productId"], len(cands)))
    except Exception:
        pass
    return cands


# --------------------------------------------------------------------------- #
# compare — Wellbecoming-axis ranking
# --------------------------------------------------------------------------- #
def handle_compare(state: dict) -> dict:
    products = state.get("products", [])
    ranked = sorted(products, key=_wellbecoming_score, reverse=True)
    return {**state, "ranked": ranked}


# --------------------------------------------------------------------------- #
# basket — landed-cost roll-up (items + shipping + tariff + tithe)
# --------------------------------------------------------------------------- #
def handle_basket(state: dict) -> dict:
    lines = state.get("lines", [])
    items = sum(int(l.get("priceMinor", 0)) * int(l.get("qty", 1)) for l in lines)
    shipping = sum(int(l.get("shippingMinor", 0)) for l in lines)
    tariff = sum(int(l.get("tariffMinor", 0)) for l in lines)
    # tithe applies only to the internal SBT↔SBT portion (G7)
    internal_items = sum(
        int(l.get("priceMinor", 0)) * int(l.get("qty", 1))
        for l in lines
        if l.get("ring") == "internal"
    )
    tithe = (internal_items * TITHE_BPS) // 10_000
    return {**state, "landedMinor": items + shipping + tariff + tithe, "titheMinor": tithe}


# --------------------------------------------------------------------------- #
# provision — checkout router (G2/G7/G11)
# --------------------------------------------------------------------------- #
def handle_provision(state: dict) -> dict:
    # abaki Anti-Monopoly Check (React mechanism)
    import json
    from pathlib import Path
    try:
        policy_path = Path(__file__).resolve().parents[3] / "abaki" / "out" / "routing-policy.json"
        if policy_path.exists():
            with open(policy_path, "r", encoding="utf-8") as f:
                policy = json.load(f)
            blocked_ids = {e["id"] for e in policy.get("blocked_entities", [])}
            supplier_did = state.get("supplierDid", "")
            supplier_name = state.get("supplierName", "")
            for blocked_id in blocked_ids:
                if blocked_id in supplier_did or blocked_id in supplier_name:
                    return {
                        **state,
                        "settlement": "proxy-gated",
                        "refused": True,
                        "reason": f"Provider blocked by abaki Anti-Monopoly policy (React mechanism). Route Around {blocked_id} activated."
                    }
    except Exception:
        pass

    ring = state.get("ring")
    if ring == "commons":
        return {**state, "settlement": "commons-none", "titheMinor": 0}
    if ring == "internal":
        # SBT↔SBT carve-out (§3): settle USDC + warifu, TitheRouter 10% auto-split (G7)
        return {**state, "settlement": "usdc-warifu", "titheMinor": state.get("titheMinor", 0)}
    if ring == "external":
        gate_ref = state.get("gateRef")
        if state.get("requestProxy"):
            # 代理-purchase (scope 3) — refused at R0 unless an explicit gate-ref is present (G2/G11)
            if not gate_ref:
                return {
                    **state,
                    "settlement": "proxy-gated",
                    "refused": True,
                    "reason": "external 代理-purchase requires Council Lv7+ amendment OR vendor arm + operator (G2/G11)",
                }
            return {**state, "settlement": "proxy-gated", "gateRef": gate_ref}
        # R0 default: self-checkout handoff — member pays externally; NO affiliate tag (G3)
        return {**state, "settlement": "self-checkout-handoff", "titheMinor": 0}
    return {**state, "settlement": "commons-none"}


# --------------------------------------------------------------------------- #
# lifecycle — end-of-life route + Wellbecoming trajectory (G13)
# --------------------------------------------------------------------------- #
def handle_lifecycle(state: dict) -> dict:
    # stamp a new as-of stage; never write a terminal "consumed" datom (G13)
    return {
        **state,
        "stage": state.get("stage", "in-use"),
        "routeActor": state.get("lifecycleRoute", "hodoki"),
    }


# =========================================================================== #
# R1 — Ring 1 internal economy (ADR-2606012100 §R1)
# =========================================================================== #

# Producing actors integrated into Ring 1 (mirrors manifest :actor/integrates).
MAKER_ACTORS = {"makura", "mitsuho", "yakushi", "tsutae", "futawa", "hikari"}

# Order as-of trajectory (G13: no terminal "consumed" state — :in-use hands to lifecycle).
ORDER_STATES = ["cart", "placed", "settle-intent", "fulfilling", "delivered", "in-use"]

# Item-class → etzhayyim logistics actor (G8: no gig labor).
_FULFILLMENT = {
    "heavy": "sarutahiko",  # Class-8 truck (motorcycles, PV, batteries)
    "road": "wadachi",      # autonomous-mobility last-mile
    "bulky": "haraedo",     # has a fleet + crew registry
}


def check_sbt_eligibility(buyer_did: str, maker_actor: str, sbt_registry: dict) -> dict:
    """§3 carve-out (G2): an internal trade is permitted ONLY between two active Adherent
    SBT holders. Returns {eligible, reason}. At R1 the registry is an attestation map
    {did → active?}; the on-chain SBT check is operator-gated (G11)."""
    if maker_actor not in MAKER_ACTORS:
        return {"eligible": False, "reason": f"{maker_actor} is not a Ring 1 producing actor"}
    if not sbt_registry.get(buyer_did, False):
        return {"eligible": False, "reason": "buyer is not an active Adherent SBT holder (§3/G2)"}
    maker_did = f"did:web:etzhayyim.com:{maker_actor}"
    if not sbt_registry.get(maker_did, False):
        return {"eligible": False, "reason": f"maker {maker_actor} SBT not active (§3/G2)"}
    return {"eligible": True, "reason": "both parties active Adherent SBT (SBT↔SBT carve-out)"}


def build_settlement_intent(gross_minor: int, maker_actor: str, operator_ref: str | None = None) -> dict:
    """USDC settlement with TitheRouter 10% auto-split (G7). Produces an INTENT only —
    it is NOT broadcast on-chain at R1 (G11): broadcast requires operator_ref. The
    arithmetic is the canonical contract: gross = tithe + maker_payout (no remainder loss)."""
    gross = int(gross_minor)
    tithe = (gross * TITHE_BPS) // 10_000
    payout = gross - tithe  # tithe rounds down ⇒ payout absorbs the remainder; sum is exact
    return {
        "rail": "usdc-base-l2",
        "grossMinor": gross,
        "titheMinor": tithe,
        "makerPayoutMinor": payout,
        "titheRouter": "50-infra/etzhayyim-tithe-router",
        "makerActor": maker_actor,
        "state": "executed" if operator_ref else "intent",
        "operatorRef": operator_ref,
    }


def build_user_op(intent: dict, member_did: str) -> dict:
    """Construct an UNSIGNED ERC-4337 userOp from a settlement intent (R1 live-rail wiring).
    no-server-key invariant: the required signer is the MEMBER's smart account; okaimono holds
    no key and signs nothing. The TitheRouter 10% split rides along unchanged (G7). This models
    the userOp envelope, not a live bundler submission (that is operator-gated, G11)."""
    return {
        "rail": "erc4337-user-op",
        "sender": member_did,
        "grossMinor": intent["grossMinor"],
        "titheMinor": intent["titheMinor"],
        "makerPayoutMinor": intent["makerPayoutMinor"],
        "titheRouter": intent["titheRouter"],
        "requiredSigner": "member-smart-account",
        "serverHeldKey": False,           # invariant — okaimono never holds a key
        "signed": False,
    }


def submit_settlement(intent: dict, member_signature: dict,
                      operator_ref: str | None = None) -> dict:
    """Broadcast a USDC+Tithe settlement on the live rail. ONLY a member-origin signature
    authorizes it (G15 no-server-key); a platform/server signature is refused outright. The
    live bundler submit additionally needs an operator (G11): with a member signature but no
    operator the userOp is :authorized-pending-operator (signed, not yet broadcast). The
    TitheRouter 10% split is preserved (G7); a non-:intent state is refused (idempotency)."""
    if intent.get("state") not in ("intent", None):
        return {**intent, "refused": True,
                "reason": f"settlement not in :intent state ({intent.get('state')})"}
    if member_signature.get("origin") != "member":
        return {**intent, "refused": True,
                "reason": "only a member smart-account signature can authorize (G15 no-server-key)"}
    user_op = build_user_op(intent, member_signature.get("memberDid", ""))
    user_op["signed"] = True
    user_op["signatureRef"] = member_signature.get("ref")
    if not operator_ref:
        return {**intent, "state": "authorized-pending-operator", "userOp": user_op}
    return {**intent, "state": "submitted", "userOp": user_op, "operatorRef": operator_ref}


def assign_fulfillment(item_class: str) -> str:
    """Route fulfillment to an etzhayyim logistics actor; never a gig courier (G8)."""
    return _FULFILLMENT.get(item_class, "wadachi")


def place_order(buyer_did: str, maker_actor: str, gross_minor: int,
                item_class: str, sbt_registry: dict) -> dict:
    """Ring 1 order entry. Enforces internal-only + SBT↔SBT eligibility (G2) before
    computing a settlement intent (G7) and a fulfillment assignment (G8). Refused
    orders carry the reason and never reach :settle-intent."""
    elig = check_sbt_eligibility(buyer_did, maker_actor, sbt_registry)
    if not elig["eligible"]:
        return {"state": "refused", "reason": elig["reason"], "ring": "internal"}
    settlement = build_settlement_intent(gross_minor, maker_actor)
    return {
        "state": "settle-intent",
        "ring": "internal",
        "buyerDid": buyer_did,
        "makerActor": maker_actor,
        "settlement": settlement,
        "fulfillmentActor": assign_fulfillment(item_class),
    }


def advance_order(order: dict) -> dict:
    """Move an order one step along ORDER_STATES (G13: caps at :in-use, never :consumed)."""
    st = order.get("state")
    if st not in ORDER_STATES:
        return order
    i = ORDER_STATES.index(st)
    return {**order, "state": ORDER_STATES[min(i + 1, len(ORDER_STATES) - 1)]}


# =========================================================================== #
# R2 — Ring 2 external world catalog (ADR-2606012100 §R2)
# =========================================================================== #
# The constitutional crux of Ring 2 is G3 (no ads / no affiliate): external product
# APIs are DATA-ONLY, affiliate + tracking parameters are stripped, zero commission,
# and the §1.3 value-inflow boundary means R0 ships only a *self-checkout handoff*
# (member pays the retailer directly); 代理-purchase stays R3-gated.

# Affiliate / tracking query-parameter denylist (case-insensitive, exact names).
_AFFILIATE_PARAMS = frozenset({
    # generic affiliate
    "aff", "affid", "aff_id", "affiliate", "affiliate_id", "partner", "partner_id",
    "pid", "click_id", "clickid", "cjevent", "irclickid", "irgwc",
    "ranmid", "raneaid", "ransiteid", "siteid", "subid", "sub_id",
    # Amazon Associates
    "tag", "ascsubtag", "linkcode", "linkid", "creativeasin", "camp", "creative",
    "smid", "psc",
    # Rakuten / Yahoo / others
    "scid", "sc2id", "rafcid", "icm_cid", "icm_acid",
    # ad / analytics tracking
    "gclid", "fbclid", "msclkid", "dclid", "yclid", "twclid", "ttclid",
    "mc_cid", "mc_eid", "ref", "ref_", "referrer", "_branch_match_id",
})
# Any param whose lowercase name starts with one of these prefixes is also stripped.
_AFFILIATE_PREFIXES = ("utm_", "aff_", "pk_", "_hs", "spm")
# External catalog data sources (G10 honesty: provenance per product).
_EXTERNAL_SOURCES = {"open-standard", "vendor-direct", "api-data-only", "scraped"}


def strip_affiliate(url: str) -> str:
    """Remove affiliate + tracking parameters from a retailer URL (G3). Functional
    params (product id, sku, gtin, node, q, …) are preserved; order is kept stable.
    Also drops Amazon-style `/ref=...` path segments. This is the single enforcement
    point that guarantees okaimono earns NO commission and plants NO tracker."""
    parts = urlsplit(url)
    kept = [
        (k, v) for (k, v) in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in _AFFILIATE_PARAMS
        and not any(k.lower().startswith(p) for p in _AFFILIATE_PREFIXES)
    ]
    # strip Amazon `/ref=...` path segment (affiliate/cross-link tag in the path)
    path = "/".join(seg for seg in parts.path.split("/") if not seg.startswith("ref="))
    if parts.path.endswith("/") and not path.endswith("/"):
        path += "/"
    return urlunsplit((parts.scheme, parts.netloc, path, urlencode(kept), ""))


def normalize_external(raw: dict, source: str) -> dict:
    """Map a raw external product record to an okaimono `:product/* :ring :external`
    entry, DATA-ONLY: only price / availability / spec / provenance fields are kept;
    any affiliate-link, commission, or sponsored-rank field in `raw` is dropped (G3).
    Source provenance is recorded and `:sourcing` is :representative (G10 honesty)."""
    if source not in _EXTERNAL_SOURCES:
        raise ValueError(f"unknown external source {source!r}")
    retailer_url = raw.get("url") or raw.get("retailerUrl") or ""
    return {
        "productId": f"ext.{raw.get('gtin') or raw.get('id') or 'unknown'}",
        "title": raw.get("title", ""),
        "ring": "external",
        "source": source,
        "gtin": raw.get("gtin"),
        "unspsc": raw.get("unspsc"),
        "retailerUrl": strip_affiliate(retailer_url) if retailer_url else "",
        "priceMinor": int(raw.get("priceMinor", 0)),
        "currency": raw.get("currency", "USD"),
        "availability": raw.get("availability", "unknown"),
        "durabilityYears": float(raw.get("durabilityYears", 0.0)),
        "repairability": int(raw.get("repairability", 0)),
        "laborProvenance": raw.get("laborProvenance", "unknown"),
        "carbonKg": float(raw.get("carbonKg", 0.0)),
        "lifecycleRoute": raw.get("lifecycleRoute", "haraedo"),
        "sourcing": "representative",
        # explicitly NOT carried over: affiliateLink / commissionBps / sponsoredRank / trackingPixel
    }


def build_external_handoff(product: dict) -> dict:
    """Ring 2 R0 checkout: a self-checkout handoff (member pays the retailer directly).
    The deep-link is affiliate-stripped (G3); no tithe (external, no internal value flow,
    G2/G7); 代理-purchase is NOT offered here (R3-gated)."""
    return {
        "ring": "external",
        "settlement": "self-checkout-handoff",
        "handoffUri": strip_affiliate(product.get("retailerUrl", "")),
        "titheMinor": 0,
    }


def scrape_gate(url: str, robots_disallow: list, rate_state: dict,
                operator_ref: str | None = None) -> dict:
    """G10 catalog-sourcing legality gate for the scraping source. Checks robots.txt
    disallow + public-only + a simple per-host rate budget. Even when policy-ALLOWED,
    the actual fetch is G11-gated: without an operator_ref the verdict is :gated
    (compute the plan, do not fetch). Returns {allowed, verdict, reason}."""
    host = urlsplit(url).netloc
    path = urlsplit(url).path or "/"
    if any(path.startswith(rule) for rule in robots_disallow):
        return {"allowed": False, "verdict": "denied", "reason": f"robots.txt disallows {path}"}
    used = int(rate_state.get(host, 0))
    if used >= int(rate_state.get("_limit", 30)):
        return {"allowed": False, "verdict": "denied", "reason": f"rate budget exhausted for {host}"}
    if not operator_ref:
        # policy-clean but outward fetch needs Council/operator (G11)
        return {"allowed": True, "verdict": "gated", "reason": "robots-ok; live fetch is operator-gated (G11)"}
    return {"allowed": True, "verdict": "fetch", "reason": "robots-ok + operator authorized"}


def landed_cost_external(price_minor: int, shipping_minor: int, tariff_bps: int) -> dict:
    """Cross-border landed cost for an external product: price + shipping + tariff.
    tariff_bps applies to the goods price (not shipping). No tithe (external, G2/G7)."""
    price = int(price_minor)
    tariff = (price * int(tariff_bps)) // 10_000
    return {
        "priceMinor": price,
        "shippingMinor": int(shipping_minor),
        "tariffMinor": tariff,
        "landedMinor": price + int(shipping_minor) + tariff,
    }


# =========================================================================== #
# R3 — Assisted secure checkout, MEMBER-PRINCIPAL (ADR-2606012100 §R3)
# =========================================================================== #
# Corrects the earlier "代理-purchase" framing of scope-3. okaimono does NOT become
# the buyer. The MEMBER remains the purchasing principal and pays the external retailer
# with their OWN instrument; okaimono only provides a secure rail — safe card entry,
# encrypted transport, procedure assist, delivery. Because value flows member→retailer
# (never INTO etzhayyim), §1.3 is preserved and NO Lv7+ amendment is required. The binding
# gates are: G14 member-principal (no inflow), G15 no-server-key (member signs each
# payment), G9 encryption, G11 outward-operator for live action.

PAYMENT_INSTRUMENTS = {"member-external-card", "warifu"}


def seal_encrypted(fields: dict, recipient_did: str) -> dict:
    """Wrap card / PII fields into an com.etzhayyim.encrypted.* envelope (G9). Returns ONLY
    an opaque envelope ref + recipient — never the plaintext. The plaintext is assumed to be
    sealed client-side (XChaCha20-Poly1305, Signal-wrapped, DID-bound, ADR-2605181100); this
    function models the contract: no cleartext PII crosses the okaimono boundary."""
    # deterministic opaque ref from field keys only (NOT values) — values never leave plaintext
    keysig = "+".join(sorted(fields.keys()))
    ref = f"com.etzhayyim.encrypted:{abs(hash(keysig)) & 0xFFFFFFFF:08x}"
    return {"envelopeRef": ref, "recipientDid": recipient_did, "sealedFields": sorted(fields.keys())}


def build_payment_intent(member_did: str, retailer: str, amount_minor: int,
                         currency: str, instrument: str, external: bool = True) -> dict:
    """Construct an UNSIGNED payment intent that ONLY the member can authorize (G15 no-server-key).
    okaimono never holds the card secret or a signing key; it returns an intent whose required
    signer is the member's own passkey/smart-account. ERC-4337 user-op for on-chain rails.
    warifu used at an EXTERNAL retailer additionally trips warifu's own Phase-2 Lv7+ gate
    (ADR-2605302000) — flagged, not silently allowed."""
    if instrument not in PAYMENT_INSTRUMENTS:
        raise ValueError(f"unknown instrument {instrument!r}")
    intent = {
        "memberDid": member_did,
        "retailer": retailer,
        "amountMinor": int(amount_minor),
        "currency": currency,
        "instrument": instrument,
        "rail": "erc4337-user-op" if instrument == "warifu" else "member-card-direct",
        "principal": "member",        # G14: the buyer is the member, NOT okaimono
        "serverHeldKey": False,        # G15: invariant — okaimono holds no key/secret
        "requiredSigner": "member-passkey-or-smart-account",
        "signed": False,               # must be authorized by the member before it is live
    }
    if instrument == "warifu" and external:
        intent["requiresWarifuExternalGate"] = True  # warifu Phase-2 Lv7+ (ADR-2605302000)
    return intent


def authorize_payment(intent: dict, signature: dict) -> dict:
    """Authorize a payment intent. ONLY a member-origin signature is accepted (G15);
    a platform/server signature is refused outright. Does not itself broadcast (G11)."""
    if signature.get("origin") != "member":
        return {**intent, "signed": False, "refused": True,
                "reason": "only a member passkey/wallet signature can authorize (G15 no-server-key)"}
    if intent.get("serverHeldKey"):
        return {**intent, "signed": False, "refused": True,
                "reason": "intent carries a server-held key — invariant violation (G15)"}
    return {**intent, "signed": True, "signatureRef": signature.get("ref")}


def assist_checkout(member_did: str, product: dict, profile_fields: dict,
                    member_signature: dict | None = None, operator_ref: str | None = None) -> dict:
    """Orchestrate a member-principal assisted external checkout: seal PII (G9), fill the
    retailer procedure from the member's consented profile, build a member-signable payment
    intent (G14/G15), and arrange delivery — but SUBMIT only with the member's per-transaction
    authorization AND an operator for the live outward action (G11). Without the member
    signature it returns :awaiting-member-authorization and submits nothing."""
    envelope = seal_encrypted(profile_fields, member_did)
    amount = int(product.get("priceMinor", 0))
    instrument = product.get("instrument", "member-external-card")
    intent = build_payment_intent(member_did, product.get("retailer", ""), amount,
                                  product.get("currency", "USD"), instrument)
    handoff = build_external_handoff(product)  # affiliate-stripped target (G3)
    base = {
        "ring": "external",
        "mode": "assisted-secure-checkout",
        "principal": "member",         # §1.3 preserved: okaimono is not the buyer (G14)
        "encrypted": envelope,
        "handoffUri": handoff["handoffUri"],
        "paymentIntent": intent,
        "titheMinor": 0,               # external: no internal value flow (G2/G7)
    }
    if member_signature is None:
        return {**base, "state": "awaiting-member-authorization"}
    authed = authorize_payment(intent, member_signature)
    if authed.get("refused"):
        return {**base, "state": "refused", "reason": authed["reason"]}
    if not operator_ref:
        # member-authorized, but the live outward submit needs an operator (G11)
        return {**base, "state": "authorized-pending-operator", "paymentIntent": authed}
    return {**base, "state": "submitted", "paymentIntent": authed, "operatorRef": operator_ref}


def arrange_delivery(product: dict, region: str) -> dict:
    """Choose a delivery path: prefer an etzhayyim logistics actor (no gig, G8) for last-mile
    where serviceable, else fall back to the retailer's own shipping. Hands to lifecycle (G13)."""
    serviceable = region in {"jp", "shibuya"}  # representative: where etzhayyim logistics runs
    if serviceable:
        carrier = assign_fulfillment(product.get("itemClass", "road"))
        mode = "etzhayyim-logistics"
    else:
        carrier = "retailer-ship"
        mode = "retailer-shipping"
    return {
        "carrier": carrier,
        "mode": mode,
        "gig": False,                  # G8: never gig labor on the etzhayyim leg
        "lifecycleRoute": product.get("lifecycleRoute", "haraedo"),
    }
