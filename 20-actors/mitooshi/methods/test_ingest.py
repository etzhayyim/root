#!/usr/bin/env python3
"""Tests for the mitooshi offline public-series normalizer (methods/ingest.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_ingest.py
    python3 test_ingest.py
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

try:
    from ingest import normalize
except ImportError:
    from mitooshi.methods.ingest import normalize  # type: ignore

_HERE = pathlib.Path(__file__).resolve().parent
SAMPLE = _HERE.parent / "data" / "ingest" / "sample-batch.json"


def _batch():
    return json.loads(SAMPLE.read_text())


def test_sample_batch_normalizes_two_public_series():
    n = normalize(_batch())
    assert set(n["series"]) == {"s-hormuz-transit", "s-port-congestion"}


def test_proprietary_terminal_series_is_refused():
    n = normalize(_batch())
    assert len(n["refused"]) == 1
    r = n["refused"][0]
    assert r["id"] == "s-blocked-terminal" and "G4" in r["reason"]


def test_observations_are_sorted_append_only():
    n = normalize(_batch())
    hormuz = [o for o in n["obs"] if o[":obs/series"] == "s-hormuz-transit"]
    ats = [o[":obs/observed-at"] for o in hormuz]
    assert ats == sorted(ats)              # 非終末論: append-only, latest = current
    assert ats[-1] == 3 and hormuz[-1][":obs/value"] == 2.7


def test_categorical_class_preserved():
    n = normalize(_batch())
    cong = [o for o in n["obs"] if o[":obs/series"] == "s-port-congestion"]
    assert any(o.get(":obs/class") == "up" for o in cong)


def test_source_class_normalized_to_keyword():
    n = normalize(_batch())
    assert n["series"]["s-hormuz-transit"][":series/source-class"] == ":public-broadcast"
    assert n["series"]["s-hormuz-transit"][":series/sourcing"] == ":representative"


def test_live_flag_refused_without_operator_gate():
    env = dict(os.environ)
    env.pop("MITOOSHI_OPERATOR_GATE", None)
    p = subprocess.run([sys.executable, str(_HERE / "ingest.py"), "--live"],
                       capture_output=True, text=True, env=env)
    assert p.returncode != 0
    assert "G10" in (p.stdout + p.stderr) and "Council+operator gated" in (p.stdout + p.stderr)


def test_live_flag_gated_still_design_only_when_attested():
    env = dict(os.environ)
    env["MITOOSHI_OPERATOR_GATE"] = "1"
    p = subprocess.run([sys.executable, str(_HERE / "ingest.py"), "--live"],
                       capture_output=True, text=True, env=env)
    # attested but R0 → exits with the design-only message, NOT a live fetch
    assert "not implemented (design-only)" in (p.stdout + p.stderr)


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"ingest.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
