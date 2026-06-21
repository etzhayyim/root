"""Lock-in tests for the hotaru (蛍) constitutional invariants.

Pins the structural properties designed in ADR-2606051200 (hotaru — the
open-publication III-V / InP substrate knowledge COMMONS; NOT a fab) so a future
refactor cannot silently weaken a constitutional invariant. hotaru exists to
construct the open commons that ADR-2605265500 §2's R4+ re-evaluation gate is
conditioned on — so its three structural invariants are load-bearing and each is
declared in THREE places (ontology schema + lexicon enum/const + analyze.cljc
guard). This suite proves all three agree:

  INVARIANT #1 — OPEN-IP-ONLY (G1): :iiiv.proc/source-license is a practiceable-
      open license; :vendor-proprietary / :patent-active / :trade-secret are
      structurally UNREPRESENTABLE (the nusa :thc-class / kamado feedstock pattern).
  INVARIANT #2 — DESIGN-ONLY / NOT-FABRICATED (G2): crystal + wafer `fabricated`
      is :db/allowed [false]; a grown boule / manufactured wafer is unrepresentable
      through R3 (III-V fabrication PROHIBITED).
  INVARIANT #3 — CONFLICT-MINERAL SOURCING (G4): conflict-mineral In/Ga crystals
      must declare a clean in-sourcing.

Invariants under test:

  1. G1 (ontology) — source-license :db/allowed is exactly the 5-license open set;
     no proprietary/patent-active/trade-secret member.
  2. G1 (lexicon) — processKnowledge.sourceLicense enum matches the open set.
  3. G1 (guard) — ALLOWED-LICENSES matches; screen-licenses raises on
     :vendor-proprietary and passes the open set.
  4. G2 (ontology) — crystal + wafer fabricated :db/allowed is exactly [false]
     (no true is representable).
  5. G2 (lexicon) — crystalGrowthDesign.fabricated + waferSpec.fabricated are
     const false; commonsReadinessReport + silenHotaruReview fabricationProhibited
     are const true.
  6. G2 (guard) — screen-fabrication raises on a fabricated crystal AND a
     fabricated wafer, and passes when both are false.
  7. G4 — crystalGrowthDesign.inSourcing enum is the clean set; guard
     CLEAN-SOURCING matches.
  8. G3 — silenHotaruReview is non-adjudicating: councilLevel const "Lv7+"
     (hotaru reports; Council Lv7+ decides the fabrication gate).

NOTE: enforcement points 3, 6, and 7 now exercise the cljc port
(methods/analyze.cljc via bb subprocess) since the Python methods/analyze.py
was migrated to cljc.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_ONTOLOGY = _REPO / "00-contracts" / "schemas" / "iii-v-substrate-ontology.kotoba.edn"
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "hotaru"
_ACTORS = _REPO / "20-actors"

_EXPECTED_LICENSES = {
    "academic-oa",
    "patent-expired",
    "textbook-public",
    "standard-public",
    "own-rnd",
}
_FORBIDDEN_LICENSES = {"vendor-proprietary", "patent-active", "trade-secret"}
_CLEAN_SOURCING = {"recycled", "conflict-free-attested"}


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text())


def _record_props(lex: dict) -> dict:
    defs = lex["defs"]["main"]
    return defs.get("record", defs)["properties"]


def _ontology_allowed(attr: str) -> list[str]:
    """Return the raw tokens of an attribute's :db/allowed vector."""
    text = _ONTOLOGY.read_text()
    m = re.search(re.escape(attr) + r"\s*\{.*?:db/allowed\s*\[(.*?)\]", text, re.S)
    assert m, f"could not locate {attr} :db/allowed in the ontology"
    return m.group(1).split()


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
# 1. G1 — ontology source-license open set
# ─────────────────────────────────────────────────────────────────────────


def test_g1_ontology_source_license_is_open_set():
    assert _ONTOLOGY.exists(), f"missing ontology: {_ONTOLOGY}"
    members = {t.lstrip(":") for t in _ontology_allowed(":iiiv.proc/source-license")}
    assert members == _EXPECTED_LICENSES, (
        f"G1: ontology source-license :db/allowed drifted; got {sorted(members)}"
    )
    for bad in _FORBIDDEN_LICENSES:
        assert bad not in members, (
            f"G1 VIOLATION: {bad!r} became a representable license — proprietary / "
            f"patent-active / trade-secret recipes must stay structurally excluded"
        )


