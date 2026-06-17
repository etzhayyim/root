#!/usr/bin/env python3
"""tatekata 建方 — constitutional-gate conformance tests (manifest + lexicons).

tatekata is the construction actor (onshore civil + MEP, low-rise). It is an EXECUTION-ONLY
actor with a tightly bounded scope: no high-rise (N1 >12 stories), no architectural design
(N9 — design ≠ construction), no cost estimation / budgeting (N10 — finance domain). Its gates
are operationalized at the schema layer: G2 site survey + IPFS pin before entry; G3 witness
quorum (≥2 robot DIDs); G5 sourcing audit (material provenance); safety-incident transparency.

The existing test (`py/test_agent.py`) covers the AGENT layer; the manifest gate set + scope
non-goals + lexicon required fields had NO conformance check. This is that check.
Standalone-runnable (`python3 test_charter_gates.py`) AND pytest-compatible; pure stdlib.
"""
from __future__ import annotations

import json
import os


def _repo_root():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != "/":
        if os.path.isdir(os.path.join(d, "00-contracts")) and os.path.isdir(os.path.join(d, "20-actors")):
            return d
        d = os.path.dirname(d)
    raise FileNotFoundError("repo root not found")


ROOT = _repo_root()
MANIFEST = os.path.join(ROOT, "20-actors", "tatekata", "manifest.jsonld")
LEXDIR = os.path.join(ROOT, "00-contracts", "lexicons", "com", "etzhayyim", "tatekata")


def _manifest():
    with open(MANIFEST) as f:
        return json.load(f)


def _nongoals():
    ng = _manifest()["nonGoals"]
    return ng.get("goals", ng.get("nonGoals", ng))


def _lex(name):
    with open(os.path.join(LEXDIR, name)) as f:
        return json.load(f)


def _required_union(doc):
    s = set()

    def walk(o):
        if isinstance(o, dict):
            r = o.get("required")
            if isinstance(r, list):
                s.update(r)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(doc)
    return s


# ── full gate set ──
def test_all_14_gates_declared():
    gates = _manifest()["constitutionalGates"]["gates"]
    assert set(gates) == {f"G{i}" for i in range(1, 15)}, f"manifest must declare G1–G14, got {sorted(gates)}"


# ── scope discipline: no high-rise, execution-only (no design), no cost estimation ──
def test_no_high_rise():
    n = _nongoals()
    assert "high-rise" in n["N1"].lower() or "stories" in n["N1"].lower(), "N1 must exclude high-rise"


def test_execution_only_no_architectural_design():
    n = _nongoals()
    assert "design" in n["N9"].lower(), "N9: tatekata is execution-only — no architectural design"


def test_no_cost_estimation():
    n = _nongoals()
    assert "cost" in n["N10"].lower() or "budget" in n["N10"].lower(), "N10: no cost estimation / budgeting (finance domain)"


# ── G3 witness quorum on progress/material/site records ──
def test_g3_witness_quorum():
    for name in ("constructionProgressRecord.json", "materialAttestation.json", "siteAttestation.json"):
        assert "attestingRobots" in _required_union(_lex(name)), f"G3: {name} must require attestingRobots"


# ── G5 sourcing audit — material provenance ──
def test_g5_material_provenance():
    req = _required_union(_lex("materialAttestation.json"))
    for field in ("grade", "standard", "qcResult", "supplierName"):
        assert field in req, f"G5: materialAttestation must require {field}"


# ── G2 site survey before entry ──
def test_g2_site_survey():
    req = _required_union(_lex("siteAttestation.json"))
    for field in ("soilClassification", "surveyDate"):
        assert field in req, f"G2: siteAttestation must require {field}"


# ── safety-incident transparency ──
def test_safety_incident_transparency():
    req = _required_union(_lex("safetyIncidentReport.json"))
    for field in ("incidentType", "severity", "incidentDate", "reportDate"):
        assert field in req, f"safety: safetyIncidentReport must require {field}"


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"tatekata/charter_gates: {len(fns)} tests passed")


if __name__ == "__main__":
    _run()
