#!/usr/bin/env python3
"""kanjō 勘定 — canonical concept dictionary (the GAAP-normalization layer).

The single source of truth that maps a SOURCE XBRL taxonomy element (EDINET
jppfs_cor / jpcrp_cor · US-GAAP us-gaap:* · IFRS ifrs-full:*) onto a kanjō
CANONICAL concept keyword (:revenue, :operating-income, …) so that JP-GAAP,
US-GAAP and IFRS filings land in one comparable EAVT vocabulary.

This is the G5 :synthesized normalization layer — it is honest about where two
standards are NOT comparable (e.g. 経常利益 / ordinary-income is JGAAP-only).

Run directly to emit the `:fin.concept/*` dictionary datoms:

    python3 methods/concept_map.py            # → out/concept-dictionary.kotoba.edn

Used by ingest.py (element → canonical) and analyze.py (which concepts feed which metric).
ADR-2606032000.
"""
from __future__ import annotations
import os

# ── canonical concept catalogue ──────────────────────────────────────────────
# Each entry: canonical-keyword -> (statement, label, jgaap[], usgaap[], ifrs[], note)
# `jgaap` lists EDINET taxonomy element local-names (namespace prefix stripped/kept
# as published); first match wins at ingest. Lists are ordered most-specific first.
CONCEPTS = {
    # ── PL — 損益計算書 / income statement ──
    "revenue": (
        ":pl", "Revenue / 売上高",
        ["NetSales", "OperatingRevenue1", "Revenue", "NetSalesSummaryOfBusinessResults"],
        ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"],
        ["Revenue"],
        "",
    ),
    "gross-profit": (
        ":pl", "Gross profit / 売上総利益",
        ["GrossProfit"],
        ["GrossProfit"],
        ["GrossProfit"],
        "",
    ),
    "operating-income": (
        ":pl", "Operating income / 営業利益",
        ["OperatingIncome", "OperatingProfitLoss"],
        ["OperatingIncomeLoss"],
        ["ProfitLossFromOperatingActivities"],
        "",
    ),
    "ordinary-income": (
        ":pl", "Ordinary income / 経常利益",
        ["OrdinaryIncome", "OrdinaryProfitLoss"],
        [],
        [],
        "JGAAP-only. No US-GAAP / IFRS equivalent — do NOT cross-compare across standards.",
    ),
    "pretax-income": (
        ":pl", "Pre-tax income / 税引前当期純利益",
        ["IncomeBeforeIncomeTaxes", "ProfitLossBeforeTax"],
        ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"],
        ["ProfitLossBeforeTax"],
        "",
    ),
    "net-income": (
        ":pl", "Net income attributable to owners of parent / 親会社株主に帰属する当期純利益",
        ["ProfitLossAttributableToOwnersOfParent", "ProfitLoss", "NetIncome"],
        ["NetIncomeLoss"],
        ["ProfitLossAttributableToOwnersOfParent", "ProfitLoss"],
        "",
    ),
    # ── BS — 貸借対照表 / balance sheet (instant at period end) ──
    "total-assets": (
        ":bs", "Total assets / 資産合計",
        ["Assets"],
        ["Assets"],
        ["Assets"],
        "",
    ),
    "current-assets": (
        ":bs", "Current assets / 流動資産",
        ["CurrentAssets"],
        ["AssetsCurrent"],
        ["CurrentAssets"],
        "",
    ),
    "total-liabilities": (
        ":bs", "Total liabilities / 負債合計",
        ["Liabilities"],
        ["Liabilities"],
        ["Liabilities"],
        "",
    ),
    "current-liabilities": (
        ":bs", "Current liabilities / 流動負債",
        ["CurrentLiabilities"],
        ["LiabilitiesCurrent"],
        ["CurrentLiabilities"],
        "",
    ),
    "total-equity": (
        ":bs", "Total equity / net assets / 純資産",
        ["NetAssets", "EquityAttributableToOwnersOfParent"],
        ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
        ["Equity", "EquityAttributableToOwnersOfParent"],
        "JGAAP 純資産 (NetAssets) includes non-controlling interests; equity-ratio here uses it as-published.",
    ),
    "cash-and-equivalents": (
        ":bs", "Cash and cash equivalents / 現金及び現金同等物",
        ["CashAndDeposits", "CashAndCashEquivalents"],
        ["CashAndCashEquivalentsAtCarryingValue"],
        ["CashAndCashEquivalents"],
        "",
    ),
    # ── CF — キャッシュフロー計算書 / cash-flow statement (flow over period) ──
    "cfo": (
        ":cf", "Operating cash flow / 営業活動によるCF",
        ["NetCashProvidedByUsedInOperatingActivities"],
        ["NetCashProvidedByUsedInOperatingActivities"],
        ["CashFlowsFromUsedInOperatingActivities"],
        "",
    ),
    "cfi": (
        ":cf", "Investing cash flow / 投資活動によるCF",
        ["NetCashProvidedByUsedInInvestmentActivities", "NetCashProvidedByUsedInInvestingActivities"],
        ["NetCashProvidedByUsedInInvestingActivities"],
        ["CashFlowsFromUsedInInvestingActivities"],
        "",
    ),
    "cff": (
        ":cf", "Financing cash flow / 財務活動によるCF",
        ["NetCashProvidedByUsedInFinancingActivities"],
        ["NetCashProvidedByUsedInFinancingActivities"],
        ["CashFlowsFromUsedInFinancingActivities"],
        "",
    ),
    "capex": (
        ":cf", "Capital expenditure / 設備投資 (有形固定資産の取得)",
        ["PurchaseOfPropertyPlantAndEquipment"],
        ["PaymentsToAcquirePropertyPlantAndEquipment"],
        ["PurchaseOfPropertyPlantAndEquipment"],
        "Sign as-published (a cash OUTFLOW; typically negative in the CF statement).",
    ),
    # ── per-share / 諸数値 ──
    "eps": (
        ":eps", "Basic earnings per share / 1株当たり当期純利益",
        ["BasicEarningsLossPerShare", "BasicEarningsPerShare"],
        ["EarningsPerShareBasic"],
        ["BasicEarningsLossPerShare"],
        "",
    ),
}

