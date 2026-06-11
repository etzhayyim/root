#!/usr/bin/env python3
"""End-to-end GREEN-path test: a calibrated, skilled, member-signed model CLEARS the gate.

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_clearpath.py
    python3 test_clearpath.py

The real two-regime trail is honestly REFUSED (test_promote). This proves the complement:
on a single-regime time-varying fixture, calibrated persistence is skilled (G12) AND
calibrated (G7), so a member signature CLEARS promotion — and is still refused unsigned
(G9 no-server-key). Regenerated from the committed fixture (hermetic).
"""
from __future__ import annotations

import pathlib
import sys

try:
    from forecast import backtest_calibrated
    from promote import decide_from_scorecard
    from analyze import load_edn
except ImportError:
    from mitooshi.methods.forecast import backtest_calibrated  # type: ignore
    from mitooshi.methods.promote import decide_from_scorecard  # type: ignore
    from mitooshi.methods.analyze import load_edn  # type: ignore

_FIXTURE = (pathlib.Path(__file__).resolve().parent.parent / "data" / "fixtures"
            / "single-regime-trail.kotoba.edn")
_MEMBER = "did:web:etzhayyim.com:member:alice"


def _scorecard_row(method):
    rows = load_edn(_FIXTURE)
    s = backtest_calibrated(rows, method)
    return {":fc.score/method": f":{method}",
            ":fc.score/mean-skill": s["mean_skill"],
            ":fc.score/calibration-deviation": s["calibration"]["deviation"]}, s


def test_fixture_persistence_is_skilled_and_calibrated():
    _row, s = _scorecard_row("persistence")
    assert s["mean_skill"] > 0                       # G12 — beats climatology baseline
    assert s["calibration"]["deviation"] <= 0.4      # G7 — within the PIT-deviation ceiling


def test_member_signed_persistence_clears():
    row, _s = _scorecard_row("persistence")
    d = decide_from_scorecard([row], signed_by=_MEMBER)[0]
    assert d["phase"] == "cleared" and d["promoted"] is True


def test_unsigned_persistence_refused_g9():
    row, _s = _scorecard_row("persistence")
    d = decide_from_scorecard([row], signed_by="")[0]
    assert d["phase"] == "refused" and "G9" in d["refusal"]


def test_climatology_refused_on_calibration_g7():
    # climatology is skilled but worse-calibrated here → honest G7 refusal
    row, s = _scorecard_row("climatology")
    assert s["mean_skill"] > 0
    d = decide_from_scorecard([row], signed_by=_MEMBER)[0]
    assert d["phase"] == "refused" and "G7" in d["refusal"]


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"clearpath: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
