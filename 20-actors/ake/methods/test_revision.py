#!/usr/bin/env python3
"""Tests for revision.py — append-only history, time-travel reads, non-destructive promotion (G5)."""
from __future__ import annotations

import pathlib

from _edn import load_edn
from revision import append_revision, as_of, current, history_of, promote_sourcing

_SEED = pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-edit-graph.kotoba.edn"


def _e(eid):
    return {e[":edit/id"]: e for e in load_edn(_SEED)[":edit/batch"]}[eid]


def test_append_returns_new_list_and_never_shrinks():
    h0: list = []
    h1 = append_revision(h0, _e("e1"), as_of=100)
    assert len(h0) == 0 and len(h1) == 1          # input untouched
    h2 = append_revision(h1, _e("e3"), as_of=110)
    assert len(h2) == 2 and len(h1) == 1


def test_current_is_latest_as_of():
    h = []
    h = append_revision(h, {**_e("e1"), ":edit/proposed-value": "old"}, as_of=100)
    h = append_revision(h, {**_e("e1"), ":edit/proposed-value": "new"}, as_of=200)
    cur = current(h, "org.corp.tsmc", "hq-address")
    assert cur[":revision/value"] == "new"


def test_as_of_time_travel():
    h = []
    h = append_revision(h, {**_e("e1"), ":edit/proposed-value": "old"}, as_of=100)
    h = append_revision(h, {**_e("e1"), ":edit/proposed-value": "new"}, as_of=200)
    assert as_of(h, "org.corp.tsmc", "hq-address", 150)[":revision/value"] == "old"
    assert as_of(h, "org.corp.tsmc", "hq-address", 250)[":revision/value"] == "new"
    assert as_of(h, "org.corp.tsmc", "hq-address", 50) is None


def test_history_of_is_ordered_and_full():
    h = []
    h = append_revision(h, {**_e("e1"), ":edit/proposed-value": "v1"}, as_of=300)
    h = append_revision(h, {**_e("e1"), ":edit/proposed-value": "v2"}, as_of=100)
    h = append_revision(h, {**_e("e1"), ":edit/proposed-value": "v3"}, as_of=200)
    hist = history_of(h, "org.corp.tsmc", "hq-address")
    assert [r[":revision/as-of"] for r in hist] == [100, 200, 300]   # sorted, nothing dropped


def test_promote_sourcing_is_non_destructive():
    h = []
    h = append_revision(h, {**_e("e1"), ":edit/sourcing": ":representative",
                            ":edit/proposed-value": "addr"}, as_of=100)
    before = len(h)
    h2 = promote_sourcing(h, "org.corp.tsmc", "hq-address",
                          provenance="https://tsmc.com/profile", as_of=200, by="did:member:x",
                          edit_id="ePromote")
    assert len(h2) == before + 1                       # appended, not replaced
    assert current(h2, "org.corp.tsmc", "hq-address")[":revision/sourcing"] == ":authoritative"
    # the representative revision still exists at its own as-of
    assert as_of(h2, "org.corp.tsmc", "hq-address", 150)[":revision/sourcing"] == ":representative"


def test_promote_requires_verifiable_provenance():
    h = append_revision([], _e("e1"), as_of=100)
    try:
        promote_sourcing(h, "org.corp.tsmc", "hq-address", provenance="trust me",
                         as_of=200, by="did:member:x", edit_id="eP")
        assert False, "expected ValueError"
    except ValueError as ex:
        assert "G4" in str(ex)


def test_promote_with_nothing_to_promote_raises():
    try:
        promote_sourcing([], "org.corp.none", "x", provenance="https://e.com",
                         as_of=1, by="did:member:x", edit_id="eP")
        assert False, "expected ValueError"
    except ValueError as ex:
        assert "nothing to promote" in str(ex)


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
    print(f"{len(fns) - failed}/{len(fns)} passed in test_revision.py")
    sys.exit(1 if failed else 0)
