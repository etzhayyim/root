#!/usr/bin/env python3
"""State-machine tests for 朱 (ake) cells (R0). .solve() is NOT called (it raises).

Standalone-runnable AND pytest-compatible (repo pytest plugin env is broken):
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_state_machines.py
    python3 test_state_machines.py
"""
from __future__ import annotations

import sys

from propose.cell import ProposeCell
from propose.state_machine import ProposePhase, transition_to_recorded, transition_to_screened
from edit_triage.cell import TriageCell
from edit_triage.state_machine import TriagePhase, triage
from review_vote.cell import ReviewVoteCell
from review_vote.state_machine import ReviewPhase, tally
from promote.cell import PromoteCell
from promote.state_machine import PromotePhase, review_promotion
from revision_log.cell import RevisionLogCell
from revision_log.state_machine import RevisionPhase, append


def _good_edit():
    return {
        ":edit/id": "e1", ":edit/target-kind": ":kg-fact", ":edit/target-entity": "org.corp.tsmc",
        ":edit/target-attr": ":corp/hq-address", ":edit/op": ":assert",
        ":edit/proposed-value": "Hsinchu 300-096, Taiwan", ":edit/author": "did:web:etzhayyim.com:member:abel",
        ":edit/author-kind": ":member", ":edit/provenance": "https://tsmc.com/profile",
        ":edit/rationale": "postal code update", ":edit/server-held-key": False, ":edit/sourcing": ":authoritative",
    }


# ───────────────────────────── propose (G1/G3/G4) ───────────────────────────
def _screen(**over):
    base = {"cell_state": {}, "edit_id": "e1", "target_kind": "kg-fact",
            "target_entity": "org.corp.tsmc", "target_attr": ":corp/hq-address", "op": "assert",
            "author": "did:web:etzhayyim.com:member:abel", "author_kind": "member",
            "provenance": "https://tsmc.com/profile", "server_held_key": False}
    base.update(over)
    return transition_to_screened(base)


def test_propose_screens_and_records_a_good_edit():
    cs = _screen()["cell_state"]
    assert cs["phase"] == ProposePhase.SCREENED.value
    cs2 = transition_to_recorded({"cell_state": cs})["cell_state"]
    assert cs2["phase"] == ProposePhase.RECORDED.value
    assert cs2["payload"]["authorKind"] == "member" and cs2["payload"]["serverHeldKey"] is False


def test_propose_refuses_non_member():
    cs = _screen(author_kind="server")["cell_state"]
    assert cs["phase"] == ProposePhase.REFUSED.value and "G1" in cs["refusal"]


def test_propose_refuses_server_held_key():
    cs = _screen(server_held_key=True)["cell_state"]
    assert cs["phase"] == ProposePhase.REFUSED.value and "no-server-key" in cs["refusal"]


def test_propose_refuses_unsourced():
    cs = _screen(provenance="")["cell_state"]
    assert cs["phase"] == ProposePhase.REFUSED.value and "G4" in cs["refusal"]


def test_propose_refuses_impersonation_target():
    cs = _screen(target_kind="entity-speech")["cell_state"]
    assert cs["phase"] == ProposePhase.REFUSED.value and "G3" in cs["refusal"]


def test_propose_cannot_record_without_screening():
    cs = transition_to_recorded({"cell_state": {}})["cell_state"]
    assert cs["phase"] == ProposePhase.REFUSED.value


# ───────────────────────────── triage (G2/G6) ───────────────────────────────
def test_triage_scores_and_routes():
    cs = triage({"cell_state": {}, "edit": _good_edit()})["cell_state"]
    assert cs["phase"] == TriagePhase.TRIAGED.value
    assert cs["payload"]["route"] == "auto-accept" and cs["payload"]["risk"] == "low"


def test_triage_refuses_a_hard_gate_violation():
    bad = _good_edit(); bad[":edit/provenance"] = ""
    cs = triage({"cell_state": {}, "edit": bad})["cell_state"]
    assert cs["phase"] == TriagePhase.REFUSED.value and "G4" in cs["refusal"]


def test_triage_routes_invariant_to_council():
    e = _good_edit(); e[":edit/target-attr"] = ":license"
    cs = triage({"cell_state": {}, "edit": e})["cell_state"]
    assert cs["payload"]["route"] == "council-lv7"


# ───────────────────────────── review_vote ──────────────────────────────────
def test_vote_accepts_majority_yes():
    cs = tally({"cell_state": {}, "edit_id": "e2", "mechanism": "sbt-vote", "yes": 8, "no": 1,
                "signed_by": "did:web:etzhayyim.com:member:op"})["cell_state"]
    assert cs["phase"] == ReviewPhase.TALLIED.value and cs["payload"]["outcome"] == "accepted"


def test_vote_rejects_majority_no():
    cs = tally({"cell_state": {}, "edit_id": "e2", "mechanism": "sbt-vote", "yes": 1, "no": 8,
                "signed_by": "did:web:etzhayyim.com:member:op"})["cell_state"]
    assert cs["payload"]["outcome"] == "rejected"


