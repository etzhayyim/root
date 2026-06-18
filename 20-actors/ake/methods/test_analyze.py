#!/usr/bin/env python3
"""End-to-end membrane test for analyze.py — propose → triage → route → revision."""
from __future__ import annotations

import pathlib
import tempfile

import contributor as contrib
from analyze import _report, run
from revision import current, history_of

# A synthetic batch the :representative seed can't express: a hard-gate refusal AT INTAKE
# (unsourced → G4 raises inside score_edit) alongside two accepted edits on the SAME
# (entity, attr) — exercises the intake-refused arm and the revision-history dedup.
_EDGE_SEED = """{:edit/batch
 [{:edit/id "g1" :edit/target-kind :kg-fact :edit/target-entity "org.corp.x"
   :edit/target-attr :corp/hq-address :edit/op :assert :edit/proposed-value "addr v1"
   :edit/author "did:web:etzhayyim.com:member:abel" :edit/author-kind :member
   :edit/provenance "https://example.com/x1" :edit/rationale "a clear sourced reason"
   :edit/server-held-key false :edit/info-as-of 1000 :edit/sourcing :authoritative}
  {:edit/id "g2" :edit/target-kind :kg-fact :edit/target-entity "org.corp.x"
   :edit/target-attr :corp/hq-address :edit/op :assert :edit/proposed-value "addr v2"
   :edit/author "did:web:etzhayyim.com:member:abel" :edit/author-kind :member
   :edit/provenance "https://example.com/x2" :edit/rationale "a later sourced correction"
   :edit/server-held-key false :edit/info-as-of 1020 :edit/sourcing :authoritative}
  {:edit/id "bad" :edit/target-kind :kg-fact :edit/target-entity "org.corp.x"
   :edit/target-attr :corp/note :edit/op :assert :edit/proposed-value "unsourced claim"
   :edit/author "did:web:etzhayyim.com:member:korah" :edit/author-kind :member
   :edit/provenance "" :edit/rationale "no source provided"
   :edit/server-held-key false :edit/info-as-of 1010 :edit/sourcing :representative}]}"""


def _run_edge():
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "edge-seed.kotoba.edn"
        p.write_text(_EDGE_SEED, encoding="utf-8")
        return run(p)


def test_intake_refused_edit_is_recorded_not_accepted_and_does_not_crash_the_run():
    res = _run_edge()
    by_id = {r["edit"]: r for r in res["rows"]}
    # an unsourced edit fails the G4 hard gate INSIDE score_edit → :refused-at-intake row,
    # carrying the ValueError text, and the run keeps going (the good edits still route).
    assert by_id["bad"]["route"] == ":refused-at-intake"
    assert by_id["bad"]["accepted"] is False
    assert by_id["bad"]["note"]
    assert by_id["g1"]["accepted"] and by_id["g2"]["accepted"]
    # the refused author earns a "refused" trajectory event (G9), accepts none.
    korah = "did:web:etzhayyim.com:member:korah"
    assert contrib.counts(res["trajectory"], korah) == {"accepted": 0, "refused": 1}


def test_report_dedups_repeated_entity_attr_key():
    res = _run_edge()
    # two accepted edits on the SAME (entity, attr) → history has both, current = the later.
    assert len(history_of(res["history"], "org.corp.x", "hq-address")) == 2
    assert current(res["history"], "org.corp.x", "hq-address")[":revision/value"] == "addr v2"
    # _report collapses the repeated key to ONE bullet and reports the revision count.
    md = _report(res)
    assert md.count("`org.corp.x` `hq-address`") == 1
    assert "2 revision(s)" in md


def test_run_routes_every_seed_edit():
    res = run()
    by_id = {r["edit"]: r for r in res["rows"]}
    assert set(by_id) == {"e1", "e2", "e3", "e4", "e5"}


def test_optimistic_and_voted_edits_are_accepted():
    res = run()
    by_id = {r["edit"]: r for r in res["rows"]}
    assert by_id["e1"]["route"] == ":auto-accept" and by_id["e1"]["accepted"]
    assert by_id["e2"]["route"] == ":vote" and by_id["e2"]["accepted"]      # 8-1
    assert by_id["e3"]["route"] == ":vote" and by_id["e3"]["accepted"]      # 5-0


def test_invariant_and_rider_edits_are_not_accepted():
    res = run()
    by_id = {r["edit"]: r for r in res["rows"]}
    assert by_id["e4"]["route"] == ":council-lv7" and not by_id["e4"]["accepted"]
    assert by_id["e5"]["route"] == ":refused" and not by_id["e5"]["accepted"]


def test_accepted_edits_landed_in_revision_history():
    res = run()
    # e1 (tsmc hq-address) and e2 (example-listed status) accepted → present as current
    assert current(res["history"], "org.corp.tsmc", "hq-address") is not None
    assert current(res["history"], "org.corp.example-listed", "status") is not None
    # e4 (license, council-pending) and e5 (refused) did NOT land
    assert current(res["history"], "org.corp.example-listed", "license") is None


def test_contributor_trajectory_recorded():
    res = run()
    # the rider-violating author (esau) is recorded as refused, not accepted
    esau = "did:web:etzhayyim.com:member:esau"
    c = contrib.counts(res["trajectory"], esau)
    assert c["accepted"] == 0 and c["refused"] >= 1
    # the council-pending author (dan) has no decided event yet (pending ≠ refused)
    dan = "did:web:etzhayyim.com:member:dan"
    assert contrib.counts(res["trajectory"], dan) == {"accepted": 0, "refused": 0}


def test_report_renders():
    md = _report(run())
    assert "community-edit membrane dry-run" in md
    assert "Revision history" in md


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
    print(f"{len(fns) - failed}/{len(fns)} passed in test_analyze.py")
    sys.exit(1 if failed else 0)
