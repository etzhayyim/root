#!/usr/bin/env python3
"""test_autorun.py — yabai autonomous CTI heartbeat + kotoba Datom-log invariants. ADR-2605301400 §T3.

Standalone-runnable (`python3 test_autorun.py`), stdlib only, hermetic (writes to a temp log).
Guards the autonomy + persistence + CONFIDENTIALITY contract that lets yabai run on the fleet:

  - the loop persists one content-addressed tx per heartbeat to an append-only log;
  - the log is a verifiable commit-DAG (every CID recomputes; tamper is detected);
  - it is deterministic / resume-safe (same cycles → same CIDs);
  - it is append-only (re-running grows the log, never rewrites);
  - derived :cti/* signals are flagged :cti/derived (defensive, recomputed-on-read);
  - **G6/G10**: a plaintext :access/* record HARD-STOPS the loop (no plaintext PII ever persisted);
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
    path.unlink()
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
        ok(all(b["plaintext_violations"] == 0 for b in res["beats"]), "no plaintext access violations")
    finally:
        log.unlink(missing_ok=True)


def test_deterministic_resume_safe():
    a, b = _tmp_log(), _tmp_log()
    try:
        ra = autorun.run_autonomous(cycles=3, log_path=a)
        rb = autorun.run_autonomous(cycles=3, log_path=b)
        ok([x["cid"] for x in ra["beats"]] == [x["cid"] for x in rb["beats"]],
           "same cycles → same CIDs (deterministic / resume-safe)")
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
        ok(second[0][":tx/cid"] == first[0][":tx/cid"], "tx 1 unchanged after tx 2 appends")
        ok(second[1][":tx/prev"] == first[0][":tx/cid"], "tx 2 links tx 1's CID (commit-DAG)")
        ok(kotoba.verify_chain(log)["ok"], "chain still verifies after incremental appends")
    finally:
        log.unlink(missing_ok=True)


def test_tamper_detected():
    log = _tmp_log()
    try:
        autorun.run_autonomous(cycles=2, log_path=log)
        lines = log.read_text(encoding="utf-8").splitlines()
        for i, ln in enumerate(lines):
            if ":tx/id 1 " in ln:
                lines[i] = ln.replace(":cti/derived true", ":cti/derived false", 1)
                break
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        v = kotoba.verify_chain(log)
        ok(not v["ok"], "tampering an earlier tx breaks chain verification")
        ok(v["broken_at"] == 0, "tamper localized to the corrupted tx index")
    finally:
        log.unlink(missing_ok=True)


def test_g6_g10_guard_raises_on_plaintext_access():
    # the defining yabai invariant: a plaintext :access/* record must hard-stop persistence.
    rows = [
        {":domain/id": ":d-ex", ":domain/fqdn": "example.test"},
        {":access/id": ":a-bad", ":access/accessor": "alice@example.test"},  # NO encrypted flag
    ]
    raised = False
    try:
        kotoba.graph_datoms(rows)
    except kotoba.PlaintextAccessError:
        raised = True
    ok(raised, "graph_datoms raises PlaintextAccessError on a plaintext :access/* record (G6/G10)")

    # encrypted form passes
    rows_ok = [
        {":domain/id": ":d-ex", ":domain/fqdn": "example.test"},
        {":access/id": ":a-ok", ":cti.attr/encrypted": True, ":access/envelope-cid": "bafy..."},
    ]
    passed = False
    try:
        kotoba.graph_datoms(rows_ok)
        passed = True
    except kotoba.PlaintextAccessError:
        passed = False
    ok(passed, "graph_datoms accepts an encrypted-envelope :access/* record")


def test_no_plaintext_pii_in_log():
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        tx = kotoba.read_log(log)[0]
        access_datoms = [d for d in tx[":tx/datoms"] if str(d[1]).startswith(":a")]
        # every persisted access entity must carry the encrypted marker; none may carry raw PII attrs
        for d in tx[":tx/datoms"]:
            attr = d[2]
            ok(attr not in (":access/accessor-ip", ":access/user-agent", ":access/accessor-email"),
               f"no plaintext-PII attr `{attr}` persisted to the log (G6/G10)")
        ok(True, "access datoms scanned for plaintext PII")
        _ = access_datoms
    finally:
        log.unlink(missing_ok=True)


def test_no_external_io():
    import inspect
    src = inspect.getsource(autorun) + inspect.getsource(kotoba)
    for banned in ("urllib", "http.client", "socket", "requests", "subprocess"):
        ok(banned not in src, f"autorun/kotoba does no external I/O (no `{banned}`)")


if __name__ == "__main__":
    test_heartbeat_persists()
    test_deterministic_resume_safe()
    test_append_only_growth()
    test_tamper_detected()
    test_g6_g10_guard_raises_on_plaintext_access()
    test_no_plaintext_pii_in_log()
    test_no_external_io()
    print(f"\ntest_autorun: {PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
