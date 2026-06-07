#!/usr/bin/env python3
"""Tests for the watari 渡り offline AIS/ADS-B normalizer (methods/ingest.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_ingest.py
    python3 test_ingest.py

Covers offline normalization (public-broadcast → :craft/:craft.fix datoms, all
:representative) AND the G7 outward gate: a live network fetch is REFUSED unless the
operator attestation env var is set.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

try:
    import ingest
    from ingest import normalize
except ImportError:
    from watari.methods import ingest  # type: ignore
    from watari.methods.ingest import normalize  # type: ignore

_BATCH = pathlib.Path(__file__).resolve().parent.parent / "data" / "ingest" / "sample-batch.json"


def _batch():
    return json.loads(_BATCH.read_text())


def test_normalize_emits_vessel_and_aircraft_craft():
    craft, fixes = normalize(_batch())
    kinds = {c[":craft/kind"] for c in craft.values()}
    assert ":vessel" in kinds and ":aircraft" in kinds
    assert len(fixes) >= len(craft)            # at least one fix per craft


def test_normalized_records_are_representative():
    craft, fixes = normalize(_batch())
    assert all(c.get(":craft/sourcing") == ":representative" for c in craft.values())
    assert all(f.get(":craft.fix/sourcing") == ":representative" for f in fixes)


def test_fix_carries_source_tag():
    craft, fixes = normalize(_batch())
    sources = {f.get(":craft.fix/source") for f in fixes}
    assert sources <= {":ais", ":adsb"}        # only public-broadcast sources


def test_g4_no_person_fields_in_normalized_output():
    craft, fixes = normalize(_batch())
    for rec in list(craft.values()) + fixes:
        for k in rec:
            assert ":person" not in k          # craft, never a person (G4)


def test_g7_live_fetch_refused_without_operator_gate():
    # default mode (no WATARI_OPERATOR_GATE) must REFUSE --live
    saved = os.environ.pop("WATARI_OPERATOR_GATE", None)
    try:
        raised = False
        try:
            ingest.main(["ingest.py", "--live"])
        except SystemExit as e:
            raised = True
            assert "G7" in str(e) or "refus" in str(e).lower() or "gate" in str(e).lower()
        assert raised, "--live must refuse without the operator gate"
    finally:
        if saved is not None:
            os.environ["WATARI_OPERATOR_GATE"] = saved


def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"watari ingest.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
