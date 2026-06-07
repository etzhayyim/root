#!/usr/bin/env python3
"""Tests for mitooshi backtest→promotion decision (methods/promote.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_promote.py
    python3 test_promote.py

The calibration_gate is a REFUSAL gate. These tests prove each gate fires on the scorecard:
G12 (skill≤0 refused), G7 (miscalibrated refused — the real two-regime trail's outcome),
G9 (unsigned / server-signed refused), and that a skilled+calibrated+member-signed model
clears. The gate logic itself is the cell's review_promotion (single source of truth).
"""
from __future__ import annotations

import pathlib
import sys

try:
    from promote import decide_from_scorecard, emit_decision_edn
    from analyze import load_edn
except ImportError:
    from mitooshi.methods.promote import decide_from_scorecard, emit_decision_edn  # type: ignore
    from mitooshi.methods.analyze import load_edn  # type: ignore

_SCORECARD = (pathlib.Path(__file__).resolve().parent.parent / "data" / "persisted"
              / "chokepoint-backtest-scorecard.kotoba.edn")
_MEMBER = "did:web:etzhayyim.com:member:alice"


def _rows(skill, deviation, method="persistence"):
    return [{":fc.score/method": f":{method}", ":fc.score/mean-skill": skill,
             ":fc.score/calibration-deviation": deviation}]


def test_skilled_calibrated_signed_clears():
    d = decide_from_scorecard(_rows(0.5, 0.2), signed_by=_MEMBER)[0]
    assert d["phase"] == "cleared" and d["promoted"] is True


def test_unskilled_refused_g12():
    d = decide_from_scorecard(_rows(-0.1, 0.2), signed_by=_MEMBER)[0]
    assert d["phase"] == "refused" and "G12" in d["refusal"]


def test_miscalibrated_refused_g7():
    # skill is fine but deviation exceeds the ceiling → G7 refusal
    d = decide_from_scorecard(_rows(0.7, 1.3), signed_by=_MEMBER)[0]
    assert d["phase"] == "refused" and "G7" in d["refusal"]


def test_unsigned_refused_g9_no_server_key():
    d = decide_from_scorecard(_rows(0.5, 0.2), signed_by="")[0]
    assert d["phase"] == "refused" and "G9" in d["refusal"]


def test_server_signature_refused_g9():
    d = decide_from_scorecard(_rows(0.5, 0.2), signed_by="server:etzhayyim")[0]
    assert d["phase"] == "refused" and "G9" in d["refusal"]


def test_decision_edn_records_server_held_key_false():
    edn = emit_decision_edn(decide_from_scorecard(_rows(0.5, 0.2), signed_by=_MEMBER), _MEMBER)
    assert ":fc.promotion/server-held-key false" in edn
    assert ":fc.promotion/promoted true" in edn


def test_real_scorecard_is_refused_on_calibration():
    # honest end-to-end: the real two-regime trail is SKILLED but MISCALIBRATED, so even
    # a member signature does NOT clear it — the gate working as designed.
    if not _SCORECARD.exists():
        return
    rows = load_edn(_SCORECARD)
    decisions = decide_from_scorecard(rows, signed_by=_MEMBER)
    assert decisions, "expected scorecard methods"
    for d in decisions:
        assert d["skill"] > 0                      # G12 satisfied (skilled)
        assert d["phase"] == "refused" and "G7" in d["refusal"]   # but miscalibrated


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"promote.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
