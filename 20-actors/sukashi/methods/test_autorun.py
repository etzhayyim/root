#!/usr/bin/env python3
"""test_autorun.py — sukashi autonomous observatory heartbeat + kotoba Datom-log invariants.
ADR-2606071600. Standalone-runnable (`python3 test_autorun.py`), stdlib only, hermetic.

Guards the autonomy + persistence + non-adjudication contract that lets sukashi run on the fleet:

  - the loop persists one content-addressed tx per heartbeat to an append-only log;
  - the log is a verifiable commit-DAG (every CID recomputes; tamper is detected);
  - it is deterministic / resume-safe (same cycles → same CIDs) and append-only;
  - derived :adsupply/* + :adfraud/* signals are flagged :derived (recomputed-on-read);
  - **G4 non-adjudication**: every persisted fraud-signal carries :non-adjudicating true +
    :sourcing :synthesized — no real entity is implicated;
  - it does NO external I/O (offline ingest, local persist — G7/G11 stay gated).
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
        ok(res["log_length"] == 3, "one tx per heartbeat")
        ok(all(b["datoms"] > 0 for b in res["beats"]), "every heartbeat persisted datoms")
        ok(res["chain"]["ok"], "commit-DAG verifies (chain OK)")
        ok(res["head_cid"].startswith("b"), "head CID is content-addressed")
    finally:
        log.unlink(missing_ok=True)


def test_deterministic_resume_safe():
    a, b = _tmp_log(), _tmp_log()
    try:
        ra = autorun.run_autonomous(cycles=3, log_path=a)
        rb = autorun.run_autonomous(cycles=3, log_path=b)
        ok([x["cid"] for x in ra["beats"]] == [x["cid"] for x in rb["beats"]],
           "same cycles → same CIDs (deterministic / resume-safe)")
    finally:
        a.unlink(missing_ok=True)
        b.unlink(missing_ok=True)


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
                lines[i] = ln.replace(":adsupply/derived true", ":adsupply/derived false", 1)
                break
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        v = kotoba.verify_chain(log)
        ok(not v["ok"] and v["broken_at"] == 0, "tampering an earlier tx breaks the chain")
    finally:
        log.unlink(missing_ok=True)


def test_g4_fraud_signals_non_adjudicating():
    # the defining sukashi invariant: every persisted fraud-signal is non-adjudicating + synthesized.
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        tx = kotoba.read_log(log)[0]
        # collect every entity that is a fraud signal (carries an :adfraud.signal/* attr)
        sig_entities = {d[1] for d in tx[":tx/datoms"] if str(d[2]).startswith(":adfraud.signal/")}
        ok(len(sig_entities) > 0, "fraud-signal entities are persisted")
        for e in sig_entities:
            attrs = {d[2]: d[3] for d in tx[":tx/datoms"] if d[1] == e}
            ok(attrs.get(":adfraud.signal/non-adjudicating") is True,
               f"fraud signal {e} carries :non-adjudicating true (G4)")
            ok(attrs.get(":adfraud.signal/sourcing") == ":synthesized",
               f"fraud signal {e} is :synthesized (G4 — no real entity implicated)")
    finally:
        log.unlink(missing_ok=True)


def test_derived_flagged():
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        tx = kotoba.read_log(log)[0]
        derived_attrs = [d for d in tx[":tx/datoms"]
                         if d[2] in (":adsupply/derived", ":adfraud/derived")]
        ok(len(derived_attrs) > 0, "derived :adsupply/* + :adfraud/* signals are persisted")
        ok(all(d[3] is True for d in derived_attrs), "every derived flag is true (recomputed-on-read)")
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
    test_deterministic_resume_safe()
    test_append_only_and_tamper()
    test_g4_fraud_signals_non_adjudicating()
    test_derived_flagged()
    test_no_external_io()
    print(f"\ntest_autorun: {PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
