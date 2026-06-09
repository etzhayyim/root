#!/usr/bin/env python3
"""test_autorun.py — tadori autonomous self-audit heartbeat + audit-log invariants. ADR-2605301400.

Standalone-runnable (`python3 test_autorun.py`), stdlib only, hermetic (temp logs/corpora).
Guards the constitutionally-constrained autonomy contract that lets tadori run on the fleet:

  - the loop persists ONE content-addressed audit tx per heartbeat to an append-only log;
  - the log holds ONLY silenTadoriReview counters — NO observation / PII / case datom (G3/G6/G10);
  - the commit-DAG verifies (every CID recomputes; tamper is detected);
  - it is deterministic / resume-safe and append-only;
  - **G12**: a nonzero counter (e.g. a plaintext PII obs) HALTS — persisting NOTHING;
  - a not-gate-clean corpus (vendor system-of-record) is rejected by validation;
  - it does NO external I/O.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit_log  # noqa: E402
import autorun  # noqa: E402

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


def _tmp_corpus(records: list[dict]) -> pathlib.Path:
    fd, p = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r) + "\n")
    return pathlib.Path(p)


# a minimal gate-clean corpus: one public source + one encrypted ip-obs
_CLEAN = [
    {"kind": "intel-source", "id": "source:public:s1", "name": "Staged public sample",
     "vendor_family": "public-archive", "source_role": "system-of-record", "license_tier": "A"},
    {"kind": "ip-obs", "id": "ip:192.0.2.1:t", "address": "192.0.2.1", "source": "source:public:s1",
     "case_id": "case:dry", "encrypted": True, "collection_mode": "operator-staged-passive-archive"},
]


def test_heartbeat_persists_audit_only():
    log = _tmp_log()
    corpus = _tmp_corpus(_CLEAN)
    try:
        res = autorun.run_autonomous(cycles=3, seed_path=corpus, log_path=log)
        ok(res["log_length"] == 3, "one audit tx per heartbeat")
        ok(res["chain"]["ok"], "commit-DAG verifies (chain OK)")
        tx = audit_log.read_log(log)[0]
        attrs = {d[2] for d in tx[":tx/datoms"]}
        ops = {d[0] for d in tx[":tx/datoms"]}
        ok(all(str(a).startswith(":tadori.review/") for a in attrs),
           "every datom attr is a :tadori.review/* counter (NO obs/PII/case attrs)")
        ok(ops == {":db/add"}, "every datom is append-only :db/add (G2)")
        for forbidden in (":tadori.obs/case-id", ":tadori.ip/address", ":tadori.dns/domain",
                          ":tadori.indicator/value", ":tadori.obs/evidence-cid"):
            ok(forbidden not in attrs, f"no observation/PII attr `{forbidden}` in the audit log (G3)")
    finally:
        log.unlink(missing_ok=True)
        corpus.unlink(missing_ok=True)


def test_deterministic_resume_safe():
    a, b = _tmp_log(), _tmp_log()
    corpus = _tmp_corpus(_CLEAN)
    try:
        ra = autorun.run_autonomous(cycles=3, seed_path=corpus, log_path=a)
        rb = autorun.run_autonomous(cycles=3, seed_path=corpus, log_path=b)
        ok([x["cid"] for x in ra["beats"]] == [x["cid"] for x in rb["beats"]],
           "same cycles → same CIDs (deterministic / resume-safe)")
    finally:
        a.unlink(missing_ok=True)
        b.unlink(missing_ok=True)
        corpus.unlink(missing_ok=True)


def test_append_only_and_tamper():
    log = _tmp_log()
    corpus = _tmp_corpus(_CLEAN)
    try:
        autorun.run_cycle(1, seed_path=corpus, log_path=log)
        first = audit_log.read_log(log)
        autorun.run_cycle(2, seed_path=corpus, log_path=log)
        second = audit_log.read_log(log)
        ok(len(second) == len(first) + 1, "second heartbeat appends, does not rewrite")
        ok(second[1][":tx/prev"] == first[0][":tx/cid"], "tx 2 links tx 1's CID (commit-DAG)")
        lines = log.read_text(encoding="utf-8").splitlines()
        for i, ln in enumerate(lines):
            if ":tx/id 1 " in ln:
                lines[i] = ln.replace(":tadori.review/cycle 1", ":tadori.review/cycle 9", 1)
                break
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        v = audit_log.verify_chain(log)
        ok(not v["ok"] and v["broken_at"] == 0, "tampering an earlier audit tx breaks the chain")
    finally:
        log.unlink(missing_ok=True)
        corpus.unlink(missing_ok=True)


def test_g12_halt_on_plaintext_pii():
    # the defining tadori invariant: a plaintext PII obs must HALT — persisting NOTHING.
    bad = [
        {"kind": "intel-source", "id": "source:public:s1", "name": "s",
         "vendor_family": "public-archive", "source_role": "system-of-record", "license_tier": "A"},
        {"kind": "ip-obs", "id": "ip:192.0.2.9:t", "address": "192.0.2.9", "source": "source:public:s1",
         "case_id": "case:dry", "encrypted": False,  # ← plaintext PII (G6/G10 violation)
         "collection_mode": "operator-staged-passive-archive"},
    ]
    log = _tmp_log()
    corpus = _tmp_corpus(bad)
    try:
        halted = False
        try:
            autorun.run_cycle(1, seed_path=corpus, log_path=log)
        except audit_log.SilenReviewHalt:
            halted = True
        ok(halted, "plaintext PII obs triggers SilenReviewHalt (G12)")
        ok(not log.exists() or len(audit_log.read_log(log)) == 0,
           "HALT persists NOTHING — no audit datom written on a violation")
    finally:
        log.unlink(missing_ok=True)
        corpus.unlink(missing_ok=True)


def test_vendor_sor_rejected_by_validation():
    # a vendor-compatible feed declared system-of-record must be rejected before any persist (G4).
    bad = [
        {"kind": "intel-source", "id": "source:vendor:st", "name": "vendor",
         "vendor_family": "securitytrails-compatible", "source_role": "system-of-record",
         "license_tier": "C"},
    ]
    log = _tmp_log()
    corpus = _tmp_corpus(bad)
    try:
        rejected = False
        try:
            autorun.run_cycle(1, seed_path=corpus, log_path=log)
        except autorun.ValidationError:
            rejected = True
        ok(rejected, "vendor-compatible system-of-record is rejected by validate_records (G4)")
        ok(not log.exists() or len(audit_log.read_log(log)) == 0, "rejected corpus persists nothing")
    finally:
        log.unlink(missing_ok=True)
        corpus.unlink(missing_ok=True)


def test_no_external_io():
    import inspect
    src = inspect.getsource(autorun) + inspect.getsource(audit_log)
    for banned in ("urllib", "http.client", "socket", "requests"):
        ok(banned not in src, f"autorun/audit_log does no external I/O (no `{banned}`)")


if __name__ == "__main__":
    test_heartbeat_persists_audit_only()
    test_deterministic_resume_safe()
    test_append_only_and_tamper()
    test_g12_halt_on_plaintext_pii()
    test_vendor_sor_rejected_by_validation()
    test_no_external_io()
    print(f"\ntest_autorun: {PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
