"""provision.py — 扶持 (fuchi) R1(a): wire in-kind rails to the real producing actors.

Per ADR-2606052300 R1. Takes the routing rails (from route.py) and emits a PROVISIONING
INTENT per rail, addressed to the real producing actor / commons / infra that delivers the
sustenance IN KIND:

    housing-commons   → commons-land (LANDS.md, inalienable waqf)     [commons]
    food-mitsuho      → did:web:etzhayyim.com:actor:mitsuho           [actor]
    energy-hikari     → did:web:etzhayyim.com:actor:hikari            [actor]
    compute-murakumo  → murakumo (mesh)                               [infra]
    tooling-okaimono  → did:web:etzhayyim.com:actor:okaimono          [actor]
    care-iyashi       → did:web:etzhayyim.com:actor:iyashi            [actor]
    liquidity-warifu  → did:web:etzhayyim.com:actor:warifu            [actor, MEMBER-PRINCIPAL]

A provisioning intent is a DRY-RUN at R0/R1: `published` is structurally False (G10 — live
provisioning to the producing actors is Council Lv6+ + operator gated), cash is structurally 0
(G2), and `server_held_key` is False (G9 — the intent is member/Council-signed). The liquidity
intent is `member_principal` (the member is the borrower/payer via warifu 0% qard-ḥasan; 扶持
never holds, lends, or pays).

Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass

# rail kind → (provider id, provider kind, short label). The single map; mirrors the ontology
# :ontology/rails + :ontology/provider-kinds and route.LINE_TO_RAIL.
PROVIDER_REGISTRY: dict[str, tuple[str, str, str]] = {
    "housing-commons":  ("commons-land", "commons", "LANDS.md commons"),
    "food-mitsuho":     ("did:web:etzhayyim.com:actor:mitsuho", "actor", "mitsuho 瑞穂"),
    "energy-hikari":    ("did:web:etzhayyim.com:actor:hikari", "actor", "hikari 光"),
    "compute-murakumo": ("murakumo", "infra", "Murakumo mesh"),
    "tooling-okaimono": ("did:web:etzhayyim.com:actor:okaimono", "actor", "okaimono 御買物"),
    "care-iyashi":      ("did:web:etzhayyim.com:actor:iyashi", "actor", "iyashi 癒"),
    "liquidity-warifu": ("did:web:etzhayyim.com:actor:warifu", "actor", "warifu 割符 (0% qard-ḥasan)"),
}


@dataclass(frozen=True)
class ProvisioningIntent:
    alloc_id: str
    rail_kind: str
    provider_did: str
    provider_kind: str            # actor | commons | infra
    imputed_usd_micros_yr: int
    member_principal: bool = False
    cash_usd_micros: int = 0      # G2 — structural
    server_held_key: bool = False  # G9 — structural
    published: bool = False        # G10 — structural at R0/R1

    def __post_init__(self) -> None:
        if self.cash_usd_micros != 0:
            raise ValueError("cash≡0 INVARIANT (G2): a provisioning intent never moves cash")
        if self.server_held_key:
            raise ValueError("no-server-key INVARIANT (G9): the intent is member/Council-signed")
        if self.published:
            raise ValueError("G10: published must be false — live provisioning is Council Lv6+ + operator gated")
        if self.rail_kind not in PROVIDER_REGISTRY:
            raise ValueError(f"G3: rail kind {self.rail_kind!r} has no provider")


def provision(rails: list, alloc_id: str) -> list[ProvisioningIntent]:
    """Map routing rails → provisioning intents addressed to real producing actors.

    `rails` are route.Rail instances (or dicts with .kind/.imputed_usd_micros_yr/.member_principal).
    """
    out: list[ProvisioningIntent] = []
    for r in rails:
        kind = getattr(r, "kind", None) or r.get("kind")
        imputed = getattr(r, "imputed_usd_micros_yr", None)
        if imputed is None:
            imputed = r.get("imputedUsdMicrosYr", r.get("imputed_usd_micros_yr", 0))
        member_principal = getattr(r, "member_principal", None)
        if member_principal is None:
            member_principal = bool(r.get("memberPrincipal", r.get("member_principal", False)))
        provider_did, provider_kind, _label = PROVIDER_REGISTRY[kind]
        out.append(ProvisioningIntent(
            alloc_id=alloc_id,
            rail_kind=kind,
            provider_did=provider_did,
            provider_kind=provider_kind,
            imputed_usd_micros_yr=int(imputed),
            member_principal=bool(member_principal),
        ))
    return out
