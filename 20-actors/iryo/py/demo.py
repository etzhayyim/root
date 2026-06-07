#!/usr/bin/env python3
"""iryo 医療 — end-to-end demo: 診療録 → レセプト点数計算 → レセ電 → FHIR.

    python3 demo.py

Builds a representative outpatient encounter (初診 + 検査 + 投薬, 3割負担, 高額療養費区分ウ)
and prints the computed レセプト, the レセ電 record stream, the 件数 reconciliation, and the
FHIR Claim bundle — all PHI-free.
"""
from __future__ import annotations

import json

import agent

ENCOUNTER = {
    "futanWari": 0.3,
    "acts": [
        {"code": "111000110"},   # 初診料
        {"code": "112011010"},   # 外来管理加算
        {"code": "113002510"},   # 特定疾患療養管理料(診療所)
        {"code": "160008010"},   # 末梢血液一般
        {"code": "160019410"},   # HbA1c
        {"code": "170000110"},   # 心電図
        {"code": "120002910"},   # 処方箋料
    ],
    "prescriptions": [
        {"shikibetsu": "21", "days": 28,
         "drugs": [{"code": "620003991", "amount": 2},     # メトホルミン 2錠/日
                   {"code": "610463011", "amount": 1}]},   # アムロジピン 1錠/日
    ],
}

KARTE = {
    "patient": {"pseudonymDid": "did:web:patient.iryo.etzhayyim.com:demo01",
                "sex": "F", "birthYear": 1968},
    "insurance": {"hokenshaBango": "06270013", "futanWari": 0.3,
                  "honninKazoku": "honnin", "kogakuKubun": "ウ"},
    "diagnoses": [
        {"shobyoCode": "2500013", "icd10": "E119", "name": "2型糖尿病",
         "onset": "2024-04-01", "outcome": "継続", "isMain": True},
        {"shobyoCode": "4019005", "icd10": "I10", "name": "高血圧症",
         "onset": "2024-04-01", "outcome": "継続"},
    ],
}


def main() -> None:
    print("=" * 68)
    print("iryo 医療 — 診療録 → レセプト → レセ電 → FHIR  (representative seed)")
    print("=" * 68)

    rez = agent.handle_rezept({"encounter": ENCOUNTER})["result"]
    print("\n── レセプト点数欄 (区分集計) ──")
    for kubun, ten in rez["kubunTotals"].items():
        print(f"  {kubun:　<6} {ten:>6} 点")
    print(f"  {'合計':　<6} {rez['totalTen']:>6} 点")
    print(f"\n  総医療費(10割)   : {rez['totalIryohiYen']:>8,} 円")
    print(f"  負担割合         : {int(rez['futanWari']*10)} 割")
    print(f"  一部負担金(算定)  : {rez['ichibuFutanYen']:>8,} 円")
    if rez["kogakuApplied"]:
        print(f"  高額療養費限度額  : {rez['kogakuLimitYen']:>8,} 円 (区分{rez['kogakuKubun']})")
    print(f"  → 窓口負担       : {rez['patientPayYen']:>8,} 円")

    rec = agent.handle_receden({"encounter": ENCOUNTER, "karte": KARTE,
                                "shinryoYear": 2026, "shinryoMonth": 6})
    print("\n── レセ電 (レセプト電算処理) レコード ──")
    print(rec["csv"].rstrip())
    print(f"\n  件数: {rec['summary']}   状態: {rec['state']} (G3 no-server-key)")

    val = agent.handle_validate({"encounter": ENCOUNTER, "karte": KARTE})
    print("\n── 算定整合性チェック (G5 non-adjudicating) ──")
    print(f"  ok={val['ok']}  observations={val['observations'] or 'なし'}")

    fhir = agent.export_fhir({"encounter": ENCOUNTER, "karte": KARTE})["bundle"]
    print("\n── FHIR R4 Claim Bundle (codes-only / PHI-free) ──")
    print(json.dumps(fhir, ensure_ascii=False, indent=2)[:900] + "\n  ...")


if __name__ == "__main__":
    main()
