#!/usr/bin/env python3
"""test_autorun.py — kabuto autonomous supply-chain heartbeat + kotoba Datom-log invariants.
ADR-2606022000. Standalone-runnable (`python3 test_autorun.py`), stdlib only, hermetic.

Guards the autonomy + persistence + resilience-not-target-list contract for the fleet:

  - the loop persists one content-addressed tx per heartbeat to an append-only log;
  - the log is a verifiable commit-DAG (every CID recomputes; tamper is detected);
  - **determinism / resume-safe**: the persisted datoms are in CANONICAL sorted order, so the CID
    is reproducible across processes even though kabuto's analyze builds some derived lists by
    iterating PYTHONHASHSEED-randomized sets (this is the bug `_canonical_order` fixes);
  - it is append-only (re-running grows the log, never rewrites);
  - derived :supply/* signals are flagged :supply/derived (recomputed-on-read);
  - **G2 resilience, not target-list**: the log carries concentration/accountability framing and
    NO raid/takeover/target attr;
  - it does NO external I/O (offline ingest, local persist — G7/G11 stay gated).
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import autorun  # noqa: E402
import kotoba  # noqa: E402

PASS = 0
FAIL = 0


def ok(cond, msg):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"  ✗ {msg}")


def _tmp_log() -> pathlib.Path:
    fd, p = tempfile.mkstemp(suffix=".datoms.kotoba.edn")
    os.close(fd)
    path = pathlib.Path(p)
    path.unlink()
    return path


def test_heartbeat_persists():
    log = _tmp_log()
    try:
        res = autorun.run_autonomous(cycles=3, log_path=log)
        ok(res["log_length"] == 3, "one tx per heartbeat")
        ok(all(b["datoms"] > 0 for b in res["beats"]), "every heartbeat persisted datoms")
        ok(res["chain"]["ok"], "commit-DAG verifies (chain OK)")
        ok(res["head_cid"].startswith("b"), "head CID is content-addressed")
    finally:
        log.unlink(missing_ok=True)


def test_canonical_order_is_deterministic():
    # the determinism guarantee: persisted datoms are in canonical sorted order, so the CID is
    # reproducible across processes regardless of analyze's set-iteration order.
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        tx = kotoba.read_log(log)[0]
        datoms = tx[":tx/datoms"]
        keyed = [json.dumps(d, ensure_ascii=False, sort_keys=True) for d in datoms]
        ok(keyed == sorted(keyed), "persisted datoms are in canonical sorted order (cross-process deterministic)")
        # _canonical_order is idempotent
        once = autorun._canonical_order(datoms)
        twice = autorun._canonical_order(once)
        ok(once == twice, "_canonical_order is idempotent")
    finally:
        log.unlink(missing_ok=True)


def test_append_only_and_tamper():
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        first = kotoba.read_log(log)
        autorun.run_cycle(2, log_path=log)
        second = kotoba.read_log(log)
        ok(len(second) == len(first) + 1, "second heartbeat appends, does not rewrite")
        ok(second[1][":tx/prev"] == first[0][":tx/cid"], "tx 2 links tx 1's CID (commit-DAG)")
        lines = log.read_text(encoding="utf-8").splitlines()
        for i, ln in enumerate(lines):
            if ":tx/id 1 " in ln:
                lines[i] = ln.replace(":supply/derived true", ":supply/derived false", 1)
                break
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        v = kotoba.verify_chain(log)
        ok(not v["ok"] and v["broken_at"] == 0, "tampering an earlier tx breaks the chain")
    finally:
        log.unlink(missing_ok=True)


def test_g2_resilience_not_target_list():
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        tx = kotoba.read_log(log)[0]
        attrs = {str(d[2]) for d in tx[":tx/datoms"]}
        ok(any(a.startswith(":supply/") for a in attrs), "derived :supply/* signals persisted")
        for forbidden in (":supply/target", ":supply/raid", ":supply/takeover-target",
                          ":target", ":supply/who-to-hit", ":supply/attack"):
            ok(forbidden not in attrs, f"no target-list attr `{forbidden}` in the log (G2)")
    finally:
        log.unlink(missing_ok=True)


def test_derived_flagged_and_append_only_op():
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        tx = kotoba.read_log(log)[0]
        derived = [d for d in tx[":tx/datoms"] if d[2] == ":supply/derived"]
        ok(len(derived) > 0, "derived :supply/* signals are persisted")
        ok(all(d[3] is True for d in derived), "every :supply/derived flag is true")
        ops = {d[0] for d in tx[":tx/datoms"]}
        ok(ops == {":db/add"}, "every datom is append-only :db/add (no :db/retract)")
    finally:
        log.unlink(missing_ok=True)


def test_no_external_io():
    import inspect
    src = inspect.getsource(autorun) + inspect.getsource(kotoba)
    for banned in ("urllib", "http.client", "socket", "requests", "subprocess"):
        ok(banned not in src, f"autorun/kotoba does no external I/O (no `{banned}`)")


if __name__ == "__main__":
    test_heartbeat_persists()
    test_canonical_order_is_deterministic()
    test_append_only_and_tamper()
    test_g2_resilience_not_target_list()
    test_derived_flagged_and_append_only_op()
    test_no_external_io()
    print(f"\ntest_autorun: {PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
