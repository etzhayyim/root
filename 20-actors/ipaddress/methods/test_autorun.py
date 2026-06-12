#!/usr/bin/env python3
"""test_autorun.py — ipaddress autonomous heartbeat + kotoba Datom-log invariants. ADR-2605301400 §T2.

Standalone-runnable (`python3 test_autorun.py`), stdlib only, hermetic (writes to a temp log).
Guards the autonomy + persistence contract that lets ipaddress run on the Murakumo fleet:

  - the loop persists one content-addressed tx per heartbeat to an append-only log;
  - the log is a verifiable commit-DAG (every CID recomputes; tamper is detected);
  - it is deterministic / resume-safe (same cycles → same CIDs);
  - it is append-only (re-running grows the log, never rewrites);
  - derived :ipnet/* concentration datoms are flagged :ipnet/derived (G2/G10);
  - it does NO external I/O (offline ingest, local persist — G7/G8 stay gated).
"""
from __future__ import annotations

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
    path.unlink()  # start absent — append_tx writes the header
    return path


def test_heartbeat_persists():
    log = _tmp_log()
    try:
        res = autorun.run_autonomous(cycles=3, log_path=log)
        ok(res["cycles"] == 3, "ran 3 cycles")
        ok(res["log_length"] == 3, "log has one tx per heartbeat")
        ok(all(b["datoms"] > 0 for b in res["beats"]), "every heartbeat persisted datoms")
        ok(res["chain"]["ok"], "commit-DAG verifies (chain OK)")
        ok(res["head_cid"].startswith("b"), "head CID is content-addressed")
    finally:
        log.unlink(missing_ok=True)


def test_deterministic_resume_safe():
    a = _tmp_log()
    b = _tmp_log()
    try:
        ra = autorun.run_autonomous(cycles=3, log_path=a)
        rb = autorun.run_autonomous(cycles=3, log_path=b)
        cids_a = [bt["cid"] for bt in ra["beats"]]
        cids_b = [bt["cid"] for bt in rb["beats"]]
        ok(cids_a == cids_b, "same cycles → same CIDs (deterministic / resume-safe)")
        ok(ra["head_cid"] == rb["head_cid"], "head CID reproduces across independent runs")
    finally:
        a.unlink(missing_ok=True)
        b.unlink(missing_ok=True)


def test_append_only_growth():
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        first = kotoba.read_log(log)
        autorun.run_cycle(2, log_path=log)
        second = kotoba.read_log(log)
        ok(len(second) == len(first) + 1, "second heartbeat appends, does not rewrite")
        ok(second[0][":tx/cid"] == first[0][":tx/cid"], "tx 1 is unchanged after tx 2 appends")
        ok(second[1][":tx/prev"] == first[0][":tx/cid"], "tx 2 links tx 1's CID (commit-DAG)")
        ok(kotoba.verify_chain(log)["ok"], "chain still verifies after incremental appends")
    finally:
        log.unlink(missing_ok=True)


def test_tamper_detected():
    log = _tmp_log()
    try:
        autorun.run_autonomous(cycles=2, log_path=log)
        lines = log.read_text(encoding="utf-8").splitlines()
        # corrupt a value inside the FIRST transaction's datoms
        for i, ln in enumerate(lines):
            if ":tx/id 1 " in ln:
                lines[i] = ln.replace(":ipnet/derived true", ":ipnet/derived false", 1)
                break
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        v = kotoba.verify_chain(log)
        ok(not v["ok"], "tampering an earlier tx breaks chain verification")
        ok(v["broken_at"] == 0, "tamper localized to the corrupted tx index")
    finally:
        log.unlink(missing_ok=True)


def test_derived_datoms_flagged():
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        tx = kotoba.read_log(log)[0]
        derived = [d for d in tx[":tx/datoms"] if d[2] == ":ipnet/derived"]
        ok(len(derived) > 0, "derived :ipnet/* concentration datoms are persisted")
        ok(all(d[3] is True for d in derived), "every :ipnet/derived datom is flagged true (G2/G10)")
        ops = {d[0] for d in tx[":tx/datoms"]}
        ok(ops == {":db/add"}, "every datom is append-only :db/add (no :db/retract — non-eschatological)")
    finally:
        log.unlink(missing_ok=True)


def test_no_external_io():
    # the loop must import no network module path; offline ingest + local persist only (G7/G8).
    import inspect
    src = inspect.getsource(autorun) + inspect.getsource(kotoba)
    for banned in ("urllib", "http.client", "socket", "requests", "subprocess"):
        ok(banned not in src, f"autorun/kotoba does no external I/O (no `{banned}`)")


if __name__ == "__main__":
    test_heartbeat_persists()
    test_deterministic_resume_safe()
    test_append_only_growth()
    test_tamper_detected()
    test_derived_datoms_flagged()
    test_no_external_io()
    print(f"\ntest_autorun: {PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
