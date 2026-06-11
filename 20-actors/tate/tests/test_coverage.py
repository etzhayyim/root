#!/usr/bin/env python3
"""tate 盾 — jurisdiction-coverage honesty tests (G10, ADR-2606112400). Pure stdlib.

Verifies the worldwide expansion stays HONEST:
  - the jurisdiction registry is bounded + representative (5 systems), every entry
    carries the UPL anchor + fake-help + referral directories + verify-current-law
  - every covered jurisdiction has ≥1 clause pattern AND ≥1 procedure (no hollow flag)
  - the coverage ratio against ~193 UN states is LOW and reported as such (推測より空白)
  - named gaps are non-empty (the next-wave worklist exists)
"""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from coverage_report import coverage, report  # noqa: E402
from respond_plan import load_jurisdictions, load_procs, load_us_states, plans  # noqa: E402
from terms_scan import load_docs, load_patterns, scan  # noqa: E402


CORE = {":jp", ":us", ":eu", ":uk", ":de"}


def test_jurisdiction_registry_complete():
    """Growth-proof: the core 5 stay present; EVERY entry (current and future) is
    complete — UPL anchor, directories, service note, refer-over line, honesty flags."""
    juris = load_jurisdictions()
    assert CORE <= set(juris.keys())
    for j in juris.values():
        assert j[":juris/upl-anchor"], j[":juris/id"]
        assert j[":juris/fake-help"] and j[":juris/referrals"], j[":juris/id"]
        # the in-house victim-support route (tasuke 助) must exist in EVERY jurisdiction
        assert any("tasuke" in x for x in j[":juris/fake-help"]), j[":juris/id"]
        assert j[":juris/service-note"], j[":juris/id"]
        assert j[":juris/verify-current-law"] is True
        assert j[":juris/sourcing"] == ":representative"
        assert float(j[":juris/refer-over-amount"]) > 0


def test_no_hollow_jurisdiction():
    cov = coverage()
    for j in cov["jurisdictions"]:
        assert cov["patterns_by_jurisdiction"].get(j, 0) >= 1, f"{j} has no clause patterns"
        assert cov["procedures_by_jurisdiction"].get(j, 0) >= 1, f"{j} has no procedures"


def test_coverage_ratio_honest():
    cov = coverage()
    assert cov["covered_count"] == len(load_jurisdictions())
    assert cov["un_member_states"] == 193
    assert cov["coverage_ratio"] < 0.25, "coverage must be reported as the small number it is"
    assert len(cov["named_gaps"]) >= 4  # structural gaps alone guarantee this


def test_gap_list_never_stale():
    """Maturity: a covered jurisdiction must NOT still be listed as a gap, and the
    worklist remainder must all be genuinely uncovered."""
    cov = coverage()
    covered = set(cov["jurisdictions"])
    for j in cov["worklist_remaining"]:
        assert j not in covered, f"{j} is covered but still on the worklist"
    gap_text = " ".join(cov["named_gaps"])
    for j in covered:
        assert f"{j} — 未収載" not in gap_text, f"{j} is covered but named as a gap"


def test_us_states_registry():
    """Wave 6: every US-state entry is complete; the coverage report counts states
    honestly (5/50 — the structural gap is measured, not hand-waved)."""
    states = load_us_states()
    assert len(states) >= 5
    for s in states.values():
        assert s[":state/label"] and s[":state/answer-rule"], s[":state/id"]
        assert s[":state/answer-anchor"], s[":state/id"]
        assert float(s[":state/small-claims-usd"]) > 0, s[":state/id"]
        assert s[":state/verify-current-law"] is True
        assert s[":state/sourcing"] == ":representative"
    cov = coverage()
    assert cov["us_states_covered"] == len(states)
    assert cov["us_states_total"] == 50
    assert any("州レベル" in g for g in cov["named_gaps"])


def test_manifest_jurisdictions_in_sync():
    """Wave 16 maturity: manifest.edn の :actor/jurisdictions は registry と機械的に
    一致しなければならない — 14 waves 手動同期してきた doc-drift クラスの構造的封殺."""
    from terms_scan import read_edn
    manifest = read_edn((ACTOR_DIR / "manifest.edn").read_text(encoding="utf-8"))
    declared = set(manifest[":actor/jurisdictions"])
    actual = set(load_jurisdictions().keys())
    assert declared == actual, (sorted(declared - actual), sorted(actual - declared))


