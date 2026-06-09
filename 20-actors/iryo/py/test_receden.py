#!/usr/bin/env python3
"""iryo 医療 — レセ電 (レセプト電算) record generation tests."""
from datetime import date

import receden
from karte import Diagnosis, Insurance, Karte, Patient
from masters import default_masters
from receden import (Institution, build_receden, record_summary,
                     rezept_shubetsu, to_csv, wareki, wareki_ym)
from rezept import ActLine, Encounter, Prescription, DrugDose, compute

M = default_masters()


def _karte():
    return Karte(
        patient=Patient(pseudonym_did="did:web:patient.iryo.etzhayyim.com:zz9",
                        sex="M", birth_year=1980),
        insurance=Insurance(hokensha_bango="01130012", futan_wari=0.3,
                            honnin_kazoku="honnin"),
        diagnoses=[Diagnosis("8843689", "J069", "急性上気道炎",
                             onset="2026-06-07", outcome="継続", is_main=True)],
    )


def _enc():
    return Encounter(futan_wari=0.3, acts=[
        ActLine("111000110", 1),    # 初診
        ActLine("160008010", 1),    # 末梢血液一般
    ], prescriptions=[
        Prescription("21", days=5, drugs=[DrugDose("620008863", 3)]),  # カロナール
    ])


# ── 和暦変換 ────────────────────────────────────────────────────────────────
def test_wareki_reiwa_and_showa():
    assert wareki(date(2026, 6, 7)) == "5080607"     # 令和8年6月7日
    assert wareki_ym(2026, 6) == "50806"
    assert wareki(date(1980, 4, 1)) == "3550401"     # 昭和55年4月1日


def test_rezept_shubetsu_encoding():
    assert rezept_shubetsu(nyuin=False, honnin=True, kokuho=False) == "1122"
    assert rezept_shubetsu(nyuin=True, honnin=False, kokuho=True) == "1216"


# ── レコードストリーム ──────────────────────────────────────────────────────
def test_build_receden_has_required_records():
    rez = compute(_enc(), M)
    rows = build_receden(Institution("1", "13", iryokikan_code="1234567"), _karte(), rez,
                         shinryo_year=2026, shinryo_month=6, jitsunissu=1)
    ids = [r[0] for r in rows]
    assert ids[0] == "IR"
    assert "RE" in ids and "HO" in ids and "SY" in ids
    assert "SI" in ids and "IY" in ids
    summary = record_summary(rows)
    assert summary["SI"] == 2          # 2 診療行為
    assert summary["IY"] == 1          # 1 薬剤


def test_receden_is_phi_free_by_default():
    rez = compute(_enc(), M)
    rows = build_receden(Institution("1", "13"), _karte(), rez,
                         shinryo_year=2026, shinryo_month=6)
    re_row = [r for r in rows if r[0] == "RE"][0]
    # 氏名フィールドは pseudonym tail, 生年月日は空 (PHI は注入されない)
    assert re_row[4] == "zz9"
    assert re_row[6] == ""
    csv = to_csv(rows)
    assert "山田" not in csv
    assert csv.endswith("\r\n")


def test_receden_phi_injected_only_via_callback():
    rez = compute(_enc(), M)
    rows = build_receden(
        Institution("1", "13"), _karte(), rez,
        shinryo_year=2026, shinryo_month=6,
        phi=lambda k: {"name": "ヤマダタロウ", "birth": date(1980, 4, 1)},
    )
    re_row = [r for r in rows if r[0] == "RE"][0]
    assert re_row[4] == "ヤマダタロウ"
    assert re_row[6] == "3550401"


def test_ho_record_carries_kyufu_and_totals():
    rez = compute(_enc(), M)
    rows = build_receden(Institution("1", "13"), _karte(), rez,
                         shinryo_year=2026, shinryo_month=6, jitsunissu=1)
    ho = [r for r in rows if r[0] == "HO"][0]
    assert ho[3] == "7"                      # 給付割合 7割 (3割負担)
    assert ho[5] == str(rez.total_ten)       # 合計点数
    assert ho[6] == str(rez.patient_pay_yen)  # 一部負担金


def test_receden_carries_futan_kubun_from_kohi():
    enc = _enc()
    enc.kohi = [{"hobetsu": "54", "futanWari": 0.2}]
    rez = compute(enc, M)
    k = _karte()
    k.insurance.kohi = ["54136015"]
    rows = build_receden(Institution("1", "13"), k, rez,
                         shinryo_year=2026, shinryo_month=6)
    si = [r for r in rows if r[0] == "SI"][0]
    assert si[2] == "2"                       # 負担区分 保険+第1公費
    assert any(r[0] == "KO" for r in rows)     # 公費 KO record present


def test_receden_optional_ty_co_sj_records():
    rez = compute(_enc(), M)
    rows = build_receden(
        Institution("1", "13"), _karte(), rez,
        shinryo_year=2026, shinryo_month=6,
        tokki=["26区ア"], comments=[{"shikibetsu": "60", "code": "830000001",
                                     "text": "前回より継続"}],
        shojo_shoki=["経過は安定"],
    )
    ids = [r[0] for r in rows]
    assert "TY" in ids and "CO" in ids and "SJ" in ids


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
