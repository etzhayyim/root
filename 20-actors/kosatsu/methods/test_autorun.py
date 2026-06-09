#!/usr/bin/env python3
"""test_autorun.py — kosatsu autonomous competing-claim heartbeat + kotoba Datom-log invariants.
ADR-2606072000. Standalone-runnable (`python3 test_autorun.py`), stdlib only, hermetic.

Guards the autonomy + persistence + neutral-competing-claim contract for the fleet:

  - the loop persists one content-addressed tx per heartbeat to an append-only log;
  - the log is a verifiable commit-DAG (every CID recomputes; tamper is detected);
  - **determinism / resume-safe**: persisted datoms are canonically ordered → CID reproducible
    across processes regardless of report's set-iteration order;
  - it is append-only; derived :kosatsu.div/* signals are flagged :kosatsu.div/derived;
  - **every designation is an ATTRIBUTED event**: each carries a `:designation/asserter`, and the
    asserter is NEVER etzhayyim (etzhayyim authors no designation);
  - **no verdict / no per-subject score**: no score/verdict attr is representable; the per-subject
    divergence `:kosatsu.div/class` is one of {contested | unanimous | single-asserter};
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
                lines[i] = ln.replace(":kosatsu.div/derived true", ":kosatsu.div/derived false", 1)
                break
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        v = kotoba.verify_chain(log)
        ok(not v["ok"] and v["broken_at"] == 0, "tampering an earlier tx breaks the chain")
    finally:
        log.unlink(missing_ok=True)


def test_every_designation_attributed():
    # etzhayyim authors NO designation: every designation event carries a non-etzhayyim asserter.
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        datoms = kotoba.read_log(log)[0][":tx/datoms"]
        desig_ents = {d[1] for d in datoms if str(d[2]).startswith(":designation/")}
        ok(len(desig_ents) > 0, "designation events persisted")
        for e in desig_ents:
            asserters = [d[3] for d in datoms if d[1] == e and d[2] == ":designation/asserter"]
            ok(len(asserters) == 1, f"designation {e} carries exactly one :asserter")
            ok(asserters and "etzhayyim" not in str(asserters[0]).lower(),
               f"designation {e} asserter is NOT etzhayyim (etzhayyim authors no designation)")
    finally:
        log.unlink(missing_ok=True)


def test_no_score_no_verdict_neutral_class():
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        datoms = kotoba.read_log(log)[0][":tx/datoms"]
        attrs = {str(d[2]).lower() for d in datoms}
        for tok in ("score", "rank", "verdict", "guilt", "legitimacy", "true-crime", "trustworthiness"):
            ok(not any(tok in a for a in attrs), f"no `{tok}` attr in the log (no verdict / no score)")
        classes = {d[3] for d in datoms if d[2] == ":kosatsu.div/class"}
        ok(classes and classes <= {":contested", ":unanimous", ":single-asserter"},
           f"divergence class ∈ {{contested,unanimous,single-asserter}} (neutral fact), got {classes}")
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
    test_every_designation_attributed()
    test_no_score_no_verdict_neutral_class()
    test_no_external_io()
    print(f"\ntest_autorun: {PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
