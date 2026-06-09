#!/usr/bin/env python3
"""iryo 医療 — 保険・公費・年齢区分・負担割合・負担区分 (medical insurance rules).

Covers the full payer matrix a レセプト needs:

  - 年齢区分 (乳幼児 / 成人 / 前期高齢 70-74 / 後期高齢 75+) → 法定給付の負担割合
  - 公費負担医療 (法別番号つき; 生活保護/自立支援/難病/小児慢性 等) と保険の重ね合わせ
  - 負担区分 (レセ電: 保険単独 / 保険+公費 / 公費単独 …) コード導出
  - 本人/家族, 高齢受給者証の現役並み/一定以上所得

Pure stdlib. The numeric 法定割合 are stable national rules; per-自治体 公費 details
(自己負担上限月額 等) are out of engine scope and supplied by the operator.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# --------------------------------------------------------------------------- #
# 年齢区分 → 法定負担割合
# --------------------------------------------------------------------------- #
def age_kubun(age: int) -> str:
    """年齢 → 区分キー (乳幼児/未就学/成人/前期高齢/後期高齢)."""
    if age < 6:
        return "乳幼児"          # 義務教育就学前 (6歳未満)
    if age < 70:
        return "成人"
    if age < 75:
        return "前期高齢"        # 70-74 高齢受給者
    return "後期高齢"            # 75+ 後期高齢者医療


def futan_wari(
    age: int,
    *,
    gen_eki: bool = False,       # 現役並み所得
    ittei_ijo: bool = False,     # 後期高齢の「一定以上所得」(2割)
) -> float:
    """法定本人負担割合 (給付の裏返し).

    - 6歳未満            : 2割
    - 6〜69歳            : 3割
    - 70〜74歳           : 2割 (現役並み所得は 3割)
    - 75歳以上(後期高齢)  : 1割 (一定以上所得 2割 / 現役並み 3割)
    """
    k = age_kubun(age)
    if k == "乳幼児":
        return 0.2
    if k == "成人":
        return 0.3
    if k == "前期高齢":
        return 0.3 if gen_eki else 0.2
    # 後期高齢
    if gen_eki:
        return 0.3
    if ittei_ijo:
        return 0.2
    return 0.1


# --------------------------------------------------------------------------- #
# 公費負担医療
# --------------------------------------------------------------------------- #
@dataclass
class Kohi:
    """1 公費負担医療. hobetsu = 法別番号 (2桁), e.g. 12 生活保護, 21 自立支援(精神通院),
    54 難病. futan_wari = 公費の患者負担割合 (生活保護等は 0.0)."""
    hobetsu: str
    fusha_bango: str = ""        # 公費負担者番号 (8桁)
    futan_wari: float = 0.0
    jiko_futan_gendo: Optional[int] = None  # 自己負担上限月額(円); None=なし


# 代表的な法別番号 (全国共通の主要なもの; 自治体単独事業は別)
HOBETSU_NAMES = {
    "12": "生活保護(医療扶助)",
    "21": "自立支援医療(精神通院)",
    "15": "自立支援医療(更生医療)",
    "16": "自立支援医療(育成医療)",
    "54": "難病(特定医療費)",
    "52": "小児慢性特定疾病",
    "10": "結核(感染症法37条の2)",
    "38": "肝炎治療特別促進",
    "51": "特定疾患治療研究",
}


# --------------------------------------------------------------------------- #
# 負担区分 (レセ電 算定明細の負担区分コード)
# --------------------------------------------------------------------------- #
# レセ電の負担区分は、その明細をどの保険者・公費が負担するかを表す1桁コード。
# 完全な体系は審査支払機関の規定によるが、代表的な単純ケースを導出する。
def futan_kubun(num_kohi: int, hoken: bool = True) -> str:
    """保険・公費の組合せ → 負担区分コード (代表的な単純ケース).

      保険単独            → "1"
      保険 + 第1公費      → "2"
      保険 + 第1 + 第2公費 → "3"
      第1公費単独         → "5"
    """
    if hoken and num_kohi == 0:
        return "1"
    if hoken and num_kohi == 1:
        return "2"
    if hoken and num_kohi >= 2:
        return "3"
    if not hoken and num_kohi >= 1:
        return "5"
    return "1"


# --------------------------------------------------------------------------- #
# 給付割合 (レセ電 HO レコード) — 10割中の保険給付割合
# --------------------------------------------------------------------------- #
def kyufu_wari(patient_futan_wari: float) -> int:
    """患者負担割合 → 給付割合 (10割中). 0.3 → 7, 0.2 → 8, 0.1 → 9, 0.0 → 10."""
    return int(round((1.0 - patient_futan_wari) * 10))
