#!/usr/bin/env python3
"""iryo 医療 — 高額療養費 full-band tests (70歳未満 + 70歳以上)."""
from kogaku import kogaku_limit, kogaku_limit_o70, kogaku_limit_u70


# ── 70歳未満 ア〜オ ──────────────────────────────────────────────────────────
def test_u70_progressive_bands():
    assert kogaku_limit_u70(900_000, "ア") == 252_600 + (900_000 - 842_000) // 100
    assert kogaku_limit_u70(900_000, "イ") == 167_400 + (900_000 - 558_000) // 100
    assert kogaku_limit_u70(1_000_000, "ウ") == 87_430


def test_u70_flat_bands():
    assert kogaku_limit_u70(5_000_000, "エ") == 57_600
    assert kogaku_limit_u70(5_000_000, "オ") == 35_400
    assert kogaku_limit_u70(100_000, "Z") is None


# ── 70歳以上 現役並み / 一般 / 低所得 ─────────────────────────────────────────
def test_o70_geneki_progressive():
    assert kogaku_limit_o70(900_000, "現役3") == 252_600 + (900_000 - 842_000) // 100
    assert kogaku_limit_o70(900_000, "現役2") == 167_400 + (900_000 - 558_000) // 100
    assert kogaku_limit_o70(900_000, "現役1") == 80_100 + (900_000 - 267_000) // 100


def test_o70_flat_gairai_vs_setai():
    assert kogaku_limit_o70(500_000, "一般", gairai_only=True) == 18_000
    assert kogaku_limit_o70(500_000, "一般", gairai_only=False) == 57_600
    assert kogaku_limit_o70(500_000, "低2", gairai_only=True) == 8_000
    assert kogaku_limit_o70(500_000, "低2", gairai_only=False) == 24_600
    assert kogaku_limit_o70(500_000, "低1", gairai_only=False) == 15_000


def test_o70_full_name_aliases():
    assert kogaku_limit_o70(500_000, "現役並みⅢ") == kogaku_limit_o70(500_000, "現役3")
    assert kogaku_limit_o70(500_000, "低所得Ⅱ", gairai_only=True) == 8_000


# ── dispatch by age ─────────────────────────────────────────────────────────
def test_dispatch_uses_age_to_pick_regime():
    # 70歳以上, 一般, 外来 → 18,000 個人上限
    assert kogaku_limit(500_000, "一般", age=80, gairai_only=True) == 18_000
    # 70歳未満 区分ウ
    assert kogaku_limit(1_000_000, "ウ", age=45) == 87_430
    # 無区分は None
    assert kogaku_limit(100_000, None, age=45) is None


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
