#!/usr/bin/env python3
"""Lexicon well-formedness tests for 扶持 (fuchi) — all 5 com.etzhayyim.fuchi.* lexicons.

Standalone-runnable: python3 test_lexicons.py
"""
from __future__ import annotations

import pathlib
import sys

from _edn import load_edn

_LEX = pathlib.Path(__file__).resolve().parents[1] / "lex"

EXPECTED = {
    "maintainerCovenant.edn": "com.etzhayyim.fuchi.maintainerCovenant",
    "sustenanceEnvelope.edn": "com.etzhayyim.fuchi.sustenanceEnvelope",
    "allocationIntent.edn":   "com.etzhayyim.fuchi.allocationIntent",
    "routingPlan.edn":        "com.etzhayyim.fuchi.routingPlan",
    "governanceDecision.edn": "com.etzhayyim.fuchi.governanceDecision",
    "provisioningIntent.edn": "com.etzhayyim.fuchi.provisioningIntent",
    "voteBallot.edn":         "com.etzhayyim.fuchi.voteBallot",
    "sustenanceBooking.edn":  "com.etzhayyim.fuchi.sustenanceBooking",
    "cohortEarmark.edn":      "com.etzhayyim.fuchi.cohortEarmark",
}


def test_all_five_lexicons_present():
    files = {p.name for p in _LEX.glob("*.edn")}
    assert set(EXPECTED) <= files, f"missing: {set(EXPECTED) - files}"


def test_each_lexicon_well_formed():
    for fname, lid in EXPECTED.items():
        lex = load_edn(_LEX / fname)
        assert lex[":lexicon"] == 1, fname
        assert lex[":id"] == lid, fname
        rec = lex[":defs"][":main"]
        assert rec[":type"] == "record", fname
        assert ":record" in rec, fname
        assert rec[":record"][":type"] == "object", fname
        assert rec[":record"][":required"], fname


def test_namespace_prefix_is_fuchi():
    for lid in EXPECTED.values():
        assert lid.startswith("com.etzhayyim.fuchi."), lid


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"test_lexicons.py: {len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
