"""Fail-closed invariants for the himotoki (繙き) disclosure-target seed registry.

Pins the constitutional properties of the WORLDWIDE disclosure-target seed
(`20-actors/himotoki/registry/targets.seed.json`, ADR-2605302130 §2/§4) so a
future edit cannot silently weaken a constitutional invariant. R0-safe:
test-only, network-free, no cell execution, no live dispatch. Mirrors the
pytest style of test_toritsugi_invariants.py.

Invariants under test:

  1. The file parses as JSON and ships a non-empty "targets" list.
  2. Every entry has a unique "organization" id (no duplicates) — fail-closed.
  3. G14: EVERY entry ships verificationStatus == "unverified-seed"; no seed
     entry may be pre-marked verified.
  4. Every entry cites a non-empty https "provenance" source URL and a
     non-empty "lastVerified" timestamp.
  5. Every entry has a "jurisdiction"; the registry spans MULTIPLE
     jurisdictions (>= 12 distinct) — proves worldwide long-tail coverage,
     guards against regression to JP-only.
  6. Boundary caveat: every entry's "notes" is non-empty, and the registry as
     a whole references its consent-gated / own-data-only / lawful-channel
     boundary regime.
  7. A top-level integer "freshnessWindowDays" is present.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SEED = _REPO / "20-actors" / "himotoki" / "registry" / "targets.seed.json"


def _load() -> dict:
    return json.loads(_SEED.read_text())


# ─────────────────────────────────────────────────────────────────────────
# 1. parses + non-empty targets list
# ─────────────────────────────────────────────────────────────────────────


def test_file_parses_and_has_targets_list():
    assert _SEED.exists(), f"missing seed registry: {_SEED}"
    seed = _load()
    assert isinstance(seed, dict), "top-level must be a JSON object"
    assert isinstance(seed.get("targets"), list), '"targets" must be a list'
    assert seed["targets"], '"targets" must be non-empty'


# ─────────────────────────────────────────────────────────────────────────
# 2. unique organization ids — fail-closed
# ─────────────────────────────────────────────────────────────────────────


def test_organization_ids_unique():
    targets = _load()["targets"]
    ids = [t.get("organization") for t in targets]
    assert all(ids), "every entry MUST have a non-empty organization id"
    dupes = sorted({o for o in ids if ids.count(o) > 1})
    assert not dupes, f"duplicate organization ids (fail-closed): {dupes}"


# ─────────────────────────────────────────────────────────────────────────
# 3. G14: every entry is unverified-seed
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_is_unverified_seed():
    for t in _load()["targets"]:
        org = t.get("organization")
        assert t.get("verificationStatus") == "unverified-seed", (
            f"G14: {org!r} MUST ship verificationStatus=unverified-seed "
            f"(no entry may be pre-marked verified); got "
            f"{t.get('verificationStatus')!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 4. provenance source URL + lastVerified timestamp
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_has_provenance_and_last_verified():
    for t in _load()["targets"]:
        org = t.get("organization")
        prov = t.get("provenance") or ""
        assert prov, f"{org!r} MUST cite a non-empty provenance source URL"
        assert prov.startswith("https://"), (
            f"{org!r} provenance MUST be an https URL; got {prov!r}"
        )
        lv = t.get("lastVerified") or ""
        assert lv, f"{org!r} MUST carry a non-empty lastVerified timestamp"
        # Tolerant ISO-8601 parse (network-free): must be a real timestamp.
        datetime.fromisoformat(lv.replace("Z", "+00:00"))


# ─────────────────────────────────────────────────────────────────────────
# 5. jurisdiction present + multi-jurisdiction worldwide coverage
# ─────────────────────────────────────────────────────────────────────────


def test_multi_jurisdiction_worldwide_coverage():
    targets = _load()["targets"]
    jurisdictions = []
    for t in targets:
        j = t.get("jurisdiction")
        assert j, f"{t.get('organization')!r} MUST declare a jurisdiction"
        jurisdictions.append(j)
    distinct = set(jurisdictions)
    assert len(distinct) >= 12, (
        "registry MUST span >= 12 distinct jurisdictions (worldwide long-tail "
        "coverage; guards against JP-only regression); got {}".format(sorted(distinct))
    )


# ─────────────────────────────────────────────────────────────────────────
# 6. boundary caveat: per-entry notes + registry-wide boundary regime
# ─────────────────────────────────────────────────────────────────────────


def test_boundary_caveat_present():
    seed = _load()
    targets = seed["targets"]

    # 6a. every entry carries a non-empty notes caveat field.
    for t in targets:
        org = t.get("organization")
        notes = t.get("notes") or ""
        assert notes.strip(), f"{org!r} MUST carry a non-empty notes caveat"

    # 6b. the registry as a whole references its boundary regime. The phrases
    #     appear across entry notes and/or the top-level _comment; require that
    #     each boundary concept is referenced somewhere in the corpus.
    corpus = json.dumps(seed, ensure_ascii=False).lower()
    boundary_markers = [
        "own-data-only",
        "unverified-seed",  # G14 seed-only, never live use
    ]
    for marker in boundary_markers:
        assert marker in corpus, (
            f"registry MUST reference its boundary regime marker {marker!r}"
        )
    # lawful-channel-only OR consent-gated style boundary must appear somewhere.
    assert ("lawful-channel" in corpus) or ("consent-gated" in corpus), (
        "registry MUST reference a consent-gated / lawful-channel boundary regime"
    )


# ─────────────────────────────────────────────────────────────────────────
# 7. top-level freshnessWindowDays integer
# ─────────────────────────────────────────────────────────────────────────


def test_freshness_window_days_present():
    seed = _load()
    fwd = seed.get("freshnessWindowDays")
    assert isinstance(fwd, int) and not isinstance(fwd, bool), (
        f"top-level freshnessWindowDays MUST be an integer; got {fwd!r}"
    )
    assert fwd > 0, f"freshnessWindowDays MUST be positive; got {fwd}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
