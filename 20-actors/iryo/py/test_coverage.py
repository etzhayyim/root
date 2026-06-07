#!/usr/bin/env python3
"""iryo 医療 — full-coverage rezept tests (入院/年齢区分/公費/食事療養/全診療区分/負担区分)."""
from masters import default_masters
from rezept import ActLine, Encounter, Prescription, DrugDose, MaterialLine, compute

M = default_masters()


# ── 年齢区分から負担割合を導出 ──────────────────────────────────────────────
def test_futan_wari_derived_from_age():
    base = [ActLine("111000110", 1)]
    assert compute(Encounter(futan_wari=None, age=5, acts=base), M).futan_wari == 0.2
    assert compute(Encounter(futan_wari=None, age=40, acts=base), M).futan_wari == 0.3
    assert compute(Encounter(futan_wari=None, age=80, acts=base), M).futan_wari == 0.1


# ── 全診療区分が集計される ──────────────────────────────────────────────────
def test_all_kubun_categories_aggregate():
    enc = Encounter(futan_wari=0.3, acts=[
        ActLine("111000110"),   # 初診
        ActLine("112007410"),   # 再診
        ActLine("113002510"),   # 医学管理
        ActLine("113001610"),   # 在宅
        ActLine("140009410"),   # 注射
        ActLine("140000110"),   # 処置
        ActLine("150295810"),   # 手術
        ActLine("150000490"),   # 麻酔
        ActLine("160008010"),   # 検査
        ActLine("160218010"),   # 病理
        ActLine("170018510"),   # 画像診断
        ActLine("120002910"),   # その他
        ActLine("190000810"),   # 入院
    ], prescriptions=[Prescription("21", days=1, drugs=[DrugDose("620008863", 1)])])
    r = compute(enc, M)
    for k in ["初診", "再診", "医学管理", "在宅", "投薬", "注射", "処置",
              "手術", "麻酔", "検査", "病理", "画像診断", "その他", "入院"]:
        assert k in r.kubun_totals, f"missing 区分 {k}"
    # 区分は表示順 (KUBUN_ORDER) で出力される
    assert list(r.kubun_totals.keys())[0] == "初診"
    assert list(r.kubun_totals.keys())[-1] == "入院"


# ── 入院 + 食事療養標準負担額 ────────────────────────────────────────────────
def test_nyuin_with_shokuji_standard_burden():
    enc = Encounter(futan_wari=0.3, nyuin=True, shokuji_meals=6, shokuji_tanka_yen=490,
                    acts=[ActLine("190000810", 5)])  # 入院基本料 ×5日
    r = compute(enc, M)
    assert r.nyuin is True
    assert r.shokuji_futan_yen == 6 * 490        # 2,940
    assert r.total_futan_yen == r.patient_pay_yen + 2940
    assert r.kubun_totals == {"入院": 1688 * 5}


# ── 公費 (生活保護) が患者負担を肩代わり ─────────────────────────────────────
def test_kohi_seikatsuhogo_zeroes_patient_pay():
    enc = Encounter(futan_wari=0.3, acts=[ActLine("111000110", 1)],
                    kohi=[{"hobetsu": "12", "futanWari": 0.0}])
    r = compute(enc, M)
    assert r.patient_pay_yen == 0          # 公費が全額肩代わり
    assert r.futan_kubun == "2"            # 保険+第1公費
    assert all(l.futan_kubun == "2" for l in r.lines)


def test_kohi_with_jiko_futan_gendo_caps_pay():
    enc = Encounter(futan_wari=0.3, acts=[ActLine("170018510", 50)],  # 大きめ
                    kohi=[{"hobetsu": "54", "futanWari": 0.2, "jikoFutanGendo": 5000}])
    r = compute(enc, M)
    assert r.patient_pay_yen == 5000       # 難病 自己負担上限月額に圧縮


# ── 高額療養費 70歳以上 一般 外来 個人上限 ───────────────────────────────────
def test_kogaku_o70_ippan_gairai_cap():
    # age 80 → 1割; 胸部X線 210×100 = 21,000点 → 医療費 210,000円 → 窓口 21,000円
    # 一般 外来(個人)上限 18,000円 に調整
    enc = Encounter(futan_wari=None, age=80, kogaku_kubun="一般", nyuin=False,
                    acts=[ActLine("170018510", 100)])
    r = compute(enc, M)
    assert r.total_iryohi_yen == 210_000
    assert r.ichibu_futan_yen == 21_000
    assert r.kogaku_limit_yen == 18_000
    assert r.kogaku_applied is True
    assert r.patient_pay_yen == 18_000


def test_kogaku_o70_nyuin_uses_setai_limit():
    # 入院は世帯上限 (一般 57,600) を使う (外来個人上限ではない)
    enc = Encounter(futan_wari=None, age=80, kogaku_kubun="一般", nyuin=True,
                    acts=[ActLine("190000810", 50)])  # 大きめ入院料
    r = compute(enc, M)
    assert r.kogaku_limit_yen == 57_600
    assert r.kogaku_applied is True
    assert r.patient_pay_yen == 57_600


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
