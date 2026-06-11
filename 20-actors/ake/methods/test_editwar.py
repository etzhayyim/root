#!/usr/bin/env python3
"""Edit-war / challenge→revert integration test for 朱 (ake) — ADR-2606052100 roadmap item.

Wires triage (the challenge routes as high-risk → vote) to revision.revert (the append-only
rollback). Proves the Wikipedia revert/rollback semantics on the immutable log: a bad edit is
UNDONE by restoring its predecessor, yet every revision (incl. the bad one and the revert) stays in
the history — the war is fully auditable (danjo-observable), nothing is deleted (G5).
"""
from __future__ import annotations

from revision import append_revision, as_of, current, history_of, revert
from triage import score_edit

ENT, ATTR = "org.corp.example-listed", "status"


def _edit(eid, value, author, op=":assert"):
    return {
        ":edit/id": eid, ":edit/target-kind": ":kg-fact", ":edit/target-entity": ENT,
        ":edit/target-attr": ":" + ATTR, ":edit/op": op, ":edit/proposed-value": value,
        ":edit/author": author, ":edit/author-kind": ":member",
        ":edit/provenance": "https://primary.example.com/notice",
        ":edit/rationale": "sourced correction with adequate explanation",
        ":edit/sourcing": ":authoritative",
    }


def _build_war():
    """v1 good (accepted) → v2 bad (accepted) → challenge upheld → revert to v1."""
    h: list = []
    h = append_revision(h, _edit("v1", ":active", "did:m:a"), as_of=100)      # good
    h = append_revision(h, _edit("v2", ":delisted-WRONG", "did:m:b"), as_of=200)  # bad, now current
    # member C challenges the current (bad) value
    challenge = _edit("c1", "", "did:m:c", op=":challenge")
    tri = score_edit(challenge)
    # challenge upheld by vote (simulated) → revert
    h = revert(h, ENT, ATTR, by="did:m:c", edit_id="c1", as_of=300)
    return h, tri


def test_challenge_routes_high_to_vote():
    _, tri = _build_war()
    assert tri[":triage/risk"] == ":high"        # op==challenge is high-risk
    assert tri[":triage/route"] == ":vote"       # edit-wars are settled by a vote, never auto


def test_revert_restores_predecessor_value():
    h, _ = _build_war()
    cur = current(h, ENT, ATTR)
    assert cur[":revision/value"] == ":active"   # reverted to v1, NOT the bad v2
    assert cur[":revision/op"] == ":retract"     # the revert is itself an append (no delete)


def test_war_history_is_fully_preserved():
    h, _ = _build_war()
    hist = history_of(h, ENT, ATTR)
    assert len(hist) == 3                         # v1 + v2(bad) + revert — nothing deleted
    assert [r[":revision/as-of"] for r in hist] == [100, 200, 300]


def test_bad_value_remains_auditable_in_time_travel():
    h, _ = _build_war()
    # the bad edit is undone for the CURRENT reader, but the record that it once stood is intact
    assert as_of(h, ENT, ATTR, 250)[":revision/value"] == ":delisted-WRONG"  # auditable (danjo)
    assert as_of(h, ENT, ATTR, 150)[":revision/value"] == ":active"          # before the bad edit
    assert as_of(h, ENT, ATTR, 350)[":revision/value"] == ":active"          # after the revert


def test_revert_of_sole_revision_restores_empty():
    h = append_revision([], _edit("only", ":x", "did:m:a"), as_of=10)
    h = revert(h, ENT, ATTR, by="did:m:c", edit_id="c", as_of=20)
    assert current(h, ENT, ATTR)[":revision/value"] == ""   # undone to pre-existence


def test_revert_with_no_history_raises():
    try:
        revert([], ENT, ATTR, by="did:m:c", edit_id="c", as_of=1)
        assert False, "expected ValueError"
    except ValueError as ex:
        assert "nothing to revert" in str(ex)


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
    print(f"{len(fns) - failed}/{len(fns)} passed in test_editwar.py")
    sys.exit(1 if failed else 0)
