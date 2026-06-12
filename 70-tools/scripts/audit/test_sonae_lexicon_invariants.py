"""Fail-closed invariants for the sonae (備え) pre-disaster substrate.

Pins the constitutional properties of sonae's R0 scaffold (ADR-2606091200)
at the schema level. R0-safe: test-only, deterministic, network-free — it
never imports/executes a cell (cells are import-time RuntimeError until R1)
and never touches a live feed or channel. It fails fast (fail-closed) if any
constitutional invariant drifts out of the manifest or Lexicon skeletons.

Sibling of test_kazaori_registry_seed.py. Where that suite pins kazaori's
(風折) OBSERVATIONAL disaster-agency directory, THIS suite pins sonae's
(備え) BEFORE-phase substrate: foresight / preparedness / early-warning.

sonae boundary (re-asserted by these tests):
  - G8 NO false authority — sonae MUST NOT originate official seismic/tsunami
    warnings; earlyWarningRelay is relay-only (relayOnly const true) and MUST
    cite an authoritativeSource.
  - G10 NO unilateral declaration — emergency state is owned by kazaori's
    Council Lv6+ >=4/7 path; sonae only signals/recommends.
  - N3 NOT response — sonae is the BEFORE half; response is kazaori.
  - G4 OPEN gov feeds only — no commercial disaster-prediction vendor may
    appear as an allowed value anywhere.
  - G6 NO surveillance — open feeds + opt-in only; aggregate-only, no
    individual-level fields.

Invariants under test:
  1.  manifest parses as JSON and is an ActorManifest for did:web:sonae.*
  2.  exactly 6 cells, all on the naphtali node
  3.  exactly 6 lexiconNamespaces, all under com.etzhayyim.sonae.*
  4.  every declared lexiconNamespace resolves to an on-disk Lexicon file
  5.  every Lexicon file parses and its `id` matches its namespace + path
  6.  earlyWarningRelay: relayOnly is const true AND authoritativeSource is
      required (G8 STRUCTURAL — the defining gate)
  7.  hazardSignalRecord: openDataOnlyAttested const true (G6) AND sourceFeed
      knownValues are a subset of the OPEN gov-feed allowlist (G4)
  8.  siteRiskProfile: communityScaleAttested const true (G3) AND no
      individual-level field names (G6)
  9.  drillAttestation: participantsOptIn const true (G6)
  10. G4 NEGATIVE: no prohibited commercial vendor string appears as a
      Lexicon `knownValues` (allowed) value in any sonae Lexicon
  11. manifest declares the no-false-authority + phase-boundary invariants
      and N3 (not response) non-goal
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_ACTOR = _REPO / "20-actors" / "sonae"
_MANIFEST = _ACTOR / "manifest.jsonld"
_LEXDIR = _REPO / "00-contracts" / "lexicons" / "com" / "etzhayyim" / "sonae"

# Open-publication government / inter-gov hazard feeds (G4). sourceFeed
# knownValues MUST be a subset of this allowlist — no commercial vendor.
_OPEN_FEED_ALLOWLIST = {
    "usgs", "phivolcs", "jma", "ptwc", "gdacs",
    "copernicus-ems", "wmo-gts", "national-met-service-other",
}

# Commercial disaster-prediction / alerting vendors PROHIBITED per G4
# (Charter Rider §2(e)+§2(c)). These may appear in PROSE (prohibition
# notes) but MUST NEVER appear as an allowed `knownValues` enum value.
_PROHIBITED_VENDORS = (
    "one concern", "oneconcern", "floodflash", "jupiter intelligence",
    "tomorrow.io", "everbridge", "onsolve", "alertmedia", "rms",
)

# Field-name fragments that would imply individual-level tracking (G6).
_INDIVIDUAL_LEVEL_FORBIDDEN = (
    "personname", "fullname", "individualid", "householdid",
    "homeaddress", "biometric", "phonenumber", "deviceid",
    "facialid", "gpscoordinate", "personlocation",
)


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads(_MANIFEST.read_text(encoding="utf-8"))


def _load_lexicon(name: str) -> dict:
    return json.loads((_LEXDIR / f"{name}.json").read_text(encoding="utf-8"))


def _all_lexicon_files() -> list[Path]:
    return sorted(p for p in _LEXDIR.glob("*.json"))


def _record_props(lex: dict) -> dict:
    """Top-level record properties of a Lexicon's `main` def."""
    return lex["defs"]["main"]["record"]["properties"]


# ── 1. manifest identity ────────────────────────────────────────────────

