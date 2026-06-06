#!/usr/bin/env python3
"""Cell-chain integration test for 朱 (ake) — the full membrane as the cells actually compose it.

The individual cell state machines are unit-tested in test_state_machines.py; the methods-layer
end-to-end is in methods/test_analyze.py. THIS suite threads one edit through all five CELLS in
sequence — propose → edit_triage → review_vote → promote → revision_log — exactly as the runtime
Pregel graph would, proving they compose (output of each is valid input to the next). Hermetic; no
external files; .solve() is never called (R0 scaffolds raise).
"""
from __future__ import annotations

import sys

from propose.state_machine import ProposePhase, transition_to_recorded, transition_to_screened
from edit_triage.state_machine import TriagePhase, triage
from review_vote.state_machine import ReviewPhase, tally
from promote.state_machine import PromotePhase, review_promotion
from revision_log.state_machine import RevisionPhase, append

_ROUTE_TO_MECHANISM = {
    "auto-accept": "optimistic",
    "vote": "sbt-vote",
    "council-lv7": "council-lv7",
}


def _edit(eid, *, kind=":kg-fact", entity="org.corp.x", attr=":status", op=":assert",
          value=":delisted", author="did:web:etzhayyim.com:member:a",
          provenance="https://primary.example.com/notice",
          rationale="a sourced correction with an adequate explanation",
          sourcing=":authoritative"):
    return {
        ":edit/id": eid, ":edit/target-kind": kind, ":edit/target-entity": entity,
        ":edit/target-attr": attr, ":edit/op": op, ":edit/proposed-value": value,
        ":edit/author": author, ":edit/author-kind": ":member",
        ":edit/provenance": provenance, ":edit/rationale": rationale, ":edit/sourcing": sourcing,
    }


def run_flow(edit: dict, *, yes=0, no=0, signer="did:web:etzhayyim.com:member:op",
             history=None, as_of=500) -> dict:
    """Thread one :edit/* through all five cells. Returns a trace of where it ended up."""
    history = list(history or [])
    trace = {"recorded": False, "route": None, "outcome": None,
             "promoted": False, "appended": False, "stopped_at": None, "history": history}

    # 1) propose — screen + record (flat-keyed cell input)
    flat = {"cell_state": {}, "edit_id": edit[":edit/id"],
            "target_kind": edit[":edit/target-kind"], "target_entity": edit[":edit/target-entity"],
            "target_attr": edit[":edit/target-attr"], "op": edit[":edit/op"],
            "author": edit[":edit/author"], "author_kind": edit[":edit/author-kind"],
            "provenance": edit[":edit/provenance"], "server_held_key": False}
    s = transition_to_screened(flat)
    if s["cell_state"]["phase"] != ProposePhase.SCREENED.value:
        trace["stopped_at"] = "propose"; return trace
    s = transition_to_recorded({"cell_state": s["cell_state"]})
    trace["recorded"] = s["cell_state"]["phase"] == ProposePhase.RECORDED.value

    # 2) edit_triage — score + route (never decides)
    t = triage({"cell_state": {}, "edit": edit})
    if t["cell_state"]["phase"] != TriagePhase.TRIAGED.value:
        trace["stopped_at"] = "triage"; return trace
    route = t["cell_state"]["payload"]["route"]
    trace["route"] = route
    if route == "refused":
        trace["stopped_at"] = "triage:refused"; return trace

    # 3) review_vote — optimistic / sbt-vote / council-lv7
    r = tally({"cell_state": {}, "edit_id": edit[":edit/id"],
               "mechanism": _ROUTE_TO_MECHANISM[route], "yes": yes, "no": no, "signed_by": signer})
    if r["cell_state"]["phase"] != ReviewPhase.TALLIED.value:
        trace["stopped_at"] = "review"; return trace
    outcome = r["cell_state"]["payload"]["outcome"]
    trace["outcome"] = outcome
    if outcome != "accepted":
        trace["stopped_at"] = f"review:{outcome}"; return trace

    # 4) promote — no-server-key membrane
    p = review_promotion({"cell_state": {}, "edit_id": edit[":edit/id"],
                          "entity": edit[":edit/target-entity"], "attr": edit[":edit/target-attr"],
                          "value": edit[":edit/proposed-value"], "outcome": outcome,
                          "to_sourcing": edit[":edit/sourcing"], "provenance": edit[":edit/provenance"],
                          "signed_by": signer, "as_of": as_of})
    if p["cell_state"]["phase"] != PromotePhase.CLEARED.value:
        trace["stopped_at"] = "promote"; return trace
    trace["promoted"] = True

    # 5) revision_log — append-only
    a = append({"cell_state": {}, "history": history, "edit": edit, "as_of": as_of})
    if a["cell_state"]["phase"] != RevisionPhase.APPENDED.value:
        trace["stopped_at"] = "revision_log"; return trace
    trace["appended"] = True
    trace["history"] = a["cell_state"]["history"]
    return trace


# ── the four routes, threaded through the real cells ────────────────────────────
def test_auto_accept_flows_to_appended():
    e = _edit("f1", kind=":kg-fact", attr=":hq-address", value="Hsinchu 300-096")
    tr = run_flow(e)
    assert tr["route"] == "auto-accept" and tr["outcome"] == "accepted"
    assert tr["promoted"] and tr["appended"] and len(tr["history"]) == 1


def test_high_risk_vote_accepted_flows_to_appended():
    e = _edit("f2", attr=":status", value=":delisted")    # :status → high → vote
    tr = run_flow(e, yes=8, no=1)
    assert tr["route"] == "vote" and tr["outcome"] == "accepted"
    assert tr["promoted"] and tr["appended"]


def test_high_risk_vote_rejected_stops_before_promote():
    e = _edit("f3", attr=":status", value=":delisted")
    tr = run_flow(e, yes=1, no=8)
    assert tr["route"] == "vote" and tr["outcome"] == "rejected"
    assert not tr["promoted"] and not tr["appended"] and tr["stopped_at"] == "review:rejected"


def test_invariant_edit_reaches_council_pending_not_promoted():
    e = _edit("f4", attr=":license", value="Apache-2.0")   # invariant-adjacent
    tr = run_flow(e, yes=9, no=0)
    assert tr["route"] == "council-lv7" and tr["outcome"] == "pending"
    assert not tr["promoted"] and tr["stopped_at"] == "review:pending"


def test_rider_edit_refused_at_triage_never_reaches_review():
    e = _edit("f5", kind=":actor-profile", entity="kataribe", attr=":actor/description",
              value="now also runs third-party advertising", sourcing=":representative")
    tr = run_flow(e)
    assert tr["route"] == "refused" and tr["stopped_at"] == "triage:refused"
    assert tr["outcome"] is None and not tr["promoted"]


def test_server_signed_promotion_is_refused_in_the_chain():
    e = _edit("f6", attr=":hq-address", value="X", kind=":kg-fact")
    tr = run_flow(e, signer="server-bot")
    # review tally refuses a server signature first (no-server-key), so it never promotes
    assert not tr["promoted"] and tr["stopped_at"] in ("review", "promote")


def test_chain_history_grows_across_two_accepted_edits():
    h = []
    h = run_flow(_edit("g1", attr=":hq-address", value="v1", kind=":kg-fact"), history=h, as_of=10)["history"]
    h = run_flow(_edit("g2", attr=":hq-address", value="v2", kind=":kg-fact"), history=h, as_of=20)["history"]
    assert len(h) == 2     # append-only across independent membrane runs


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"{len(fns) - failed}/{len(fns)} passed in cells/test_membrane_flow.py")
    sys.exit(1 if failed else 0)
