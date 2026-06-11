"""test_integrity.py — the integrity ruleset REJECTS non-conforming data (integrity-zome stance)."""
from __future__ import annotations

import integrity as ig
from _t import expect_raises, run

RULES = {
    ":integrity/spec": "kotoba-integrity/v0",
    ":integrity/graph": "ibuki",
    ":integrity/append-only": True,
    ":integrity/closed-attrs": [":joucho/mood", ":heartbeat/beat", ":organism/niche"],
    ":integrity/required-attrs": {":organism": [":organism/niche"]},
    ":integrity/attr-types": {":joucho/mood": "keyword", ":heartbeat/beat": "int"},
    ":integrity/deny-attrs": [":published"],
}


def test_validation_cid_is_deterministic():
    assert ig.validation_cid(RULES) == ig.validation_cid(dict(RULES))
    assert ig.validation_cid(RULES).startswith("bafkrei")


def test_conforming_datoms_pass():
    ok, v = ig.validate([
        (":db/add", "o1", ":organism/niche", ":producer"),
        (":db/add", "o1", ":joucho/mood", ":flourishing"),
        (":db/add", "o1", ":heartbeat/beat", 7),
    ], RULES, graph="ibuki")
    assert ok and v == []


def test_append_only_is_enforced():
    ok, v = ig.validate([(":db/retract", "o1", ":joucho/mood", ":x")], RULES)
    assert not ok and any("append-only" in m for m in v)


def test_denied_attribute_is_structurally_forbidden():
    ok, v = ig.validate([(":db/add", "o1", ":published", True)], RULES)
    assert not ok and any("structurally forbidden" in m for m in v)


def test_closed_vocabulary_rejects_unknown_attr():
    ok, v = ig.validate([(":db/add", "o1", ":mystery/attr", 1)], RULES)
    assert not ok and any("closed vocabulary" in m for m in v)


def test_attr_type_is_checked():
    ok, v = ig.validate([(":db/add", "o1", ":heartbeat/beat", "seven")], RULES)
    assert not ok and any("is not a int" in m for m in v)
    ok2, v2 = ig.validate([(":db/add", "o1", ":joucho/mood", "flourishing")], RULES)  # not a keyword
    assert not ok2 and any("is not a keyword" in m for m in v2)


def test_required_attrs_for_an_entity_tag():
    # asserts a :organism/* attr but omits the required :organism/niche
    ok, v = ig.validate([(":db/add", "o9", ":organism/niche", ":router")], RULES)
    assert ok, v  # niche present → fine
    ok2, v2 = ig.validate([
        (":db/add", "o9", ":joucho/mood", ":neutral"),     # no :organism/* attr → rule not triggered
    ], RULES)
    assert ok2, v2


def test_graph_mismatch_is_rejected():
    ok, v = ig.validate([(":db/add", "o1", ":joucho/mood", ":neutral")], RULES, graph="other-graph")
    assert not ok and any("ruleset-bound graph" in m for m in v)


def test_malformed_datom_is_caught():
    ok, v = ig.validate([("just", "three")], RULES)
    assert not ok and any("not a 4-tuple" in m for m in v)


def test_rules_edn_rejects_unknown_key_and_bad_spec():
    expect_raises(lambda: ig.rules_edn({**RULES, ":integrity/rogue": 1}), contains="unknown keys")
    expect_raises(lambda: ig.rules_edn({":integrity/spec": "wrong"}), contains="spec must be")


if __name__ == "__main__":
    run("integrity", [(n, f) for n, f in sorted(globals().items())
                      if n.startswith("test_") and callable(f)])
