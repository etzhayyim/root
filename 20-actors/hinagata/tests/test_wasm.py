#!/usr/bin/env python3
"""hinagata 雛形 — WASM component entry tests (ADR-2606111954). Pure stdlib, NETWORK-FREE.

Verifies the four `wasm/app.py` export bodies (the componentize-py world implementation)
produce valid output from the embedded/dev seed — so the component logic is CI-covered before
the operator's `wasm/build.sh` (componentize-py) build.
"""
import sys
import json
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "wasm"))
sys.path.insert(0, str(ACTOR_DIR / "methods"))

import app  # noqa: E402  (wasm/app.py)


def test_analyze_export_shape():
    out = json.loads(app.analyze())
    assert set(out) == {"grounded", "reuse", "statute_pull"}
    assert out["grounded"], "no groundedness rows"
    top = out["grounded"][0]
    assert {"id", "label", "score"} <= set(top)
    scores = [r["score"] for r in out["grounded"]]
    assert scores == sorted(scores, reverse=True)


def test_datoms_export_is_eavt_edn():
    edn = app.datoms(7)
    assert edn.lstrip().startswith(";;") and "[" in edn
    assert " 7 :add]" in edn                      # tx threads through ground datoms
    assert ":bond/is-transient true" in edn       # derived readouts flagged transient (N1/G2)


def test_coverage_export_is_markdown():
    md = app.coverage()
    assert md.startswith("# hinagata") and "coverage of all template families" in md


def test_envelope_export_builds_unsigned_record():
    out = json.loads(app.envelope("tmpl.nda-mutual",
                                   "did:web:etzhayyim.com:actor:x",
                                   "did:plc:alice,did:plc:bob"))
    assert "document" in out and "envelope" in out
    env = out["envelope"]
    assert env["$type"] == "com.etzhayyim.esign.envelope"
    assert env["status"] == "pending"             # UNSIGNED — member signs client-side
    assert env["signers"] == ["did:plc:alice", "did:plc:bob"]
    assert env["documentCid"].startswith("bafkrei")


def test_exports_are_deterministic():
    assert app.analyze() == app.analyze()
    assert app.datoms(1) == app.datoms(1)
    assert app.envelope("tmpl.dpa-gdpr", "did:web:x", "did:plc:a") == \
        app.envelope("tmpl.dpa-gdpr", "did:web:x", "did:plc:a")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
