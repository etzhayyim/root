#!/usr/bin/env python3
"""rasen 螺旋 — WASM component entry tests (ADR-2606101000). Pure stdlib, NETWORK-FREE.

Verifies the three `wasm/app.py` export bodies (the componentize-py world implementation)
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
    assert set(out) == {"care", "burden", "pleiotropy"}
    assert out["care"], "no care-priority rows"
    top = out["care"][0]
    assert {"id", "label", "score"} <= set(top)
    # rows are score-descending
    scores = [r["score"] for r in out["care"]]
    assert scores == sorted(scores, reverse=True)


def test_datoms_export_is_eavt_edn():
    edn = app.datoms(7)
    assert edn.lstrip().startswith(";;") and "[" in edn
    assert " 7 :add]" in edn                      # tx threads through ground datoms
    assert ":bond/is-transient true" in edn       # derived readouts flagged transient (N1/G2)


def test_coverage_export_is_markdown():
    md = app.coverage()
    assert md.startswith("# rasen") and "coverage of all genes/variants is ~0 by design" in md


def test_exports_are_deterministic():
    assert app.analyze() == app.analyze()
    assert app.datoms(1) == app.datoms(1)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
