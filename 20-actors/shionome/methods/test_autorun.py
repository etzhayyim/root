"""test_autorun.py — 潮目 (shionome) AUTONOMOUS heartbeat loop. ADR-2606072200.

Proves the actor runs its full observe→validate→weave→analyze→dry-run-post→persist cycle by
ITSELF over the kotoba Datom log, append-only + content-addressed, with NO live external I/O.
"""
from __future__ import annotations

import pathlib
import tempfile

import autorun
import kotoba
from _t import run


def test_single_cycle_persists_tx():
    with tempfile.TemporaryDirectory() as dr:
        log = pathlib.Path(dr) / "log.edn"
        beat = autorun.run_cycle(1, log_path=log)
        assert beat["regime"] == "risk-on"
        assert beat["datoms"] > 0 and beat["posts"] == 3
        assert len(kotoba.read_log(log)) == 1


def test_multi_cycle_grows_append_only():
    with tempfile.TemporaryDirectory() as dr:
        log = pathlib.Path(dr) / "log.edn"
        res = autorun.run_autonomous(3, log_path=log)
        assert res["cycles"] == 3
        assert res["log_length"] == 3
        assert res["chain"]["ok"] is True


def test_cycles_link_into_dag():
    with tempfile.TemporaryDirectory() as dr:
        log = pathlib.Path(dr) / "log.edn"
        autorun.run_autonomous(2, log_path=log)
        txs = kotoba.read_log(log)
        # tx 2's prev is tx 1's cid (a real commit-DAG, not independent snapshots)
        assert txs[1][":tx/prev"] == txs[0][":tx/cid"]


def test_run_is_deterministic_resume_safe():
    with tempfile.TemporaryDirectory() as dr:
        a = autorun.run_autonomous(2, log_path=pathlib.Path(dr) / "a.edn")
        b = autorun.run_autonomous(2, log_path=pathlib.Path(dr) / "b.edn")
        assert a["head_cid"] == b["head_cid"]   # same input → same content address


def test_persisted_posts_are_dry_run_only():
    with tempfile.TemporaryDirectory() as dr:
        log = pathlib.Path(dr) / "log.edn"
        autorun.run_cycle(1, log_path=log)
        txs = kotoba.read_log(log)
        statuses = [d[3] for d in txs[0][":tx/datoms"] if d[2] == ":post/status"]
        assert statuses and all(s == ":dry-run" for s in statuses)   # G8 — never :published


def test_no_published_status_anywhere():
    with tempfile.TemporaryDirectory() as dr:
        log = pathlib.Path(dr) / "log.edn"
        autorun.run_autonomous(2, log_path=log)
        blob = log.read_text(encoding="utf-8")
        assert ":published" not in blob   # outward publication stays G8-gated


if __name__ == "__main__":
    run("autorun", [(n, f) for n, f in sorted(globals().items())
                    if n.startswith("test_") and callable(f)])
