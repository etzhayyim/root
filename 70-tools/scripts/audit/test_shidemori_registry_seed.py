"""Fail-closed invariants for the shidemori (死出守) WORLDWIDE death-registration seed.

Pins the constitutional properties of the multi-jurisdiction death-registration
seed registry (`20-actors/shidemori/registry/registries.seed.json`, per
ADR-2605263800). This suite is R0-safe: test-only, deterministic, network-free —
it never imports/executes a cell and never touches a live channel. It fails fast
(fail-closed) if any constitutional invariant drifts.

shidemori is a *community memorial substrate* and an *informational directory of
OFFICIAL death-registration/civil-registry authorities* for bereavement
wayfinding. It is NOT a state-licensed mortuary, NOT a commercial funeral/cemetery
business, and NOT a legal-advice service (the non-mortuary / non-commercial
boundary, G14 + ADR-2605263800). The most safety-critical datum in each entry is
the statutory registration DEADLINE — a wrong deadline is directly harmful to the
bereaved — so the registry ships every entry as `unverified-seed` until a human
re-verifies the deadline against the cited law (see registry/VERIFICATION.md).

Invariants under test:

  1. file parses as JSON and exposes a non-empty `registries` list.
  2. every entry has a UNIQUE `registryId` (no duplicates) — fail-closed.
  3. EVERY entry ships verificationStatus == "unverified-seed" (G14 — no entry
     may be pre-marked verified in the seed; a verified death-registration
     deadline requires the human checklist).
  4. every entry has a non-empty accessUrl + provenance + lastVerified.
  5. every entry has a `jurisdiction`, and the registry spans MULTIPLE
     jurisdictions (>= 12 distinct) — proves worldwide coverage.
  6. every entry's `recordKind` is one of the five known death-registration kinds.
  7. every entry's `notes` is non-empty AND references shidemori's NON-mortuary /
     non-commercial bereavement-wayfinding boundary.
  8. a top-level integer `freshnessWindowDays` is present.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_SEED = _REPO / "20-actors" / "shidemori" / "registry" / "registries.seed.json"

# ISO-8601 Zulu timestamp, e.g. 2026-06-02T00:00:00Z
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")

# The five death-registration record kinds. shidemori MUST NOT invent a kind
# outside this closed set (guards against scope-creep into mortuary/commercial
# record kinds — the non-mortuary boundary, G14).
_RECORD_KINDS = {
    "death-registration-authority",
    "death-certificate-issuer",
    "burial-cremation-permit",
    "civil-registry-office",
    "intl-guidance",
}


def _load() -> dict:
    return json.loads(_SEED.read_text())


# ─────────────────────────────────────────────────────────────────────────
# 1. parses + non-empty registries list
# ─────────────────────────────────────────────────────────────────────────


def test_registry_parses_and_has_registries():
    assert _SEED.exists(), f"missing seed registry: {_SEED}"
    seed = _load()
    assert isinstance(seed, dict), "top-level must be a JSON object"
    regs = seed.get("registries")
    assert isinstance(regs, list), "`registries` MUST be a list"
    assert len(regs) > 0, "`registries` MUST be non-empty"


# ─────────────────────────────────────────────────────────────────────────
# 2. unique registryId (fail-closed on duplicates)
# ─────────────────────────────────────────────────────────────────────────


def test_registry_ids_unique():
    regs = _load()["registries"]
    ids = [r.get("registryId") for r in regs]
    assert all(ids), "every entry MUST have a non-empty registryId"
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate registryId(s) — fail-closed: {dupes}"
    assert len(set(ids)) == len(ids)


# ─────────────────────────────────────────────────────────────────────────
# 3. G14 — every entry is unverified-seed
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_is_unverified_seed():
    regs = _load()["registries"]
    for r in regs:
        assert r.get("verificationStatus") == "unverified-seed", (
            f"G14: {r.get('registryId')} MUST ship verificationStatus="
            f"unverified-seed (no entry may be pre-marked verified — a verified "
            f"death-registration deadline requires the human re-verification "
            f"checklist); got {r.get('verificationStatus')!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 4. accessUrl + provenance + lastVerified present
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_has_access_provenance_last_verified():
    regs = _load()["registries"]
    for r in regs:
        rid = r.get("registryId")

        access = (r.get("accessUrl") or "").strip()
        assert access, f"{rid}: MUST carry a non-empty accessUrl"
        assert access.startswith("http://") or access.startswith("https://"), (
            f"{rid}: accessUrl MUST be an http(s) URL; got {access!r}"
        )

        # provenance MUST be a non-empty official-source URL. Most are https,
        # but a handful of genuine official sources are served over http only
        # (e.g. some national civil-affairs portals) — these are real official
        # sources, not aggregators, so we require an http(s) URL rather than
        # forcing https (do not mask real data).
        prov = (r.get("provenance") or "").strip()
        assert prov, f"{rid}: MUST cite a non-empty provenance/source URL"
        assert prov.startswith("http://") or prov.startswith("https://"), (
            f"{rid}: provenance MUST be an http(s) URL; got {prov!r}"
        )

        lv = (r.get("lastVerified") or "").strip()
        assert lv, f"{rid}: MUST carry a lastVerified timestamp"
        assert _TS_RE.match(lv), (
            f"{rid}: lastVerified MUST be ISO-8601 Zulu; got {lv!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 5. worldwide coverage — >= 12 distinct jurisdictions
# ─────────────────────────────────────────────────────────────────────────


def test_registry_spans_multiple_jurisdictions():
    regs = _load()["registries"]
    for r in regs:
        assert r.get("jurisdiction"), (
            f"{r.get('registryId')}: MUST declare a jurisdiction"
        )
    jurisdictions = {r["jurisdiction"] for r in regs}
    assert len(jurisdictions) >= 12, (
        "WORLDWIDE coverage invariant: registry MUST span >= 12 distinct "
        f"jurisdictions (guards against regression to a single-country list); "
        f"got {sorted(jurisdictions)}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 6. recordKind in the closed set
# ─────────────────────────────────────────────────────────────────────────


def test_every_record_kind_known():
    regs = _load()["registries"]
    for r in regs:
        kind = r.get("recordKind")
        assert kind in _RECORD_KINDS, (
            f"{r.get('registryId')}: recordKind {kind!r} not in the closed "
            f"death-registration kind set {sorted(_RECORD_KINDS)} (guards the "
            f"non-mortuary scope boundary)"
        )


# ─────────────────────────────────────────────────────────────────────────
# 7. notes non-empty AND reference the non-mortuary / non-commercial boundary
# ─────────────────────────────────────────────────────────────────────────


def test_notes_present_and_reference_boundary():
    regs = _load()["registries"]
    for r in regs:
        rid = r.get("registryId")
        notes = (r.get("notes") or "")
        assert notes.strip(), (
            f"{rid}: notes MUST be non-empty (carries the per-entry boundary "
            "caveat)"
        )
        low = notes.lower()
        # The NON-mortuary boundary: shidemori is not a state-licensed mortuary.
        assert "mortuary" in low, (
            f"{rid}: notes MUST reference shidemori's NON-mortuary boundary "
            "(it is an informational directory, not a state-licensed mortuary)"
        )
        # The non-commercial boundary: not a commercial funeral/cemetery business.
        assert "commercial" in low, (
            f"{rid}: notes MUST reference shidemori's non-commercial boundary "
            "(not a commercial funeral/cemetery business)"
        )


# ─────────────────────────────────────────────────────────────────────────
# 8. top-level integer freshnessWindowDays
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
