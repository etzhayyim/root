"""analyze.py — 助 (tasuke) end-to-end membrane over the :representative victim cases.

Runs each seed case through the full free support pipeline:
    intake → triage (scam-kind + severity + free windows + action checklist)
           → generate member-authored documents (被害届 / 被害状況報告書 / 証拠目録 /
             被害額算定書 / 銀行組戻し依頼 / プラットフォーム依頼 / 復旧手順)
           → assert every document is FREE, member-authored, signature-required, draft-only

and emits an offline scorecard (Markdown). NO live filing / submission / send — all of that is
G9 (Council Lv6+ + operator). This is a dry-run demonstration that the whole journey costs ¥0.
"""

from __future__ import annotations

import pathlib

import report_gen as rg
from _edn import load_edn
from triage import _WINDOWS  # noqa: F401  (kept for parity; windows come via triage())
from triage import triage

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SEED = _ROOT / "data" / "seed-cybercrime-cases.kotoba.edn"
_OUT = _ROOT / "methods" / "out"

# a tiny encrypted-evidence stand-in (G6 — ref + hash only, never plaintext)
_DEMO_EVIDENCE = [
    {":evidence/id": "ev1", ":evidence/kind": ":screenshot",
     ":evidence/envelope-ref": "ipfs://bafyEVIDENCE1", ":evidence/bytes": "screenshot-bytes",
     ":evidence/captured-at": 1717500100},
    {":evidence/id": "ev2", ":evidence/kind": ":transaction-record",
     ":evidence/envelope-ref": "ipfs://bafyEVIDENCE2", ":evidence/bytes": "tx-record-bytes",
     ":evidence/captured-at": 1717500200},
]


def _docs_for(case: dict, kind: str) -> list[dict]:
    """Pick the document set that fits the scam KIND — always police core + kind-specific extras."""
    cid = case.get(":case/id")
    ev = [{**e, ":evidence/case": cid} for e in _DEMO_EVIDENCE]
    docs = [
        rg.damage_report(case),
        rg.incident_statement(case),
        rg.evidence_index_doc(case, ev),
        rg.damage_calculation(case),
    ]
    if kind == "unauthorized-transfer":
        docs.append(rg.bank_freeze_request(case))
    if kind in ("account-takeover", "impersonation", "sns-fraud", "phishing"):
        docs.append(rg.platform_request(case, purpose="凍結・復旧"))
    if kind in ("account-takeover", "phishing"):
        docs.append(rg.recovery_plan(case, service="（対象サービス）"))
    return docs


def run(seed_path: pathlib.Path = _SEED) -> dict:
    seed = load_edn(seed_path)
    rows = []
    for case in seed[":case/batch"]:
        tri = triage(case)                       # raises if not free / not consented (G1/G7)
        kind = tri[":triage/scam-kind"].lstrip(":")
        docs = _docs_for(case, kind)
        for d in docs:
            rg.assert_member_authored(d)         # G1/G2/G3/G9 guard on every generated doc
        rows.append({
            "case": case.get(":case/id"),
            "kind": kind,
            "severity": tri[":triage/severity"].lstrip(":"),
            "cost": tri[":triage/support-cost-jpy"],
            "windows": [w.lstrip(":") for w in tri[":triage/windows"]],
            "docs": [d[":doc/kind"].lstrip(":") for d in docs],
            "actions": tri[":triage/actions"],
            "deadlines": tri[":triage/deadlines"],
            "paid_referral": tri[":triage/paid-referral"],
        })
    total_cost = sum(r["cost"] for r in rows)
    return {"rows": rows, "total_cost": total_cost}


def _report(res: dict) -> str:
    out = ["# 助 (tasuke) — free cybercrime-victim-support membrane dry-run\n",
           "End-to-end pipeline over the `:representative` victim cases. No live filing / send "
           "(G9). Every case costs the victim **¥0** (G1), every document is **member-authored** "
           "(G3) and **awaits the member's signature** (G2).\n",
           "## Cases\n",
           "| case | scam-kind | severity | victim cost | generated documents | free windows |",
           "|---|---|---|---|---|---|"]
    for r in res["rows"]:
        out.append(f"| {r['case']} | {r['kind']} | {r['severity']} | ¥{r['cost']} | "
                   f"{', '.join(r['docs'])} | {', '.join(r['windows'])} |")
    out.append(f"\n**Total victim cost across all cases: ¥{res['total_cost']} "
               f"({'FREE — G1 holds' if res['total_cost'] == 0 else 'NON-ZERO — G1 VIOLATED'}).**\n")
    out.append("## First-response checklist (sample — first case)\n")
    if res["rows"]:
        for a in res["rows"][0]["actions"]:
            out.append(f"- {a}")
        if res["rows"][0]["deadlines"]:
            out.append("\n**期限の注意:**")
            for d in res["rows"][0]["deadlines"]:
                out.append(f"- ⏰ {d}")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    res = run()
    report = _report(res)
    _OUT.mkdir(parents=True, exist_ok=True)
    (_OUT / "support-dryrun.md").write_text(report, encoding="utf-8")
    print(report)
    assert res["total_cost"] == 0, "G1 全て無料 violated"
