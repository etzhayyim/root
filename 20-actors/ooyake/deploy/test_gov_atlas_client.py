#!/usr/bin/env python3
"""Tests for the shared gov-atlas read client (ADR-2606021600).

Run: python3 test_gov_atlas_client.py   (or pytest)
Asserts against the committed registry seeds (curated core).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gov_atlas_client import GovAtlas  # noqa: E402

A = GovAtlas()


def test_get_unit():
    u = A.get_unit("gov.jpn.mof")
    assert u and u[":gov.unit/name-local"] == "財務省"
    assert A.get_unit("gov.nonexistent") is None


def test_resolve_path():
    chain = A.resolve_path("gov.jpn.mof.nta.tokyo.kojimachi")
    ids = [u[":gov.unit/id"] for u in chain]
    assert ids == ["gov.jpn", "gov.jpn.mof", "gov.jpn.mof.nta",
                   "gov.jpn.mof.nta.tokyo", "gov.jpn.mof.nta.tokyo.kojimachi"], ids


def test_children():
    kids = {u[":gov.unit/id"] for u in A.children("gov.jpn")}
    # 財務省 + the JP-central ministries are direct children of gov.jpn
    assert "gov.jpn.mof" in kids and "gov.jpn.cao" in kids


def test_facets():
    assert any(u[":gov.unit/id"] == "gov.jpn.mof" for u in A.by_level("ministry"))
    jp = A.by_jurisdiction("jpn")
    assert len(jp) >= 20  # base + JP central
    assert all((u.get(":gov.unit/jurisdiction") or "").startswith("jpn") for u in jp)


def test_search():
    hits = {u[":gov.unit/id"] for u in A.search("財務")}
    assert "gov.jpn.mof" in hits


def test_resolve_procedure():
    r = A.resolve_procedure("jp-juminhyo-utsushi")
    assert r and r["owner"]["name"] == "新宿区"
    assert r["windows"][0]["resolved"] and "戸籍住民課" in r["windows"][0]["name"]
    assert r["forms"][0]["chigiriRef"] == "chigiri:gov:jp-juminhyo:v0"
    assert A.resolve_procedure("nope") is None


def test_find_service():
    res = A.find_service("住民票")
    assert res and res[0]["owner"]["name"] == "新宿区"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print(f"PASS {fn.__name__}")
    print(f"{len(fns)} passed")
