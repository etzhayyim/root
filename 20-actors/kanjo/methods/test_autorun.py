#!/usr/bin/env python3
"""test_autorun.py — kanjō autonomous financial-disclosure heartbeat + kotoba Datom-log invariants.
ADR-2606032000. Standalone-runnable (`python3 test_autorun.py`), stdlib only, hermetic.

Guards the autonomy + persistence + non-adjudication contract for the fleet:

  - the loop persists one content-addressed tx per heartbeat to an append-only log;
  - the log is a verifiable commit-DAG (every CID recomputes; tamper is detected);
  - it is deterministic / resume-safe (same cycles → same CIDs) and append-only;
  - **G5 sourcing-honesty**: every persisted derived :fin.metric / :fin.agg carries
    :sourcing :synthesized — never re-ingested as a disclosed fact;
  - **G2/G4 non-adjudicating / no-advice / no-forecast**: the log carries disclosed facts + ratios
    and NO rating/recommendation/target/forecast attr;
  - it does NO external I/O (offline ingest, local persist — G7 stays gated).
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
        ok(all(b["metrics"] > 0 for b in res["beats"]), "derived ratios computed + persisted")
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
                lines[i] = ln.replace(':fin.metric/sourcing :synthesized',
                                      ':fin.metric/sourcing :authoritative', 1)
                break
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        v = kotoba.verify_chain(log)
        ok(not v["ok"] and v["broken_at"] == 0, "tampering an earlier tx breaks the chain")
    finally:
        log.unlink(missing_ok=True)


def test_g5_derived_synthesized():
    # G5: every derived metric/agg must declare :synthesized — never masquerade as a disclosed fact.
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        tx = kotoba.read_log(log)[0]
        datoms = tx[":tx/datoms"]
        # group by entity; any entity with a :fin.metric/* or :fin.agg/* attr must carry :synthesized
        ent_attrs = {}
        for d in datoms:
            ent_attrs.setdefault(d[1], {})[d[2]] = d[3]
        derived_ents = [e for e, at in ent_attrs.items()
                        if any(str(k).startswith((":fin.metric/", ":fin.agg/")) for k in at)]
        ok(len(derived_ents) > 0, "derived :fin.metric / :fin.agg entities persisted")
        for e in derived_ents:
            srcs = [v for k, v in ent_attrs[e].items() if str(k).endswith("/sourcing")]
            ok(srcs and all(v == ":synthesized" for v in srcs),
               f"derived entity {e} declares :sourcing :synthesized (G5)")
    finally:
        log.unlink(missing_ok=True)


def test_g2_g4_no_advice_no_forecast():
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        tx = kotoba.read_log(log)[0]
        attrs = {str(d[2]) for d in tx[":tx/datoms"]}
        for forbidden in (":fin.metric/rating", ":fin.metric/recommendation", ":fin.metric/target-price",
                          ":fin.metric/forecast", ":fin.fact/forecast", ":fin.metric/buy-sell",
                          ":fin.metric/valuation", ":rating", ":recommendation"):
            ok(forbidden not in attrs, f"no advice/forecast attr `{forbidden}` in the log (G2/G4)")
        ops = {d[0] for d in tx[":tx/datoms"]}
        ok(ops == {":db/add"}, "every datom is append-only :db/add (restatement = new fact, 非終末論 G11)")
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
    test_g5_derived_synthesized()
    test_g2_g4_no_advice_no_forecast()
    test_no_external_io()
    print(f"\ntest_autorun: {PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
