#!/usr/bin/env python3
"""test_autorun.py — keizu autonomous power-relations heartbeat + kotoba Datom-log invariants.
ADR-2606066000. Standalone-runnable (`python3 test_autorun.py`), stdlib only, hermetic.

Guards the autonomy + persistence + accountability-not-target-list contract for the fleet:

  - the loop persists one content-addressed tx per heartbeat to an append-only log;
  - the log is a verifiable commit-DAG (every CID recomputes; tamper is detected);
  - **determinism / resume-safe**: persisted datoms are canonically ordered, so the CID is
    reproducible across processes regardless of concentration's set-iteration order;
  - it is append-only; derived :keizu.conc/* signals are flagged :keizu.conc/derived;
  - **G4 edge-primary / non-adjudicating**: revolving-door + award-and-fund datoms carry
    `:keizu.conc/non-adjudicating true` (a co-occurrence of disclosed flows, NOT an allegation);
  - **G1 no-doxxing**: NO PII node attr (email/phone/address/dob/…) appears in the log;
  - it does NO external I/O (offline seed, local persist — G7/G8 stay gated).
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
from weave import PII_FORBIDDEN_NODE_ATTRS  # noqa: E402

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


def test_canonical_order_deterministic():
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        datoms = kotoba.read_log(log)[0][":tx/datoms"]
        keyed = [json.dumps(d, ensure_ascii=False, sort_keys=True) for d in datoms]
        ok(keyed == sorted(keyed), "persisted datoms are in canonical sorted order (cross-process deterministic)")
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
                lines[i] = ln.replace(":keizu.conc/derived true", ":keizu.conc/derived false", 1)
                break
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        v = kotoba.verify_chain(log)
        ok(not v["ok"] and v["broken_at"] == 0, "tampering an earlier tx breaks the chain")
    finally:
        log.unlink(missing_ok=True)


def test_g4_non_adjudicating_co_occurrence():
    # revolving-door + award-and-fund are co-occurrences of disclosed flows, NEVER allegations.
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        datoms = kotoba.read_log(log)[0][":tx/datoms"]
        flagged_ents = {d[1] for d in datoms if d[2] == ":keizu.conc/non-adjudicating" and d[3] is True}
        award_ents = {d[1] for d in datoms if d[2] == ":keizu.conc/award-and-fund-node"}
        revolving_ents = {d[1] for d in datoms if d[2] == ":keizu.conc/revolving-from"}
        for e in award_ents | revolving_ents:
            ok(e in flagged_ents, f"{e} carries :keizu.conc/non-adjudicating true (G4)")
        # no verdict/allegation attr anywhere
        attrs = {str(d[2]).lower() for d in datoms}
        for tok in ("verdict", "guilt", "corrupt", "bribe", "illegal", "wrongdoing", "allegation"):
            ok(not any(tok in a for a in attrs), f"no verdict token `{tok}` in any attr (G4)")
    finally:
        log.unlink(missing_ok=True)


def test_g1_no_doxxing():
    # G1: NO PII node attr may reach the log — keizu maps power entities, never private persons.
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        datoms = kotoba.read_log(log)[0][":tx/datoms"]
        attrs = {str(d[2]).lower() for d in datoms}
        for pii in PII_FORBIDDEN_NODE_ATTRS:
            ok(not any(pii in a.split("/")[-1] for a in attrs),
               f"no PII attr containing `{pii}` in the log (G1 no-doxxing)")
        ops = {d[0] for d in datoms}
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
    test_canonical_order_deterministic()
    test_deterministic_resume_safe()
    test_append_only_and_tamper()
    test_g4_non_adjudicating_co_occurrence()
    test_g1_no_doxxing()
    test_no_external_io()
    print(f"\ntest_autorun: {PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