# ─────────────────────────────────────────────────────────────────────────
# 2. G1 — lexicon sourceLicense enum matches the open set
# ─────────────────────────────────────────────────────────────────────────


def test_g1_lexicon_source_license_enum_matches():
    enum = set(_record_props(_load_json(_LEX / "processKnowledge.json"))["sourceLicense"]["enum"])
    assert enum == _EXPECTED_LICENSES, (
        f"G1: processKnowledge.sourceLicense enum drifted from the ontology set; got {sorted(enum)}"
    )
    for bad in _FORBIDDEN_LICENSES:
        assert bad not in enum, f"G1 VIOLATION: lexicon admits proprietary license {bad!r}"


# ─────────────────────────────────────────────────────────────────────────
# 3. G1 — the analyzer guard refuses non-open licenses
# ─────────────────────────────────────────────────────────────────────────


def test_g1_guard_rejects_proprietary_license():
    """G1: screen-licenses MUST raise on :vendor-proprietary; pass on the open set (via bb)."""
    # Verify ALLOWED-LICENSES set agrees with the expected open set
    result_lics = _bb(
        "(require '[hotaru.methods.analyze :as a])"
        "(pr (into #{} (map #(clojure.string/replace % #\"^:\" \"\") a/ALLOWED-LICENSES)))"
    )
    assert result_lics.returncode == 0, f"bb failed: {result_lics.stderr}"
    lics_str = result_lics.stdout.strip()
    for expected in _EXPECTED_LICENSES:
        assert expected in lics_str, (
            f"G1: ALLOWED-LICENSES missing {expected!r}; got {lics_str!r}"
        )
    for bad in _FORBIDDEN_LICENSES:
        assert bad not in lics_str, (
            f"G1 VIOLATION: {bad!r} found in ALLOWED-LICENSES; got {lics_str!r}"
        )

    # screen-licenses must throw on :vendor-proprietary
    result_bad = _bb(
        "(require '[hotaru.methods.analyze :as a])"
        "(def r (try (a/screen-licenses {\"p1\" {\":iiiv.proc/source-license\" \":vendor-proprietary\"}})"
        "            :no-throw (catch Exception e :threw)))"
        "(pr r)"
    )
    assert result_bad.returncode == 0, f"bb failed: {result_bad.stderr}"
    assert ":threw" in result_bad.stdout, (
        "G1: screen-licenses MUST throw on :vendor-proprietary "
        f"(proprietary recipes are structurally unrepresentable); stdout={result_bad.stdout!r}"
    )

    # the full open set passes
    open_procs = "{" + " ".join(
        f'"p{i}" {{":iiiv.proc/source-license" ":{lic}"}}'
        for i, lic in enumerate(_EXPECTED_LICENSES)
    ) + "}"
    result_ok = _bb(
        "(require '[hotaru.methods.analyze :as a])"
        f"(def r (a/screen-licenses {open_procs}))"
        "(pr (nil? r))"
    )
    assert result_ok.returncode == 0, f"bb failed: {result_ok.stderr}"
    assert "true" in result_ok.stdout, (
        f"G1: the full open-license set should pass screen-licenses; stdout={result_ok.stdout!r}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 4. G2 — ontology crystal + wafer fabricated :db/allowed is [false]
# ─────────────────────────────────────────────────────────────────────────


def test_g2_ontology_fabricated_allows_only_false():
    for attr in (":iiiv.crystal/fabricated", ":iiiv.wafer/fabricated"):
        toks = _ontology_allowed(attr)
        assert toks == ["false"], (
            f"G2: {attr} :db/allowed MUST be [false] (design/spec ONLY through R3); got {toks}"
        )
        assert "true" not in toks, f"G2 VIOLATION: {attr} admits a fabricated=true value"


# ─────────────────────────────────────────────────────────────────────────
# 5. G2 — lexicon fabricated const false + fabricationProhibited const true
# ─────────────────────────────────────────────────────────────────────────


def test_g2_lexicon_fabricated_and_prohibited_consts():
    for name in ("crystalGrowthDesign.json", "waferSpec.json"):
        props = _record_props(_load_json(_LEX / name))
        assert props["fabricated"].get("const") is False, (
            f"G2: {name} fabricated MUST be const false (no fabrication through R3)"
        )
    for name in ("commonsReadinessReport.json", "silenHotaruReview.json"):
        props = _record_props(_load_json(_LEX / name))
        assert props["fabricationProhibited"].get("const") is True, (
            f"G2: {name} fabricationProhibited MUST be const true"
        )


# ─────────────────────────────────────────────────────────────────────────
# 6. G2 — guard refuses fabricated crystal/wafer
# ─────────────────────────────────────────────────────────────────────────


def test_g2_guard_rejects_fabricated_crystal_and_wafer():
    """G2: screen-fabrication MUST raise on fabricated=true crystal or wafer (via bb)."""
    result = _bb(
        "(require '[hotaru.methods.analyze :as a])"
        # fabricated crystal: refuse
        "(def r1 (try (a/screen-fabrication {\"c1\" {\":iiiv.crystal/fabricated\" true}} {})"
        "             :no-throw (catch Exception e :threw)))"
        # fabricated wafer: refuse
        "(def r2 (try (a/screen-fabrication {} {\"w1\" {\":iiiv.wafer/fabricated\" true}})"
        "             :no-throw (catch Exception e :threw)))"
        # both false: passes
        "(def r3 (a/screen-fabrication {\"c1\" {\":iiiv.crystal/fabricated\" false}}"
        "                              {\"w1\" {\":iiiv.wafer/fabricated\" false}}))"
        "(pr {:r1 r1 :r2 r2 :r3-nil (nil? r3)})"
    )
    assert result.returncode == 0, f"bb failed: {result.stderr}"
    out = result.stdout
    assert ":r1 :threw" in out, (
        f"G2: screen-fabrication MUST throw on fabricated crystal (III-V fab prohibited); "
        f"stdout={out!r}"
    )
    assert ":r2 :threw" in out, (
        f"G2: screen-fabrication MUST throw on fabricated wafer (III-V fab prohibited); "
        f"stdout={out!r}"
    )
    assert ":r3-nil true" in out, (
        f"G2: screen-fabrication should pass when both crystal and wafer have fabricated=false; "
        f"stdout={out!r}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 7. G4 — conflict-mineral clean-sourcing set agrees (lexicon + guard)
# ─────────────────────────────────────────────────────────────────────────


def test_g4_in_sourcing_clean_set_agrees():
    enum = set(_record_props(_load_json(_LEX / "crystalGrowthDesign.json"))["inSourcing"]["enum"])
    assert enum == _CLEAN_SOURCING, (
        f"G4: crystalGrowthDesign.inSourcing enum MUST be the clean set "
        f"{sorted(_CLEAN_SOURCING)} (the lexicon excludes :unverified); got {sorted(enum)}"
    )

    # Verify CLEAN-SOURCING in cljc matches the expected set
    result_sourcing = _bb(
        "(require '[hotaru.methods.analyze :as a])"
        "(pr (into #{} (map #(clojure.string/replace % #\"^:\" \"\") a/CLEAN-SOURCING)))"
    )
    assert result_sourcing.returncode == 0, f"bb failed: {result_sourcing.stderr}"
    sourcing_str = result_sourcing.stdout.strip()
    for expected in _CLEAN_SOURCING:
        assert expected in sourcing_str, (
            f"G4: CLEAN-SOURCING missing {expected!r}; got {sourcing_str!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 8. G3 — non-adjudicating: Council Lv7+ decides the gate, hotaru reports
# ─────────────────────────────────────────────────────────────────────────


def test_g3_review_is_council_lv7_non_adjudicating():
    props = _record_props(_load_json(_LEX / "silenHotaruReview.json"))
    assert props["councilLevel"].get("const") == "Lv7+", (
        "G3: silenHotaruReview.councilLevel MUST be const 'Lv7+' — hotaru is "
        "NON-adjudicating on the fabrication gate; Council Lv7+ decides "
        "(Lv7+, not Lv6+, because III-V is gated through R3)"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
