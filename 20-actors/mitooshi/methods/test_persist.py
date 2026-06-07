#!/usr/bin/env python3
"""Tests for the mitooshi append-only chokepoint-intel persistence (methods/persist.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_persist.py
    python3 test_persist.py

The load-bearing property under test: the trail is APPEND-ONLY (非終末論). A re-run is
idempotent; a new snapshot is additive; an existing observation is NEVER removed or
mutated; the emitted EDN round-trips through the same reader a live ingest would use.
"""
from __future__ import annotations

import pathlib
import sys
import tempfile

try:
    from bridge import bridge
    from analyze import load_edn
    from persist import (append_obs, emit_trail_edn, load_trail, merge_series, persist)
except ImportError:
    from mitooshi.methods.bridge import bridge  # type: ignore
    from mitooshi.methods.analyze import load_edn  # type: ignore
    from mitooshi.methods.persist import (  # type: ignore
        append_obs, emit_trail_edn, load_trail, merge_series, persist)

_BRIDGE = pathlib.Path(__file__).resolve().parent.parent / "data" / "bridge"


def _by_actor():
    return {
        "watari": load_edn(_BRIDGE / "watari-sample.edn"),
        "watatsuna": load_edn(_BRIDGE / "watatsuna-sample.edn"),
    }


def test_append_to_empty_trail_adds_all():
    b = bridge(_by_actor(), observed_at=1)
    merged, added, dup = append_obs([], b["obs"])
    assert added == len(b["obs"]) and dup == 0
    assert len(merged) == len(b["obs"])


def test_reappend_same_snapshot_is_idempotent():
    b = bridge(_by_actor(), observed_at=1)
    merged, _, _ = append_obs([], b["obs"])
    merged2, added2, dup2 = append_obs(merged, b["obs"])
    assert added2 == 0 and dup2 == len(b["obs"])      # nothing new, all duplicates
    assert len(merged2) == len(merged)                 # trail unchanged


def test_new_snapshot_is_additive_never_removes():
    b1 = bridge(_by_actor(), observed_at=1)
    b2 = bridge(_by_actor(), observed_at=2)
    merged, _, _ = append_obs([], b1["obs"])
    before_ids = {o[":obs/id"] for o in merged}
    merged2, added2, dup2 = append_obs(merged, b2["obs"])
    after_ids = {o[":obs/id"] for o in merged2}
    assert before_ids <= after_ids                     # 非終末論: never drops an obs
    assert added2 == len(b2["obs"]) and dup2 == 0      # different ts → all new


def test_existing_obs_values_are_not_mutated():
    b1 = bridge(_by_actor(), observed_at=1)
    merged, _, _ = append_obs([], b1["obs"])
    snapshot = {o[":obs/id"]: o[":obs/value"] for o in merged}
    # a later (hypothetically revised) snapshot at the same ts must NOT overwrite
    merged2, added, dup = append_obs(merged, b1["obs"])
    after = {o[":obs/id"]: o[":obs/value"] for o in merged2}
    assert after == snapshot and added == 0


def test_merge_series_is_union_first_wins():
    b = bridge(_by_actor(), observed_at=1)
    merged = merge_series({}, b["series"])
    assert set(merged) == set(b["series"])
    # re-merging keeps the first definition (stable identity)
    again = merge_series(merged, b["series"])
    assert again == merged


def test_emit_round_trips_through_reader():
    b = bridge(_by_actor(), observed_at=1)
    merged_obs, _, _ = append_obs([], b["obs"])
    edn = emit_trail_edn(b["series"], merged_obs)
    recs = load_edn_from_str(edn)
    obs = [r for r in recs if ":obs/id" in r]
    series = [r for r in recs if ":series/id" in r]
    assert len(obs) == len(merged_obs) and len(series) == len(b["series"])
    # values survive the round-trip
    vals = sorted(o[":obs/value"] for o in obs)
    assert vals == sorted(o[":obs/value"] for o in merged_obs)


def test_persist_to_disk_two_snapshots_accumulate():
    with tempfile.TemporaryDirectory() as d:
        trail = pathlib.Path(d) / "chokepoint-trail.kotoba.edn"
        s1 = persist(trail, bridge(_by_actor(), observed_at=1))
        s2 = persist(trail, bridge(_by_actor(), observed_at=2))
        s3 = persist(trail, bridge(_by_actor(), observed_at=2))  # idempotent re-run
        assert s1["added"] > 0
        assert s2["added"] == s1["added"] and s2["duplicate"] == 0
        assert s3["added"] == 0 and s3["duplicate"] == s2["added"]
        # on-disk trail holds both snapshots
        _, obs = load_trail(trail)
        ats = sorted({o[":obs/observed-at"] for o in obs})
        assert ats == [1, 2]


def test_persist_header_marks_derived_and_gated():
    edn = emit_trail_edn(*(lambda b: (b["series"],
                                      append_obs([], b["obs"])[0]))(bridge(_by_actor(), 1)))
    assert "APPEND-ONLY" in edn and "DERIVED" in edn
    assert "G10-gated" in edn and "非終末論" in edn


# ── helper: parse EDN from a string (load_edn only takes a path) ──────────────
def load_edn_from_str(s: str):
    with tempfile.NamedTemporaryFile("w", suffix=".edn", delete=False) as f:
        f.write(s)
        p = pathlib.Path(f.name)
    try:
        return load_edn(p)
    finally:
        p.unlink()


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"persist.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