def test_report_names_the_gap():
    text = report(coverage())
    assert "named gaps" in text.lower() or "Named gaps" in text
    assert ":unknown-jurisdiction" in text  # the degrade path is documented in the readout
    assert "193" in text


def test_every_clause_pattern_exercised():
    """Maturity: NO untested registry entry — every clause pattern must be hit by at
    least one synthetic seed doc, or it is dead weight nobody has proven fires."""
    docs, _ = load_docs()
    patterns = load_patterns()
    hit = {f["clause"] for f in scan(docs, patterns)["flags"]}
    missing = sorted(p[":clause/id"] for p in patterns if p[":clause/id"] not in hit)
    assert not missing, f"patterns with no exercising seed doc: {missing}"


def test_every_procedure_exercised():
    """Maturity: every procedure must be matched :genuine by at least one seed notice
    (the fake/unknown fixtures don't count as exercising a procedure's happy path)."""
    _, notices = load_docs()
    procs = load_procs()
    exercised = {p["proc"] for p in plans(notices, procs) if p["status"] == ":genuine"}
    missing = sorted(p[":proc/id"] for p in procs if p[":proc/id"] not in exercised)
    assert not missing, f"procedures with no genuine seed notice: {missing}"


def test_registry_lint():
    """Maturity: unique ids; every procedure has ≥1 option and ≥1 anchored deadline
    rule; every pattern has keywords + anchor."""
    patterns = load_patterns()
    procs = load_procs()
    pids = [p[":clause/id"] for p in patterns]
    assert len(pids) == len(set(pids)), "duplicate clause ids"
    qids = [p[":proc/id"] for p in procs]
    assert len(qids) == len(set(qids)), "duplicate proc ids"
    for p in patterns:
        assert p[":clause/keywords"] and p[":clause/anchor"], p[":clause/id"]
    for p in procs:
        assert p[":proc/options"], p[":proc/id"]
        assert p[":proc/deadline-rules"], p[":proc/id"]
        for dl in p[":proc/deadline-rules"]:
            assert dl[":dl/anchor"], (p[":proc/id"], dl)
        assert p[":proc/genuine-channels"], p[":proc/id"]
        # wave 15: there is ALWAYS someone to ask — no procedure ships without referrals
        assert p.get(":proc/refer-when"), p[":proc/id"]
        assert p.get(":proc/track", ":civil") in (":civil", ":labor", ":housing",
                                                  ":enforcement", ":insolvency",
                                                  ":family"), p[":proc/id"]


def test_specialty_track_counted():
    """Waves 8-12: all five planned specialty tracks are open and measured; the
    coverage line now names the NEXT gap honestly — per-track jurisdiction depth."""
    cov = coverage()
    assert cov["procedure_tracks"].get(":labor", 0) >= 3
    assert cov["procedure_tracks"].get(":housing", 0) >= 4
    assert cov["procedure_tracks"].get(":enforcement", 0) >= 3
    assert cov["procedure_tracks"].get(":insolvency", 0) >= 3
    assert cov["procedure_tracks"].get(":family", 0) >= 3
    assert cov["procedure_tracks"].get(":civil", 0) >= 20
    assert any("専門トラック" in g and "管轄横展開" in g for g in cov["named_gaps"])


def test_track_matrix():
    """Wave 13: the track × jurisdiction matrix makes horizontal gaps measurable —
    matrix totals must equal the per-track totals, and the expansion is real
    (:labor in ≥5 jurisdictions, :housing in ≥6)."""
    cov = coverage()
    matrix = cov["track_matrix"]
    for track, total in cov["procedure_tracks"].items():
        assert sum(ts.get(track, 0) for ts in matrix.values()) == total, track
    assert sum(1 for ts in matrix.values() if ts.get(":labor", 0)) >= 6
    assert sum(1 for ts in matrix.values() if ts.get(":housing", 0)) >= 6
    assert sum(1 for ts in matrix.values() if ts.get(":enforcement", 0)) >= 5
    assert sum(1 for ts in matrix.values() if ts.get(":insolvency", 0)) >= 5
    assert sum(1 for ts in matrix.values() if ts.get(":family", 0)) >= 4
    text = report(cov)
    assert "Track × jurisdiction matrix" in text


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok {fn.__name__}")
    print(f"{len(fns)} passed")
