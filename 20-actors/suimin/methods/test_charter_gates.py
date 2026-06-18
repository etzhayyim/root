#!/usr/bin/env python3
"""suimin 睡眠 — structural charter-gate conformance tests over the central lexicons.

ADR-2606072800. suimin synthesizes population-level sleep-disorder treatment EVIDENCE
from reliable sources only — it does NOT diagnose, treat, book, or sell. Four invariants
are enforced at the schema level (see lexicons/com/etzhayyim/suimin/README.md §Invariants);
this is the first executable check that pins them so a future edit cannot silently weaken
a gate (a sleep actor that drops provenance, GRADE, or the disclaimer can mislead care).

These lexicons had NO test anywhere in the repo before this file (verified 2026-06-16).
Standalone-runnable (`python3 test_charter_gates.py`) AND pytest-compatible; pure stdlib.
"""
from __future__ import annotations

import glob
import json
import os


def _lex_dir():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != "/":
        cand = os.path.join(d, "00-contracts", "lexicons", "com", "etzhayyim", "suimin")
        if os.path.isdir(cand):
            return cand
        d = os.path.dirname(d)
    raise FileNotFoundError("could not locate 00-contracts/lexicons/com/etzhayyim/suimin")


LEX = _lex_dir()


def _load(name):
    with open(os.path.join(LEX, name)) as f:
        return json.load(f)


def _collect(doc, key):
    """Collect every value stored under `key` anywhere in the lexicon tree."""
    out = []

    def walk(o):
        if isinstance(o, dict):
            if key in o:
                out.append(o[key])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(doc)
    return out


def _required_union(doc):
    s = set()
    for req in _collect(doc, "required"):
        if isinstance(req, list):
            s.update(req)
    return s


# Whitelisted provenance id kinds (G1) — verifiable scientific identifiers only.
PROVENANCE_WHITELIST = {"pmid", "doi", "cochrane-cd-id", "guideline-id", "icsd3-code", "icd11-code"}
GRADE_VALUES = {"high", "moderate", "low", "very-low"}


# ── G1 source-whitelist + provenance ──
def test_g1_evidence_requires_source_and_provenance():
    req = _required_union(_load("evidenceRecord.json"))
    for field in ("sourceClass", "provenanceId", "provenanceIdKind"):
        assert field in req, f"G1: evidenceRecord must require {field} (no claim without verifiable provenance)"


def test_g1_provenance_id_kinds_are_whitelisted():
    kinds = set()
    for kv in _collect(_load("evidenceRecord.json"), "knownValues"):
        if isinstance(kv, list) and set(kv) & PROVENANCE_WHITELIST:
            kinds |= set(kv)
    assert kinds, "G1: evidenceRecord must enumerate provenanceIdKind"
    assert kinds <= PROVENANCE_WHITELIST, f"G1: provenance kinds escaped the whitelist: {kinds - PROVENANCE_WHITELIST}"


def test_g1_source_whitelist_requires_grade_ceiling():
    req = _required_union(_load("sourceWhitelist.json"))
    for field in ("maxDefaultGrade", "provenanceIdKind"):
        assert field in req, f"G1: each whitelisted sourceClass must declare {field}"


# ── G2 evidence-grade mandatory ──
def test_g2_evidence_record_requires_grade_and_studytype():
    req = _required_union(_load("evidenceRecord.json"))
    assert "evidenceGrade" in req and "studyType" in req, "G2: evidenceRecord must require evidenceGrade + studyType"


def test_g2_grade_vocabulary_is_grade_shaped():
    grades = set()
    for kv in _collect(_load("evidenceRecord.json"), "knownValues"):
        if isinstance(kv, list) and set(kv) & GRADE_VALUES:
            grades |= set(kv)
    assert GRADE_VALUES <= grades, f"G2: evidenceGrade must cover GRADE levels {GRADE_VALUES}, got {grades}"


def test_g2_synthesis_requires_overall_grade():
    req = _required_union(_load("treatmentSynthesis.json"))
    assert "overallEvidenceGrade" in req, "G2: treatmentSynthesis must require overallEvidenceGrade"


# ── G3 mandatory disclaimer ──
def test_g3_patient_facing_outputs_require_disclaimer():
    for name in ("conditionProfile.json", "referralPathway.json", "treatmentSynthesis.json"):
        req = _required_union(_load(name))
        assert "disclaimerTextUri" in req, f"G3: {name} must require disclaimerTextUri (non-diagnostic disclaimer)"


# ── G4 referral-not-treatment ──
def test_g4_referral_lists_facilities_only():
    req = _required_union(_load("referralPathway.json"))
    assert "recommendedFacilityKinds" in req, "G4: referralPathway must list facility kinds"


def _property_keys(doc):
    """Every field NAME declared under a `properties` object (not descriptions)."""
    keys = set()

    def walk(o):
        if isinstance(o, dict):
            props = o.get("properties")
            if isinstance(props, dict):
                keys.update(props.keys())
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(doc)
    return keys


def test_g4_no_booking_purchase_or_diagnosis_field():
    # G4: referral stops at naming facilities — never books, sells a device, or diagnoses.
    # Check FIELD NAMES only: a description that affirms "NO booking" is the gate working,
    # not a violation, so substring-scanning the whole file would be wrong.
    forbidden = ("booking", "reservation", "appointment", "purchase", "diagnosis", "prescription", "devicesale")
    for f in glob.glob(os.path.join(LEX, "*.json")):
        keys = {k.lower() for k in _property_keys(json.load(open(f)))}
        for word in forbidden:
            assert word not in keys, f"G4: {os.path.basename(f)} must not declare a '{word}' field"


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"suimin/charter_gates: {len(fns)} tests passed (lex dir: {os.path.relpath(LEX)})")


if __name__ == "__main__":
    _run()
