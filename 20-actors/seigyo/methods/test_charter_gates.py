#!/usr/bin/env python3
"""seigyo 制御 — structural charter/safety-gate conformance tests over the lexicons.

ADR-2606111000. seigyo is the ISA-95 L0–L2 industrial CONTROL layer. Its safety invariant
is ABSOLUTE (§3): safety interlocks are hardwired / safety-relay only; no LLM / Murakumo /
kotoba cell / network round-trip ever enters the safety path; software above L1S is
advisory-only; Murakumo optimization reaches actuation ONLY through an attested setpoint
envelope (min/max + rate-of-change limit). Commercial DCS/PLC/SCADA runtimes
(Siemens/Honeywell/Yokogawa/Emerson/Rockwell/ABB/Schneider/Mitsubishi/GE/AVEVA/Ignition)
are PROHIBITED — only the open stack (OpenPLC + FUXA/Rapid SCADA + open62541) is
representable. This is the first executable check that pins those gates at the schema layer.

seigyo had NO test anywhere before this file (verified 2026-06-16).
Standalone-runnable (`python3 test_charter_gates.py`) AND pytest-compatible; pure stdlib.
"""
from __future__ import annotations

import glob
import json
import os

OPEN_SCADA = {"fuxa", "rapid-scada", "openscada"}
COMMERCIAL_VENDORS = (
    "siemens", "honeywell", "yokogawa", "emerson", "rockwell", "abb",
    "schneider", "mitsubishi", "aveva", "ignition", "wonderware", "deltav",
)


def _lex_dir():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != "/":
        cand = os.path.join(d, "00-contracts", "lexicons", "com", "etzhayyim", "seigyo")
        if os.path.isdir(cand):
            return cand
        d = os.path.dirname(d)
    raise FileNotFoundError("could not locate 00-contracts/lexicons/com/etzhayyim/seigyo")


LEX = _lex_dir()


def _load(name):
    with open(os.path.join(LEX, name)) as f:
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
    out = []

    def walk(o, parent=None):
        if isinstance(o, dict):
            if "knownValues" in o and parent == field:
                out.extend(o["knownValues"])
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, parent)
    walk(doc)
    return set(out)


def _all_enum_values(doc):
    out = set()

    def walk(o):
        if isinstance(o, dict):
            kv = o.get("knownValues")
            if isinstance(kv, list):
                out.update(str(x).lower() for x in kv)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(doc)
    return out


# ── no commercial DCS/SCADA — only the open stack is representable ──
def test_scada_stack_is_open_only():
    enum = _known(_load("scadaProjectAttestation.json"), "scadaStack")
    assert enum == OPEN_SCADA, f"scadaStack must be exactly the open set {OPEN_SCADA}, got {enum}"


def test_no_commercial_vendor_in_any_enum_value():
    # field/enum-value check (not description prose — the README naming prohibited vendors is fine).
    for f in glob.glob(os.path.join(LEX, "*.json")):
        vals = _all_enum_values(_load(os.path.basename(f)))
        for vendor in COMMERCIAL_VENDORS:
            assert not any(vendor in v for v in vals), \
                f"{os.path.basename(f)}: commercial vendor '{vendor}' must not be a representable enum value"


# ── safety interlock: physically verified, hardwired safety functions ──
def test_interlock_physically_verified_required():
    doc = _load("interlockVerificationRecord.json")
    req = _required_union(doc)
    assert "physicallyVerified" in req, "safety: interlock verification must require physicallyVerified (reset is physical/human)"
    types = _known(doc, "interlockType")
    for t in ("estop", "over-pressure", "over-temperature", "gas-detection", "light-curtain", "loto"):
        assert t in types, f"safety: interlockType must cover {t}"


# ── IO trust isolation: external untrusted, safety mirror read-only ──
def test_io_trust_class_isolates_safety():
    enum = _known(_load("ioPointRegistry.json"), "trustClass")
    assert enum == {"attested", "untrusted-external", "safety-mirror-readonly"}, \
        f"trustClass must isolate external + read-only safety mirror, got {enum}"


# ── attestation: every PLC program Council-attested + content-addressed, running==attested ──
def test_plc_program_attested_and_addressed():
    req = _required_union(_load("plcProgramAttestation.json"))
    for field in ("councilAttestationRef", "programCid", "stSourceCid"):
        assert field in req, f"attestation: plcProgramAttestation must require {field}"


def test_runtime_attestation_matches_attested_program():
    req = _required_union(_load("runtimeAttestation.json"))
    for field in ("loadedProgramHash", "attestedProgramCid", "match"):
        assert field in req, f"attestation: runtimeAttestation must require {field} (running == attested)"


# ── advisory-only actuation: Murakumo reaches the valve only via a bounded envelope ──
def test_setpoint_envelope_is_bounded_with_rate_limit():
    req = _required_union(_load("setpointEnvelope.json"))
    for field in ("minMilli", "maxMilli", "maxRateOfChangeMilli"):
        assert field in req or field in _all_property_keys(_load("setpointEnvelope.json")), \
            f"safety: setpointEnvelope must carry {field} (bounded min/max + rate-of-change limit)"


def _all_property_keys(doc):
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


# ── G6 surveillance: telemetry declares person-attributability ──
def test_telemetry_declares_person_attributability():
    req = _required_union(_load("telemetryAggregateRecord.json"))
    assert "personAttributable" in req, "G6: telemetry must declare personAttributable (no covert person-attribution)"


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"seigyo/charter_gates: {len(fns)} tests passed (lex dir: {os.path.relpath(LEX)})")


if __name__ == "__main__":
    _run()
