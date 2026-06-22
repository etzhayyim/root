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
  enforcement point 3 — the analyzer guard (`methods/analyze.cljc`):
      `screen-thc` raises ex-info on :psychoactive (and on a missing class).

Invariants under test:

  1. G1 (ontology) — :hemp/thc-class :db/allowed is exactly {fiber, low-thc};
     :psychoactive is absent.
  2. G1 (lexicon) — fiberProvenance + hempCultivar thcClass enum match the
     ontology set and exclude psychoactive.
  3. G1 (guard) — allowed-thc-classes matches; screen-thc raises on
     :psychoactive and on a cultivar with no thc-class.
  4. G4 — cultivationLicensePlan is member-principal / no-fiat-inflow:
     licenseePrincipal const "member", signedBy enum ["member"], fundingSource
     enum ["member-okaimono"] (the religious-corp never funds the licence).
  5. G5 — cultivationLicensePlan.serverHeldKey is const false (no-server-key).
  6. G8 — cultivationLicensePlan.outwardGated is const true (real cultivation /
     licence filing gated to Council Lv6+ + operator).
  7. G1 — fiberProvenance.screened is const true (a provenance record exists
     ONLY after the fibre/THC screen passes).

NOTE: enforcement point 3 now exercises the cljc port (methods/analyze.cljc via
bb subprocess) since the Python methods/analyze.py was migrated to cljc.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_ONTOLOGY = _REPO / "00-contracts" / "schemas" / "ritual-hemp-ontology.kotoba.edn"
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "nusa"
_ACTORS = _REPO / "20-actors"

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


def _bb(expr: str) -> subprocess.CompletedProcess:
    """Run a Clojure expression via bb with the actors classpath."""
    return subprocess.run(
        ["bb", "--classpath", str(_ACTORS), "-e", expr],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(_REPO),
    )


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
    """G1: screen-thc MUST raise on :psychoactive and on a cultivar with no thc-class (via bb)."""
    # Verify allowed-thc-classes set agrees with the expected set
    result_classes = _bb(
        "(require '[nusa.methods.analyze :as a])"
        "(pr (into #{} (map #(clojure.string/replace % #\"^:\" \"\") a/allowed-thc-classes)))"
    )
    assert result_classes.returncode == 0, f"bb failed: {result_classes.stderr}"
    classes_str = result_classes.stdout.strip()
    for expected in _EXPECTED_THC:
        assert expected in classes_str, (
            f"G1: allowed-thc-classes missing {expected!r}; got {classes_str!r}"
        )
    for bad in _FORBIDDEN_THC:
        assert bad not in classes_str, (
            f"G1 VIOLATION: {bad!r} found in allowed-thc-classes; got {classes_str!r}"
        )

    # screen-thc must throw on :psychoactive
    result_psy = _bb(
        "(require '[nusa.methods.analyze :as a])"
        "(def r (try (a/screen-thc"
        "              {\"hemp.bad\" {\":hemp/id\" \"hemp.bad\" \":hemp/thc-class\" \":psychoactive\"}})"
        "            :no-throw (catch Exception e :threw)))"
        "(pr r)"
    )
    assert result_psy.returncode == 0, f"bb failed: {result_psy.stderr}"
    assert ":threw" in result_psy.stdout, (
        "G1: screen-thc MUST throw on :psychoactive THC class "
        f"(structurally unrepresentable); stdout={result_psy.stdout!r}"
    )

    # screen-thc must throw on missing thc-class
    result_missing = _bb(
        "(require '[nusa.methods.analyze :as a])"
        "(def r (try (a/screen-thc {\"hemp.x\" {\":hemp/id\" \"hemp.x\"}})"
        "            :no-throw (catch Exception e :threw)))"
        "(pr r)"
    )
    assert result_missing.returncode == 0, f"bb failed: {result_missing.stderr}"
    assert ":threw" in result_missing.stdout, (
        "G1: screen-thc MUST throw on a cultivar with no thc-class "
        f"(nil class is rejected); stdout={result_missing.stdout!r}"
    )

    # a clean fibre cultivar passes
    result_clean = _bb(
        "(require '[nusa.methods.analyze :as a])"
        "(def r (a/screen-thc {\"hemp.ok\" {\":hemp/id\" \"hemp.ok\" \":hemp/thc-class\" \":fiber\"}}))"
        "(pr (map? r))"
    )
    assert result_clean.returncode == 0, f"bb failed: {result_clean.stderr}"
    assert "true" in result_clean.stdout, (
        f"G1: a clean :fiber cultivar should pass screen-thc; stdout={result_clean.stdout!r}"
    )


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
