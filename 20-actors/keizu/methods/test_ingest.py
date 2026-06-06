"""test_ingest.py — 系図 (keizu) offline normalizer + G8 live refusal. ADR-2606066000."""
from __future__ import annotations

import os

from _t import expect_raises, run
from ingest import (ingest_live, normalize_batch, normalize_committee,
                    normalize_money, normalize_rel)


def test_normalize_committee():
    c = normalize_committee({"id": "c1", "label": "x", "jurisdiction": "jp", "organ": "m",
                             "members": ["s1", "s2"], "term_from": 20250101,
                             "sources": ["https://x.gov/"]})
    assert c[":committee/members"] == ["s1", "s2"]
    assert c[":committee/sourcing"] == ":representative"


def test_committee_needs_members():
    expect_raises(lambda: normalize_committee({"id": "c1", "members": [], "sources": ["u"]}),
                  contains="G1")


def test_committee_needs_source():
    expect_raises(lambda: normalize_committee({"id": "c1", "members": ["s1"], "sources": []}),
                  contains="G3")


def test_normalize_rel_validates():
    r = normalize_rel({"id": "r1", "source": "a", "target": "b", "kind": "funding-tie",
                       "as_of": 20250101, "sources": ["u1", "u2"]})
    assert r[":rel/non-adjudicating-notice"] is True


def test_normalize_rel_rejects_verdict():
    expect_raises(lambda: normalize_rel({"id": "r1", "source": "a", "target": "b",
                                         "kind": "bribe", "sources": ["u1", "u2"]}),
                  contains="G2")


def test_normalize_money_validates():
    m = normalize_money({"id": "m1", "payer": "a", "payee": "b", "kind": "subsidy",
                         "amount": 1.0, "currency": "JPY", "sources": ["u1", "u2"]})
    assert m[":money/kind"] == ":subsidy"


def test_batch():
    out = normalize_batch({
        "committees": [{"id": "c1", "members": ["s1"], "sources": ["u"]}],
        "rels": [{"id": "r1", "source": "s1", "target": "c1", "kind": "committee-membership",
                  "sources": ["u1", "u2"]}],
        "money": [{"id": "m1", "payer": "m", "payee": "s1", "kind": "procurement-award",
                   "amount": 1.0, "currency": "JPY", "sources": ["u1", "u2"]}],
    })
    assert len(out["committees"]) == 1 and len(out["rels"]) == 1 and len(out["money"]) == 1


def test_g8_live_refused_without_gate():
    os.environ.pop("KEIZU_ALLOW_LIVE", None)
    expect_raises(lambda: ingest_live(), contains="G8")


def test_g8_live_refused_even_with_gate():
    os.environ["KEIZU_ALLOW_LIVE"] = "1"
    try:
        expect_raises(lambda: ingest_live(), contains="not wired")
    finally:
        os.environ.pop("KEIZU_ALLOW_LIVE", None)


if __name__ == "__main__":
    run("ingest", [(k, v) for k, v in sorted(globals().items())
                   if k.startswith("test_") and callable(v)])
