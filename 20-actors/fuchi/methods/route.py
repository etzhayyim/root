"""route.py — 扶持 (fuchi) in-kind rail decomposition + governance gate. ADR-2606052300.

Two pure functions, both charter-clean by construction:

1. route_envelope(envelope) — decompose a maintainer's sustenance envelope into delivery
   RAILS over the EXISTING producing actors / commons. This is the honest answer to
   "real-world maintainers need to live": their needs are met IN KIND wherever possible —

       :housing   → commons land (LANDS.md, inalienable waqf)   [housing-commons]
       :food      → mitsuho 瑞穂 (agriculture)                   [food-mitsuho]
       :energy    → hikari 光 (energy)                           [energy-hikari]
       :compute   → Murakumo mesh / donated nodes                [compute-murakumo]
       :tooling   → okaimono 御買物 provisioning (Ring 1)         [tooling-okaimono]
       :care      → iyashi / hagukumi / kokoro (L4 Care)         [care-iyashi]
       :liquidity → warifu 割符 0% qard-ḥasan, MEMBER-PRINCIPAL   [liquidity-warifu]

   The irreducible EXTERNAL fiat need (a pre-existing fiat-bank rent, taxes) is routed ONLY
   as MEMBER-PRINCIPAL 0% liquidity via warifu/okaimono — the member is the borrower/payer,
   扶持 is never the creditor or the payer (§1.3 holds without a Lv7+ amendment; no-server-key).
   A :cash-disbursement rail is UNREPRESENTABLE (cash≡0).

2. gov_route(imputed_total, invariant_touch, rider) — the governance gate. A PURE FUNCTION of
   (total imputed value, whether the allocation touches an invariant, Charter-Rider hit):
       rider hit                      → :refused        (no vote can promote it)
       touches a constitutional inv.  → :council-lv7    (e.g. a new commons-land grant)
       above the optimistic ceiling   → :sbt-vote       (1 SBT = 1 vote, 48h timelock)
       else                           → :auto           (optimistic fast-path)
   扶持 computes + routes; it never DECIDES accept/reject (the vote / Council decides, 非裁定,
   the ake G2 pattern).

Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass

# G3 — envelope line → (rail kind, provider actor). The closed map (mirror of the ontology).
LINE_TO_RAIL = {
    "housing":   ("housing-commons", "commons-land"),
    "food":      ("food-mitsuho", "mitsuho"),
    "energy":    ("energy-hikari", "hikari"),
    "compute":   ("compute-murakumo", "murakumo"),
    "tooling":   ("tooling-okaimono", "okaimono"),
    "care":      ("care-iyashi", "iyashi"),
    "liquidity": ("liquidity-warifu", "warifu"),
}
IN_KIND_LINES = ("housing", "food", "energy", "compute", "tooling", "care")

# G7 — governance thresholds (imputed USD micros / yr). Tunable by Council; conservative R0.
OPTIMISTIC_CEILING_USD_MICROS_YR = 24_000_000_000   # ~$24k/yr in-kind: auto fast-path below
# Charter-Rider §2(a)-(h) hard-gate tokens (local mirror of charter_rider.scan()).
RIDER_FORBIDDEN = (
    "advertis", "affiliate", "adsense", "weapon", "munition", "fire-control",
    "surveillance", "biometric", "addictive", "dark-pattern", "広告", "兵器",
)
# Allocation contexts that touch a constitutional invariant → Council Lv7+ (never optimistic).
INVARIANT_TOUCH_TOKENS = (
    "commons-land", "land-grant", "new-land", "force", "license-change", "charter",
)


@dataclass(frozen=True)
class Rail:
    kind: str                 # G3 — one of LINE_TO_RAIL kinds
    provider_actor: str
    imputed_usd_micros_yr: int
    member_principal: bool = False   # True only for liquidity-warifu (qard ḥasan)


def _kw(v) -> str:
    return str(v or "").lstrip(":").split("/")[-1].lower()


def route_envelope(envelope: list[dict]) -> list[Rail]:
    """Decompose envelope lines → in-kind delivery rails. The liquidity line becomes a
    MEMBER-PRINCIPAL warifu rail (扶持 never pays); a :cash line is a ValueError (cash≡0)."""
    rails: list[Rail] = []
    for line in envelope:
        kind_kw = _kw(line.get(":envelope/line", ""))
        if kind_kw in ("cash", "cash-disbursement", "stipend"):
            raise ValueError("cash≡0 INVARIANT: a cash/stipend rail is UNREPRESENTABLE (扶持 never pays cash)")
        if int(line.get(":envelope/cash-usd-micros", 0)) != 0:
            raise ValueError("cash≡0 INVARIANT: :envelope/cash-usd-micros must be 0")
        if kind_kw not in LINE_TO_RAIL:
            raise ValueError(f"G3: envelope line {kind_kw!r} has no in-kind rail")
        rail_kind, provider = LINE_TO_RAIL[kind_kw]
        imputed = int(line.get(":envelope/imputed-usd-micros-yr", 0))
        rails.append(Rail(
            kind=rail_kind,
            provider_actor=provider,
            imputed_usd_micros_yr=imputed,
            member_principal=(kind_kw == "liquidity"),
        ))
    return rails


def in_kind_coverage(rails: list[Rail]) -> float:
    """Fraction of total imputed value delivered IN KIND (vs member-principal liquidity).
    The honesty metric: how much of a maintainer's sustenance never touches fiat at all."""
    total = sum(r.imputed_usd_micros_yr for r in rails)
    if total <= 0:
        return 1.0
    in_kind = sum(r.imputed_usd_micros_yr for r in rails if not r.member_principal)
    return round(in_kind / total, 4)


def rider_hit(*texts: str) -> str:
    blob = " ".join(t or "" for t in texts).lower()
    for tok in RIDER_FORBIDDEN:
        if tok in blob:
            return tok
    return ""


def touches_invariant(*texts: str) -> bool:
    blob = " ".join(t or "" for t in texts).lower()
    return any(tok in blob for tok in INVARIANT_TOUCH_TOKENS)


def gov_route(imputed_total_usd_micros_yr: int, invariant_touch: bool, rider: str) -> str:
    """G7 INVARIANT — route is a PURE FUNCTION of (imputed total, invariant touch, rider).
    扶持 never decides; this only ROUTES to the body that decides (非裁定, ake G2 pattern)."""
    if rider:
        return "refused"          # Charter-Rider §2 hit: no vote can promote it
    if invariant_touch:
        return "council-lv7"      # e.g. a new commons-land grant → Council Lv7+
    if imputed_total_usd_micros_yr > OPTIMISTIC_CEILING_USD_MICROS_YR:
        return "sbt-vote"         # above the ceiling → 1 SBT = 1 vote (48h timelock)
    return "auto"                 # optimistic fast-path