# reverse index: source element local-name -> canonical keyword (per standard)
def _index():
    idx = {"jgaap": {}, "usgaap": {}, "ifrs": {}}
    for canon, (_stmt, _label, jg, us, ifrs, _note) in CONCEPTS.items():
        for e in jg:
            idx["jgaap"].setdefault(e, canon)
        for e in us:
            idx["usgaap"].setdefault(e, canon)
        for e in ifrs:
            idx["ifrs"].setdefault(e, canon)
    return idx

_IDX = _index()


def canonical(element: str, standard: str) -> str | None:
    """Map a source taxonomy element (local-name, prefix optional) onto a
    canonical concept keyword (without the leading ':'), or None if unmapped.

    standard ∈ {"jgaap","usgaap","ifrs"}. Accepts "us-gaap:Revenues",
    "jppfs_cor:NetSales", "ifrs-full:Revenue" or bare "NetSales".
    """
    local = element.split(":")[-1]
    return _IDX.get(standard, {}).get(local)


def metric_inputs():
    """Which canonical concepts each derived :fin.metric depends on (used by analyze.py)."""
    return {
        "operating-margin": ("operating-income", "revenue"),
        "net-margin": ("net-income", "revenue"),
        "gross-margin": ("gross-profit", "revenue"),
        "roe": ("net-income", "total-equity"),
        "roa": ("net-income", "total-assets"),
        "equity-ratio": ("total-equity", "total-assets"),
        "current-ratio": ("current-assets", "current-liabilities"),
    }


def _edn():
    lines = [
        ";; kanjō 勘定 — canonical concept dictionary (GAAP-normalization map)",
        ";; GENERATED by methods/concept_map.py — ADR-2606032000. :synthesized normalization layer (G5).",
        ";; vocabulary: corporate-financials-ontology.kotoba.edn (:fin.concept/*)",
        "[",
    ]
    for canon, (stmt, label, jg, us, ifrs, note) in CONCEPTS.items():
        parts = [
            f':fin.concept/id :{canon}',
            f':fin.concept/statement {stmt}',
            f':fin.concept/label {_s(label)}',
            f':fin.concept/jgaap {_s(",".join(jg))}',
            f':fin.concept/usgaap {_s(",".join(us))}',
            f':fin.concept/ifrs {_s(",".join(ifrs))}',
        ]
        if note:
            parts.append(f':fin.concept/note {_s(note)}')
        lines.append(" {" + " ".join(parts) + "}")
    lines.append("]")
    return "\n".join(lines) + "\n"


def _s(x: str) -> str:
    return '"' + x.replace("\\", "\\\\").replace('"', '\\"') + '"'


if __name__ == "__main__":
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outdir = os.path.join(here, "out")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "concept-dictionary.kotoba.edn")
    with open(path, "w") as f:
        f.write(_edn())
    print(f"wrote {len(CONCEPTS)} canonical concepts → {path}")
    # tiny self-check
    assert canonical("jppfs_cor:NetSales", "jgaap") == "revenue"
    assert canonical("us-gaap:NetIncomeLoss", "usgaap") == "net-income"
    assert canonical("ifrs-full:Assets", "ifrs") == "total-assets"
    assert canonical("OrdinaryIncome", "usgaap") is None  # JGAAP-only, correctly unmapped
    print("concept_map self-check ok")
