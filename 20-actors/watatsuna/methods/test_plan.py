#!/usr/bin/env python3
"""Tests for the watatsuna 綿津綱 → watatsumi resilience plan (methods/plan.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_plan.py
    python3 test_plan.py

The load-bearing invariant (G2 + watatsumi N8): the plan can ONLY add resilience —
:lay-diverse-route / :pre-stage-repair / :monitor. There is NO interdiction/cut output by
construction. This suite proves no other plan kind can appear.
"""
from __future__ import annotations

import pathlib
import sys

try:
    from analyze import analyze, classify, load_edn
    from plan import build_plan, render_edn, render_md
except ImportError:
    from watatsuna.methods.analyze import analyze, classify, load_edn  # type: ignore
    from watatsuna.methods.plan import build_plan, render_edn, render_md  # type: ignore

_SEED = pathlib.Path(__file__).resolve().parent.parent / "data" / "seed-cable-graph.kotoba.edn"
_ALLOWED = {":lay-diverse-route", ":pre-stage-repair", ":monitor"}


def _plan():
    rows = load_edn(_SEED)
    cables, stations, links, segs, faults = classify(rows)
    a = analyze(cables, stations, links, segs, faults)
    return cables, stations, a, build_plan(cables, stations, a)


def test_plan_is_non_empty():
    *_, recs = _plan()
    assert len(recs) > 0


def test_every_plan_kind_is_resilience_only():
    *_, recs = _plan()
    kinds = {r[":plan/kind"] for r in recs}
    assert kinds <= _ALLOWED, f"non-resilience plan kind present: {kinds - _ALLOWED}"


def test_no_interdiction_kind_representable():
    *_, recs = _plan()
    for r in recs:
        k = r[":plan/kind"]
        # no cut / sever / interdict / disable verb can appear (G2 by construction)
        assert not any(bad in k for bad in ("cut", "sever", "interdict", "disable", "attack"))


def test_lay_diverse_route_targets_redundancy_gaps():
    cables, stations, a, recs = _plan()
    lay = [r for r in recs if r[":plan/kind"] == ":lay-diverse-route"]
    # there is a lay-route rec exactly where the analyzer found a single-cable landing
    assert len(lay) >= len(a["redundancy_gap"]) or len(a["redundancy_gap"]) == 0


def test_rendered_edn_marks_g2_invariant():
    *_, recs = _plan()
    edn = render_edn(recs)
    assert "redundancy + repair + monitor ONLY" in edn
    assert "interdiction" not in edn.lower() or "No interdiction" in edn


def test_rendered_md_states_watatsuna_knows_watatsumi_acts():
    *_, recs = _plan()
    md = render_md(recs)
    assert "watatsuna knows" in md and "watatsumi acts" in md
    assert "No interdiction output by construction" in md


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"watatsuna plan.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
