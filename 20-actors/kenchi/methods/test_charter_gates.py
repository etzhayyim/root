#!/usr/bin/env python3
"""kenchi 検地 — structural charter-gate conformance tests over the central lexicons.

ADR-2606272030. kenchi is an EXTERNAL-MARKET real-estate valuation + transparency
substrate — NOT a brokerage, NOT a closed AVM, NOT an advice renderer. Its discipline
is structural and is pinned here at the schema layer so a silent weakening is caught:

  G3 PROVENANCE-OR-SILENCE   — a valuation MUST carry provenance + nComps(≥3) + nAuthorities(≥2) + CI.
  G4 DERIVED/AGGREGATE       — a PUBLISHED record's license is exactly {open, derived-only}; never raw/restricted.
  G5 INALIENABLE-LAND        — assetClass is exactly {external-market}; manifest pins the Land-Trust exclusion + N1.
  G6 NO-PII                  — no owner/person/PII field is representable on a valuation (a parcel is a place).
  N8 NO SINGLE-SOURCE ORACLE — provenanceAttestation MUST carry nAuthorities + nComps + verdict.

Standalone-runnable (`python3 test_charter_gates.py`) AND pytest-compatible; pure stdlib.
"""
from __future__ import annotations

import json
import os

PUBLISH_LICENSES = {"open", "derived-only"}          # G4: a published record is never raw/restricted
PII_TOKENS = ("owner", "ownername", "person", "occupant", "resident", "pii", "ssn", "name")  # G6
ASSET_CLASSES = {"external-market"}                  # G5: inalienable land is not market-valued here


def _root():
    d = os.path.dirname(os.path.abspath(__file__))
    while d != "/":
        if os.path.isdir(os.path.join(d, "00-contracts", "lexicons", "com", "etzhayyim", "kenchi")):
            return d
        d = os.path.dirname(d)
    raise FileNotFoundError("could not locate 00-contracts/lexicons/com/etzhayyim/kenchi")


ROOT = _root()
LEX = os.path.join(ROOT, "00-contracts", "lexicons", "com", "etzhayyim", "kenchi")
ACTOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(path):
    with open(path) as f:
        return json.load(f)


def _lex(name):
    return _load(os.path.join(LEX, name))


def _record_props(doc):
    return doc["defs"]["main"]["record"]["properties"]


def _required(doc):
    return set(doc["defs"]["main"]["record"].get("required", []))


def _all_property_names(o, acc):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "properties" and isinstance(v, dict):
                acc.update(v.keys())
            _all_property_names(v, acc)
    elif isinstance(o, list):
        for v in o:
            _all_property_names(v, acc)
    return acc


def test_g3_provenance_or_silence():
    """A valuation cannot exist without provenance + comps + authorities + CI."""
    v = _lex("valuation.json")
    req = _required(v)
    for field in ("provenance", "nComps", "nAuthorities", "ciLoUsd", "ciHiUsd", "valueUsd"):
        assert field in req, f"G3: valuation must require {field}"
    props = _record_props(v)
    assert props["nComps"].get("minimum") == 3, "G3: nComps minimum must be 3"
    assert props["nAuthorities"].get("minimum") == 2, "G3: nAuthorities minimum must be 2"


def test_g4_published_license_is_open_or_derived_only():
    """No published record may be raw/restricted; only open | derived-only."""
    for name in ("valuation.json", "regionReport.json"):
        lic = _record_props(_lex(name))["license"]
        assert set(lic["knownValues"]) == PUBLISH_LICENSES, \
            f"G4: {name} license must be exactly {PUBLISH_LICENSES}, got {lic['knownValues']}"
    # but the SOURCE registry must still be able to mark a source 'restricted'
    sl = _record_props(_lex("sourceLicense.json"))["licenseClass"]
    assert "restricted" in set(sl["knownValues"]), "G4: sourceLicense must represent 'restricted' sources"


def test_g5_asset_class_is_external_market_only():
    """Inalienable Land Trust land is never market-valued: assetClass == {external-market}."""
    ac = _record_props(_lex("valuation.json"))["assetClass"]
    assert set(ac["knownValues"]) == ASSET_CLASSES, \
        f"G5: assetClass must be exactly {ASSET_CLASSES}, got {ac['knownValues']}"


def test_g5_manifest_pins_inalienable_exclusion():
    """The manifest must encode G5 + N1 (the Land-Trust exclusion) immutably."""
    m = _load(os.path.join(ACTOR, "manifest.jsonld"))
    gates = m["constitutionalGates"]["gates"]
    assert "G5" in gates and "INALIENABLE" in gates["G5"].upper(), "G5 must be a named gate"
    assert "2605192245" in gates["G5"], "G5 must cite the Land-Sovereignty ADR"
    n1 = m["nonGoals"]["goals"]["N1"]
    assert "Land Trust" in n1 and "no market price" in n1.lower(), "N1 must exclude Land-Trust valuation"


def test_g6_no_pii_fields_anywhere_in_valuation():
    """A parcel is a place, not a person: no owner/person/PII property is representable."""
    names = {n.lower() for n in _all_property_names(_lex("valuation.json"), set())}
    leaked = sorted(n for n in names if any(tok in n for tok in PII_TOKENS))
    assert not leaked, f"G6: PII-like fields must not exist on valuation: {leaked}"


def test_n8_no_single_source_oracle():
    """provenanceAttestation must pin authority + comp counts and a verdict."""
    pa = _lex("provenanceAttestation.json")
    req = _required(pa)
    for field in ("nAuthorities", "nComps", "verdict", "comps"):
        assert field in req, f"N8: provenanceAttestation must require {field}"
    verdict = _record_props(pa)["verdict"]["knownValues"]
    assert {"published", "withheld-mrv", "insufficient-evidence"} == set(verdict), \
        "G3: verdict must offer MRV / insufficient-evidence, not only 'published'"


def _run():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL {t.__name__}: {e}")
    print(f"── kenchi charter gates: {len(tests) - failed}/{len(tests)} passed ──")
    return failed


if __name__ == "__main__":
    raise SystemExit(1 if _run() else 0)
