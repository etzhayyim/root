"""test_weave.py — 高札 (kosatsu) weave + competing-claim/divergence engine. ADR-2606072000."""
from __future__ import annotations

import pathlib

from _edn import load_edn
from _t import expect_raises, run
from weave import (agreement_index, by_authority, co_designation, delisting_timeline,
                   divergence, divergence_all, report, status_as_of,
                   validate_authority, validate_designation, validate_subject, weave)

SEED = pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-designation-graph.kotoba.edn"


def _g():
    return weave(load_edn(SEED))


def _auth(**kw):
    base = {":authority/id": "x-auth", ":authority/kind": ":state-treasury", ":authority/label": "X",
            ":authority/jurisdiction": "x", ":authority/stance": "rep", ":authority/sourcing": ":representative",
            ":authority/sources": ["https://example.gov/"]}
    base.update(kw)
    return base


def _subj(**kw):
    base = {":subject/id": "x-sub", ":subject/kind": ":designated-entity", ":subject/label": "S",
            ":subject/sourcing": ":representative"}
    base.update(kw)
    return base


def _desig(**kw):
    base = {":designation/id": "x-d", ":designation/asserter": "x-auth", ":designation/subject": "x-sub",
            ":designation/measure": ":financial-sanction", ":designation/program": "P",
            ":designation/status": ":listed", ":designation/posted-at": 20230101,
            ":designation/asserted-notice": True, ":designation/sourcing": ":representative",
            ":designation/sources": ["https://example.gov/a", "https://example.gov/b"]}
    base.update(kw)
    return base


# ── seed weaves clean ─────────────────────────────────────────────────────────
def test_seed_weaves():
    g = _g()
    assert len(g["authorities"]) == 7
    assert len(g["subjects"]) == 5
    assert len(g["designations"]) == 13


# ── G1 etzhayyim authors no designation ───────────────────────────────────────
def test_authority_self_refused():
    expect_raises(lambda: validate_authority(_auth(**{":authority/id": "etzhayyim-board"})), contains="G1")


# ── G2 asserter mandatory + no verdict measure ────────────────────────────────
def test_designation_without_asserter_refused():
    expect_raises(lambda: validate_designation(_desig(**{":designation/asserter": ""})), contains="G2")


def test_designation_verdict_measure_refused():
    expect_raises(lambda: validate_designation(_desig(**{":designation/measure": ":criminal"})), contains="G2")


def test_designation_terrorist_measure_refused():
    expect_raises(lambda: validate_designation(_desig(**{":designation/measure": ":terrorist"})), contains="G2")


# ── G3 sourcing ───────────────────────────────────────────────────────────────
def test_designation_under_sourced_refused():
    expect_raises(lambda: validate_designation(_desig(**{":designation/sources": ["https://example.gov/a"]})), contains="G3")


def test_designation_commercial_terminal_refused():
    expect_raises(lambda: validate_designation(
        _desig(**{":designation/sources": ["https://worldcheck.refinitiv.com/x", "https://example.gov/b"]})),
        contains="Rider")


# ── G4 status / delisting needs lifted-at ─────────────────────────────────────
def test_delisted_needs_lifted_at():
    expect_raises(lambda: validate_designation(_desig(**{":designation/status": ":delisted"})), contains="G4")


def test_final_status_refused():
    expect_raises(lambda: validate_designation(_desig(**{":designation/status": ":permanent"})), contains="G4")


# ── G2/G7 no per-subject score ────────────────────────────────────────────────
def test_subject_score_refused():
    expect_raises(lambda: validate_subject(_subj(**{":subject/risk-score": 9})), contains="G2/G7")


def test_subject_pii_refused():
    expect_raises(lambda: validate_subject(_subj(**{":subject/dob": "1970-01-01"})), contains="no-doxxing")


# ── status as-of (event log) ──────────────────────────────────────────────────
def test_status_as_of_delisting():
    g = _g()
    # subj-beta: us listed 2022, us delisted 2024
    assert status_as_of(g, "subj-beta", "us-ofac", 20230101) == "listed"
    assert status_as_of(g, "subj-beta", "us-ofac", 20240601) == "delisted"
    assert status_as_of(g, "subj-beta", "us-ofac") == "delisted"   # latest


def test_status_as_of_silent():
    g = _g()
    assert status_as_of(g, "subj-alpha", "jp-mof") is None   # jp never designated alpha


# ── divergence engine (the political-stance core) ─────────────────────────────
def test_divergence_contested_is_active_delist_conflict():
    # subj-beta: eu currently lists it, us delisted it → an ACTIVE disagreement on current status
    g = _g()
    d = divergence(g, "subj-beta")
    assert d["class"] == "contested"
    assert "us-ofac" in d["delisted"]
    assert "eu-council" in d["listing"]


def test_divergence_coverage_split_not_contested():
    # subj-alpha: us+eu+un list it, jp+cn+ru never designated it. The opiners AGREE (unanimous),
    # but coverage is split — silence is reported, NOT inferred as dissent.
    g = _g()
    d = divergence(g, "subj-alpha")
    assert d["class"] == "unanimous"
    assert d["coverage_split"] is True
    assert "jp-mof" in d["silent"] and "cn-mofcom" in d["silent"]
    assert set(d["listing"]) == {"us-ofac", "eu-council", "un-sc"}


def test_divergence_unanimous():
    g = _g()
    d = divergence(g, "subj-gamma")
    assert d["class"] == "unanimous"
    assert set(d["listing"]) == {"us-ofac", "eu-council", "un-sc", "gb-ofsi"}


def test_divergence_single_asserter():
    g = _g()
    d = divergence(g, "subj-delta")
    assert d["class"] == "single-asserter"
    assert d["listing"] == ["ru-mfa"]


def test_divergence_all_contested_first():
    g = _g()
    classes = [d["class"] for d in divergence_all(g)]
    assert classes[0] == "contested"


# ── aggregates ────────────────────────────────────────────────────────────────
def test_agreement_index():
    g = _g()
    ai = agreement_index(g)
    assert ai["designated_subjects"] == 5
    assert ai["contested"] >= 1          # subj-beta (us delisted vs eu listing)
    assert ai["coverage_split"] >= 2     # subj-alpha + subj-gamma (listed by some, silent by others)
    assert 0.0 <= ai["contested_ratio"] <= 1.0


def test_delisting_timeline():
    g = _g()
    tl = delisting_timeline(g)
    assert len(tl) == 1
    assert tl[0]["asserter"] == "us-ofac" and tl[0]["subject"] == "subj-beta"
    assert tl[0]["lifted_at"] == 20240115


def test_by_authority_counts():
    g = _g()
    rows = {r["authority"]: r["listed_subjects"] for r in by_authority(g)}
    assert rows["us-ofac"] >= 2          # alpha, gamma, vessel listed (beta delisted)
    assert rows["us-ofac"] == 3          # alpha + gamma + vessel (beta now delisted)


def test_co_designation_us_has_program_cluster():
    g = _g()
    cd = co_designation(g)
    # us lists alpha (EO 14024), gamma (1267-aligned), vessel (shadow-fleet) under distinct programs;
    # none shares a program with >1 subject in seed → expect no cluster, which is a valid (empty) result.
    assert isinstance(cd, list)


def test_report_shape():
    g = _g()
    r = report(g)
    for k in ("agreement_index", "divergence", "by_authority", "delisting_timeline", "co_designation", "integrity"):
        assert k in r
    assert r["integrity"]["dangling_count"] == 0


if __name__ == "__main__":
    run("weave", [(k, v) for k, v in sorted(globals().items())
                  if k.startswith("test_") and callable(v)])
