"""Fail-closed invariants for the chigiri (契) worldwide legal-aid seed registry.

Pins the constitutional properties of
`20-actors/chigiri/registry/legal-aid.seed.json` (the worldwide legal-aid
REFERRAL seed authored at iter-1, ADR-2605262700) so a later refactor cannot
silently weaken a constitutional invariant. R0-safe: test-only, network-free,
no cell execution, no live use. Mirrors the pytest style of
test_toritsugi_invariants.py.

chigiri is a procedural / referral-routing substrate, NOT a law firm and NOT
the unauthorized practice of law (G8/G14). The boundary regime is:
**UPL strictly prohibited — referral-only, no advice, zero compensation,
Public-Fund-routed.** Every seed entry MUST ship verificationStatus =
unverified-seed (G14): no entry may be pre-marked verified in the seed.

Invariants under test:

  1. File parses as JSON and has a non-empty "referrals" list.
  2. Every entry has a unique "referralId" (no duplicates) — fail-closed.
  3. EVERY entry has verificationStatus == "unverified-seed" (G14).
  4. Every entry has a non-empty provenance URL (https) + a lastVerified stamp.
  5. Every entry has a "jurisdiction"; registry spans >= 12 distinct
     jurisdictions (proves long-tail worldwide coverage, guards JP-only and
     core-only regression).
  6. Every entry's notes is non-empty, and the registry references its
     boundary regime (UPL / referral-only / no advice / zero compensation).
  7. A top-level integer "freshnessWindowDays" is present.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SEED = _REPO / "20-actors" / "chigiri" / "registry" / "legal-aid.seed.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def seed() -> dict:
    return _load(_SEED)


@pytest.fixture(scope="module")
def referrals(seed: dict) -> list:
    return seed["referrals"]


# ─────────────────────────────────────────────────────────────────────────
# 1. parses as JSON + non-empty referrals list
# ─────────────────────────────────────────────────────────────────────────


def test_seed_parses_and_has_referrals(seed: dict):
    assert _SEED.exists(), f"missing seed registry: {_SEED}"
    assert isinstance(seed.get("referrals"), list), "top-level 'referrals' must be a list"
    assert len(seed["referrals"]) >= 1, "registry MUST be non-empty"


# ─────────────────────────────────────────────────────────────────────────
# 2. unique referralId — fail-closed on duplicates
# ─────────────────────────────────────────────────────────────────────────


def test_referral_ids_unique(referrals: list):
    ids = [e.get("referralId") for e in referrals]
    assert all(i for i in ids), "every entry MUST have a non-empty referralId"
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate referralId(s) — fail-closed: {dupes}"
    assert len(set(ids)) == len(ids), "referralId values MUST be unique"


# ─────────────────────────────────────────────────────────────────────────
# 3. G14 — every entry ships verificationStatus == unverified-seed
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_unverified_seed(referrals: list):
    for e in referrals:
        rid = e.get("referralId")
        assert e.get("verificationStatus") == "unverified-seed", (
            f"G14: {rid} MUST ship verificationStatus=unverified-seed "
            f"(no seed entry may be pre-marked verified); got "
            f"{e.get('verificationStatus')!r}"
        )


# ─────────────────────────────────────────────────────────────────────────
# 4. every entry has a provenance https URL + a lastVerified stamp
# ─────────────────────────────────────────────────────────────────────────


def test_every_entry_has_provenance_and_lastverified(referrals: list):
    for e in referrals:
        rid = e.get("referralId")
        prov = (e.get("provenance") or "").strip()
        assert prov, f"{rid}: MUST cite a non-empty provenance source"
        assert prov.startswith("https://"), (
            f"{rid}: provenance MUST be an https URL; got {prov!r}"
        )
        lv = (e.get("lastVerified") or "").strip()
        assert lv, f"{rid}: MUST carry a lastVerified timestamp"


# ─────────────────────────────────────────────────────────────────────────
# 5. worldwide coverage — jurisdiction present + >= 5 distinct values
# ─────────────────────────────────────────────────────────────────────────


def test_multiple_jurisdictions(referrals: list):
    for e in referrals:
        rid = e.get("referralId")
        assert (e.get("jurisdiction") or "").strip(), (
            f"{rid}: MUST carry a non-empty jurisdiction"
        )
    distinct = {e["jurisdiction"] for e in referrals}
    assert len(distinct) >= 12, (
        "registry MUST span >= 12 distinct jurisdictions (long-tail worldwide "
        "coverage; guards JP-only AND core-only regression); got "
        f"{sorted(distinct)}"
    )


# ─────────────────────────────────────────────────────────────────────────
# 6. boundary caveat — per-entry notes non-empty + registry-wide UPL regime
# ─────────────────────────────────────────────────────────────────────────


def test_boundary_caveat_present(seed: dict, referrals: list):
    # 6a. Every entry carries a non-empty notes caveat.
    for e in referrals:
        rid = e.get("referralId")
        notes = (e.get("notes") or "").strip()
        assert notes, f"{rid}: notes (boundary caveat) MUST be non-empty"

    # 6b. The registry as a whole references its boundary regime:
    #     UPL-prohibited / referral-only / no advice / zero compensation.
    #     Asserted over the union of per-entry notes + the top-level _comment,
    #     case-insensitively (adapts to the file's actual wording).
    corpus = (seed.get("_comment") or "") + " ".join(
        (e.get("notes") or "") for e in referrals
    )
    corpus_l = corpus.lower()
    for token in ("upl", "referral", "no legal advice", "zero compensation"):
        assert token in corpus_l, (
            f"boundary regime token {token!r} MUST appear in the registry "
            f"(UPL — referral-only, no advice, zero compensation)"
        )

    # 6c. And the canonical boundary sentence must appear on EVERY entry's
    #     notes — the structural fail-closed caveat, not just somewhere.
    for e in referrals:
        rid = e.get("referralId")
        n = (e.get("notes") or "").lower()
        assert "upl" in n and "no legal advice" in n, (
            f"{rid}: notes MUST restate the UPL no-legal-advice boundary"
        )


# ─────────────────────────────────────────────────────────────────────────
# 7. top-level freshnessWindowDays integer
# ─────────────────────────────────────────────────────────────────────────


def test_freshness_window_days_integer(seed: dict):
    fwd = seed.get("freshnessWindowDays")
    assert isinstance(fwd, int) and not isinstance(fwd, bool), (
        f"freshnessWindowDays MUST be a top-level integer; got {fwd!r}"
    )
    assert fwd > 0, f"freshnessWindowDays MUST be positive; got {fwd}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
