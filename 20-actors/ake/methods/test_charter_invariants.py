#!/usr/bin/env python3
"""Structural charter-invariant tests for 朱 (ake) — ADR-2606052100.

Assert the invariants STRUCTURALLY over the parsed ontology / lexicons / code constants — not by
grepping prose. A regression here means an invariant was weakened: 信者-gated + no-server-key (G1),
LLM-non-adjudicating (G2), mirror-preserving (G3), sourcing-mandatory (G4), append-only (G5),
invariant-lock (G7), outward-gated (G8).
"""
from __future__ import annotations

import pathlib

from _edn import load_edn

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_LEX = _ROOT / "lex"
_ONTOLOGY = _ROOT.parents[1] / "00-contracts" / "schemas" / "community-edit-ontology.kotoba.edn"


def _onto():
    return load_edn(_ONTOLOGY)


def _props(lex_name: str) -> dict:
    d = load_edn(_LEX / f"{lex_name}.edn")
    return d[":defs"][":main"][":record"][":properties"]


def _required(lex_name: str) -> list:
    d = load_edn(_LEX / f"{lex_name}.edn")
    return d[":defs"][":main"][":record"][":required"]


# ── G3 mirror-preserving: only facts/profiles, never speech-as-entity ───────────
def test_ontology_target_kinds_exclude_impersonation():
    tk = _onto()[":ontology/target-kinds"]
    assert tk == [":kg-fact", ":actor-profile"]
    for forbidden in (":entity-speech", ":impersonate", ":speak-as-entity"):
        assert forbidden not in tk


def test_lexicon_target_kind_enum_excludes_impersonation():
    enum = set(_props("editProposal")[":targetKind"].get(":enum", []))
    assert enum == {"kg-fact", "actor-profile"}
    assert enum.isdisjoint({"entity-speech", "impersonate", "speak-as-entity"})


# ── G5 append-only: no delete / overwrite anywhere ──────────────────────────────
def test_ontology_edit_ops_are_append_only():
    ops = _onto()[":ontology/edit-ops"]
    assert ":delete" not in ops and ":overwrite" not in ops


def test_lexicon_op_enums_exclude_delete_overwrite():
    for lex, prop in (("editProposal", ":op"), ("revisionEntry", ":op")):
        enum = set(_props(lex)[prop].get(":enum", []))
        assert enum.isdisjoint({"delete", "overwrite"})


# ── G1 信者-gated + no-server-key ───────────────────────────────────────────────
def test_ontology_author_kinds_member_only():
    ak = _onto()[":ontology/author-kinds"]
    assert ak == [":member"]
    assert ":server" not in ak and ":anon" not in ak


def test_proposal_author_kind_const_member():
    assert _props("editProposal")[":authorKind"].get(":const") == "member"


def test_proposal_server_held_key_const_false():
    assert _props("editProposal")[":serverHeldKey"].get(":const") is False


def test_promotion_server_held_key_const_false():
    assert _props("editPromotion")[":serverHeldKey"].get(":const") is False


# ── G4 sourcing-mandatory ───────────────────────────────────────────────────────
def test_proposal_requires_provenance():
    assert "provenance" in _required("editProposal")


# ── G2 LLM non-adjudicating: triage has NO decision field ───────────────────────
def test_triage_lexicon_has_no_decision_field():
    props = _props("editTriage")
    assert ":decision" not in props
    assert not any("decision" in str(k).lower() for k in props)


def test_triage_route_enum_has_no_bare_accept_reject():
    enum = set(_props("editTriage")[":route"].get(":enum", []))
    # 'auto-accept' is a ROUTE (the optimistic rule), but a bare 'accept'/'reject' verdict is not
    assert "accept" not in enum and "reject" not in enum
    assert enum == {"auto-accept", "vote", "council-lv7", "refused"}


def test_ontology_schema_has_no_triage_decision_ident():
    idents = {m.get(":db/ident") for m in _onto()[":schema"] if isinstance(m, dict)}
    assert ":triage/decision" not in idents


# ── G8 outward-gated: R0 promotion never publishes ──────────────────────────────
def test_promotion_published_const_false():
    assert _props("editPromotion")[":published"].get(":const") is False


# ── G7 invariant-lock: Council review is Lv7 ────────────────────────────────────
def test_council_review_level_const_lv7():
    assert _props("councilEditReview")[":level"].get(":const") == "Lv7"


# ── code constants agree with the ontology (single source of truth) ─────────────
def test_code_route_table_matches_ontology():
    from triage import ROUTES
    onto_routes = {r.lstrip(":") for r in _onto()[":ontology/triage-routes"]}
    assert set(ROUTES) == onto_routes


def test_code_invariant_attrs_block_optimistic_accept():
    from triage import route_for
    # a license/charter edit can never auto-accept, regardless of quality
    assert route_for("invariant", 1.0, "") == "council-lv7"


if __name__ == "__main__":
    import sys
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"{len(fns) - failed}/{len(fns)} passed in test_charter_invariants.py")
    sys.exit(1 if failed else 0)
