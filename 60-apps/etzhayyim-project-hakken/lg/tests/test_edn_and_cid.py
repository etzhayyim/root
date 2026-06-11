#!/usr/bin/env python3
"""hakken — EDN encoder + kotoba CID derivation tests (coverage loop iter 6).

These are the pure substrate-correctness functions behind hakken's writes to
the canonical kotoba Datom log: EDN tx-data encoding (what kotoba-server
parses) and content-address derivation (what makes the same graph label
resolve identically across nodes). 340+129 LoC, zero tests before this.

Run: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q
"""
import pathlib
import re
import sys

import pytest

PKG_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PKG_DIR))

from lg_hakken.edn import (  # noqa: E402
    EdnSymbol, kw, encode, tx_add, tx_retract,
    encode_tx_data, chunk_tx_data, entity_to_tx_ops,
)
from lg_hakken.kotoba_datomic import (  # noqa: E402
    kotoba_cid, graph_cid_for_label, parse_edn_value,
)


# ── edn.encode: every supported type + escaping ──────────────────────────────

def test_encode_scalars():
    assert encode(None) == "nil"
    assert encode(True) == "true"
    assert encode(False) == "false"
    assert encode(42) == "42"
    assert encode(-7) == "-7"
    assert encode(3.5) == "3.5"
    assert encode(kw("phase")) == ":phase"
    assert encode(EdnSymbol(":db/add")) == ":db/add"


def test_encode_string_escaping():
    assert encode("hi") == '"hi"'
    # backslash, quote, newline, CR, tab → EDN escapes
    assert encode('a\\b"c\nd\re\tf') == '"a\\\\b\\"c\\nd\\re\\tf"'


def test_encode_collections_and_map_keyword_keys():
    assert encode([1, 2, 3]) == "[1 2 3]"
    assert encode((1, "x")) == '[1 "x"]'
    assert encode({1, 2}).startswith("#{")
    # str map keys are promoted to keywords; EdnSymbol keys pass through
    assert encode({"phase": 1}) == "{:phase 1}"
    assert encode({EdnSymbol(":db/id"): 5}) == "{:db/id 5}"


def test_encode_rejects_unsupported_type():
    with pytest.raises(TypeError, match="unsupported EDN value"):
        encode(object())


def test_kw_normalizes_leading_colon():
    assert kw("phase") == ":phase"
    assert kw(":phase") == ":phase"
    assert kw("db/add") == ":db/add"


# ── tx-op builders ───────────────────────────────────────────────────────────

def test_tx_add_and_retract_attr_keywordization():
    assert encode(tx_add("e1", "kg/type", "product")) == '[:db/add "e1" :kg/type "product"]'
    # already-keyword attr is preserved, not double-colon'd
    assert encode(tx_add("e1", ":kg/type", "x")) == '[:db/add "e1" :kg/type "x"]'
    assert encode(tx_retract("e1", "kg/type", "x")) == '[:db/retract "e1" :kg/type "x"]'


def test_encode_tx_data_wraps_in_one_vector():
    ops = [tx_add("e1", "a", 1), tx_retract("e1", "a", 2)]
    assert encode_tx_data(ops) == '[[:db/add "e1" :a 1] [:db/retract "e1" :a 2]]'


# ── chunk_tx_data: the 1 MiB kotoba-server cap ──────────────────────────────

def test_chunk_single_when_small():
    ops = [tx_add("e", "a", i) for i in range(5)]
    chunks = chunk_tx_data(ops)
    assert len(chunks) == 1
    assert chunks[0] == encode_tx_data(ops)


def test_chunk_splits_at_byte_budget_and_loses_no_ops():
    ops = [tx_add(f"e{i}", "kg/note", "x" * 100) for i in range(200)]
    chunks = chunk_tx_data(ops, max_bytes=2_000)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c.encode("utf-8")) <= 2_000
    # every op is preserved exactly once across the chunks
    total_ops = sum(c.count(":db/add") for c in chunks)
    assert total_ops == 200


def test_chunk_oversized_single_op_still_emitted():
    # an op larger than max_bytes on its own must not be silently dropped
    big = [tx_add("e", "kg/blob", "z" * 5000)]
    chunks = chunk_tx_data(big, max_bytes=1000)
    assert len(chunks) == 1
    assert ":db/add" in chunks[0]


# ── entity_to_tx_ops ─────────────────────────────────────────────────────────

def test_entity_to_tx_ops_full_shape():
    ops = entity_to_tx_ops({
        "id": "prod:1",
        "type": "product",
        "labelJa": "製品",
        "labelEn": "Product",
        "claims": [{"pred": "price", "value": 1980}],
        "relations": [{"pred": "supplier", "dstId": "sup:9"}],
    })
    encoded = [encode(o) for o in ops]
    assert encoded[0] == '[:db/add "prod:1" :kg/id "prod:1"]'
    assert '[:db/add "prod:1" :kg/type "product"]' in encoded
    assert '[:db/add "prod:1" :kg/labelJa "製品"]' in encoded
    assert '[:db/add "prod:1" :kg/claim/price 1980]' in encoded
    assert '[:db/add "prod:1" :kg/relation/supplier "sup:9"]' in encoded


def test_entity_to_tx_ops_minimal_is_just_ident():
    ops = entity_to_tx_ops({"id": "x"})
    assert len(ops) == 1
    assert encode(ops[0]) == '[:db/add "x" :kg/id "x"]'


# ── kotoba CID derivation (content-addressing correctness) ───────────────────

CIDV1_RE = re.compile(r"^b[a-z2-7]+$")


def test_kotoba_cid_is_cidv1_dagcbor_sha256_multibase_b():
    cid = kotoba_cid(b"hello")
    assert CIDV1_RE.match(cid)
    # deterministic
    assert kotoba_cid(b"hello") == cid
    assert kotoba_cid(b"world") != cid


def test_graph_cid_for_label_is_stable_and_distinct():
    a = graph_cid_for_label("kotobase-kg-v1")
    assert a == graph_cid_for_label("kotobase-kg-v1")
    assert a != graph_cid_for_label("other-label")
    assert CIDV1_RE.match(a)


def test_graph_cid_passthrough_for_existing_cid():
    # a string already shaped like a multibase CID is returned unchanged
    existing = "b" + "a" * 59
    assert re.fullmatch(r"b[a-z2-7]{58,80}", existing)
    assert graph_cid_for_label(existing) == existing


# ── parse_edn_value: server row scalar decode ────────────────────────────────

@pytest.mark.parametrize("raw, expected", [
    ('"hello"', "hello"),
    (r'"a\"b"', 'a"b'),
    (r'"a\\b"', "a\\b"),
    ("true", True),
    ("false", False),
    ("nil", None),
    ("42", 42),
    ("-7", -7),
    ("3.5", 3.5),
    ("-2.0e3", -2000.0),
    (":kw", ":kw"),          # keywords pass through as strings
    ("unparseable", "unparseable"),
])
def test_parse_edn_value(raw, expected):
    assert parse_edn_value(raw) == expected
