#!/usr/bin/env python3
"""hodoki 解き — constitutional-gate conformance tests (manifest + lexicons).

ADR-2606051xxx (hodoki ELV disassembly + materials recovery). hodoki tears down end-of-life
vehicles into clean recovered streams. Its constitutional gates are operationalized at the
schema layer: G8 (CONSTITUTIONAL FIRST) mandatory ECU/telematics data wipe BEFORE disassembly
(anti-surveillance for vehicles); G6 F-gas capture ≥95% / no atmospheric venting; G7 Li-ion
thermal safety; G12 (CONSTITUTIONAL FIRST) right-to-repair part catalog with VIN provenance +
part DID; G13 ≥95% material recovery + cross-actor circular feed (→ kanayama metals, → hikari
second-life batteries); G14 PGM yield ≥95%; civilian only (N1 military / N2 aerospace excluded).

The existing test (`py/test_agent.py`) covers the AGENT layer; the manifest gate set and the
schema compliance fields had NO conformance check. This is that check.
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
MANIFEST = os.path.join(ROOT, "20-actors", "hodoki", "manifest.jsonld")
LEXDIR = os.path.join(ROOT, "00-contracts", "lexicons", "com", "etzhayyim", "hodoki")


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


# ── full gate set + civilian-only non-goals ──
def test_all_14_gates_declared():
    gates = _manifest()["constitutionalGates"]["gates"]
    assert set(gates) == {f"G{i}" for i in range(1, 15)}, f"manifest must declare G1–G14, got {sorted(gates)}"


def test_civilian_only_no_military_aerospace():
    ng = _manifest()["nonGoals"]
    n = ng.get("goals", ng.get("nonGoals", ng))
    assert "military" in n["N1"].lower(), "N1 must exclude military vehicles"
    assert "aerospace" in n["N2"].lower() or "aircraft" in n["N2"].lower(), "N2 must exclude aerospace vehicles"


# ── G8 (CONSTITUTIONAL FIRST) — mandatory data wipe before disassembly ──
def test_g8_data_wipe_attestation():
    doc = _lex("dataWipeAttestation.json")
    req = _required_union(doc)
    for field in ("ecuWipes", "method", "verified", "g8Compliant"):
        assert field in req, f"G8: dataWipeAttestation must require {field}"
    methods = _known(doc, "method")
    assert "cryptographic-destruction" in methods and "physical-chip-shred" in methods, \
        "G8: wipe method must include cryptographic destruction + physical chip-shred fallback"


# ── G6 — F-gas capture ≥95%, no atmospheric venting ──
def test_g6_fgas_capture():
    req = _required_union(_lex("depollutionAttestation.json"))
    for field in ("fgasCapture", "recoveryRatePct", "atmosphericVentingDetected", "g6Compliant"):
        assert field in req, f"G6: depollutionAttestation must require {field}"


# ── G7 — Li-ion thermal safety ──
def test_g7_battery_thermal_safety():
    req = _required_union(_lex("batteryHandlingRecord.json"))
    for field in ("g7Compliant", "soh", "thermalBaseline", "routingDecision"):
        assert field in req, f"G7: batteryHandlingRecord must require {field}"


# ── G12 (CONSTITUTIONAL FIRST) — right-to-repair part catalog ──
def test_g12_right_to_repair_catalog():
    req = _required_union(_lex("partsHarvestCatalog.json"))
    for field in ("g12RightToRepairInvariant", "g12NoDrmCircumvention", "g12NoProprietaryLockIn",
                  "g12PublicDiscovery", "vinProvenance", "partDid", "catalogCid"):
        assert field in req, f"G12: partsHarvestCatalog must require {field}"


# ── G14 — PGM (Pt/Pd/Rh) yield audit ──
def test_g14_pgm_yield_audit():
    req = _required_union(_lex("catalystRecoveryRecord.json"))
    assert "g14Compliant" in req and "yieldAudit" in req, "G14: catalystRecoveryRecord must require g14Compliant + yieldAudit"


# ── G13 — ≥95% recovery + cross-actor circular feed (→ kanayama) ──
def test_g13_circular_feed_to_kanayama():
    req = _required_union(_lex("shredOutputAttestation.json"))
    for field in ("g13Compliant", "kanayamaHandoff", "ferrousMassKg", "nonFerrousAlMassKg"):
        assert field in req, f"G13: shredOutputAttestation must require {field} (circular feed to kanayama)"


# ── intake: stolen / charter screen at the door ──
def test_intake_screens_stolen_and_charter():
    doc = _lex("elvIntakeRecord.json")
    req = _required_union(doc)
    for field in ("charterScan", "stolenRegistryCheck", "n7TitleVerified", "vin"):
        assert field in req, f"intake: elvIntakeRecord must require {field}"


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"hodoki/charter_gates: {len(fns)} tests passed")


if __name__ == "__main__":
    _run()
