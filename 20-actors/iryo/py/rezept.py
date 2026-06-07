#!/usr/bin/env python3
"""iryo 医療 — レセプト点数計算エンジン (診療報酬請求, pure stdlib).

Given a structured 診療録 (encounter) it computes:

  1. 点数 per 算定明細 (診療行為 / 薬剤料 / 特定器材料), grouped by 診療識別 → レセプト点数欄 区分
  2. 総点数 → 総医療費 (1点 = 10円)
  3. 一部負担金 (窓口負担) = 総医療費 × 負担割合, 10円未満四捨五入
  4. 高額療養費 — 70歳未満 所得区分 ア/イ/ウ/エ/オ の自己負担限度額で窓口負担を上限調整

The arithmetic is exact and verifiable; all point values are resolved through a
:class:`~masters.Masters` instance (never hard-coded). See ``test_rezept.py``.

薬剤料換算 (五捨五超四入)
------------------------
所定単位あたりの薬価が

  - 15円以下           → 1点
  - 15円を超えるもの    → 薬価を10で除し, 端数は「五捨五超」(0.5以下切捨, 0.5超切上)

投与日数(内服)・回数(屯服/注射)を乗じて 薬剤料点数 を得る。

一部負担金 端数処理
------------------
窓口で徴収する一部負担金は 10円未満を四捨五入 (5円以上切上, 5円未満切捨)。

高額療養費 (70歳未満, 月額自己負担限度額)
--------------------------------------
  ア 年収約1160万円〜       : 252,600 + (総医療費 - 842,000) × 1%
  イ 約770〜1160万円        : 167,400 + (総医療費 - 558,000) × 1%
  ウ 約370〜770万円         :  80,100 + (総医療費 - 267,000) × 1%
  エ 〜約370万円            :  57,600 (定額)
  オ 住民税非課税           :  35,400 (定額)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import insurance
from kogaku import kogaku_limit  # re-export (full 70歳未満+以上 全区分)
from masters import Masters

# 診療識別 (レセ電 2桁) → レセプト点数欄 区分名 (全区分)
SHIKIBETSU_KUBUN = {
    "11": "初診", "12": "再診", "13": "医学管理", "14": "在宅",
    "21": "投薬", "22": "投薬", "23": "投薬", "24": "投薬",
    "25": "投薬", "26": "投薬", "27": "投薬", "28": "投薬",
    "31": "注射", "32": "注射", "33": "注射",
    "40": "処置", "50": "手術", "54": "麻酔",
    "60": "検査", "64": "病理", "70": "画像診断",
    "80": "その他", "90": "入院",
}

# レセプト点数欄での区分表示順 (全区分)。
KUBUN_ORDER = [
    "初診", "再診", "医学管理", "在宅", "投薬", "注射",
    "処置", "手術", "麻酔", "検査", "病理", "画像診断", "その他", "入院",
]


# --------------------------------------------------------------------------- #
# primitive arithmetic (exact, independently verifiable)
# --------------------------------------------------------------------------- #
def yakka_to_ten(price_yen: float) -> int:
    """薬価(円)→ 点数. ≤15円→1点; >15円→ price/10 を五捨五超四入."""
    if price_yen <= 15:
        return 1
    q = price_yen / 10.0
    floor = math.floor(q)
    frac = q - floor
    # 五捨五超: 0.5ちょうど以下は切捨, 0.5超は切上
    return int(floor if frac <= 0.5 + 1e-9 else floor + 1)


def round_ichibu_futan(yen: float) -> int:
    """一部負担金 端数処理: 10円未満四捨五入 (5円以上切上)."""
    return int((int(round(yen)) + 5) // 10 * 10)


# --------------------------------------------------------------------------- #
# input model
# --------------------------------------------------------------------------- #
@dataclass
class ActLine:
    """1 診療行為 算定 (診療行為マスタ参照)."""
    code: str
    count: int = 1


@dataclass
class DrugDose:
    code: str
    amount: float  # 所定単位数 (例: 1日あたり錠数)


@dataclass
class Prescription:
    """1 剤 の投薬. shikibetsu: 21内服/22屯服/23外用. 内服は days を乗じる."""
    shikibetsu: str
    drugs: list[DrugDose]
    days: int = 1            # 投与日数(内服) / 回数(屯服) — 外用は通常1
    label: str = ""


@dataclass
class MaterialLine:
    code: str
    amount: float = 1.0
    shikibetsu: str = "40"   # 特定器材は使用文脈の区分(処置40 等)に従う


@dataclass
class Encounter:
    """レセプト1件分の算定対象 (1患者・1医療機関・1ヶ月相当).

    外来/入院, 年齢区分・公費・高額療養費 全区分, 食事療養 をカバーする。
    futan_wari を None にすると age から法定割合を導出する。
    """
    futan_wari: Optional[float] = 0.3        # None → age から導出
    kogaku_kubun: Optional[str] = None       # 高額療養費 所得区分 (ア〜オ / 現役3 等)
    age: Optional[int] = None                # 年齢 (負担割合・高額療養費体系の判定)
    gen_eki: bool = False                    # 現役並み所得 (高齢)
    ittei_ijo: bool = False                  # 後期高齢 一定以上所得 (2割)
    nyuin: bool = False                      # 入院レセプト (高額療養費=世帯, 外来加算なし)
    kohi: list[dict] = field(default_factory=list)  # [{hobetsu, fushaBango, futanWari}]
    shokuji_meals: int = 0                   # 入院時食事療養の食数
    shokuji_tanka_yen: int = 490             # 食事療養標準負担額 (円/食, 一般)
    acts: list[ActLine] = field(default_factory=list)
    prescriptions: list[Prescription] = field(default_factory=list)
    materials: list[MaterialLine] = field(default_factory=list)

    def resolved_futan_wari(self) -> float:
        if self.futan_wari is not None:
            return self.futan_wari
        if self.age is not None:
            return insurance.futan_wari(self.age, gen_eki=self.gen_eki,
                                        ittei_ijo=self.ittei_ijo)
        return 0.3


# --------------------------------------------------------------------------- #
# computed model
# --------------------------------------------------------------------------- #
@dataclass
class ComputedLine:
    kind: str          # "act" | "drug" | "material"
    shikibetsu: str
    kubun: str
    code: str
    name: str
    unit_ten: int      # 1回/1単位あたり点数
    count: int         # 回数 / 日数
    ten: int           # この明細の合計点数 (unit_ten * count)
    futan_kubun: str = "1"   # レセ電 負担区分 (保険単独=1 / 保険+公費=2,3 …)


@dataclass
class RezeptResult:
    lines: list[ComputedLine]
    kubun_totals: dict[str, int]
    total_ten: int
    total_iryohi_yen: int      # 総医療費 (10割)
    futan_wari: float
    ichibu_futan_yen: int      # 高額療養費 適用前の窓口負担
    kogaku_kubun: Optional[str]
    kogaku_limit_yen: Optional[int]
    kogaku_applied: bool
    patient_pay_yen: int       # 医療費の窓口負担 (高額療養費 適用後)
    nyuin: bool = False
    shokuji_futan_yen: int = 0      # 入院時食事療養 標準負担額 (患者)
    total_futan_yen: int = 0        # 窓口総額 (医療 + 食事)
    futan_kubun: str = "1"          # レセ電 負担区分

    def to_dict(self) -> dict:
        return {
            "lines": [vars(l) for l in self.lines],
            "kubunTotals": self.kubun_totals,
            "totalTen": self.total_ten,
            "totalIryohiYen": self.total_iryohi_yen,
            "futanWari": self.futan_wari,
            "ichibuFutanYen": self.ichibu_futan_yen,
            "kogakuKubun": self.kogaku_kubun,
            "kogakuLimitYen": self.kogaku_limit_yen,
            "kogakuApplied": self.kogaku_applied,
            "patientPayYen": self.patient_pay_yen,
            "nyuin": self.nyuin,
            "shokujiFutanYen": self.shokuji_futan_yen,
            "totalFutanYen": self.total_futan_yen,
            "futanKubun": self.futan_kubun,
        }


# --------------------------------------------------------------------------- #
# engine
# --------------------------------------------------------------------------- #
def _kubun_of(shikibetsu: str) -> str:
    return SHIKIBETSU_KUBUN.get(shikibetsu, "その他")


def compute_drug_ten(rx: Prescription, m: Masters) -> int:
    """1剤の薬剤料点数 = 五捨五超(1所定単位の合計薬価) × 日数/回数.

    内服(21)は「1剤1日分の薬価合計」を点数換算し投与日数を乗じる。屯服(22)は1回分×回数,
    外用(23)は1調剤分×1。算定単位(1剤1日分 等)の薬価合計に対して換算するのが点数表の規定。
    """
    yakka_per_unit = sum(m.drug(d.code).yakka * d.amount for d in rx.drugs)
    ten_per_unit = yakka_to_ten(yakka_per_unit)
    return ten_per_unit * max(1, rx.days)


def compute(enc: Encounter, m: Masters) -> RezeptResult:
    """Encounter → RezeptResult (全点数・年齢区分・公費・一部負担金・高額療養費・食事療養)."""
    lines: list[ComputedLine] = []
    fk = insurance.futan_kubun(len(enc.kohi))   # レセ電 負担区分

    # 1) 診療行為
    for a in enc.acts:
        item = m.shinryo(a.code)
        lines.append(ComputedLine(
            kind="act", shikibetsu=item.shikibetsu, kubun=_kubun_of(item.shikibetsu),
            code=item.code, name=item.name, unit_ten=item.ten,
            count=a.count, ten=item.ten * a.count, futan_kubun=fk,
        ))

    # 2) 薬剤料 (投薬)
    for rx in enc.prescriptions:
        ten = compute_drug_ten(rx, m)
        names = "+".join(m.drug(d.code).name for d in rx.drugs)
        label = rx.label or names
        unit_ten = ten // max(1, rx.days)
        lines.append(ComputedLine(
            kind="drug", shikibetsu=rx.shikibetsu, kubun=_kubun_of(rx.shikibetsu),
            code=rx.drugs[0].code if rx.drugs else "", name=label,
            unit_ten=unit_ten, count=max(1, rx.days), ten=ten, futan_kubun=fk,
        ))

    # 3) 特定器材料 (特定器材も薬価同様 五捨五超 で点数換算)
    for mat in enc.materials:
        item = m.material(mat.code)
        ten = yakka_to_ten(item.yakka * mat.amount)
        lines.append(ComputedLine(
            kind="material", shikibetsu=mat.shikibetsu, kubun=_kubun_of(mat.shikibetsu),
            code=item.code, name=item.name, unit_ten=ten, count=1, ten=ten,
            futan_kubun=fk,
        ))

    # 区分集計
    kubun_totals: dict[str, int] = {}
    for l in lines:
        kubun_totals[l.kubun] = kubun_totals.get(l.kubun, 0) + l.ten
    total_ten = sum(l.ten for l in lines)

    # 円換算 + 一部負担金 (負担割合は age から導出可)
    wari = enc.resolved_futan_wari()
    total_iryohi_yen = total_ten * m.tensu_tanka_yen
    ichibu = round_ichibu_futan(total_iryohi_yen * wari)

    # 高額療養費 (70歳未満 ア〜オ / 70歳以上 現役・一般・低所得; 外来は個人上限)
    limit = (kogaku_limit(total_iryohi_yen, enc.kogaku_kubun,
                          age=enc.age, gairai_only=not enc.nyuin)
             if enc.kogaku_kubun else None)
    applied = limit is not None and ichibu > limit
    patient_pay = limit if applied else ichibu

    # 公費負担: 公費が患者負担を肩代わりする場合 (生活保護等 futanWari 0) → 患者負担を圧縮
    for k in enc.kohi:
        kf = float(k.get("futanWari", 0.0))
        kohi_cap = round_ichibu_futan(total_iryohi_yen * kf)
        patient_pay = min(patient_pay, kohi_cap)
        gendo = k.get("jikoFutanGendo")
        if gendo is not None:
            patient_pay = min(patient_pay, int(gendo))

    # 入院時食事療養 標準負担額 (高額療養費の対象外, 別建て)
    shokuji = enc.shokuji_meals * enc.shokuji_tanka_yen if enc.nyuin else 0
    total_futan = int(patient_pay) + shokuji

    ordered = {k: kubun_totals[k] for k in KUBUN_ORDER if k in kubun_totals}

    return RezeptResult(
        lines=lines,
        kubun_totals=ordered,
        total_ten=total_ten,
        total_iryohi_yen=total_iryohi_yen,
        futan_wari=wari,
        ichibu_futan_yen=ichibu,
        kogaku_kubun=enc.kogaku_kubun,
        kogaku_limit_yen=limit,
        kogaku_applied=applied,
        patient_pay_yen=int(patient_pay),
        nyuin=enc.nyuin,
        shokuji_futan_yen=shokuji,
        total_futan_yen=total_futan,
        futan_kubun=fk,
    )
