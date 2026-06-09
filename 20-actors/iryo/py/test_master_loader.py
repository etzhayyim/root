#!/usr/bin/env python3
"""iryo 医療 — master ingestion tests (全件対応の鍵: 公式/正規化マスタの取り込み)."""
import os
import tempfile

from master_loader import (ColMap, load_mhlw_shinryo, load_normalized,
                           masters_with_official)
from masters import Masters


def _write(d, name, text):
    with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
        fh.write(text)


def test_load_normalized_all_classes():
    with tempfile.TemporaryDirectory() as d:
        _write(d, "shinryo.csv", "# code,name,ten,shikibetsu\n999999910,新規診療行為,123,60\n")
        _write(d, "iyaku.csv", "999999920,新規薬剤,30.0,錠\n")
        _write(d, "shobyo.csv", "9999999,新規病名,Z999\n")
        _write(d, "shushokugo.csv", "9001,新規修飾語\n")
        _write(d, "comment.csv", "899999999,free,新規コメント\n")
        m = Masters.from_dict(load_normalized(d))
        assert m.shinryo("999999910").ten == 123
        assert m.shinryo("999999910").shikibetsu == "60"
        assert m.drug("999999920").yakka == 30.0
        assert m.shobyo("9999999").icd10 == "Z999"
        assert m.shushokugo("9001").name == "新規修飾語"
        assert m.comment("899999999").name == "新規コメント"


def test_official_master_merges_over_seed():
    # Loading an official/normalized master adds codes the seed never had → "全件対応".
    with tempfile.TemporaryDirectory() as d:
        _write(d, "shinryo.csv", "888888810,特殊手技,9999,50\n")
        merged = masters_with_official(d, fmt="normalized")
        # seed code still present
        assert merged.shinryo("111000110").ten == 291
        # newly loaded code now resolvable
        assert merged.shinryo("888888810").ten == 9999
        assert merged.counts()["shinryo"] >= 2


def test_mhlw_colmap_parse_tolerant():
    # A synthetic MHLW-style row: code at col 2, name at col 4, ten at col 22, shikibetsu col 8.
    row = ["1", "S", "777777710"] + [""] + ["手技名"] + [""] * 3 + ["60"] + [""] * 13 + ["456"]
    with tempfile.TemporaryDirectory() as d:
        _write(d, "s_test.csv", ",".join(row) + "\n")
        out = load_mhlw_shinryo(os.path.join(d, "s_test.csv"),
                                ColMap(code=2, name=4, value=22, shikibetsu=8))
        assert out["777777710"]["ten"] == 456
        assert out["777777710"]["shikibetsu"] == "60"


def test_merge_does_not_mutate_base():
    base = Masters.load()
    n0 = base.counts()["shinryo"]
    other = Masters.from_dict({"shinryo": {"000000010": {"name": "x", "ten": 1,
                                                         "shikibetsu": "80"}}})
    base.merge(other)
    assert base.counts()["shinryo"] == n0  # base unchanged


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
