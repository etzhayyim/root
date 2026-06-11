#!/usr/bin/env python3
"""iryo 医療 — 高額療養費 自己負担限度額 (full 区分: 70歳未満 + 70歳以上).

Monthly self-pay cap on the window 一部負担金. Two age regimes, each with income bands:

70歳未満
  ア 年収約1160万円〜   : 252,600 + (総医療費 - 842,000) × 1%
  イ 約770〜1160万円    : 167,400 + (総医療費 - 558,000) × 1%
  ウ 約370〜770万円     :  80,100 + (総医療費 - 267,000) × 1%
  エ 〜約370万円        :  57,600 (定額)
  オ 住民税非課税       :  35,400 (定額)

70歳以上 (外来は個人ごとの上限, 世帯は入院含む世帯上限)
  現役並みⅢ 課税所得690万円〜 : 252,600 + (総医療費 - 842,000) × 1%   (外来=世帯)
  現役並みⅡ 課税所得380万円〜 : 167,400 + (総医療費 - 558,000) × 1%   (外来=世帯)
  現役並みⅠ 課税所得145万円〜 :  80,100 + (総医療費 - 267,000) × 1%   (外来=世帯)
  一般                       : 外来(個人) 18,000 / 世帯 57,600
  低所得Ⅱ                    : 外来 8,000 / 世帯 24,600
  低所得Ⅰ                    : 外来 8,000 / 世帯 15,000
"""
from __future__ import annotations

import math
from typing import Optional

# 70歳未満: kubun → (定額 or 定率基準, 基準額 or None, 逓増率)
_U70 = {
    "ア": (252_600, 842_000, 0.01),
    "イ": (167_400, 558_000, 0.01),
    "ウ": (80_100, 267_000, 0.01),
    "エ": (57_600, None, 0.0),
    "オ": (35_400, None, 0.0),
}

# 70歳以上 現役並み: kubun → (定額, 基準額, 逓増率)  — 外来も世帯と同額
_O70_GENEKI = {
    "現役3": (252_600, 842_000, 0.01),
    "現役2": (167_400, 558_000, 0.01),
    "現役1": (80_100, 267_000, 0.01),
}

# 70歳以上 一般/低所得: kubun → (外来個人上限, 世帯上限)
_O70_FLAT = {
    "一般": (18_000, 57_600),
    "低2": (8_000, 24_600),
    "低1": (8_000, 15_000),
}

# 別名 (full-name → canonical key)
_ALIAS = {
    "現役並みⅢ": "現役3", "現役並み3": "現役3", "現役並みIII": "現役3",
    "現役並みⅡ": "現役2", "現役並み2": "現役2", "現役並みII": "現役2",
    "現役並みⅠ": "現役1", "現役並み1": "現役1", "現役並みI": "現役1",
    "低所得Ⅱ": "低2", "低所得2": "低2", "低所得II": "低2",
    "低所得Ⅰ": "低1", "低所得1": "低1", "低所得I": "低1",
}


def _canon(kubun: str) -> str:
    return _ALIAS.get(kubun, kubun)


def kogaku_limit_u70(total_iryohi_yen: int, kubun: str) -> Optional[int]:
    """70歳未満の月額自己負担限度額(円). 未知区分は None."""
    spec = _U70.get(kubun)
    if spec is None:
        return None
    base, threshold, rate = spec
    if threshold is None or rate == 0.0:
        return int(base)
    return int(base + math.floor(max(0, total_iryohi_yen - threshold) * rate))


def kogaku_limit_o70(
    total_iryohi_yen: int, kubun: str, *, gairai_only: bool = False
) -> Optional[int]:
    """70歳以上の月額自己負担限度額(円). gairai_only=True は外来(個人)上限. 未知区分は None."""
    k = _canon(kubun)
    if k in _O70_GENEKI:
        base, threshold, rate = _O70_GENEKI[k]
        return int(base + math.floor(max(0, total_iryohi_yen - threshold) * rate))
    if k in _O70_FLAT:
        gairai, setai = _O70_FLAT[k]
        return int(gairai if gairai_only else setai)
    return None


def kogaku_limit(
    total_iryohi_yen: int,
    kubun: Optional[str],
    *,
    age: Optional[int] = None,
    gairai_only: bool = False,
) -> Optional[int]:
    """区分 + 年齢 から限度額を解決. 70歳以上区分名なら以上ロジック, ア〜オなら未満ロジック.

    age を渡せば 70歳以上/未満 を年齢で判定し、不整合な区分名は None を返す。
    """
    if not kubun:
        return None
    is_o70_kubun = _canon(kubun) in _O70_GENEKI or _canon(kubun) in _O70_FLAT
    is_u70_kubun = kubun in _U70

    if age is not None:
        if age >= 70 and is_o70_kubun:
            return kogaku_limit_o70(total_iryohi_yen, kubun, gairai_only=gairai_only)
        if age < 70 and is_u70_kubun:
            return kogaku_limit_u70(total_iryohi_yen, kubun)
        # 年齢と区分体系が不整合
        if is_o70_kubun:
            return kogaku_limit_o70(total_iryohi_yen, kubun, gairai_only=gairai_only)
        if is_u70_kubun:
            return kogaku_limit_u70(total_iryohi_yen, kubun)
        return None

    # 年齢未指定: 区分名から体系を推定
    if is_o70_kubun:
        return kogaku_limit_o70(total_iryohi_yen, kubun, gairai_only=gairai_only)
    if is_u70_kubun:
        return kogaku_limit_u70(total_iryohi_yen, kubun)
    return None
