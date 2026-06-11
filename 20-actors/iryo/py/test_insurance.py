#!/usr/bin/env python3
"""iryo 医療 — 年齢区分 / 負担割合 / 負担区分 tests."""
from insurance import (age_kubun, futan_kubun, futan_wari, kyufu_wari)


def test_age_kubun():
    assert age_kubun(3) == "乳幼児"
    assert age_kubun(40) == "成人"
    assert age_kubun(72) == "前期高齢"
    assert age_kubun(80) == "後期高齢"


def test_futan_wari_by_age():
    assert futan_wari(3) == 0.2        # 6歳未満
    assert futan_wari(40) == 0.3       # 成人
    assert futan_wari(72) == 0.2       # 前期高齢 一般
    assert futan_wari(72, gen_eki=True) == 0.3
    assert futan_wari(80) == 0.1       # 後期高齢 一般
    assert futan_wari(80, ittei_ijo=True) == 0.2
    assert futan_wari(80, gen_eki=True) == 0.3


def test_futan_kubun_codes():
    assert futan_kubun(0) == "1"       # 保険単独
    assert futan_kubun(1) == "2"       # 保険+第1公費
    assert futan_kubun(2) == "3"       # 保険+第1+第2公費
    assert futan_kubun(1, hoken=False) == "5"  # 公費単独


def test_kyufu_wari():
    assert kyufu_wari(0.3) == 7
    assert kyufu_wari(0.2) == 8
    assert kyufu_wari(0.1) == 9
    assert kyufu_wari(0.0) == 10


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