def test_manifest_parses_and_is_sonae(manifest):
    assert manifest["@type"] == "ActorManifest"
    assert manifest["id"] == "did:web:sonae.etzhayyim.com"
    assert manifest["name"] == "sonae"


# ── 2. cells ────────────────────────────────────────────────────────────

def test_exactly_six_cells_on_naphtali(manifest):
    cells = manifest["cells"]
    assert len(cells) == 6, f"expected 6 cells, got {len(cells)}"
    for c in cells:
        assert c["murakumoNode"] == "naphtali", c["name"]


# ── 3-5. lexicon namespaces resolve to files with matching ids ──────────

def test_six_namespaces_all_under_sonae(manifest):
    ns = manifest["lexiconNamespaces"]
    assert len(ns) == 6, f"expected 6 lexiconNamespaces, got {len(ns)}"
    for n in ns:
        assert n.startswith("com.etzhayyim.sonae."), n


def test_every_namespace_resolves_to_file_with_matching_id(manifest):
    for n in manifest["lexiconNamespaces"]:
        leaf = n.rsplit(".", 1)[-1]
        path = _LEXDIR / f"{leaf}.json"
        assert path.exists(), f"missing Lexicon file for {n}"
        lex = json.loads(path.read_text(encoding="utf-8"))
        assert lex["id"] == n, f"{path.name} id {lex['id']!r} != namespace {n!r}"


# ── 6. earlyWarningRelay: NO false authority (G8) ───────────────────────

def test_early_warning_relay_is_relay_only_with_source():
    lex = _load_lexicon("earlyWarningRelay")
    props = _record_props(lex)
    assert props["relayOnly"].get("const") is True, "G8: relayOnly must be const true"
    required = lex["defs"]["main"]["record"]["required"]
    assert "authoritativeSource" in required, "G8: authoritativeSource must be required"
    assert "relayOnly" in required, "G8: relayOnly must be required"


# ── 7. hazardSignalRecord: open-data-only (G6) + open feeds (G4) ────────

def test_hazard_signal_open_data_only_and_open_feeds():
    lex = _load_lexicon("hazardSignalRecord")
    props = _record_props(lex)
    assert props["openDataOnlyAttested"].get("const") is True, "G6: const true"
    feeds = set(props["sourceFeed"]["knownValues"])
    assert feeds <= _OPEN_FEED_ALLOWLIST, (
        f"G4: sourceFeed has non-open-feed values: {feeds - _OPEN_FEED_ALLOWLIST}"
    )


# ── 8. siteRiskProfile: community-scale (G3) + no individual data (G6) ──

def test_site_risk_profile_community_scale_no_individual_data():
    lex = _load_lexicon("siteRiskProfile")
    props = _record_props(lex)
    assert props["communityScaleAttested"].get("const") is True, "G3: const true"
    blob = json.dumps(lex).lower()
    for frag in _INDIVIDUAL_LEVEL_FORBIDDEN:
        assert frag not in blob, f"G6: forbidden individual-level field fragment {frag!r}"


# ── 9. drillAttestation: opt-in (G6) ────────────────────────────────────

def test_drill_attestation_opt_in():
    lex = _load_lexicon("drillAttestation")
    props = _record_props(lex)
    assert props["participantsOptIn"].get("const") is True, "G6: participantsOptIn const true"


# ── 10. G4 NEGATIVE: no commercial vendor as an allowed enum value ──────

def test_no_prohibited_vendor_in_known_values():
    offenders: list[str] = []
    for path in _all_lexicon_files():
        lex = json.loads(path.read_text(encoding="utf-8"))

        def _walk(node):
            if isinstance(node, dict):
                if "knownValues" in node and isinstance(node["knownValues"], list):
                    for v in node["knownValues"]:
                        if isinstance(v, str):
                            low = v.lower()
                            for vendor in _PROHIBITED_VENDORS:
                                if vendor in low:
                                    offenders.append(f"{path.name}: {v}")
                for v in node.values():
                    _walk(v)
            elif isinstance(node, list):
                for v in node:
                    _walk(v)

        _walk(lex)
    assert not offenders, f"G4: prohibited vendor as allowed value: {offenders}"


# ── 11. manifest declares the defining invariants + N3 ──────────────────

def test_manifest_declares_false_authority_and_phase_boundary(manifest):
    assert "falseAuthorityInvariant" in manifest, "G8 invariant must be declared"
    assert "phaseBoundaryInvariant" in manifest, "N3 phase-boundary must be declared"
    n3 = manifest["nonGoals"]["goals"]["N3"].lower()
    assert "response" in n3, "N3 must state sonae is NOT response"
