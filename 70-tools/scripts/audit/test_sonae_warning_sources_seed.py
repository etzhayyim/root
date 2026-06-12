"""Fail-closed invariants for the sonae (備え) authoritative-warning-source seed.

Pins the constitutional properties of sonae's worldwide directory of
OFFICIAL authoritative warning issuers (`registry/warning-sources.seed.json`,
per ADR-2606091200). R0-safe: test-only, deterministic, network-free — it
never imports/executes a cell and never touches a live feed/channel. It fails
fast (fail-closed) if any constitutional invariant drifts.

Sibling of test_kazaori_registry_seed.py. Where that suite pins kazaori's
disaster-AGENCY directory, THIS suite pins sonae's directory of AUTHORITATIVE
WARNING ISSUERS — the allowlist of official sources whose warnings sonae's
earlyWarningRelay may RELAY (relay-only) but MUST NOT originate.

sonae boundary (re-asserted by these tests):
  - G8 NO false authority — every entry is an AUTHORITATIVE official issuer
    (isAuthoritativeIssuer=true) and every entry's notes re-assert the
    relay-only / sonae-originates-nothing boundary.
  - G10 NO unilateral declaration — the registry routes to official issuers;
    sonae declares no emergency (that is kazaori's Council path).
  - G14 honesty — every entry ships verificationStatus="unverified-seed".

Invariants under test:
  1.  file parses as JSON and exposes a non-empty `sources` list.
  2.  every entry has a UNIQUE `sourceId` (no duplicates) — fail-closed.
  3.  EVERY entry ships verificationStatus == "unverified-seed" (G14).
  4.  every entry has a non-empty accessUrl + provenance (each a valid
      http(s) URL) + a lastVerified ISO-8601 Zulu stamp.
  5.  registry spans MULTIPLE jurisdictions (>= 12 distinct) — worldwide.
  6.  every entry's `sourceKind` is in the allowed authoritative taxonomy.
  7.  G8 STRUCTURAL: every entry isAuthoritativeIssuer is True AND its `notes`
      re-assert the relay-only boundary (mentions "relay" + "G8").
  8.  a top-level integer `freshnessWindowDays` is present.
  9.  G8 CROSS-LEXICON: every non-catch-all token in earlyWarningRelay's
      `authoritativeSource` enum is realized by some entry's
      `authoritativeSourceToken` (registry covers the lexicon's vocabulary).
  10. every `authoritativeSourceToken` is itself a value the lexicon enum
      admits (no registry token outside the lexicon vocabulary).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SEED = _REPO / "20-actors" / "sonae" / "registry" / "warning-sources.seed.json"
_RELAY_LEX = (
    _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "sonae"
    / "earlyWarningRelay.json"
)

_ISO_Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_HTTP = re.compile(r"^https?://", re.IGNORECASE)

_ALLOWED_SOURCE_KINDS = {
    "national-seismic-tsunami-authority",
    "national-seismic-network",
    "national-met-service",
    "regional-tsunami-warning-center",
    "multi-hazard-alert-aggregator",
    "national-disaster-management-agency",
}

# Catch-all enum members that need not be realized by a specific entry.
_CATCH_ALL_TOKENS = {"national-met-service-other", "national-disaster-agency-other"}


@pytest.fixture(scope="module")
def seed() -> dict:
    return json.loads(_SEED.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sources(seed) -> list:
    return seed["sources"]


@pytest.fixture(scope="module")
def relay_enum() -> set:
    lex = json.loads(_RELAY_LEX.read_text(encoding="utf-8"))
    props = lex["defs"]["main"]["record"]["properties"]
    return set(props["authoritativeSource"]["knownValues"])


def test_parses_nonempty(sources):
    assert isinstance(sources, list) and len(sources) > 0


def test_unique_source_ids(sources):
    ids = [s["sourceId"] for s in sources]
    assert len(ids) == len(set(ids)), "duplicate sourceId — fail-closed"


def test_all_unverified_seed(sources):
    for s in sources:
        assert s["verificationStatus"] == "unverified-seed", s["sourceId"]


def test_urls_and_timestamps(sources):
    for s in sources:
        assert s.get("accessUrl") and _HTTP.match(s["accessUrl"]), s["sourceId"]
        assert s.get("provenance") and _HTTP.match(s["provenance"]), s["sourceId"]
        assert _ISO_Z.match(s.get("lastVerified", "")), s["sourceId"]


def test_worldwide_jurisdiction_spread(sources):
    juris = {s["jurisdiction"] for s in sources}
    assert len(juris) >= 12, f"expected >=12 jurisdictions, got {len(juris)}: {sorted(juris)}"


def test_source_kind_taxonomy(sources):
    for s in sources:
        assert s["sourceKind"] in _ALLOWED_SOURCE_KINDS, f"{s['sourceId']}: {s['sourceKind']}"


def test_g8_authoritative_and_relay_only_notes(sources):
    for s in sources:
        assert s.get("isAuthoritativeIssuer") is True, f"G8: {s['sourceId']} not authoritative"
        notes = s.get("notes", "").lower()
        assert "relay" in notes and "g8" in notes, (
            f"G8: {s['sourceId']} notes must re-assert the relay-only boundary"
        )


def test_freshness_window_present(seed):
    assert isinstance(seed.get("freshnessWindowDays"), int)


def test_g8_registry_covers_lexicon_vocabulary(sources, relay_enum):
    needed = relay_enum - _CATCH_ALL_TOKENS
    present = {s.get("authoritativeSourceToken") for s in sources}
    missing = needed - present
    assert not missing, f"G8: lexicon authoritativeSource tokens not in registry: {missing}"


def test_registry_tokens_within_lexicon_vocabulary(sources, relay_enum):
    for s in sources:
        tok = s.get("authoritativeSourceToken")
        assert tok in relay_enum, (
            f"{s['sourceId']}: token {tok!r} outside earlyWarningRelay enum {sorted(relay_enum)}"
        )
