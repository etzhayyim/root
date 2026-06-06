"""test_charter_invariants.py — 系図 (keizu) structural-invariant drift-lock. ADR-2606066000.

Parses the THREE homes of each invariant (ontology :db/allowed/enum vectors · lexicon
:const/:enum · the seed values) and asserts they agree and carry no representable charter
violation. Touch one home without the others and this suite fails loudly.
"""
from __future__ import annotations

import pathlib

from _edn import load_edn
from _t import run
from weave import VERDICT_TOKENS

ROOT = pathlib.Path(__file__).resolve().parents[3]
ONT = ROOT / "00-contracts/schemas/government-relations-ontology.kotoba.edn"
LEXDIR = pathlib.Path(__file__).resolve().parents[1] / "lex"
SEED = pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-relation-graph.kotoba.edn"

PRIVATE_TOKENS = ("private-person", "individual", "citizen", "person", "natural-person")


def _ont():
    return load_edn(ONT)


def _datom(ident: str):
    for d in _ont()[":schema"]:
        if d.get(":db/ident") == ident:
            return d
    raise AssertionError(f"no schema datom {ident}")


def _lex(name: str):
    return load_edn(LEXDIR / f"{name}.edn")


def _props(name: str):
    return _lex(name)[":defs"][":main"][":record"][":properties"]


# ── ontology closed-vocab invariants ────────────────────────────────────────────
def test_ont_node_scopes_no_private():
    scopes = [s.lstrip(":") for s in _ont()[":ontology/node-scopes"]]
    for tok in PRIVATE_TOKENS:
        assert tok not in scopes, f"G1: {tok} must not be a node scope"


def test_ont_rel_kinds_no_verdict():
    kinds = [k.lstrip(":") for k in _ont()[":ontology/rel-kinds"]]
    for tok in VERDICT_TOKENS:
        assert tok not in kinds, f"G2: verdict {tok} must not be a rel kind"


def test_ont_money_kinds_no_verdict():
    kinds = [k.lstrip(":") for k in _ont()[":ontology/money-kinds"]]
    for tok in VERDICT_TOKENS:
        assert tok not in kinds, f"G2: verdict {tok} must not be a money kind"


def test_ont_post_status_dry_run_only():
    statuses = [s.lstrip(":") for s in _ont()[":ontology/post-statuses"]]
    assert statuses == ["dry-run"], f"G8: post status must be dry-run only, got {statuses}"


# ── ontology schema :db/allowed invariants ──────────────────────────────────────
def test_schema_scope_allowed():
    allowed = [s.lstrip(":") for s in _datom(":node/scope")[":db/allowed"]]
    for tok in PRIVATE_TOKENS:
        assert tok not in allowed


def test_schema_no_power_score_attr():
    idents = {d.get(":db/ident") for d in _ont()[":schema"]}
    for bad in (":node/power-score", ":node/influence", ":node/rank", ":node/score-of-soul"):
        assert bad not in idents, f"G4: {bad} must not exist"


def test_schema_rel_notice_true_only():
    assert _datom(":rel/non-adjudicating-notice")[":db/allowed"] == [True]


def test_schema_post_status_dry_run_only():
    assert [s.lstrip(":") for s in _datom(":post/status")[":db/allowed"]] == ["dry-run"]


def test_schema_post_server_key_false_only():
    assert _datom(":post/server-held-key")[":db/allowed"] == [False]


def test_schema_post_is_mirror_true_only():
    assert _datom(":post/is-mirror")[":db/allowed"] == [True]


# ── lexicon :enum/:const invariants ─────────────────────────────────────────────
def test_lex_rel_kind_no_verdict():
    enum = _props("relationEdge")[":kind"][":enum"]
    for tok in VERDICT_TOKENS:
        assert tok not in enum


def test_lex_rel_notice_const_true():
    assert _props("relationEdge")[":nonAdjudicatingNotice"][":const"] is True


def test_lex_rel_sources_min_two():
    assert _props("relationEdge")[":sources"][":minLength"] == 2


def test_lex_money_kind_no_verdict():
    enum = _props("moneyFlowObservation")[":kind"][":enum"]
    for tok in VERDICT_TOKENS:
        assert tok not in enum


