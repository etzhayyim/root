#!/usr/bin/env python3
"""kanayama 金山 — constitutional-gate conformance tests (manifest + lexicons).

ADR-2605252400. kanayama is the circular-metallurgy actor (Wave 1 = closed-loop UBC
aluminum recycling). It is RECYCLING-ONLY by constitution: no bauxite / primary mining
(N1), no Hall-Héroult primary smelting (N2), no munitions / cartridge-brass recovery (N3),
no nuclear-decontamination feedstock (N4); mass-balance ≥98% closure (G2), recovery ≥95%
+ ≤6 kWh/kg (G12), renewable energy only — no captive coal/petcoke (G13).

The existing test (`py/test_agent.py`) covers the AGENT layer; the constitutional gates in
the manifest and the schema enums had NO conformance check. This is that check — it pins the
full G1–G14 gate set, the N1–N4 recycling-only non-goals, and the G8 emissions/leachate basis.
Standalone-runnable (`python3 test_charter_gates.py`) AND pytest-compatible; pure stdlib.
"""
from __future__ import annotations

import glob
import json
import os


def _repo_root():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != "/":
        if os.path.isdir(os.path.join(d, "00-contracts")) and os.path.isdir(os.path.join(d, "20-actors")):
            return d
        d = os.path.dirname(d)
    raise FileNotFoundError("repo root (with 00-contracts + 20-actors) not found")


ROOT = _repo_root()
MANIFEST = os.path.join(ROOT, "20-actors", "kanayama", "manifest.jsonld")
LEXDIR = os.path.join(ROOT, "00-contracts", "lexicons", "com", "etzhayyim", "kanayama")


def _manifest():
    with open(MANIFEST) as f:
        return json.load(f)


def _lex(name):
    with open(os.path.join(LEXDIR, name)) as f:
        return json.load(f)


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


# ── full constitutional gate set is declared ──
def test_all_14_gates_declared():
    gates = _manifest()["constitutionalGates"]["gates"]
    assert set(gates) == {f"G{i}" for i in range(1, 15)}, f"manifest must declare G1–G14, got {sorted(gates)}"


# ── recycling-only: N1–N4 exclude primary mining / smelting / munitions / nuclear ──
def test_recycling_only_nongoals():
    n = _manifest()["nonGoals"]["goals"]
    for key in ("N1", "N2", "N3", "N4"):
        assert key in n, f"recycling-only: non-goal {key} must be declared"
    assert "primary mining" in n["N1"].lower() or "bauxite" in n["N1"].lower(), "N1 must exclude primary mining"
    assert "hall-héroult" in n["N2"].lower() or "primary" in n["N2"].lower(), "N2 must exclude primary smelting"
    assert "munition" in n["N3"].lower() or "cartridge" in n["N3"].lower(), "N3 must exclude munitions/cartridge brass"
    assert "nuclear" in n["N4"].lower() or "radio" in n["N4"].lower(), "N4 must exclude nuclear/radiological feedstock"


# ── G2/G12/G13 quantitative discipline is stated ──
def test_mass_balance_recovery_energy_gates():
    g = _manifest()["constitutionalGates"]["gates"]
    assert "98%" in g["G2"] or "≥98" in g["G2"], "G2 must state ≥98% mass-balance closure"
    assert "95%" in g["G12"] or "≥95" in g["G12"], "G12 must state ≥95% recovery rate"
    assert "captive coal" in g["G13"].lower() or "petroleum coke" in g["G13"].lower() or "petcoke" in g["G13"].lower(), \
        "G13 must prohibit captive coal / petcoke"


# ── G8 emissions / leachate regulatory basis enumerated ──
def test_g8_emissions_regulatory_basis():
    basis = _known(_lex("airEmissionsAuditRecord.json"), "regulatoryBasis") or set()
    if not basis:  # enum may sit under an items list — collect any knownValues containing IED
        for f in (_lex("airEmissionsAuditRecord.json"),):
            def collect(o):
                acc = set()

                def w(o):
                    if isinstance(o, dict):
                        kv = o.get("knownValues")
                        if isinstance(kv, list):
                            acc.update(kv)
                        for v in o.values():
                            w(v)
                    elif isinstance(o, list):
                        for v in o:
                            w(v)
                w(o)
                return acc
            basis = collect(f)
    assert any("IED" in b for b in basis), "G8: must cite EU IED 2010/75/EU"
    assert any("12457" in b for b in basis), "G8: must cite EN 12457 leachate"


# ── G4 witness quorum: melt pour records attesting robots ──
def test_g4_melt_requires_attesting_robots():
    req = _required_union(_lex("meltingAttestation.json"))
    assert "attestingRobots" in req, "G4: meltingAttestation must require attestingRobots (witness quorum)"
    assert "alloyComposition" in req, "meltingAttestation must record alloyComposition"


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"kanayama/charter_gates: {len(fns)} tests passed")


if __name__ == "__main__":
    _run()
