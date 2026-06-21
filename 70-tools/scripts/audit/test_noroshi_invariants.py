"""Lock-in tests for the noroshi (烽) constitutional invariants.

Pins the structural properties designed in ADR-2606051600 (noroshi — 光電融合
photonics-electronics convergence comms chip + ISAC + photonic packaging
robotics; civilian by construction) so a future refactor cannot silently weaken a
constitutional invariant. 烽 = the watchtower beacon-fire: one emission, two
functions = ISAC. noroshi's invariants are load-bearing and each is declared in
the ontology schema + lexicon enum/const + a methods guard. This suite proves
they agree:

  N1/G3 — WEAPONISATION UNREPRESENTABLE: the ontology force-classes are civilian
      only; there is no :weaponizable value; the laser guard refuses any
      directed-energy / fire-control / dazzle use.
  N2/G4 — OBJECT-NOT-PERSON: ISAC senses :object only; :person is structurally
      absent (the watari person-tracking invariant, here in the sensing vocab).
  N5/G1 — CLEAN-ROOM OPEN-EDA: a photonic device is :open-pdk + an open-EDA tool
      (GDSFactory/Meep/KLayout/OpenLane); NDA foundry PDKs / Cadence/Synopsys/
      Lumerical/Ansys are not representable.
  G5/IEC-60825 — soft laser-safety interlock: a hazardous-class laser cannot be
      energised without a physical enclosure interlock + operator attestation.
  G7 — no-server-key + dry-run packaging.

Invariants under test:

  1. N1 (ontology) — force-classes are the 3 civilian classes; :weaponizable absent.
  2. N1 (lexicon) — photonicDevice.forceClass const civilian-comms; isacWaveform
     .civilian const true.
  3. N1 (guard) — permitted-uses carries no weapon term; enable-laser refuses
     each forbidden-use and passes a civilian Class-1 alignment laser.
  4. N2 (ontology + lexicon) — target-classes is [:object]; :person absent;
     senseEstimate.targetClass const object.
  5. G1 (lexicon) — photonicDevice.process const open-pdk; eda enum ⊆ the open
     set; no proprietary EDA member.
  6. IEC-60825 (guard) — a hazardous-class laser raises without an enclosure
     interlock, and again without a safety attestation; passes with both.
  7. G7 (lexicon) — packagingJob.serverHeldKey const false + dryRun const true.

NOTE: enforcement points 3 and 6 now exercise the cljc port
(methods/active_alignment.cljc via bb subprocess) since the Python
methods/active_alignment.py was migrated to cljc.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_ONTOLOGY = _REPO / "00-contracts" / "schemas" / "photonic-convergence-ontology.kotoba.edn"
_LEX = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "noroshi"
_ACTORS = _REPO / "20-actors"

_EXPECTED_FORCE = {"civilian-comms", "civilian-sensing", "fab-process-laser"}
_OPEN_EDA = {"gdsfactory", "meep", "klayout", "openlane"}
_PROPRIETARY_EDA = {"cadence", "synopsys", "lumerical", "ansys"}


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text())


def _record_props(lex: dict) -> dict:
    defs = lex["defs"]["main"]
    return defs.get("record", defs)["properties"]


def _ontology_vector(attr: str) -> set[str]:
    text = _ONTOLOGY.read_text()
    m = re.search(re.escape(attr) + r"\s*\[(.*?)\]", text, re.S)
    assert m, f"could not locate {attr} vector in the ontology"
    return {t.lstrip(":") for t in re.findall(r":[a-z0-9-]+", m.group(1))}


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
# 1 + 2 + 3. N1 — weaponisation unrepresentable / civilian by construction
# ─────────────────────────────────────────────────────────────────────────


def test_n1_ontology_force_classes_are_civilian_only():
    assert _ONTOLOGY.exists(), f"missing ontology: {_ONTOLOGY}"
    fc = _ontology_vector(":ontology/force-classes")
    assert fc == _EXPECTED_FORCE, f"N1: force-classes drifted; got {sorted(fc)}"
    assert "weaponizable" not in fc, (
        "N1 VIOLATION: :weaponizable became a representable force class"
    )


def test_n1_lexicon_force_class_and_civilian_consts():
    pd = _record_props(_load_json(_LEX / "photonicDevice.json"))
    assert pd["forceClass"].get("const") == "civilian-comms", (
        "N1: photonicDevice.forceClass MUST be const 'civilian-comms'"
    )
    wave = _record_props(_load_json(_LEX / "isacWaveform.json"))
    assert wave["civilian"].get("const") is True, (
        "N1: isacWaveform.civilian MUST be const true"
    )


def test_n1_guard_refuses_weaponised_use():
    """N1: permitted-uses MUST have no weapon term; enable-laser MUST refuse all forbidden-uses (via bb)."""
    # Check permitted-uses has no weapon terms
    result_permitted = _bb(
        "(require '[noroshi.methods.active-alignment :as aa])"
        "(def weapon-terms #{\"weapon\" \"directed-energy\" \"dazzle\" \"fire-control\"})"
        "(def intersection (clojure.set/intersection (set aa/permitted-uses) weapon-terms))"
        "(pr {:permitted aa/permitted-uses :intersection intersection :forbidden aa/forbidden-uses})"
    )
    assert result_permitted.returncode == 0, f"bb failed: {result_permitted.stderr}"
    out = result_permitted.stdout
    assert ":intersection #{}" in out, (
        f"N1: permitted-uses must contain no weapon term; stdout={out!r}"
    )

    # Check that each forbidden-use raises
    result_forbidden = _bb(
        "(require '[noroshi.methods.active-alignment :as aa])"
        "(def results (mapv (fn [bad]"
        "                     (try (aa/enable-laser (aa/laser-spec :use bad))"
        "                          :no-throw"
        "                          (catch Exception e :threw)))"
        "                   aa/forbidden-uses))"
        "(pr {:all-threw (every? #{:threw} results) :results results})"
    )
    assert result_forbidden.returncode == 0, f"bb failed: {result_forbidden.stderr}"
    assert ":all-threw true" in result_forbidden.stdout, (
        "N1: enable-laser MUST throw (LaserSafetyError) for all forbidden-uses "
        f"(directed-energy/weapon/dazzle/fire-control); stdout={result_forbidden.stdout!r}"
    )

    # A civilian Class-1 alignment laser passes (returns nil, no exception)
    result_clean = _bb(
        "(require '[noroshi.methods.active-alignment :as aa])"
        "(def r (aa/enable-laser (aa/laser-spec :laser-class \"1\" :use \"alignment\")))"
        "(pr (nil? r))"
    )
    assert result_clean.returncode == 0, f"bb failed: {result_clean.stderr}"
    assert "true" in result_clean.stdout, (
        f"N1: a civilian Class-1 alignment laser MUST energise (return nil); "
        f"stdout={result_clean.stdout!r}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 4. N2 — ISAC senses objects, never persons
# ─────────────────────────────────────────────────────────────────────────


def test_n2_target_class_is_object_not_person():
    tc = _ontology_vector(":ontology/target-classes")
    assert tc == {"object"}, f"N2: target-classes MUST be [:object]; got {sorted(tc)}"
    assert "person" not in tc, "N2 VIOLATION: :person became a representable target class"
    se = _record_props(_load_json(_LEX / "senseEstimate.json"))
    assert se["targetClass"].get("const") == "object", (
        "N2: senseEstimate.targetClass MUST be const 'object' (no person tracking)"
    )


# ─────────────────────────────────────────────────────────────────────────
# 5. G1 — clean-room open-EDA only
# ─────────────────────────────────────────────────────────────────────────


def test_g1_clean_room_open_eda_only():
    pd = _record_props(_load_json(_LEX / "photonicDevice.json"))
    assert pd["process"].get("const") == "open-pdk", (
        "G1: photonicDevice.process MUST be const 'open-pdk' (never an NDA foundry PDK)"
    )
    eda = set(pd["eda"]["enum"])
    assert eda <= _OPEN_EDA, f"G1: eda enum admits a non-open tool; got {sorted(eda)}"
    assert not (eda & _PROPRIETARY_EDA), (
        f"G1 VIOLATION: proprietary EDA in the enum; got {sorted(eda & _PROPRIETARY_EDA)}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 6. IEC 60825 — hazardous-class laser interlock + attestation gate
# ─────────────────────────────────────────────────────────────────────────


def test_iec60825_hazardous_laser_requires_interlock_and_attestation():
    """IEC 60825: hazardous laser MUST require interlock AND attestation (via bb)."""
    result = _bb(
        "(require '[noroshi.methods.active-alignment :as aa])"
        # hazardous class, no interlock: refuse
        "(def r1 (try (aa/enable-laser (aa/laser-spec :laser-class \"4\" :use \"alignment\""
        "                                             :enclosure-interlock false))"
        "             :no-throw (catch Exception e :threw)))"
        # hazardous class, interlock but no attestation: refuse
        "(def r2 (try (aa/enable-laser (aa/laser-spec :laser-class \"4\" :use \"alignment\""
        "                                             :enclosure-interlock true"
        "                                             :safety-attestation-ref \"\"))"
        "             :no-throw (catch Exception e :threw)))"
        # hazardous class, interlock + valid attestation: energises (returns nil)
        "(def r3 (aa/enable-laser (aa/laser-spec :laser-class \"4\" :use \"alignment\""
        "                                        :enclosure-interlock true"
        "                                        :safety-attestation-ref \"attest:noroshi-lsm-001\")))"
        "(pr {:r1 r1 :r2 r2 :r3-nil (nil? r3)})"
    )
    assert result.returncode == 0, f"bb failed: {result.stderr}"
    out = result.stdout
    assert ":r1 :threw" in out, (
        f"IEC 60825: a Class-4 laser WITHOUT interlock MUST be refused; stdout={out!r}"
    )
    assert ":r2 :threw" in out, (
        f"IEC 60825: a Class-4 laser WITHOUT attestation MUST be refused; stdout={out!r}"
    )
    assert ":r3-nil true" in out, (
        f"IEC 60825: a Class-4 laser WITH interlock + attestation MUST energise; stdout={out!r}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 7. G7 — packaging is no-server-key + dry-run
# ─────────────────────────────────────────────────────────────────────────


def test_g7_packaging_no_server_key_and_dry_run():
    pkg = _record_props(_load_json(_LEX / "packagingJob.json"))
    assert pkg["serverHeldKey"].get("const") is False, (
        "G7: packagingJob.serverHeldKey MUST be const false (no-server-key)"
    )
    assert pkg["dryRun"].get("const") is True, (
        "G7: packagingJob.dryRun MUST be const true (R0 — live actuation gated)"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