def test_vote_optimistic_accepts():
    cs = tally({"cell_state": {}, "edit_id": "e1", "mechanism": "optimistic",
                "signed_by": "did:web:etzhayyim.com:member:op"})["cell_state"]
    assert cs["payload"]["outcome"] == "accepted"


def test_vote_council_is_pending():
    cs = tally({"cell_state": {}, "edit_id": "e4", "mechanism": "council-lv7",
                "signed_by": "did:web:etzhayyim.com:member:op"})["cell_state"]
    assert cs["payload"]["outcome"] == "pending"


def test_vote_refuses_server_signature():
    cs = tally({"cell_state": {}, "edit_id": "e2", "mechanism": "sbt-vote", "yes": 9, "no": 0,
                "signed_by": "server-bot"})["cell_state"]
    assert cs["phase"] == ReviewPhase.REFUSED.value and "no-server-key" in cs["refusal"]


def test_vote_refuses_unknown_mechanism():
    # the closed-vocab guard: only the declared mechanisms (optimistic / sbt-vote / council-lv7)
    # can tally — an off-vocab mechanism is refused before any count is read.
    cs = tally({"cell_state": {}, "edit_id": "e2", "mechanism": "coin-flip", "yes": 9, "no": 0,
                "signed_by": "did:web:etzhayyim.com:member:op"})["cell_state"]
    assert cs["phase"] == ReviewPhase.REFUSED.value and "unknown review mechanism" in cs["refusal"]


# ───────────────────────────── promote (G4/G8/G9) ───────────────────────────
def test_promote_clears_accepted_member_signed():
    cs = review_promotion({"cell_state": {}, "edit_id": "e1", "entity": "org.corp.tsmc",
                           "attr": ":corp/hq-address", "value": "Hsinchu 300-096", "outcome": "accepted",
                           "to_sourcing": "authoritative", "provenance": "https://tsmc.com/profile",
                           "signed_by": "did:web:etzhayyim.com:member:abel", "as_of": 2010})["cell_state"]
    assert cs["phase"] == PromotePhase.CLEARED.value
    assert cs["payload"]["promoted"] is True and cs["payload"]["published"] is False
    assert cs["payload"]["serverHeldKey"] is False


def test_promote_refuses_server_signature():
    cs = review_promotion({"cell_state": {}, "edit_id": "e1", "outcome": "accepted",
                           "signed_by": "server", "to_sourcing": "representative"})["cell_state"]
    assert cs["phase"] == PromotePhase.REFUSED.value and "G9" in cs["refusal"]


def test_promote_refuses_unaccepted():
    cs = review_promotion({"cell_state": {}, "edit_id": "e4", "outcome": "pending",
                           "signed_by": "did:web:etzhayyim.com:member:op"})["cell_state"]
    assert cs["phase"] == PromotePhase.REFUSED.value


def test_promote_authoritative_needs_verifiable_provenance():
    cs = review_promotion({"cell_state": {}, "edit_id": "e1", "outcome": "accepted",
                           "to_sourcing": "authoritative", "provenance": "trust me",
                           "signed_by": "did:web:etzhayyim.com:member:op"})["cell_state"]
    assert cs["phase"] == PromotePhase.REFUSED.value and "G4" in cs["refusal"]


# ───────────────────────────── revision_log (G5) ────────────────────────────
def test_revision_log_appends_and_grows():
    s1 = append({"cell_state": {}, "history": [], "edit": _good_edit(), "as_of": 100})["cell_state"]
    assert s1["phase"] == RevisionPhase.APPENDED.value and s1["payload"]["revisions"] == 1
    s2 = append({"cell_state": {}, "history": s1["history"], "edit": _good_edit(), "as_of": 200})["cell_state"]
    assert s2["payload"]["revisions"] == 2   # append-only, never overwrites


def test_revision_log_refuses_if_log_does_not_grow_by_exactly_one():
    # the G5 cell-level guard: if the underlying log fails to grow by exactly one, the cell
    # REFUSES rather than silently proceed. Force the violation by stubbing append_revision to
    # return the history unchanged (Python resolves the global at call time, so this is seen).
    import revision_log.state_machine as rlsm
    orig = rlsm.append_revision
    rlsm.append_revision = lambda history, edit, as_of: list(history)  # no growth
    try:
        cs = append({"cell_state": {}, "history": [], "edit": _good_edit(), "as_of": 100})["cell_state"]
    finally:
        rlsm.append_revision = orig
    assert cs["phase"] == RevisionPhase.REFUSED.value and "G5" in cs["refusal"]


# ───────────────────────────── .solve() raises at R0 ────────────────────────
def test_all_cells_solve_raise():
    for C in (ProposeCell, TriageCell, ReviewVoteCell, PromoteCell, RevisionLogCell):
        try:
            C().solve({})
            assert False, f"{C.__name__}.solve should raise at R0"
        except RuntimeError:
            pass


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"{len(fns) - failed}/{len(fns)} passed in cells/test_state_machines.py")
    sys.exit(1 if failed else 0)
