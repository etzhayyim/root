"""Structural charter-invariant tests for noroshi (烽) — ADR-2606051600 (items 3+4).

These assert the constitution *structurally* over the parsed lexicons / kotoba schema / ontology and
the code constants — not by grepping prose (the descriptions legitimately mention 'weaponizable is
unrepresentable'). A regression here means an invariant was weakened: civilian-only (G3/N1),
sensing-not-surveillance (G4/N2), no-server-key (G7), open-EDA (G1/N5), sourcing-honesty (G10).
"""

from __future__ import annotations

import pathlib

import pytest

from _edn import load_edn

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_LEX = _ROOT / "lex"
_ONTOLOGY = _ROOT.parents[1] / "00-contracts" / "schemas" / "photonic-convergence-ontology.kotoba.edn"

_FORBIDDEN_USE_VALUES = {"weapon", "directed-energy", "dazzle", "fire-control", "person"}


def _props(lex_name: str) -> dict:
    d = load_edn(_LEX / f"{lex_name}.edn")
    return d[":defs"][":main"][":record"][":properties"]


# ── G3/N1 civilian force-separation ──────────────────────────────────────────
def test_photonic_device_force_class_is_civilian_const():
    assert _props("photonicDevice")[":forceClass"].get(":const") == "civilian-comms"


def test_packaging_use_enum_excludes_weaponisation():
    uses = set(_props("packagingJob")[":use"].get(":enum", []))
    assert uses and uses.isdisjoint(_FORBIDDEN_USE_VALUES)


def test_code_permitted_uses_disjoint_from_forbidden():
    from active_alignment import FORBIDDEN_USES, PERMITTED_USES
    assert set(PERMITTED_USES).isdisjoint(FORBIDDEN_USES)
    assert "weapon" not in PERMITTED_USES and "directed-energy" not in PERMITTED_USES


# ── G4/N2 sensing-not-surveillance: an estimate is an OBJECT, never a person ──
def test_sense_estimate_target_class_is_object_const():
    tc = _props("senseEstimate")[":targetClass"]
    assert tc.get(":const") == "object"
    assert "person" not in str(tc.get(":enum", []))


def test_ontology_target_classes_are_object_only():
    onto = load_edn(_ONTOLOGY)
    assert onto[":ontology/target-classes"] == [":object"]
    assert ":weaponizable" not in onto[":ontology/force-classes"]


# ── G7 no-server-key ─────────────────────────────────────────────────────────
def test_packaging_job_server_held_key_const_false():
    assert _props("packagingJob")[":serverHeldKey"].get(":const") is False


def test_packaging_job_dry_run_const_true():
    assert _props("packagingJob")[":dryRun"].get(":const") is True


# ── G3/N1 ISAC waveform is civilian ──────────────────────────────────────────
def test_isac_waveform_civilian_const_true():
    assert _props("isacWaveform")[":civilian"].get(":const") is True


# ── G1/N5 open-EDA + G10 sourcing-honesty in the device lexicon ──────────────
def test_device_process_is_open_pdk_const():
    assert _props("photonicDevice")[":process"].get(":const") == "open-pdk"


def test_device_eda_enum_is_open_source_only():
    eda = set(_props("photonicDevice")[":eda"].get(":enum", []))
    assert eda == {"gdsfactory", "meep", "klayout", "openlane"}
    for proprietary in ("cadence", "synopsys", "lumerical", "ansys"):
        assert proprietary not in eda


def test_device_representative_const_true():
    assert _props("photonicDevice")[":representative"].get(":const") is True
