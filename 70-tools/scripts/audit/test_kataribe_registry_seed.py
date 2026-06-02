"""Fail-closed invariants for the kataribe (語部) publication-channel seed registry.

Pins the constitutional properties of the worldwide publication-channel seed
registry (`20-actors/kataribe/registry/channels.seed.json`, per ADR-2605263600).
This suite is R0-safe: test-only, deterministic, network-free — it never imports
or executes a cell and never touches a live channel. It fails fast (fail-closed)
if any constitutional invariant drifts.

Sibling of test_toritsugi_registry_seed.py (which pins the toritsugi procedure
registry). Where that suite enforced 行政書士法/UPL boundary invariants, THIS suite
enforces kataribe's NON-COMMERCIAL / OBSERVATIONAL boundary (ADR-2605263600:
kataribe is a community press / publishing / translation substrate — NOT
commercial journalism, NOT a paid press class, NOT an official publisher; the
registry is an OBSERVATIONAL directory of OFFICIAL public-record channels +
recognized press-freedom bodies that publishes nothing official itself and
editorializes nothing).

Invariants under test:

  1. file parses as JSON and exposes a non-empty `channels` list.
  2. every entry has a UNIQUE `channelId` (no duplicates) — fail-closed.
  3. EVERY entry ships verificationStatus == "unverified-seed" (G14 — no entry
     may be pre-marked verified in the seed).
  4. every entry has a non-empty `accessUrl` + `provenance` + `lastVerified`
     (accessUrl/provenance allow http(s) rather than masking real URLs; the
     lastVerified stamp is ISO-8601 Zulu).
  5. every entry has a `jurisdiction`, and the registry spans MULTIPLE
     jurisdictions (>= 12 distinct) — proves worldwide coverage / guards against
     regression to a single-jurisdiction seed.
  6. every entry's `channelKind` is in the closed publication-channel enum.
  7. every entry's `notes` is non-empty AND references kataribe's
     non-commercial / observational boundary (per-entry boundary caveat); the
     registry as a whole also carries the boundary regime.
  8. a top-level integer `freshnessWindowDays` is present (and positive).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_SEED = _REPO / "20-actors" / "kataribe" / "registry" / "channels.seed.json"

# ISO-8601 Zulu timestamp, e.g. 2026-06-02T00:00:00Z
_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")

# Closed enum of allowed publication-channel kinds (ADR-2605263600).
_ALLOWED_KINDS = {
    "official-gazette",
    "legal-publication",
    "press-freedom-org",
    "open-access-archive",
    "translation-resource",
}

# Tokens that, taken together per entry, attest the kataribe non-commercial /
# observational boundary. Each entry's notes must carry the non-commercial AND
# the observational signal so a per-entry reviewer cannot lose the boundary.
_BOUNDARY_NONCOMMERCIAL = "NOT commercial journalism"
_BOUNDARY_OBSERVATIONAL = "OBSERVATIONAL"


def _load() -> dict:
    return json.loads(_SEED.read_text())


# ─────────────────────────────────────────────────────────────────────────
# 1. parses + non-empty channels list
# ─────────────────────────────────────────────────────────────────────────


def test_registry_parses_and_has_channels():
    assert _SEED.exists(), f"missing seed registry: {_SEED}"
    seed = _load()
    assert isinstance(seed, dict), "top-level must be a JSON object"
    chans = seed.get("channels")
    assert isinstance(chans, list), "`channels` MUST be a list"
    assert len(chans) > 0, "`channels` MUST be non-empty"


# ─────────────────────────────────────────────────────────────────────────
# 2. unique channelId (fail-closed on duplicates)
# ─────────────────────────────────────────────────────────────────────────


def test_channel_ids_unique():
    chans = _load()["channels"]
    ids = [c.get("channelId") for c in chans]
    assert all(ids), "every entry MUST have a non-empty channelId"
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate channelId(s) — fail-closed: {dupes}"
    assert len(set(ids)) == len(ids)


# ─────────────────────────────────────────────────────────────────────────
# 3. G14 — every entry is unverified-seed
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_is_unverified_seed():
    chans = _load()["channels"]
    for c in chans:
        assert c.get("verificationStatus") == "unverified-seed", (
            f"G14: {c.get('channelId')} MUST ship verificationStatus="
            f"unverified-seed (no entry may be pre-marked verified); got "
            f"{c.get('verificationStatus')!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 4. accessUrl + provenance + lastVerified
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_has_access_provenance_and_last_verified():
    chans = _load()["channels"]
    for c in chans:
        cid = c.get("channelId")
        url = c.get("accessUrl") or ""
        assert url, f"{cid}: MUST carry a non-empty accessUrl"
        # Allow http(s) for accessUrl rather than masking real channel URLs.
        assert url.startswith(("https://", "http://")), (
            f"{cid}: accessUrl MUST be an http(s) URL; got {url!r}"
        )
        prov = c.get("provenance") or ""
        assert prov, f"{cid}: MUST cite a non-empty provenance/source URL"
        assert prov.startswith(("https://", "http://")), (
            f"{cid}: provenance MUST be an http(s) URL; got {prov!r}"
        )
        lv = c.get("lastVerified") or ""
        assert lv, f"{cid}: MUST carry a lastVerified timestamp"
        assert _TS_RE.match(lv), (
            f"{cid}: lastVerified MUST be ISO-8601 Zulu; got {lv!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 5. worldwide coverage — >= 12 distinct jurisdictions
# ─────────────────────────────────────────────────────────────────────────


def test_registry_spans_multiple_jurisdictions():
    chans = _load()["channels"]
    for c in chans:
        assert c.get("jurisdiction"), (
            f"{c.get('channelId')}: MUST declare a jurisdiction"
        )
    jurisdictions = {c["jurisdiction"] for c in chans}
    assert len(jurisdictions) >= 12, (
        "WORLDWIDE coverage invariant: registry MUST span >= 12 distinct "
        "jurisdictions (guards against regression to a single-jurisdiction "
        f"seed); got {sorted(jurisdictions)}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 6. channelKind in the closed publication-channel enum
# ─────────────────────────────────────────────────────────────────────────


def test_every_channel_kind_in_enum():
    chans = _load()["channels"]
    for c in chans:
        kind = c.get("channelKind")
        assert kind in _ALLOWED_KINDS, (
            f"{c.get('channelId')}: channelKind {kind!r} not in allowed enum "
            f"{sorted(_ALLOWED_KINDS)}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 7. non-commercial / observational boundary caveat present (per-entry + whole)
# ─────────────────────────────────────────────────────────────────────────


def test_noncommercial_observational_boundary_present():
    seed = _load()
    chans = seed["channels"]
    for c in chans:
        cid = c.get("channelId")
        notes = c.get("notes") or ""
        assert notes.strip(), (
            f"{cid}: notes MUST be non-empty (carries the per-entry boundary "
            "caveat)"
        )
        assert _BOUNDARY_NONCOMMERCIAL in notes, (
            f"{cid}: notes MUST reference kataribe's non-commercial boundary "
            f"({_BOUNDARY_NONCOMMERCIAL!r})"
        )
        assert _BOUNDARY_OBSERVATIONAL in notes, (
            f"{cid}: notes MUST reference the OBSERVATIONAL-directory boundary"
        )
    # Registry-as-a-whole carries the boundary regime in the serialized file.
    blob = _SEED.read_text()
    assert _BOUNDARY_NONCOMMERCIAL in blob, (
        "registry MUST reference its non-commercial boundary"
    )
    assert "observational" in blob.lower(), (
        "registry MUST reference its observational boundary"
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
