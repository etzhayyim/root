#!/usr/bin/env python3
"""mitsuho 瑞穂 — constitutional-gate conformance tests (manifest + lexicons).

mitsuho is the food / agriculture actor (plant + aquaculture + alt-protein; the harvest side
of suki's tractors). Its constitutional gates are operationalized at the schema layer: G2 seed
sovereignty (open-source seed banks, no patented commercial lines); G4 soil regeneration
(soil-carbon delta logged, negative → halt); G6 no synthetic pesticides (pesticide manifest
hook); G7 GMO only with Council attestation; N1 no animal slaughter in R0–R3 (R4-gated);
non-chemical preservation only.

The existing test (`py/test_agent.py`) covers the AGENT layer; the manifest gate set and the
lexicon gate hooks had NO conformance check. This is that check.
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
MANIFEST = os.path.join(ROOT, "20-actors", "mitsuho", "manifest.jsonld")
LEXDIR = os.path.join(ROOT, "00-contracts", "lexicons", "com", "etzhayyim", "mitsuho")
NON_CHEMICAL_PRESERVATION = {"dried", "canned", "lacto-fermented", "cold-stored", "vacuum-sealed", "freeze-dried"}


def _manifest():
    with open(MANIFEST) as f:
        return json.load(f)


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


def _property_keys(doc):
    keys = set()

    def walk(o):
        if isinstance(o, dict):
            p = o.get("properties")
            if isinstance(p, dict):
                keys.update(p.keys())
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(doc)
    return keys


def _known(doc, field):
    out = set()

    def walk(o, parent=None):
        if isinstance(o, dict):
            if "knownValues" in o and parent == field:
                out.update(o["knownValues"])
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, parent)
    walk(doc)
    return out


# ── full gate set ──
def test_all_14_gates_declared():
    gates = _manifest()["constitutionalGates"]["gates"]
    assert set(gates) == {f"G{i}" for i in range(1, 15)}, f"manifest must declare G1–G14, got {sorted(gates)}"


# ── G2 seed sovereignty ──
def test_g2_seed_sovereignty_required():
    req = _required_union(_lex("cropPlanAttestation.json"))
    for field in ("seedSourceAttestation", "varietalManifest"):
        assert field in req, f"G2: cropPlanAttestation must require {field}"


# ── G6/G7 — pesticide manifest + GMO attestation hooks exist ──
def test_g6_g7_pesticide_and_gmo_hooks():
    keys = _property_keys(_lex("cropPlanAttestation.json"))
    assert "pesticideManifest" in keys, "G6: cropPlanAttestation must carry a pesticideManifest (synthetic-pesticide screen)"
    assert "gmoAttestationCid" in keys, "G7: cropPlanAttestation must carry a gmoAttestationCid (Council-gated GMO)"


# ── G4 soil regeneration ──
def test_g4_soil_carbon_logged():
    req = _required_union(_lex("harvestAttestation.json"))
    for field in ("soilCarbonDeltaTonsCo2Eq", "yieldKgDryMatter", "photoCid", "cropPlanAttestationCid"):
        assert field in req, f"G4: harvestAttestation must require {field}"


# ── witness quorum + agronomist signature ──
def test_witness_and_agronomist():
    assert "attestingRobots" in _required_union(_lex("harvestAttestation.json")), "harvest must require attestingRobots"
    assert "attestingAgronomistDid" in _required_union(_lex("cropPlanAttestation.json")), "crop plan must require agronomist DID"


# ── parcel biodiversity-no-harm + LANDS registry ──
def test_parcel_biodiversity_and_lands():
    req = _required_union(_lex("parcelAttestation.json"))
    for field in ("biodiversityNoHarmAttestationCid", "landsRegistryCid"):
        assert field in req, f"parcel must require {field}"


# ── non-chemical preservation only ──
def test_preservation_non_chemical():
    methods = _known(_lex("foodLotAttestation.json"), "preservationMethod")
    assert methods == NON_CHEMICAL_PRESERVATION, f"preservation must be the non-chemical set, got {methods}"


# ── N1 — animal product is R4-gated (not R0–R3) ──
def test_n1_animal_product_r4_gated():
    scopes = _known(_lex("silenAgricultureReview.json"), "scope")
    assert "n1-animal-product-r4-gate" in scopes, "N1: animal product must be an explicit R4 Council gate"


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"mitsuho/charter_gates: {len(fns)} tests passed")


if __name__ == "__main__":
    _run()
