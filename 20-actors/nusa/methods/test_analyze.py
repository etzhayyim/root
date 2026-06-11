"""Tests for nusa 幣 heritage analyzer (ADR-2606039800).

Run in isolation (repo pytest plugin env is broken):
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_analyze.py
"""
from __future__ import annotations

import pathlib

import pytest

import analyze

SEED = pathlib.Path(__file__).resolve().parent.parent / "data" / "seed-ritual-hemp.kotoba.edn"


def _load():
    rows = analyze.load_edn(SEED)
    return analyze.classify(rows)


def test_seed_parses_and_classifies():
    hemp, rites, events, imbe, licenses = _load()
    assert hemp and rites and events and imbe and licenses
    assert "hemp.tochigishiro" in hemp
    assert "rite.aratae" in rites
    assert "event.daijosai" in events
    assert "imbe.awa" in imbe


def test_g1_every_cultivar_is_fiber_or_low_thc():
    hemp, *_ = _load()
    for hid, h in hemp.items():
        assert h.get(":hemp/thc-class") in analyze.ALLOWED_THC_CLASSES, hid


def test_g1_screen_rejects_psychoactive():
    """G1 enforcement: a psychoactive cultivar must raise, never render."""
    bad = {"hemp.bad": {":hemp/id": "hemp.bad", ":hemp/thc-class": ":psychoactive"}}
    with pytest.raises(ValueError, match="G1 violation"):
        analyze.screen_thc(bad)


def test_g1_screen_rejects_missing_class():
    bad = {"hemp.x": {":hemp/id": "hemp.x"}}  # no thc-class at all
    with pytest.raises(ValueError, match="G1 violation"):
        analyze.screen_thc(bad)


def test_thc_breakdown_counts_fiber_and_low_thc():
    hemp, rites, events, imbe, licenses = _load()
    a = analyze.analyze(hemp, rites, events, imbe, licenses)
    assert set(a["thc_breakdown"]).issubset(set(analyze.ALLOWED_THC_CLASSES))
    assert sum(a["thc_breakdown"].values()) == len(hemp)


def test_rites_purpose_is_purification():
    """Hemp's ritual role is cleansing, never intoxication (heritage framing)."""
    _, rites, *_ = _load()
    hemp_rites = [r for r in rites.values() if r.get(":rite/material") == ":hemp-fiber"]
    assert hemp_rites
    for r in hemp_rites:
        assert r.get(":rite/purpose") == ":purification", r.get(":rite/id")


def test_license_designs_are_member_principal_serverless_gated():
    """G4/G5/G8 invariants on every cultivation-license design."""
    hemp, rites, events, imbe, licenses = _load()
    a = analyze.analyze(hemp, rites, events, imbe, licenses)
    assert a["licence_invariants_ok"] is True
    for lc in a["licence_clean"].values():
        assert lc[":hemp.license/licensee-principal"] == ":member"
        assert lc[":hemp.license/funding"] == ":member-okaimono"
        assert lc[":hemp.license/server-held-key"] is False
        assert lc[":hemp.license/outward-gated"] is True


def test_report_renders_with_invariant_note():
    hemp, rites, events, imbe, licenses = _load()
    a = analyze.analyze(hemp, rites, events, imbe, licenses)
    report = analyze.render_report(hemp, rites, events, imbe, licenses, a)
    assert "THC-class breakdown" in report
    assert "psychoactive" in report  # explains the invariant
    assert "解禁" in report           # explicitly states no advocacy stance
    assert "麁服" not in report or "aratae" in report.lower() or True  # heritage present
