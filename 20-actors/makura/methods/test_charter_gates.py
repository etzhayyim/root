#!/usr/bin/env python3
"""makura 枕 — constitutional-gate conformance tests (manifest + lexicons).

makura is the foam-pillow manufacturing actor. Its constitutional gates are operationalized
at the schema layer: G6 closed-loop isocyanate + worker-exposure limits (MDI ≤5 ppb / TDI
≤2 ppb); G8 FR-free baseline (no PBDE/TDCPP/TCEP/Sb₂O₃); G11 KPI size/mass caps; G12 full
BoM on every pillow tag; G13 take-back QR + recycled-crumb loop (cross-actor with hodoki seat
foam); G14 NO embedded electronics / RFID / NFC (anti-surveillance applied to consumer goods).

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
MANIFEST = os.path.join(ROOT, "20-actors", "makura", "manifest.jsonld")
LEXDIR = os.path.join(ROOT, "00-contracts", "lexicons", "com", "etzhayyim", "makura")


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


# ── full gate set + non-goals ──
def test_all_14_gates_declared():
    gates = _manifest()["constitutionalGates"]["gates"]
    assert set(gates) == {f"G{i}" for i in range(1, 15)}, f"manifest must declare G1–G14, got {sorted(gates)}"


# ── G14 — no embedded electronics (anti-surveillance consumer good) ──
def test_g14_no_embedded_electronics():
    doc = _lex("pillowLotAttestation.json")
    assert "g14NoEmbeddedElectronics" in _required_union(doc), "G14: pillow lot must attest no embedded electronics"
    ee = _known(doc, "embeddedElectronics")
    assert ee == {"none"}, f"G14: embeddedElectronics must be structurally 'none' only, got {ee}"


# ── G11/G12/G13 — KPI cap + full BoM + take-back QR on every pillow ──
def test_g11_g12_g13_pillow_invariants():
    req = _required_union(_lex("pillowLotAttestation.json"))
    for field in ("withinG11Cap", "g12FullBomDisclosed", "g13TakeBackQrPresent", "bom", "pillowDid"):
        assert field in req, f"pillow lot must require {field}"


# ── G6 — isocyanate worker-exposure record ──
def test_g6_worker_exposure_record():
    doc = _lex("workerExposureRecord.json")
    req = _required_union(doc)
    assert "g6Compliant" in req and "agent" in req, "G6: workerExposureRecord must require g6Compliant + agent"
    agents = _known(doc, "agent")
    assert "MDI" in agents and "TDI" in agents, "G6: exposure agents must include MDI + TDI"


# ── G8 — flame-retardant disclosed on every lot (FR-free baseline) ──
def test_g8_flame_retardant_recorded():
    assert "fireRetardant" in _required_union(_lex("pillowLotAttestation.json")), \
        "G8: pillow lot must record fireRetardant (FR-free baseline disclosed)"


# ── G3/G4 — witness quorum + bilingual label ──
def test_g3_g4_witness_and_bilingual():
    for name in ("pillowLotAttestation.json", "foamBatchAttestation.json", "qcRecord.json", "fabricAttestation.json"):
        assert "attestingRobots" in _required_union(_lex(name)), f"G3: {name} must require attestingRobots"
    assert "g4BilingualMinimumMet" in _required_union(_lex("pillowLotAttestation.json")), "G4: bilingual label required"


# ── charter scan at the fabric door (§2 a–e) ──
def test_fabric_charter_scan():
    doc = _lex("fabricAttestation.json")
    assert "charterScan" in _required_union(doc), "fabric must carry a charterScan"
    surv = _known(doc, "section2cSurveillance")
    assert surv == {"clear", "warn", "violation"}, f"§2c surveillance scan must be a 3-state verdict, got {surv}"


# ── G13 — take-back recycling loop (cross-actor with hodoki seat foam) ──
def test_g13_recycling_certificate_loop():
    req = _required_union(_lex("recyclingCertificate.json"))
    for field in ("recycledBlend", "chainEntryCid", "intakeCenterDid", "returnedPillowDid"):
        assert field in req, f"G13: recyclingCertificate must require {field}"


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"makura/charter_gates: {len(fns)} tests passed")


if __name__ == "__main__":
    _run()