def test_lex_money_sources_min_two():
    assert _props("moneyFlowObservation")[":sources"][":minLength"] == 2


def test_lex_post_status_const_dry_run():
    assert _props("networkPost")[":status"][":const"] == "dry-run"


def test_lex_post_is_mirror_const_true():
    assert _props("networkPost")[":isMirror"][":const"] is True


def test_lex_post_server_key_const_false():
    assert _props("networkPost")[":serverHeldKey"][":const"] is False


# ── seed value invariants ───────────────────────────────────────────────────────
def test_seed_nodes_public_scope():
    seed = load_edn(SEED)
    allowed = {s.lstrip(":") for s in _ont()[":ontology/node-scopes"]}
    for n in seed[":nodes"]:
        assert n[":node/scope"].lstrip(":") in allowed
        assert ":node/power-score" not in n


def test_seed_nodes_carry_no_pii():
    from weave import PII_FORBIDDEN_NODE_ATTRS
    assert PII_FORBIDDEN_NODE_ATTRS  # the closed no-doxxing set exists
    seed = load_edn(SEED)
    for n in seed[":nodes"]:
        for key in n:
            assert key.lstrip(":").split("/")[-1].lower() not in PII_FORBIDDEN_NODE_ATTRS, key


def test_seed_rels_two_sources_and_factual():
    seed = load_edn(SEED)
    kinds = {k.lstrip(":") for k in _ont()[":ontology/rel-kinds"]}
    for r in seed[":rels"]:
        assert len(r[":rel/sources"]) >= 2, r[":rel/id"]
        assert r[":rel/non-adjudicating-notice"] is True
        assert r[":rel/kind"].lstrip(":") in kinds


def test_seed_money_two_sources_and_factual():
    seed = load_edn(SEED)
    kinds = {k.lstrip(":") for k in _ont()[":ontology/money-kinds"]}
    for m in seed[":money"]:
        assert len(m[":money/sources"]) >= 2, m[":money/id"]
        assert m[":money/kind"].lstrip(":") in kinds


# ── lexicon ⊆ ontology drift-lock (BOTH directions) ─────────────────────────────
def test_lex_rel_kind_subset_of_ontology():
    enum = set(_props("relationEdge")[":kind"][":enum"])
    vocab = {k.lstrip(":") for k in _ont()[":ontology/rel-kinds"]}
    assert enum <= vocab, f"lexicon rel kinds not in ontology: {enum - vocab}"


def test_ontology_rel_kinds_all_in_lex():
    enum = set(_props("relationEdge")[":kind"][":enum"])
    vocab = {k.lstrip(":") for k in _ont()[":ontology/rel-kinds"]}
    assert vocab <= enum, f"ontology rel kinds missing from lexicon: {vocab - enum}"


def test_lex_money_kind_subset_of_ontology():
    enum = set(_props("moneyFlowObservation")[":kind"][":enum"])
    vocab = {k.lstrip(":") for k in _ont()[":ontology/money-kinds"]}
    assert enum <= vocab, f"lexicon money kinds not in ontology: {enum - vocab}"


def test_ontology_money_kinds_all_in_lex():
    enum = set(_props("moneyFlowObservation")[":kind"][":enum"])
    vocab = {k.lstrip(":") for k in _ont()[":ontology/money-kinds"]}
    assert vocab <= enum, f"ontology money kinds missing from lexicon: {vocab - enum}"


def test_lex_sourcing_matches_ontology_grades():
    grades = {g.lstrip(":") for g in _ont()[":ontology/sourcing-grades"]}
    for lx in ("relationEdge", "moneyFlowObservation", "committeeComposition"):
        enum = set(_props(lx)[":sourcing"][":enum"])
        assert enum == grades, f"{lx} sourcing {enum} != ontology grades {grades}"


def test_post_status_const_matches_ontology():
    statuses = {s.lstrip(":") for s in _ont()[":ontology/post-statuses"]}
    assert {_props("networkPost")[":status"][":const"]} == statuses


if __name__ == "__main__":
    run("charter-invariants", [(k, v) for k, v in sorted(globals().items())
                               if k.startswith("test_") and callable(v)])
