"""Lock-in tests for the nusa (幣) constitutional invariants.

Pins the structural properties designed in ADR-2606039800 (nusa — ritual /
industrial hemp heritage + low-THC fibre cultivation; NOT a legalization actor)
so a future refactor cannot silently weaken a constitutional invariant. The
signature nusa invariant is G1: a cultivar's THC class is :fiber | :low-thc ONLY
— `:psychoactive` is structurally UNREPRESENTABLE (the same discipline as
kamado's `:feedstock/class` fossil exclusion and tazuna's `:weaponizable`).

nusa declares the invariant in THREE places and this suite proves they agree:

  enforcement point 1 — the ontology schema (`ritual-hemp-ontology.kotoba.edn`):
      `:hemp/thc-class :db/allowed [:fiber :low-thc]` (no :psychoactive).
  enforcement point 2 — the published lexicons (`com.etzhayyim.nusa.*`):
      thcClass `enum` is exactly [fiber, low-thc].
  enforcement point 3 — the analyzer guard (`methods/analyze.py`):
      `screen_thc` raises ValueError on :psychoactive (and on a missing class).

Invariants under test:

  1. G1 (ontology) — :hemp/thc-class :db/allowed is exactly {fiber, low-thc};
     :psychoactive is absent.
  2. G1 (lexicon) — fiberProvenance + hempCultivar thcClass enum match the
     ontology set and exclude psychoactive.
  3. G1 (guard) — ALLOWED_THC_CLASSES matches; screen_thc raises on
     :psychoactive and on a cultivar with no thc-class.
  4. G4 — cultivationLicensePlan is member-principal / no-fiat-inflow:
     licenseePrincipal const "member", signedBy enum ["member"], fundingSource
     enum ["member-okaimono"] (the religious-corp never funds the licence).
  5. G5 — cultivationLicensePlan.serverHeldKey is const false (no-server-key).
  6. G8 — cultivationLicensePlan.outwardGated is const true (real cultivation /
     licence filing gated to Council Lv6+ + operator).
  7. G1 — fiberProvenance.screened is const true (a provenance record exists
     ONLY after the fibre/THC screen passes).
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_ONTOLOGY = _REPO / "00-contracts" / "schemas" / "ritual-hemp-ontology.kotoba.edn"
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "nusa"
_ANALYZE = _REPO / "20-actors" / "nusa" / "methods" / "analyze.py"

# The ONLY representable THC classes (G1). :psychoactive is unrepresentable.
_EXPECTED_THC = {"fiber", "low-thc"}
_FORBIDDEN_THC = {"psychoactive", "recreational", "high-thc"}


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text())


def _record_props(lex: dict) -> dict:
    return lex["defs"]["main"]["record"]["properties"]


def _ontology_thc_allowed() -> set[str]:
    text = _ONTOLOGY.read_text()
    m = re.search(r":hemp/thc-class\s*\{.*?:db/allowed\s*\[(.*?)\]", text, re.S)
    assert m, "could not locate :hemp/thc-class :db/allowed in the ontology"
    return {tok.lstrip(":") for tok in re.findall(r":[a-z0-9-]+", m.group(1))}


def _import_analyze():
    spec = importlib.util.spec_from_file_location("nusa_analyze", _ANALYZE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─────────────────────────────────────────────────────────────────────────
# 1. G1 — ontology :hemp/thc-class :db/allowed excludes psychoactive
# ─────────────────────────────────────────────────────────────────────────


def test_g1_ontology_thc_class_allowed_excludes_psychoactive():
    assert _ONTOLOGY.exists(), f"missing ontology: {_ONTOLOGY}"
    allowed = _ontology_thc_allowed()
    assert allowed == _EXPECTED_THC, (
        f"G1: ontology :hemp/thc-class drifted; got {sorted(allowed)}"
    )
    for bad in _FORBIDDEN_THC:
        assert bad not in allowed, (
            f"G1 VIOLATION: {bad!r} became a representable THC class — "
            f":psychoactive must stay structurally absent (nusa is fibre/ritual-only)"
        )


# ─────────────────────────────────────────────────────────────────────────
# 2. G1 — lexicon thcClass enum matches and excludes psychoactive
# ─────────────────────────────────────────────────────────────────────────


def test_g1_lexicon_thc_enum_matches_and_excludes_psychoactive():
    for name in ("fiberProvenance.json", "hempCultivar.json"):
        p = _LEX / name
        assert p.exists(), f"missing published lexicon: {p}"
        enum = set(_record_props(_load_json(p))["thcClass"]["enum"])
        assert enum == _EXPECTED_THC, (
            f"G1: {name} thcClass enum drifted from the ontology set; got {sorted(enum)}"
        )
        for bad in _FORBIDDEN_THC:
            assert bad not in enum, (
                f"G1 VIOLATION: {name} thcClass enum admits {bad!r}"
            )


# ─────────────────────────────────────────────────────────────────────────
# 3. G1 — the analyzer guard rejects psychoactive / missing class
# ─────────────────────────────────────────────────────────────────────────


def test_g1_guard_rejects_psychoactive_and_missing_class():
    analyze = _import_analyze()
    assert {c.lstrip(":") for c in analyze.ALLOWED_THC_CLASSES} == _EXPECTED_THC, (
        f"G1: ALLOWED_THC_CLASSES drifted; got {analyze.ALLOWED_THC_CLASSES}"
    )
    with pytest.raises(ValueError):
        analyze.screen_thc({"hemp.bad": {":hemp/id": "hemp.bad", ":hemp/thc-class": ":psychoactive"}})
    with pytest.raises(ValueError):
        analyze.screen_thc({"hemp.x": {":hemp/id": "hemp.x"}})  # no thc-class at all
    # a clean fibre cultivar passes.
    ok = analyze.screen_thc({"hemp.ok": {":hemp/id": "hemp.ok", ":hemp/thc-class": ":fiber"}})
    assert isinstance(ok, dict)


# ─────────────────────────────────────────────────────────────────────────
# 4. G4 — cultivationLicensePlan is member-principal / no-fiat-inflow
# ─────────────────────────────────────────────────────────────────────────


def test_g4_cultivation_license_is_member_principal():
    props = _record_props(_load_json(_LEX / "cultivationLicensePlan.json"))
    assert props["licenseePrincipal"].get("const") == "member", (
        "G4: cultivationLicensePlan.licenseePrincipal MUST be const 'member' — "
        "nusa is never the licensee/funder; the member is the principal"
    )
    assert props["signedBy"].get("enum") == ["member"], (
        f"G4: signedBy MUST be ['member']; got {props['signedBy'].get('enum')}"
    )
    assert props["fundingSource"].get("enum") == ["member-okaimono"], (
        "G4: fundingSource MUST be ['member-okaimono'] — religious-corp funds "
        "never pay the cultivation licence (okaimono assisted-checkout, §1.3)"
    )


# ─────────────────────────────────────────────────────────────────────────
# 5 + 6. G5 / G8 — no-server-key + outward-gated
# ─────────────────────────────────────────────────────────────────────────


def test_g5_g8_cultivation_license_key_and_gate_consts():
    props = _record_props(_load_json(_LEX / "cultivationLicensePlan.json"))
    assert props["serverHeldKey"].get("const") is False, (
        "G5: cultivationLicensePlan.serverHeldKey MUST be const false (no-server-key)"
    )
    assert props["outwardGated"].get("const") is True, (
        "G8: cultivationLicensePlan.outwardGated MUST be const true (live "
        "cultivation / licence filing = Council Lv6+ + operator)"
    )


# ─────────────────────────────────────────────────────────────────────────
# 7. G1 — fiberProvenance only exists after the screen passes
# ─────────────────────────────────────────────────────────────────────────


def test_g1_fiber_provenance_screened_const_true():
    props = _record_props(_load_json(_LEX / "fiberProvenance.json"))
    assert props["screened"].get("const") is True, (
        "G1: fiberProvenance.screened MUST be const true (a provenance record "
        "exists ONLY after the fibre/THC-class screen passes)"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
