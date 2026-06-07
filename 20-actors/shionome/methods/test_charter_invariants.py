"""test_charter_invariants.py — 潮目 (shionome) THREE-PLACE invariant consistency. ADR-2606072200.

Every structural invariant lives in three homes: the ontology `:db/allowed` / closed-vocab
vectors, the lexicon `:const` / `:enum`, and the Python `weave` constants + validators. This
suite parses all three and asserts they AGREE — so adding a trade-bearing flow kind, a private
bucket scope, a per-bucket rating, or a `:published` post status in ONE place (and not the
others) FAILS here. This is the actor's charter tripwire. Standalone.
"""
from __future__ import annotations

import pathlib

from _edn import load_edn
from _t import run
from weave import BUCKET_SCOPES, FLOW_KINDS, SNAPSHOT_METRICS, TRADE_TOKENS

ROOT = pathlib.Path(__file__).resolve().parents[3]
ACTOR = pathlib.Path(__file__).resolve().parents[1]
ONTO = ROOT / "00-contracts" / "schemas" / "capital-flow-ontology.kotoba.edn"
LEX = ACTOR / "lex"


def _onto():
    return load_edn(ONTO)


def _bare(seq):
    return tuple(str(x).lstrip(":") for x in seq)


# ── ontology ↔ python vocab agreement ───────────────────────────────────────────
def test_bucket_scopes_agree():
    assert _bare(_onto()[":ontology/bucket-scopes"]) == BUCKET_SCOPES


def test_flow_kinds_agree():
    assert _bare(_onto()[":ontology/flow-kinds"]) == FLOW_KINDS


def test_snapshot_metrics_agree():
    assert _bare(_onto()[":ontology/snapshot-metrics"]) == SNAPSHOT_METRICS


# ── no-trade invariant (G2 / トレードはしない) ──────────────────────────────────
def test_no_trade_token_in_ontology_flow_kinds():
    for k in _bare(_onto()[":ontology/flow-kinds"]):
        for t in TRADE_TOKENS:
            assert t not in k, f"trade token {t!r} leaked into flow kind {k!r}"


def test_no_person_scope_in_ontology():
    forbidden = {"individual", "person", "account", "portfolio", "trader", "investor"}
    assert not (set(_bare(_onto()[":ontology/bucket-scopes"])) & forbidden)


# ── G8 — post statuses are dry-run only (published unrepresentable) ───────────────
def test_post_statuses_dry_run_only():
    assert _bare(_onto()[":ontology/post-statuses"]) == ("dry-run",)


# ── G4 — ontology declares NO per-bucket rating/signal/target/score attr ──────────
def test_ontology_has_no_bucket_score_attr():
    idents = {str(d.get(":db/ident")) for d in _onto()[":schema"]}
    for forbidden in (":bucket/rating", ":bucket/signal", ":bucket/target",
                      ":bucket/score", ":bucket/recommendation"):
        assert forbidden not in idents


# ── lexicon consistency ──────────────────────────────────────────────────────────
def _lex(name):
    return load_edn(LEX / name)


def test_networkpost_status_const_dry_run():
    lex = _lex("networkPost.edn")
    props = lex[":defs"][":main"][":record"][":properties"]
    assert props[":status"][":const"] == "dry-run"


def test_networkpost_is_mirror_const_true():
    props = _lex("networkPost.edn")[":defs"][":main"][":record"][":properties"]
    assert props[":isMirror"][":const"] is True


def test_networkpost_no_trade_const_true():
    props = _lex("networkPost.edn")[":defs"][":main"][":record"][":properties"]
    assert props[":noTradeNotice"][":const"] is True


def test_networkpost_server_held_key_const_false():
    props = _lex("networkPost.edn")[":defs"][":main"][":record"][":properties"]
    assert props[":serverHeldKey"][":const"] is False


def test_capitalflow_kind_enum_matches_flow_kinds():
    props = _lex("capitalFlowObservation.edn")[":defs"][":main"][":record"][":properties"]
    assert tuple(props[":kind"][":enum"]) == FLOW_KINDS


def test_capitalflow_no_trade_token_in_enum():
    props = _lex("capitalFlowObservation.edn")[":defs"][":main"][":record"][":properties"]
    for k in props[":kind"][":enum"]:
        for t in TRADE_TOKENS:
            assert t not in k


def test_capitalflow_no_trade_notice_const():
    props = _lex("capitalFlowObservation.edn")[":defs"][":main"][":record"][":properties"]
    assert props[":noTradeNotice"][":const"] is True


def test_capitalflow_sources_min_two():
    props = _lex("capitalFlowObservation.edn")[":defs"][":main"][":record"][":properties"]
    assert props[":sources"][":minLength"] == 2


def test_bucketsnapshot_metric_enum_matches():
    props = _lex("bucketSnapshot.edn")[":defs"][":main"][":record"][":properties"]
    assert tuple(props[":metric"][":enum"]) == SNAPSHOT_METRICS


def test_rotationfinding_no_trade_const():
    props = _lex("rotationFinding.edn")[":defs"][":main"][":record"][":properties"]
    assert props[":noTradeNotice"][":const"] is True


def test_all_four_lexicons_present():
    for n in ("capitalFlowObservation.edn", "bucketSnapshot.edn", "rotationFinding.edn", "networkPost.edn"):
        assert (LEX / n).exists()


if __name__ == "__main__":
    run("charter-invariants", [(n, f) for n, f in sorted(globals().items())
                               if n.startswith("test_") and callable(f)])
