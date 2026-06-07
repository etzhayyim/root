#!/usr/bin/env python3
"""Tests for the danjo 弾正 discrepancy-observation analyzer (methods/analyze.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_analyze.py
    python3 test_analyze.py

Covers the single-bidder-streak detector AND the load-bearing charter invariants: every
observation is NON-adjudicating (G4 — no verdict field representable), cites ≥2 source
records (G5), references its open method (G6), and carries the method's knownFalsePositive
modes (G4 honesty). danjo is the censor's EYE, never the SWORD.
"""
from __future__ import annotations

import json
import pathlib
import sys

try:
    from analyze import (build_observation, detect_single_bidder_streak, load_json,
                         method_cid, render_edn, run_all, _FORBIDDEN_VERDICT_FIELDS)
except ImportError:
    from danjo.methods.analyze import (  # type: ignore
        build_observation, detect_single_bidder_streak, load_json, method_cid,
        render_edn, run_all, _FORBIDDEN_VERDICT_FIELDS)

_HERE = pathlib.Path(__file__).resolve().parent.parent
_CORPUS = _HERE / "data" / "corpus.seed.json"
_METHODS = _HERE / "methods" / "v1-jp-seed.json"


def _setup():
    return load_json(_CORPUS), load_json(_METHODS)


def _streak_method(methods):
    return next(m for m in methods["methods"] if m["methodId"] == "single-bidder-streak")


def test_detector_fires_on_the_streak_only():
    corpus, methods = _setup()
    params = json.loads(_streak_method(methods)["thresholdParams"])
    hits = detect_single_bidder_streak(corpus["procurementRecords"], params)
    # ACME has 6 consecutive single-bid (≥5) → 1 hit; BETA (2) and GAMMA (multi-bid) do not
    assert len(hits) == 1
    assert hits[0]["awardee"] == "lei:5493ACME000000000001" and hits[0]["count"] == 6


def test_every_observation_is_non_adjudicating():
    corpus, methods = _setup()
    obs = run_all(corpus, methods)
    assert obs
    assert all(o["nonAdjudicatingNotice"] is True for o in obs)


def test_every_observation_cites_two_or_more_sources():
    corpus, methods = _setup()
    for o in run_all(corpus, methods):
        assert len(o["sourceRecordCids"]) >= 2          # G5


def test_every_observation_references_its_open_method():
    corpus, methods = _setup()
    for o in run_all(corpus, methods):
        assert o["methodNoteCid"] and o["methodNoteCid"].startswith("method:")  # G6


def test_known_false_positive_modes_carried():
    corpus, methods = _setup()
    for o in run_all(corpus, methods):
        assert o["knownFalsePositiveModes"]             # G4 honesty — why a hit ≠ a crime


def test_no_verdict_field_representable():
    corpus, methods = _setup()
    for o in run_all(corpus, methods):
        for k in o:
            assert not any(b in k.lower() for b in _FORBIDDEN_VERDICT_FIELDS)


def test_build_observation_refuses_single_source():
    _corpus, methods = _setup()
    m = _streak_method(methods)
    try:
        build_observation({"authority": "a", "awardee": "b", "cids": ["only-one"], "count": 1}, m)
        raised = False
    except ValueError as e:
        raised = "G5" in str(e)
    assert raised, "an observation with <2 sources must be refused (G5)"


def test_method_cid_is_deterministic():
    _corpus, methods = _setup()
    m = _streak_method(methods)
    assert method_cid(m) == method_cid(m)


def test_render_edn_marks_invariants():
    corpus, methods = _setup()
    edn = render_edn(run_all(corpus, methods))
    assert ":danjo.obs/non-adjudicating true" in edn
    assert "censor's EYE" in edn and "gated" in edn


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"danjo analyze.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
