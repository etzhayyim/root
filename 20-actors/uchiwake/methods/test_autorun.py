#!/usr/bin/env python3
"""test_autorun.py — uchiwake 内訳 autonomous product-resilience heartbeat + kotoba Datom-log +
live-ingest/push gate invariants. ADR-2606081800. Standalone-runnable
(`python3 test_autorun.py`), stdlib only, hermetic.

Guards the autonomy + persistence + non-target/non-recipe + gate contract for the fleet:

  - the loop persists one content-addressed tx per heartbeat to an append-only log;
  - the log is a verifiable commit-DAG (every CID recomputes; tamper is detected);
  - it is deterministic / resume-safe (same cycles → same CIDs) and append-only;
  - **G5 sourcing-honesty**: every persisted derived :concentration/* carries
    :concentration/sourcing :synthesized — never re-ingested as an authoritative product fact;
  - **G2/G4 resilience-not-target / not-a-recipe**: the log carries public product facts +
    concentration and NO target/hit-list/clone/recipe attr;
  - the loop does NO external I/O (offline ingest, local persist — G7 stays gated);
  - **G7 live ingest**: ingest.fetch_off refuses without UCHIWAKE_OPERATOR_GATE, and bridge.push
    refuses without UCHIWAKE_KOTOBA_LIVE; the live OFF fetch validates the GS1 check digit (G5)
    BEFORE any network call;
  - **exactly-once**: a :bridge/* checkpoint advances the push cursor and is not itself re-pushed.
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import autorun  # noqa: E402
import bridge  # noqa: E402
import ingest  # noqa: E402
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
        ok(all(b["concentration"] > 0 for b in res["beats"]), "derived concentration computed + persisted")
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
                lines[i] = ln.replace(':concentration/sourcing :synthesized',
                                      ':concentration/sourcing :authoritative', 1)
                break
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        v = kotoba.verify_chain(log)
        ok(not v["ok"] and v["broken_at"] == 0, "tampering an earlier tx breaks the chain")
    finally:
        log.unlink(missing_ok=True)


def test_g5_derived_synthesized():
    # G5: every derived :concentration must declare :synthesized — never masquerade as a fact.
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        tx = kotoba.read_log(log)[0]
        datoms = tx[":tx/datoms"]
        ent_attrs = {}
        for d in datoms:
            ent_attrs.setdefault(d[1], {})[d[2]] = d[3]
        derived_ents = [e for e, at in ent_attrs.items()
                        if any(str(k).startswith(":concentration/") for k in at)]
        ok(len(derived_ents) > 0, "derived :concentration entities persisted")
        for e in derived_ents:
            srcs = [v for k, v in ent_attrs[e].items() if str(k).endswith("/sourcing")]
            ok(srcs and all(v == ":synthesized" for v in srcs),
               f"derived entity {e} declares :sourcing :synthesized (G5)")
            ok(ent_attrs[e].get(":concentration/derived") is True,
               f"derived entity {e} carries :concentration/derived true (never re-ingested as fact)")
    finally:
        log.unlink(missing_ok=True)


def test_g2_g4_not_target_not_recipe():
    log = _tmp_log()
    try:
        autorun.run_cycle(1, log_path=log)
        tx = kotoba.read_log(log)[0]
        attrs = {str(d[2]) for d in tx[":tx/datoms"]}
        # G2/G4: resilience map, never a target-list AND never a clone/counterfeit recipe.
        for forbidden in (":concentration/target", ":concentration/rank-to-hit", ":target",
                          ":product/clone", ":product/counterfeit", ":bom.edge/full-recipe",
                          ":bom.edge/exact-formulation", ":material/exact-quantity"):
            ok(forbidden not in attrs, f"no target/recipe attr `{forbidden}` in the log (G2/G4)")
        ops = {d[0] for d in tx[":tx/datoms"]}
        ok(ops == {":db/add"}, "every datom is append-only :db/add (G11)")
    finally:
        log.unlink(missing_ok=True)


def test_no_external_io():
    import inspect
    src = inspect.getsource(autorun) + inspect.getsource(kotoba)
    for banned in ("urllib", "http.client", "socket", "requests", "subprocess"):
        ok(banned not in src, f"autorun/kotoba does no external I/O (no `{banned}`)")


def test_g7_live_ingest_gated():
    # ingest.fetch_off refuses without the operator gate (G7) — checked BEFORE any network call.
    saved = os.environ.pop("UCHIWAKE_OPERATOR_GATE", None)
    try:
        try:
            ingest.fetch_off("3017620422003")  # valid Nutella GTIN, but gate is unset
            ok(False, "fetch_off must refuse without UCHIWAKE_OPERATOR_GATE (G7)")
        except SystemExit as e:
            ok("G7" in str(e), "fetch_off refuses without the operator gate (G7)")
        # with the gate set, an INVALID GTIN is refused (G5) before any network I/O
        os.environ["UCHIWAKE_OPERATOR_GATE"] = "1"
        try:
            ingest.fetch_off("3017620422000")  # bad check digit
            ok(False, "fetch_off must refuse a bad GTIN (G5)")
        except SystemExit as e:
            ok("G5" in str(e), "fetch_off validates the GS1 check digit before fetching (G5)")
    finally:
        os.environ.pop("UCHIWAKE_OPERATOR_GATE", None)
        if saved is not None:
            os.environ["UCHIWAKE_OPERATOR_GATE"] = saved


def test_g7_live_push_gated():
    saved = os.environ.pop("UCHIWAKE_KOTOBA_LIVE", None)
    try:
        try:
            bridge.push(log_path=_tmp_log())
            ok(False, "bridge.push must refuse without UCHIWAKE_KOTOBA_LIVE (G7)")
        except SystemExit as e:
            ok("G7" in str(e), "bridge.push refuses without the live-node gate (G7)")
    finally:
        if saved is not None:
            os.environ["UCHIWAKE_KOTOBA_LIVE"] = saved


def test_bridge_exactly_once_cursor():
    log = _tmp_log()
    try:
        autorun.run_autonomous(cycles=2, log_path=log)
        txs = kotoba.read_log(log)
        st = bridge.bridge_state(txs)
        pend = bridge.pending_txs(txs, st)
        ok(st["pushed_to"] == 0 and len(pend) == 2, "fresh log: cursor 0, 2 pending heartbeats")
        ck = bridge.make_checkpoint(pend, "uchiwake", "http://x:8077/y",
                                    ["bremote1", "bremote2"], log)
        kotoba.append_tx(ck, log)
        txs2 = kotoba.read_log(log)
        st2 = bridge.bridge_state(txs2)
        pend2 = bridge.pending_txs(txs2, st2)
        ok(st2["pushed_to"] == 2, "checkpoint advances the cursor to the highest pushed tx-id")
        ok(len(pend2) == 0, "exactly-once: nothing re-pushed after the checkpoint")
        ok(kotoba.verify_chain(log)["ok"], "checkpoint keeps the commit-DAG intact")
    finally:
        log.unlink(missing_ok=True)


if __name__ == "__main__":
    test_heartbeat_persists()
    test_deterministic_resume_safe()
    test_append_only_and_tamper()
    test_g5_derived_synthesized()
    test_g2_g4_not_target_not_recipe()
    test_no_external_io()
    test_g7_live_ingest_gated()
    test_g7_live_push_gated()
    test_bridge_exactly_once_cursor()
    print(f"\ntest_autorun: {PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
