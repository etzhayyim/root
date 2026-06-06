"""book.py — 扶持 (fuchi) R1(c): toritate booking + kanae-renderable flow viz.

Per ADR-2606052300 R1. Two cross-actor projections of an accepted allocation:

1. **toritate booking** (`book_toritate`) — projects each IN-KIND rail into a toritate
   `ledgerEntry` using **toritate's own category enum** (ADR-2605262900):
       housing/food/energy → subsistence-flow   (L2/L3)
       compute/tooling     → vocation-flow       (L5 internal vocation)
       care                → care-flow           (L4)
   `cashStipendUsd ≡ 0` (toritate N1); `:payroll`/`:salary`/`:wage` are unrepresentable there
   and here. The **member-principal liquidity rail is NOT booked as income** — it is the
   member's own warifu 0% loan, not a Public-Fund disbursement (honest accounting).

2. **kanae-renderable flow graph** (`flow_graph`) — emits a Sankey-ready internal sustenance
   flow: Public Fund → 扶持 → each provider → the maintainer. This is a fuchi-internal
   `:flow/*` graph for kanae's viz layer, NOT the government `:fundFlowEdge` (which is for
   external fiscal flows and carries mandatory non-adjudication fields). The liquidity leg is
   flagged `in_kind = False` (member-principal); every other leg is in kind.

Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass

# rail kind → toritate ledgerEntry category (toritate's own enum, ADR-2605262900).
# liquidity-warifu is intentionally ABSENT — it is not a Public-Fund disbursement.
RAIL_TO_CATEGORY: dict[str, str] = {
    "housing-commons":  "subsistence-flow",
    "food-mitsuho":     "subsistence-flow",
    "energy-hikari":    "subsistence-flow",
    "compute-murakumo": "vocation-flow",
    "tooling-okaimono": "vocation-flow",
    "care-iyashi":      "care-flow",
}
TORITATE_CATEGORIES = ("subsistence-flow", "vocation-flow", "care-flow", "liberation-flow", "grant")
# Never valid (toritate enforces this too) — defensive.
FORBIDDEN_CATEGORIES = ("payroll", "salary", "wage", "bonus", "commission")

PUBLIC_FUND = "did:web:etzhayyim.com:actor:etzhayyim-public-fund"
FUCHI = "did:web:etzhayyim.com:actor:fuchi"


@dataclass(frozen=True)
class LedgerEntry:
    alloc_id: str
    category: str                 # toritate ledgerEntry category
    imputed_usd_micros_yr: int
    counterparty_did: str
    cash_usd_micros: int = 0      # toritate cashStipendUsd ≡ 0

    def __post_init__(self) -> None:
        if self.cash_usd_micros != 0:
            raise ValueError("cash≡0 INVARIANT (G2): toritate cashStipendUsd ≡ 0")
        if self.category in FORBIDDEN_CATEGORIES:
            raise ValueError(f"category {self.category!r} unrepresentable (no payroll/wage)")
        if self.category not in TORITATE_CATEGORIES:
            raise ValueError(f"category {self.category!r} not a toritate ledgerEntry category")


@dataclass(frozen=True)
class FlowEdge:
    frm: str
    to: str
    flow_class: str               # publicfund-to-fuchi | fuchi-to-provider | provider-to-maintainer
    imputed_usd_micros_yr: int
    in_kind: bool = True


def _rail_fields(r):
    kind = getattr(r, "kind", None) or r.get("kind")
    imputed = getattr(r, "imputed_usd_micros_yr", None)
    if imputed is None:
        imputed = r.get("imputedUsdMicrosYr", r.get("imputed_usd_micros_yr", 0))
    member_principal = getattr(r, "member_principal", None)
    if member_principal is None:
        member_principal = bool(r.get("memberPrincipal", r.get("member_principal", False)))
    provider = getattr(r, "provider_actor", None) or r.get("providerActor", r.get("provider_actor", kind))
    return kind, int(imputed), bool(member_principal), provider


def book_toritate(rails: list, alloc_id: str, maintainer_did: str) -> list[LedgerEntry]:
    """Project in-kind rails into toritate ledgerEntry records. Skips the member-principal
    liquidity rail (not a Public-Fund disbursement)."""
    out: list[LedgerEntry] = []
    for r in rails:
        kind, imputed, member_principal, _provider = _rail_fields(r)
        if member_principal or kind not in RAIL_TO_CATEGORY:
            continue  # liquidity-warifu (member loan) is not booked as fuchi income
        out.append(LedgerEntry(
            alloc_id=alloc_id,
            category=RAIL_TO_CATEGORY[kind],
            imputed_usd_micros_yr=imputed,
            counterparty_did=maintainer_did,
        ))
    return out


def flow_graph(rails: list, alloc_id: str, maintainer_did: str) -> list[FlowEdge]:
    """Emit a kanae-renderable internal sustenance-flow graph for this allocation."""
    edges: list[FlowEdge] = []
    in_kind_total = 0
    legs: list[FlowEdge] = []
    for r in rails:
        kind, imputed, member_principal, provider = _rail_fields(r)
        in_kind = not member_principal
        if in_kind:
            in_kind_total += imputed
        legs.append(FlowEdge(FUCHI, provider, "fuchi-to-provider", imputed, in_kind))
        legs.append(FlowEdge(provider, maintainer_did, "provider-to-maintainer", imputed, in_kind))
    # the funding leg only covers the in-kind value (liquidity is a member loan, not funded here)
    if in_kind_total > 0:
        edges.append(FlowEdge(PUBLIC_FUND, FUCHI, "publicfund-to-fuchi", in_kind_total, True))
    edges.extend(legs)
    return edges
