#!/usr/bin/env python3
"""iryo 医療 — end-to-end 診療録 → レセプト → レセ電 → FHIR through the cell agent."""
import agent


# A complete encounter expressed as plain JSON-able dicts (how a cell is driven).
ENCOUNTER = {
    "futanWari": 0.3,
    "acts": [
        {"code": "111000110", "count": 1},   # 初診料
        {"code": "112011010", "count": 1},   # 外来管理加算
        {"code": "160008010", "count": 1},   # 末梢血液一般
        {"code": "160019410", "count": 1},   # HbA1c
    ],
    "prescriptions": [
        {"shikibetsu": "21", "days": 14,
         "drugs": [{"code": "620003991", "amount": 2}]},  # メトホルミン 2錠/日×14
    ],
}

KARTE = {
    "patient": {"pseudonymDid": "did:web:patient.iryo.etzhayyim.com:e2e1",
                "sex": "F", "birthYear": 1975},
    "insurance": {"hokenshaBango": "06270013", "futanWari": 0.3,
                  "honninKazoku": "honnin", "kogakuKubun": "ウ"},
    "diagnoses": [
        {"shobyoCode": "2500013", "icd10": "E119", "name": "2型糖尿病",
         "onset": "2025-04-01", "outcome": "継続", "isMain": True},
        {"shobyoCode": "4019005", "icd10": "I10", "name": "高血圧症",
         "onset": "2025-04-01", "outcome": "継続"},
    ],
}


def test_handle_rezept_computes_kubun_totals():
    out = agent.handle_rezept({"encounter": ENCOUNTER})
    r = out["result"]
    assert r["kubunTotals"]["初診"] == 291
    assert r["kubunTotals"]["再診"] == 52        # 外来管理加算 (再診区分)
    assert r["kubunTotals"]["検査"] == 21 + 49
    assert r["totalTen"] == r["kubunTotals"]["初診"] + r["kubunTotals"]["再診"] \
        + r["kubunTotals"]["検査"] + r["kubunTotals"]["投薬"]
    assert r["totalIryohiYen"] == r["totalTen"] * 10
    assert out["intent"].startswith("member-principal")


def test_handle_receden_draft_phi_free():
    out = agent.handle_receden({"encounter": ENCOUNTER, "karte": KARTE,
                                "shinryoYear": 2026, "shinryoMonth": 6})
    assert out["state"] == "draft"               # G3 no-server-key
    assert out["summary"]["SY"] == 2             # 2 傷病名
    assert out["summary"]["IY"] == 1
    assert "1975" not in out["csv"]              # no birth year leak in body


def test_handle_validate_flags_and_passes():
    out = agent.handle_validate({"encounter": ENCOUNTER, "karte": KARTE})
    codes = {o["code"] for o in out["observations"]}
    assert "NO_DIAGNOSIS" not in codes
    assert out["ok"] is True


def test_validate_flags_rx_without_diagnosis():
    karte_no_dx = {**KARTE, "diagnoses": []}
    out = agent.handle_validate({"encounter": ENCOUNTER, "karte": karte_no_dx})
    codes = {o["code"] for o in out["observations"]}
    assert "RX_WITHOUT_DX" in codes or "NO_DIAGNOSIS" in codes
    assert out["ok"] is False


def test_export_fhir_bundle_is_codes_only():
    out = agent.export_fhir({"encounter": ENCOUNTER, "karte": KARTE})
    bundle = out["bundle"]
    assert bundle["resourceType"] == "Bundle"
    types = [e["resource"]["resourceType"] for e in bundle["entry"]]
    assert "Coverage" in types and "Condition" in types and "Claim" in types
    claim = [e["resource"] for e in bundle["entry"]
             if e["resource"]["resourceType"] == "Claim"][0]
    assert claim["total"]["unit"] == "点"
    # no PHI string anywhere in the serialized bundle
    import json
    assert "1975" not in json.dumps(bundle, ensure_ascii=False)


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
