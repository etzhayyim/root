#!/usr/bin/env python3
"""iryo 医療 — レセプト点数計算エンジン tests (verifiable arithmetic).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_rezept.py
"""
import rezept
from masters import default_masters
from rezept import (ActLine, DrugDose, Encounter, MaterialLine, Prescription,
                    compute, kogaku_limit, round_ichibu_futan, yakka_to_ten)

M = default_masters()


# ── 薬剤料 五捨五超四入 ────────────────────────────────────────────────────
def test_yakka_to_ten_under_15_is_one_point():
    assert yakka_to_ten(15) == 1
    assert yakka_to_ten(5.9) == 1
    assert yakka_to_ten(10.1) == 1


def test_yakka_to_ten_gosha_gocho():
    assert yakka_to_ten(21) == 2     # 2.1 → 切捨
    assert yakka_to_ten(25) == 2     # 2.5 ちょうど → 五捨 → 切捨
    assert yakka_to_ten(26) == 3     # 2.6 → 五超 → 切上
    assert yakka_to_ten(56.4) == 6   # 5.64 → 切上
    assert yakka_to_ten(193) == 19   # 19.3 → 切捨


# ── 一部負担金 端数処理 (10円未満四捨五入) ─────────────────────────────────
def test_round_ichibu_futan():
    assert round_ichibu_futan(873) == 870    # 3円 → 切捨
    assert round_ichibu_futan(875) == 880    # 5円 → 切上
    assert round_ichibu_futan(1080) == 1080
    assert round_ichibu_futan(1084) == 1080
    assert round_ichibu_futan(1086) == 1090


# ── 高額療養費 自己負担限度額 (70歳未満) ───────────────────────────────────
def test_kogaku_limit_u_band_is_progressive():
    # 区分ウ: 80,100 + (総医療費 - 267,000) × 1%
    assert kogaku_limit(1_000_000, "ウ") == 80_100 + (1_000_000 - 267_000) // 100
    assert kogaku_limit(1_000_000, "ウ") == 87_430


def test_kogaku_limit_flat_bands():
    assert kogaku_limit(500_000, "エ") == 57_600
    assert kogaku_limit(9_000_000, "オ") == 35_400
    assert kogaku_limit(100_000, None) is None
    assert kogaku_limit(100_000, "X") is None


# ── compute: 区分集計 + 円換算 + 一部負担金 ───────────────────────────────
def test_compute_outpatient_basic():
    enc = Encounter(futan_wari=0.3, acts=[
        ActLine("111000110", 1),   # 初診料 291
        ActLine("160008010", 1),   # 末梢血液一般 21
        ActLine("160019410", 1),   # HbA1c 49
    ])
    r = compute(enc, M)
    assert r.total_ten == 291 + 21 + 49 == 361
    assert r.kubun_totals == {"初診": 291, "検査": 70}
    assert r.total_iryohi_yen == 3610
    assert r.ichibu_futan_yen == 1080          # round10(3610*0.3=1083) → 1080
    assert r.kogaku_applied is False
    assert r.patient_pay_yen == 1080


def test_compute_drug_internal_multiplies_days():
    # カロナール200 (5.9円) 3錠/日 × 5日 → 五捨五超(17.7)=2点/日 × 5 = 10点
    enc = Encounter(futan_wari=0.3, prescriptions=[
        Prescription(shikibetsu="21", days=5,
                     drugs=[DrugDose("620008863", 3)]),
    ])
    r = compute(enc, M)
    drug_line = [l for l in r.lines if l.kind == "drug"][0]
    assert drug_line.unit_ten == 2
    assert drug_line.count == 5
    assert drug_line.ten == 10
    assert r.kubun_totals == {"投薬": 10}


def test_compute_act_count_multiplies():
    enc = Encounter(futan_wari=0.3, acts=[ActLine("170018510", 2)])  # 胸部X線 210 ×2
    r = compute(enc, M)
    assert r.total_ten == 420
    assert r.kubun_totals == {"画像診断": 420}


def test_compute_material_is_yakka_converted():
    # 留置カテーテル 561円 → 五捨五超(561)=56.1→56点
    enc = Encounter(materials=[MaterialLine("700020000", 1, "40")])
    r = compute(enc, M)
    mat = [l for l in r.lines if l.kind == "material"][0]
    assert mat.ten == 56
    assert r.kubun_totals == {"処置": 56}


# ── 高額療養費 適用 (窓口負担が限度額に調整される) ─────────────────────────
def test_compute_applies_kogaku_cap():
    # 総点数 12,600 → 医療費 126,000円 → 3割 37,800円 > 区分オ限度 35,400円 → 35,400 に調整
    enc = Encounter(futan_wari=0.3, kogaku_kubun="オ",
                    acts=[ActLine("170018510", 60)])
    r = compute(enc, M)
    assert r.total_iryohi_yen == 126_000
    assert r.ichibu_futan_yen == 37_800
    assert r.kogaku_limit_yen == 35_400
    assert r.kogaku_applied is True
    assert r.patient_pay_yen == 35_400


def test_compute_kogaku_not_applied_when_under_limit():
    enc = Encounter(futan_wari=0.3, kogaku_kubun="ウ",
                    acts=[ActLine("111000110", 1)])  # 291点 → 873円 < 限度
    r = compute(enc, M)
    assert r.kogaku_applied is False
    assert r.patient_pay_yen == r.ichibu_futan_yen


def test_futan_wari_zero_means_no_patient_pay():
    enc = Encounter(futan_wari=0.0, acts=[ActLine("111000110", 1)])
    r = compute(enc, M)
    assert r.ichibu_futan_yen == 0
    assert r.patient_pay_yen == 0


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
