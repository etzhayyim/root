"""test_charter_invariants.py — 高札 (kosatsu) structural-invariant drift-lock. ADR-2606072000.

Parses the THREE homes of each invariant (ontology :db/allowed/enum vectors · lexicon
:const/:enum · the seed values) and asserts they agree and carry no representable charter
violation. Touch one home without the others and this suite fails loudly.
"""
from __future__ import annotations

import pathlib

from _edn import load_edn
from _t import run
from weave import VERDICT_TOKENS, SELF_TOKENS

ROOT = pathlib.Path(__file__).resolve().parents[3]
ONT = ROOT / "00-contracts/schemas/crime-sanctions-ontology.kotoba.edn"
LEXDIR = pathlib.Path(__file__).resolve().parents[1] / "lex"
SEED = pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-designation-graph.kotoba.edn"


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
def test_ont_authority_kinds_no_self():
    kinds = [k.lstrip(":") for k in _ont()[":ontology/authority-kinds"]]
    for tok in SELF_TOKENS:
        assert tok not in kinds, f"G1: etzhayyim/self {tok} must not be an authority kind"


def test_ont_measure_kinds_no_verdict():
    kinds = [k.lstrip(":") for k in _ont()[":ontology/measure-kinds"]]
    for tok in VERDICT_TOKENS:
        assert tok not in kinds, f"G2/G3: verdict {tok} must not be a measure kind"


def test_ont_status_no_final_or_verdict():
    statuses = [s.lstrip(":") for s in _ont()[":ontology/designation-status"]]
    assert set(statuses) == {"listed", "delisted"}, statuses
    for tok in ("guilty", "convicted", "permanent", "final"):
        assert tok not in statuses, f"G4: {tok} must not be a status (非終末論)"


def test_ont_post_status_dry_run_only():
    statuses = [s.lstrip(":") for s in _ont()[":ontology/post-statuses"]]
    assert statuses == ["dry-run"], f"G8: post status must be dry-run only, got {statuses}"


def test_ont_divergence_classes():
    cls = {c.lstrip(":") for c in _ont()[":ontology/divergence-classes"]}
    assert cls == {"unanimous", "contested", "single-asserter"}, cls


# ── ontology schema :db/allowed invariants ──────────────────────────────────────
def test_schema_authority_kind_no_self():
    allowed = [s.lstrip(":") for s in _datom(":authority/kind")[":db/allowed"]]
    for tok in SELF_TOKENS:
        assert tok not in allowed


def test_schema_measure_no_verdict():
    allowed = [s.lstrip(":") for s in _datom(":designation/measure")[":db/allowed"]]
    for tok in VERDICT_TOKENS:
        assert tok not in allowed


def test_schema_status_listed_delisted_only():
    assert [s.lstrip(":") for s in _datom(":designation/status")[":db/allowed"]] == ["listed", "delisted"]


def test_schema_asserted_notice_true_only():
    assert _datom(":designation/asserted-notice")[":db/allowed"] == [True]


def test_schema_no_subject_score_attr():
    idents = {d.get(":db/ident") for d in _ont()[":schema"]}
    for bad in (":subject/risk-score", ":subject/guilt", ":subject/threat-level", ":subject/rank"):
        assert bad not in idents, f"G2/G7: {bad} must not exist (we never rate a subject)"


def test_schema_no_self_designation_attr():
    idents = {d.get(":db/ident") for d in _ont()[":schema"]}
    for bad in (":designation/our-verdict", ":our-designation", ":verdict"):
        assert bad not in idents, f"G1: {bad} must not exist (etzhayyim authors no designation)"


def test_schema_post_status_dry_run_only():
    assert [s.lstrip(":") for s in _datom(":post/status")[":db/allowed"]] == ["dry-run"]


def test_schema_post_server_key_false_only():
    assert _datom(":post/server-held-key")[":db/allowed"] == [False]


def test_schema_post_is_mirror_true_only():
    assert _datom(":post/is-mirror")[":db/allowed"] == [True]


# ── lexicon :enum/:const invariants ─────────────────────────────────────────────
def test_lex_authority_kind_no_self():
    enum = _props("assertingAuthority")[":kind"][":enum"]
    for tok in SELF_TOKENS:
        assert tok not in enum


