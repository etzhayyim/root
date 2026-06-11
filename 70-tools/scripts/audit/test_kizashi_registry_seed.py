"""Fail-closed invariants for the kizashi (兆) modality-capability HONESTY registry.

Pins the constitutional properties of the non-invasive body-scan / sign-sensing
modality ledger (`registry/modalities.seed.json`, per ADR-2605312700 §2.F + G10).
This suite is R0-safe: test-only, deterministic, network-free — it never
imports/executes a cell and never drives any sensing hardware. It fails fast
(fail-closed) if any constitutional invariant drifts.

kizashi is the L4-Care *instrument* layer, UPSTREAM of clinical adjudication
(kizashi senses → mitate diagnoses → iyashi treats). The registry is the
HONESTY floor: each entry binds a sensing modality to its evidenceGrade +
regulatoryClass + an explicit canDetect / cannotDetect map. The signature
invariant is G10 anti-pseudoscience — `X-excluded-pseudoscience` entries are
recorded ONLY to document exclusion and may NEVER detect anything.

Sibling of `test_kokoro_registry_seed.py` (SAFETY-CRITICAL crisis-line floor).
Where that suite enforces the NON-CLINICAL support-routing boundary, THIS
suite enforces kizashi's structural constitutional invariants on the registry
data itself:

  G3  non-diagnostic   — no `canDetect` capability may claim a diagnosis.
  G4  device boundary  — R0..R2 may run ONLY non-regulated-wellness +
                          non-ionizing modalities; regulated / ionizing
                          modalities MUST be phaseGate R3.
  G7  所見≠原因         — every entry MUST declare what it cannotDetect.
  G10 anti-pseudoscience — X-excluded entries detect NOTHING and are
                          EXCLUDED (can never emit a modalityObservation).
  G14 unverified-seed  — every entry ships verificationStatus=unverified-seed
                          (evidence grade / regulatory class / phase gate MUST
                          be Council-verified before any R1+ emission).

Invariants under test:

  1. file parses as JSON and exposes a non-empty `modalities` list.
  2. every entry has a UNIQUE `modalityId` (no duplicates) — fail-closed.
  3. G14 — every entry ships verificationStatus == "unverified-seed".
  4. every entry has a non-empty `provenance` + ISO-8601 Zulu `lastVerified`
     + a non-empty `councilAttestationCid`.
  5. evidenceGrade / regulatoryClass / phaseGate are each from the allowed set;
     `ionizing` is a real bool.
  6. G7 — every entry declares a non-empty `cannotDetect` list.
  7. G10 — X-excluded entries: empty canDetect + EXCLUDED attestation +
     `EXCLUDED-` id prefix; and the prefix <-> X-grade binding is exact.
  8. G3 — no `canDetect` capability string claims a diagnosis; every
     non-excluded entry has a non-empty canDetect.
  9. G4 — phaseGate R2 ⇒ non-regulated-wellness + non-ionizing; and
     regulated/samd/ionizing OR ionizing=true ⇒ phaseGate R3.
 10. a top-level positive integer `freshnessWindowDays` is present.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_SEED = _REPO / "20-actors" / "kizashi" / "registry" / "modalities.seed.json"

# ISO-8601 Zulu timestamp, e.g. 2026-05-31T00:00:00Z
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")

_ALLOWED_EVIDENCE_GRADES = {
    "A-validated-clinical",
    "B-emerging-peer-reviewed",
    "C-screening-only",
    "X-excluded-pseudoscience",
}

_ALLOWED_REGULATORY_CLASSES = {
    "non-regulated-wellness",
    "regulated-medical-device",
    "samd-software",
    "ionizing-licensed-facility-only",
}

# The _comment caps R0..R2 emission at these phase gates; R3 is the gated tier.
_ALLOWED_PHASE_GATES = {"R1", "R2", "R3"}

# G4: anything NOT in this set is a regulated/gated class that may only run R3.
_UNGATED_REGULATORY_CLASS = "non-regulated-wellness"

_EXCLUDED_GRADE = "X-excluded-pseudoscience"
_EXCLUDED_PREFIX = "EXCLUDED-"


def _load() -> dict:
    return json.loads(_SEED.read_text())


# ─────────────────────────────────────────────────────────────────────────
# 1. parses + non-empty modalities list
# ─────────────────────────────────────────────────────────────────────────


def test_registry_parses_and_has_modalities():
    assert _SEED.exists(), f"missing seed registry: {_SEED}"
    seed = _load()
    assert isinstance(seed, dict), "top-level must be a JSON object"
    mods = seed.get("modalities")
    assert isinstance(mods, list), "`modalities` MUST be a list"
    assert len(mods) > 0, "`modalities` MUST be non-empty"


# ─────────────────────────────────────────────────────────────────────────
# 2. unique modalityId (fail-closed on duplicates)
# ─────────────────────────────────────────────────────────────────────────


def test_modality_ids_unique():
    mods = _load()["modalities"]
    ids = [m.get("modalityId") for m in mods]
    assert all(ids), "every entry MUST have a non-empty modalityId"
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate modalityId(s) — fail-closed: {dupes}"
    assert len(set(ids)) == len(ids)


# ─────────────────────────────────────────────────────────────────────────
# 3. G14 — every entry is unverified-seed
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_is_unverified_seed():
    mods = _load()["modalities"]
    for m in mods:
        assert m.get("verificationStatus") == "unverified-seed", (
            f"G14: {m.get('modalityId')} MUST ship "
            f"verificationStatus=unverified-seed — evidence grade / regulatory "
            f"class / phase gate must be Council-verified before any R1+ "
            f"emission; got {m.get('verificationStatus')!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 4. provenance + lastVerified + councilAttestationCid
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_has_provenance_timestamp_and_attestation():
    mods = _load()["modalities"]
    for m in mods:
        mid = m.get("modalityId")
        prov = (m.get("provenance") or "").strip()
        assert prov, f"{mid}: MUST cite a non-empty provenance/source"
        lv = m.get("lastVerified") or ""
        assert lv, f"{mid}: MUST carry a lastVerified timestamp"
        assert _TS_RE.match(lv), (
            f"{mid}: lastVerified MUST be ISO-8601 Zulu; got {lv!r}"
        )
        cid = (m.get("councilAttestationCid") or "").strip()
        assert cid, (
            f"{mid}: MUST carry a councilAttestationCid (PENDING/EXCLUDED/CID)"
        )


# ─────────────────────────────────────────────────────────────────────────
# 5. evidenceGrade / regulatoryClass / phaseGate / ionizing well-formed
# ─────────────────────────────────────────────────────────────────────────


def test_grade_class_phase_and_ionizing_well_formed():
    mods = _load()["modalities"]
    for m in mods:
        mid = m.get("modalityId")
        grade = m.get("evidenceGrade")
        assert grade in _ALLOWED_EVIDENCE_GRADES, (
            f"{mid}: evidenceGrade {grade!r} not in {sorted(_ALLOWED_EVIDENCE_GRADES)}"
        )
        cls = m.get("regulatoryClass")
        assert cls in _ALLOWED_REGULATORY_CLASSES, (
            f"{mid}: regulatoryClass {cls!r} not in {sorted(_ALLOWED_REGULATORY_CLASSES)}"
        )
        phase = m.get("phaseGate")
        assert phase in _ALLOWED_PHASE_GATES, (
            f"{mid}: phaseGate {phase!r} not in {sorted(_ALLOWED_PHASE_GATES)}"
        )
        ion = m.get("ionizing")
        assert isinstance(ion, bool), (
            f"{mid}: ionizing MUST be a JSON bool; got {ion!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 6. G7 — every entry declares what it cannotDetect (所見≠原因)
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_declares_cannot_detect():
    mods = _load()["modalities"]
    for m in mods:
        mid = m.get("modalityId")
        cannot = m.get("cannotDetect")
        assert isinstance(cannot, list) and len(cannot) > 0, (
            f"G7: {mid} MUST declare a non-empty cannotDetect list "
            f"(所見≠原因 — every modality states its limits); got {cannot!r}"
        )
        assert all(isinstance(x, str) and x.strip() for x in cannot), (
            f"{mid}: every cannotDetect item MUST be a non-empty string"
        )


# ─────────────────────────────────────────────────────────────────────────
# 7. G10 — anti-pseudoscience structural exclusion (the signature invariant)
# ─────────────────────────────────────────────────────────────────────────


def test_g10_excluded_entries_detect_nothing_and_are_excluded():
    mods = _load()["modalities"]
    for m in mods:
        mid = m.get("modalityId") or ""
        grade = m.get("evidenceGrade")
        is_x = grade == _EXCLUDED_GRADE
        is_prefixed = mid.startswith(_EXCLUDED_PREFIX)
        # The X-grade <-> EXCLUDED- prefix binding is exact (both ways).
        assert is_x == is_prefixed, (
            f"G10: {mid!r} — evidenceGrade==X and the 'EXCLUDED-' id prefix "
            f"MUST agree (X={is_x}, prefixed={is_prefixed})"
        )
        if is_x:
            can = m.get("canDetect")
            assert can == [], (
                f"G10: excluded {mid} MUST have an EMPTY canDetect — a "
                f"pseudoscience modality may NEVER detect anything; got {can!r}"
            )
            assert m.get("councilAttestationCid") == "EXCLUDED", (
                f"G10: excluded {mid} MUST carry councilAttestationCid=EXCLUDED"
            )


# ─────────────────────────────────────────────────────────────────────────
# 8. G3 — no canDetect claims a diagnosis; non-excluded entries detect ≥1 thing
# ─────────────────────────────────────────────────────────────────────────


def test_g3_no_can_detect_claims_a_diagnosis():
    mods = _load()["modalities"]
    for m in mods:
        mid = m.get("modalityId")
        can = m.get("canDetect")
        assert isinstance(can, list), f"{mid}: canDetect MUST be a list"
        for cap in can:
            assert isinstance(cap, str) and cap.strip(), (
                f"{mid}: every canDetect item MUST be a non-empty string"
            )
            low = cap.lower()
            assert "diagnos" not in low, (
                f"G3: {mid} canDetect {cap!r} claims a DIAGNOSIS — kizashi is "
                f"NON-diagnostic (医師法 §17): it senses signs, never diagnoses"
            )
        if m.get("evidenceGrade") != _EXCLUDED_GRADE:
            assert len(can) > 0, (
                f"{mid}: a non-excluded modality MUST detect ≥1 capability"
            )


# ─────────────────────────────────────────────────────────────────────────
# 9. G4 — medical-device / ionizing phase-gate boundary
# ─────────────────────────────────────────────────────────────────────────


def test_g4_phase_gate_boundary():
    mods = _load()["modalities"]
    for m in mods:
        mid = m.get("modalityId")
        phase = m.get("phaseGate")
        cls = m.get("regulatoryClass")
        ion = m.get("ionizing")
        # Forward: any regulated/gated class or ionizing modality is R3-only.
        if cls != _UNGATED_REGULATORY_CLASS or ion is True:
            assert phase == "R3", (
                f"G4: {mid} is regulated/ionizing (class={cls}, ionizing={ion}) "
                f"→ phaseGate MUST be R3; got {phase!r}"
            )
        # Inverse: an R2 (R0..R2-eligible) modality MUST be ungated + non-ionizing.
        if phase == "R2":
            assert cls == _UNGATED_REGULATORY_CLASS and ion is False, (
                f"G4: {mid} runs at phaseGate R2 → MUST be "
                f"non-regulated-wellness + non-ionizing (class={cls}, "
                f"ionizing={ion})"
            )


# ─────────────────────────────────────────────────────────────────────────
# 10. top-level positive integer freshnessWindowDays
# ─────────────────────────────────────────────────────────────────────────


def test_freshness_window_days_present_integer():
    seed = _load()
    fw = seed.get("freshnessWindowDays")
    assert isinstance(fw, int) and not isinstance(fw, bool), (
        f"freshnessWindowDays MUST be a top-level integer; got {fw!r}"
    )
    assert fw > 0, f"freshnessWindowDays MUST be positive; got {fw}"


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-v"]))
