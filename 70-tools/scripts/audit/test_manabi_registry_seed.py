"""Fail-closed invariants for the manabi (学び) WORLDWIDE open-education seed.

Pins the constitutional properties of the multi-jurisdiction open-education
resource directory (`registry/resources.seed.json`, per ADR-2605261045). This
suite is R0-safe: test-only, deterministic, network-free — it never imports/
executes a cell and never touches a live resource. It fails fast (fail-closed)
if any constitutional invariant drifts.

Sibling-in-idiom of `test_toritsugi_registry_seed.py`. Where that suite pins a
government-procedure registry, THIS suite pins the open-education RESOURCE
directory: a directory that ROUTES learners to free/open learning resources and
NEVER credentials, accredits, grades, or ranks (ANTI-CREDENTIALISM, G7 +
Charter §2(e)).

Invariants under test:

  1. file parses as JSON and exposes a non-empty `resources` list.
  2. every entry has a UNIQUE `resourceId` (no duplicates) — fail-closed.
  3. EVERY entry ships verificationStatus == "unverified-seed" (G14 — no entry
     may be pre-marked verified in the seed).
  4. every entry has a non-empty accessUrl + a non-empty https provenance URL +
     a lastVerified ISO-8601 Zulu stamp.
  5. every entry has a `jurisdiction`, and the registry spans MULTIPLE
     jurisdictions (>= 12 distinct) — proves worldwide coverage / guards against
     regression to a single-country directory.
  6. every entry's `resourceKind` is in the allowed open-education vocabulary.
  7. ANTI-CREDENTIALISM boundary caveat is present: every entry's `notes` is
     non-empty AND references manabi's anti-credentialism / open-resource
     routing boundary; the registry as a whole references the boundary regime.
  8. a top-level integer `freshnessWindowDays` is present.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_SEED = _REPO / "20-actors" / "manabi" / "registry" / "resources.seed.json"

# ISO-8601 Zulu timestamp, e.g. 2026-06-02T00:00:00Z
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")

# Allowed open-education resource taxonomy (closed vocabulary, fail-closed).
_ALLOWED_KINDS = {
    "oer-repository",
    "open-courseware",
    "public-digital-library",
    "open-textbook",
    "gov-open-learning-portal",
    "global-oer",
}


def _load() -> dict:
    return json.loads(_SEED.read_text())


# ─────────────────────────────────────────────────────────────────────────
# 1. parses + non-empty resources list
# ─────────────────────────────────────────────────────────────────────────


def test_registry_parses_and_has_resources():
    assert _SEED.exists(), f"missing seed registry: {_SEED}"
    seed = _load()
    assert isinstance(seed, dict), "top-level must be a JSON object"
    resources = seed.get("resources")
    assert isinstance(resources, list), "`resources` MUST be a list"
    assert len(resources) > 0, "`resources` MUST be non-empty"


# ─────────────────────────────────────────────────────────────────────────
# 2. unique resourceId (fail-closed on duplicates)
# ─────────────────────────────────────────────────────────────────────────


def test_resource_ids_unique():
    resources = _load()["resources"]
    ids = [r.get("resourceId") for r in resources]
    assert all(ids), "every entry MUST have a non-empty resourceId"
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate resourceId(s) — fail-closed: {dupes}"
    assert len(set(ids)) == len(ids)


# ─────────────────────────────────────────────────────────────────────────
# 3. G14 — every entry is unverified-seed
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_is_unverified_seed():
    resources = _load()["resources"]
    for r in resources:
        assert r.get("verificationStatus") == "unverified-seed", (
            f"G14: {r.get('resourceId')} MUST ship verificationStatus="
            f"unverified-seed (no entry may be pre-marked verified); got "
            f"{r.get('verificationStatus')!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 4. accessUrl + provenance https URL + lastVerified timestamp
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_has_access_provenance_and_last_verified():
    resources = _load()["resources"]
    for r in resources:
        rid = r.get("resourceId")

        access = r.get("accessUrl") or ""
        assert access.strip(), f"{rid}: MUST carry a non-empty accessUrl"
        assert access.startswith(("https://", "http://")), (
            f"{rid}: accessUrl MUST be an http(s) URL; got {access!r}"
        )

        prov = r.get("provenance") or ""
        assert prov.strip(), f"{rid}: MUST cite a non-empty provenance/source URL"
        assert prov.startswith("https://"), (
            f"{rid}: provenance MUST be an https URL; got {prov!r}"
        )

        lv = r.get("lastVerified") or ""
        assert lv, f"{rid}: MUST carry a lastVerified timestamp"
        assert _TS_RE.match(lv), (
            f"{rid}: lastVerified MUST be ISO-8601 Zulu; got {lv!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 5. worldwide coverage — >= 12 distinct jurisdictions
# ─────────────────────────────────────────────────────────────────────────


def test_registry_spans_multiple_jurisdictions():
    resources = _load()["resources"]
    for r in resources:
        assert r.get("jurisdiction"), (
            f"{r.get('resourceId')}: MUST declare a jurisdiction"
        )
    jurisdictions = {r["jurisdiction"] for r in resources}
    assert len(jurisdictions) >= 12, (
        "WORLDWIDE coverage invariant: registry MUST span >= 12 distinct "
        "jurisdictions (guards against regression to a single-country "
        f"directory); got {sorted(jurisdictions)}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 6. resourceKind is in the allowed open-education vocabulary
# ─────────────────────────────────────────────────────────────────────────


def test_every_resource_kind_in_allowed_vocabulary():
    resources = _load()["resources"]
    for r in resources:
        kind = r.get("resourceKind")
        assert kind in _ALLOWED_KINDS, (
            f"{r.get('resourceId')}: resourceKind {kind!r} not in allowed "
            f"open-education vocabulary {sorted(_ALLOWED_KINDS)}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 7. ANTI-CREDENTIALISM / open-resource boundary caveat present
# ─────────────────────────────────────────────────────────────────────────


def test_anti_credentialism_boundary_caveat_present():
    seed = _load()
    resources = seed["resources"]
    for r in resources:
        rid = r.get("resourceId")
        notes = r.get("notes") or ""
        assert notes.strip(), (
            f"{rid}: notes MUST be non-empty (carries the per-entry boundary "
            "caveat)"
        )
        low = notes.lower()
        # anti-credentialism boundary token
        assert ("anti-credentialism" in low) or ("credential" in low), (
            f"{rid}: notes MUST reference manabi's ANTI-CREDENTIALISM boundary "
            "(it issues no degrees/transcripts/GPA, only skillAttestation)"
        )
        # open-resource routing boundary token
        assert ("route" in low) or ("open-education resource" in low) or (
            "free/open" in low
        ), (
            f"{rid}: notes MUST reference the open-resource ROUTING boundary "
            "(manabi routes learners to free/open resources; it is not a "
            "school/university and does not accredit/grade/rank)"
        )

    # Registry-as-a-whole references the boundary regime.
    blob = _SEED.read_text()
    assert "ANTI-CREDENTIALISM" in blob, (
        "registry MUST reference its ANTI-CREDENTIALISM boundary"
    )
    assert "skillAttestation" in blob, (
        "registry MUST reference the skillAttestation-only credential boundary"
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
