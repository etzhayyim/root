"""Tests for the docs GitOffice edge adapter (blob <-> :block/* datoms).

Includes a PARITY fixture identical to the reference gitoffice.cljc /
kotoba.gitoffice tests, so the three implementations cannot drift apart silently.
"""

from lg_docs import gitoffice_normalize as gn


SAMPLE_BODY = [
    {"elementId": "el0", "kind": "heading", "headingLevel": 1, "text": "概要"},
    {"elementId": "el1", "kind": "paragraph", "text": "原材料費が上昇した。"},
    {"elementId": "el2", "kind": "listItem", "text": "項目A"},
    {"elementId": "el3", "kind": "paragraph", "text": ""},
]


def test_body_roundtrip_identity():
    ops = gn.body_to_block_ops("doc1", SAMPLE_BODY)
    rows = gn.ops_to_rows(ops)
    assert gn.blocks_to_body(rows, "doc1") == SAMPLE_BODY


def test_normalize_is_idempotent():
    ops1 = gn.body_to_block_ops("doc1", SAMPLE_BODY)
    body2 = gn.blocks_to_body(gn.ops_to_rows(ops1), "doc1")
    ops2 = gn.body_to_block_ops("doc1", body2)
    assert gn.ops_to_rows(ops1) == gn.ops_to_rows(ops2)  # stable elementId-keyed


def test_blocks_are_children_of_doc():
    ops = gn.body_to_block_ops("doc1", SAMPLE_BODY)
    rows = gn.ops_to_rows(ops)
    parents = {e: v for (e, a, v) in rows if gn._bare(a) == "block/parent"}
    assert parents == {"el0": "doc1", "el1": "doc1", "el2": "doc1", "el3": "doc1"}


def test_heading_level_only_where_present():
    ops = gn.body_to_block_ops("doc1", SAMPLE_BODY)
    rows = gn.ops_to_rows(ops)
    hl = {e: v for (e, a, v) in rows if gn._bare(a) == "block/heading-level"}
    assert hl == {"el0": 1}


# --- fractional indexing parity with the .cljc reference --------------------

def test_orders_strictly_increasing_and_distinct():
    ks = gn.initial_orders(50)
    assert len(ks) == 50
    assert ks == sorted(ks)
    assert len(set(ks)) == 50


def test_order_between_inserts():
    a, b = gn.initial_orders(2)
    mid = gn.order_between(a, b)
    assert a < mid < b
    # repeated head-insert stays ordered
    k1 = gn.order_between(None, a)
    k2 = gn.order_between(None, k1)
    assert k2 < k1 < a


def test_first_order_matches_cljc():
    # gitoffice.cljc initial-orders: first key is the base-36 midpoint of (0,1) = 'i' (18)
    assert gn.initial_orders(1)[0] == "i"


def test_order_between_rejects_noncanonical():
    import pytest
    with pytest.raises(ValueError):
        gn.order_between("1", "10")   # trailing-zero upper bound
    with pytest.raises(ValueError):
        gn.order_between("10", None)  # trailing-zero lower bound
    with pytest.raises(ValueError):
        gn.order_between("", "")      # empty upper bound
    with pytest.raises(ValueError):
        gn.order_between("b", "a")    # non-ascending
    # canonical shared-prefix keys still work
    k = gn.order_between("1", "11")
    assert "1" < k < "11"


def test_blocks_to_body_tiebreaks_on_id():
    # two blocks with the SAME order key (concurrent inserts) -> deterministic by id
    rows = [
        ("zb", ":block/parent", "doc"), ("zb", ":block/kind", ":block/paragraph"),
        ("zb", ":block/order", "i"), ("zb", ":block/text", "B"),
        ("ya", ":block/parent", "doc"), ("ya", ":block/kind", ":block/paragraph"),
        ("ya", ":block/order", "i"), ("ya", ":block/text", "A"),
    ]
    body = gn.blocks_to_body(rows, "doc")
    assert [e["elementId"] for e in body] == ["ya", "zb"]  # id tie-break, stable