def test_lex_measure_no_verdict():
    enum = _props("designationNotice")[":measure"][":enum"]
    for tok in VERDICT_TOKENS:
        assert tok not in enum


def test_lex_designation_asserter_required():
    req = _lex("designationNotice")[":defs"][":main"][":record"][":required"]
    assert "asserter" in req, "G2: asserter must be required on a designation"


def test_lex_designation_asserted_notice_const_true():
    assert _props("designationNotice")[":assertedNotice"][":const"] is True


def test_lex_designation_status_enum():
    assert set(_props("designationNotice")[":status"][":enum"]) == {"listed", "delisted"}


def test_lex_designation_sources_min_two():
    assert _props("designationNotice")[":sources"][":minLength"] == 2


def test_lex_view_non_adjudicating_const_true():
    assert _props("competingClaimView")[":nonAdjudicatingNotice"][":const"] is True


def test_lex_post_status_const_dry_run():
    assert _props("networkPost")[":status"][":const"] == "dry-run"


def test_lex_post_is_mirror_const_true():
    assert _props("networkPost")[":isMirror"][":const"] is True


def test_lex_post_server_key_const_false():
    assert _props("networkPost")[":serverHeldKey"][":const"] is False


# ── seed value invariants ───────────────────────────────────────────────────────
def test_seed_authorities_not_self():
    seed = load_edn(SEED)
    for a in seed[":authorities"]:
        aid = a[":authority/id"].lower()
        for tok in SELF_TOKENS:
            assert tok not in aid, f"G1: authority {aid} resolves to self"
        assert a[":authority/stance"].strip(), f"G6: authority {aid} must declare a stance"


def test_seed_subjects_no_score_or_pii():
    from weave import PII_FORBIDDEN_SUBJECT_ATTRS
    assert PII_FORBIDDEN_SUBJECT_ATTRS
    seed = load_edn(SEED)
    for s in seed[":subjects"]:
        assert ":subject/risk-score" not in s and ":subject/guilt" not in s
        for key in s:
            assert key.lstrip(":").split("/")[-1].lower() not in PII_FORBIDDEN_SUBJECT_ATTRS, key


def test_seed_designations_attributed_factual_sourced():
    seed = load_edn(SEED)
    measures = {m.lstrip(":") for m in _ont()[":ontology/measure-kinds"]}
    for d in seed[":designations"]:
        assert str(d[":designation/asserter"]).strip(), f"G2: {d[':designation/id']} needs an asserter"
        assert d[":designation/asserted-notice"] is True
        assert d[":designation/measure"].lstrip(":") in measures
        assert len(d[":designation/sources"]) >= 2, d[":designation/id"]


def test_seed_delisted_carries_lifted_at():
    seed = load_edn(SEED)
    for d in seed[":designations"]:
        if d[":designation/status"].lstrip(":") == "delisted":
            assert ":designation/lifted-at" in d, f"G4: {d[':designation/id']} delisted needs :lifted-at"


# ── lexicon ⊆ ontology drift-lock (BOTH directions) ─────────────────────────────
def test_measure_lex_eq_ontology():
    enum = set(_props("designationNotice")[":measure"][":enum"])
    vocab = {k.lstrip(":") for k in _ont()[":ontology/measure-kinds"]}
    assert enum == vocab, f"measure drift: {enum ^ vocab}"


def test_authority_kind_lex_eq_ontology():
    enum = set(_props("assertingAuthority")[":kind"][":enum"])
    vocab = {k.lstrip(":") for k in _ont()[":ontology/authority-kinds"]}
    assert enum == vocab, f"authority-kind drift: {enum ^ vocab}"


def test_subject_kind_lex_eq_ontology():
    enum = set(_props("subjectEntity")[":kind"][":enum"])
    vocab = {k.lstrip(":") for k in _ont()[":ontology/subject-kinds"]}
    assert enum == vocab, f"subject-kind drift: {enum ^ vocab}"


def test_post_status_const_matches_ontology():
    statuses = {s.lstrip(":") for s in _ont()[":ontology/post-statuses"]}
    assert {_props("networkPost")[":status"][":const"]} == statuses


if __name__ == "__main__":
    run("charter-invariants", [(k, v) for k, v in sorted(globals().items())
                               if k.startswith("test_") and callable(v)])
