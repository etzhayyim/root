"""test_bridge.py — 系図 (keizu) cross-actor compose (danjo + kanae). ADR-2606066000."""
from __future__ import annotations

from _t import expect_raises, run
from bridge import bridge_batch, bridge_danjo_crossref, bridge_kanae_flow

_KANAE_OK = {"id": "f1", "flowType": "appropriation", "donor": "jp-mof", "recipient": "jp-meti",
             "amount": 1.0e9, "currency": "JPY", "asOf": 20250401,
             "sources": ["https://a.gov/", "https://b.gov/"]}
_DANJO_OK = {"id": "x1", "linkType": "awardee-officer-ubo-link", "from": "jp-vendor-x",
             "to": "jp-fsc-biz-1", "sourceRecordCids": ["cid:a", "cid:b"]}


def test_kanae_flow_maps_to_money():
    m = bridge_kanae_flow(_KANAE_OK)
    assert m[":money/kind"] == ":budget-outlay"
    assert m[":money/payer"] == "jp-mof" and m[":money/payee"] == "jp-meti"
    assert m[":money/id"].startswith("kanae:")


def test_kanae_unknown_flowtype_refused():
    bad = dict(_KANAE_OK, flowType="mystery")
    expect_raises(lambda: bridge_kanae_flow(bad), contains="unknown kanae flowType")


def test_kanae_under_sourced_refused_by_keizu_gate():
    bad = dict(_KANAE_OK, sources=["only-one"])
    expect_raises(lambda: bridge_kanae_flow(bad), contains="G3")


def test_danjo_crossref_maps_to_rel():
    r = bridge_danjo_crossref(_DANJO_OK)
    assert r[":rel/kind"] == ":co-membership"
    assert r[":rel/non-adjudicating-notice"] is True
    assert r[":rel/id"].startswith("danjo:")


def test_danjo_verdict_category_refused_at_import():
    bad = dict(_DANJO_OK, linkType="corruption")
    expect_raises(lambda: bridge_danjo_crossref(bad), contains="verdict")


def test_danjo_unmapped_linktype_refused():
    bad = dict(_DANJO_OK, linkType="some-new-thing")
    expect_raises(lambda: bridge_danjo_crossref(bad), contains="unmapped")


def test_danjo_under_sourced_refused():
    bad = dict(_DANJO_OK, sourceRecordCids=["only-one"])
    expect_raises(lambda: bridge_danjo_crossref(bad), contains="G3")


def test_batch_composes_both():
    out = bridge_batch({"kanae": [_KANAE_OK], "danjo": [_DANJO_OK]})
    assert len(out["money"]) == 1 and len(out["rels"]) == 1


def test_batch_fails_whole_on_one_violation():
    # a single bad record aborts the batch — no partial smuggling
    expect_raises(lambda: bridge_batch({"danjo": [_DANJO_OK, dict(_DANJO_OK, linkType="bribe")]}),
                  contains="verdict")


def test_bridged_records_weave_clean():
    # the bridged datoms must pass the SAME validation the seed does
    from weave import validate_money, validate_rel
    out = bridge_batch({"kanae": [_KANAE_OK], "danjo": [_DANJO_OK]})
    validate_money(out["money"][0])
    validate_rel(out["rels"][0])


if __name__ == "__main__":
    run("bridge", [(k, v) for k, v in sorted(globals().items())
                   if k.startswith("test_") and callable(v)])
