"""Complete M2 shinka cell tests — evolution_validation_cell, evolution_emission_cell,
shinka_tick orchestration, and error path coverage.

Tests:
  A. EvolutionValidationCell
     1. Passes when attestation count meets threshold (WITNESS_MIN_BY_LEVEL)
     2. Fails (valid=False) when attestation count is below threshold
     3. Calls mst.council_attestation_details with correct args
     4. Calls pds.put_record with validateEvolution on success
     5. Does NOT call pds.put_record on failure
     6. Returns ValidationResult with correct fields
     7. Uses correct required count for each level (threshold table)
     8. Lv6: fails when count sufficient but Council co-signers insufficient
     9. Lv6: fails when count insufficient (before Council gate)
     10. Lv6: valid when both count and Council co-signers meet thresholds
     11. Lv7: invalid when Council votes < COUNCIL_SUPERMAJORITY_LV7 (3 votes)
     12. Lv7: valid when Council votes >= COUNCIL_SUPERMAJORITY_LV7 (4 votes)
     13. Recency filter: old attestation excluded from count

  B. EvolutionEmissionCell
     1. Pins evidence CIDs via ipfs.pin_many
     2. Anchors to Base L2 via l2.anchor
     3. Returns the anchor tx hash
     4. Calls pds.put_record with evolutionEvent (correct collection)
     5. Raises (re-raises) if ipfs.pin_many fails
     6. Raises (re-raises) if l2.anchor fails
     7. pds.put_record called with correct lexicon fields

  C. shinka_tick orchestration
     1. End-to-end: observation → validation → emission → heartbeat (all mocked)
     2. No-DID case returns early with heartbeat written
     3. Observation failure → skips validation/emission, heartbeat with error
     4. Validation fails (insufficient attestations) → no emission
     5. Emission called only when validation.valid is True
     6. heartbeat_written=True in output
     7. evolutionWritten=True when emission succeeds

  D. Pure helper tests
     1. _classify_mood: stress≥70 → stressed
     2. _classify_mood: joy≥60 → joyful
     3. _classify_mood: calm≥60 → calm
     4. _classify_mood: gratitude≥60 → grateful
     5. _classify_mood: focus≥60 → focused
     6. _classify_mood: all below → neutral
     7. _resolve_cadence: joyful mood with large elapsed → should_post=True
     8. _resolve_cadence: stressed mood → should_post=False

  E. WITNESS_MIN_BY_LEVEL constant
     1. Level 1 → 2
     2. Level 3 → 5
     3. COUNCIL_SUPERMAJORITY_LV7 = 4
     4. COUNCIL_GATE_LV6 = 2

ADR authority:
    ADR-2605215200 §1 — shinka M2 cell specifications
    ADR-2605215400 — canonical attestation threshold table (Lv1-7)
    ADR-2605171800 — MST → IPFS → Base L2 anchor pipeline
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
_py_src = Path(__file__).resolve().parents[1] / "src"
if str(_py_src) not in sys.path:
    sys.path.insert(0, str(_py_src))

_sdk_src = Path(__file__).resolve().parents[3] / "etzhayyim-sdk-py" / "src"
if str(_sdk_src) not in sys.path:
    sys.path.insert(0, str(_sdk_src))

import pymagatama.primitives.shinka_murakumo as SM  # noqa: E402


# ── Mock factories ─────────────────────────────────────────────────────────────


def _make_pds_mock(
    put_record_cid: str = "bafymockcommitcid",
) -> MagicMock:
    mock = MagicMock()
    mock.put_record = AsyncMock(
        return_value={"uri": "at://mock/mock/mock", "cid": put_record_cid}
    )
    return mock


def _make_attestation_list(
    count: int,
    council_count: int = 0,
) -> list[dict]:
    """Build a list of attestation dicts for mocking council_attestation_details.

    ``count`` total attestations; first ``council_count`` have is_council_lv6=True.
    """
    import datetime as _dt

    recent_ts = (
        _dt.datetime.now(tz=_dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    result = []
    for i in range(count):
        is_council = i < council_count
        result.append(
            {
                "attestor_did": f"did:web:witness-{i}.etzhayyim.com",
                "is_council_lv6": is_council,
                "attestation_at": recent_ts,
                "attestation_uri": f"at://mock/ai.gftd.apps.etzhayyim.charter-attestation/mock-{i}",
                "evidence_cid": None,
            }
        )
    return result


def _make_mst_mock(
    attestation_count: int = 0,
    council_count: int = 0,
    attestation_list: list[dict] | None = None,
) -> MagicMock:
    """Build an MST mock for evolution_validation_cell tests.

    ``attestation_list`` overrides ``attestation_count``/``council_count`` when provided.
    ``council_attestation_count`` is kept as a backward-compat wrapper (returns len of list).
    """
    mock = MagicMock()

    async def mock_query(collection: str, **kwargs: Any) -> list[dict]:
        if "evolutionEvent" in collection:
            return []
        if "kyumeiSignal" in collection:
            return []
        return []

    mock.query = mock_query

    # council_attestation_details returns the richer list of dicts.
    effective_list = (
        attestation_list
        if attestation_list is not None
        else _make_attestation_list(attestation_count, council_count)
    )
    mock.council_attestation_details = AsyncMock(return_value=effective_list)
    # council_attestation_count kept for any remaining callers (backward-compat).
    mock.council_attestation_count = AsyncMock(return_value=len(effective_list))
    # council_objections: by default, return empty list (no objections filed).
    # Individual tests can override if needed.
    mock.council_objections = AsyncMock(return_value=[])
    return mock


def _make_ipfs_mock(fail: bool = False) -> MagicMock:
    mock = MagicMock()
    if fail:
        mock.pin_many = AsyncMock(side_effect=RuntimeError("IPFS pin failed"))
    else:
        mock.pin_many = AsyncMock(return_value=None)
    return mock


def _make_l2_mock(
    tx_hash: str = "0xdeadbeef0123456789abcdef",
    fail: bool = False,
) -> MagicMock:
    mock = MagicMock()
    if fail:
        mock.anchor = AsyncMock(side_effect=RuntimeError("L2 anchor failed"))
    else:
        mock.anchor = AsyncMock(return_value=tx_hash)
    return mock


_SENTINEL = object()  # sentinel for "use default" in _make_claim


def _make_claim(
    *,
    claim_id: str = "claim-001",
    adherent_did: str = "did:web:alice.etzhayyim.com",
    proposed_level: int = 2,
    evidence_cids: list[str] | None | object = _SENTINEL,
) -> SM.EvolutionClaim:
    # Use sentinel to distinguish "not provided" (use default) from [] (explicit empty).
    if evidence_cids is _SENTINEL:
        effective_cids: list[str] = ["bafybeig5ev1", "bafybeig5ev2"]
    else:
        effective_cids = evidence_cids  # type: ignore[assignment]
    return SM.EvolutionClaim(
        claim_id=claim_id,
        adherent_did=adherent_did,
        proposed_level=proposed_level,
        evidence_cids=effective_cids,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# A. EvolutionValidationCell
# ═══════════════════════════════════════════════════════════════════════════════


class TestEvolutionValidationCell:
    """Tests for evolution_validation_cell() — M2 implementation."""

    @pytest.mark.asyncio
    async def test_passes_when_attestation_count_meets_threshold(self):
        """Valid when attestation_count >= WITNESS_MIN_BY_LEVEL[proposed_level]."""
        claim = _make_claim(proposed_level=2)
        required = SM.WITNESS_MIN_BY_LEVEL[2]  # 3
        mock_mst = _make_mst_mock(attestation_count=required)
        mock_pds = _make_pds_mock()

        original_mst, original_pds = SM._mst_mod, SM._pds_mod
        SM._mst_mod, SM._pds_mod = mock_mst, mock_pds
        try:
            result = await SM.evolution_validation_cell(claim)
        finally:
            SM._mst_mod, SM._pds_mod = original_mst, original_pds

        assert result.valid is True
        assert result.attestation_count == required
        assert result.required_count == required

    @pytest.mark.asyncio
    async def test_fails_when_attestation_count_below_threshold(self):
        """Invalid when attestation_count < WITNESS_MIN_BY_LEVEL[proposed_level]."""
        claim = _make_claim(proposed_level=3)
        required = SM.WITNESS_MIN_BY_LEVEL[3]  # 5
        mock_mst = _make_mst_mock(attestation_count=required - 1)
        mock_pds = _make_pds_mock()

        original_mst, original_pds = SM._mst_mod, SM._pds_mod
        SM._mst_mod, SM._pds_mod = mock_mst, mock_pds
        try:
            result = await SM.evolution_validation_cell(claim)
        finally:
            SM._mst_mod, SM._pds_mod = original_mst, original_pds

        assert result.valid is False
        assert result.attestation_count == required - 1
        assert result.required_count == required
        assert "Insufficient" in result.reason

    @pytest.mark.asyncio
    async def test_calls_mst_council_attestation_details_with_correct_args(self):
        """mst.council_attestation_details called with subject_did, level, since_days."""
        claim = _make_claim(proposed_level=4, adherent_did="did:web:bob.etzhayyim.com")
        mock_mst = _make_mst_mock(attestation_count=10)
        mock_pds = _make_pds_mock()

        original_mst, original_pds = SM._mst_mod, SM._pds_mod
        SM._mst_mod, SM._pds_mod = mock_mst, mock_pds
        try:
            await SM.evolution_validation_cell(claim)
        finally:
            SM._mst_mod, SM._pds_mod = original_mst, original_pds

        mock_mst.council_attestation_details.assert_awaited_once_with(
            "did:web:bob.etzhayyim.com",
            4,
            since_days=SM.WITNESS_RECENCY_DAYS,
        )

    @pytest.mark.asyncio
    async def test_writes_validate_evolution_on_success(self):
        """pds.put_record called with validateEvolution collection when valid."""
        claim = _make_claim(proposed_level=1)
        required = SM.WITNESS_MIN_BY_LEVEL[1]  # 2
        mock_mst = _make_mst_mock(attestation_count=required + 1)
        mock_pds = _make_pds_mock()

        original_mst, original_pds = SM._mst_mod, SM._pds_mod
        SM._mst_mod, SM._pds_mod = mock_mst, mock_pds
        try:
            result = await SM.evolution_validation_cell(claim)
        finally:
            SM._mst_mod, SM._pds_mod = original_mst, original_pds

        assert result.valid is True
        mock_pds.put_record.assert_awaited_once()
        call_kwargs = mock_pds.put_record.call_args.kwargs
        assert call_kwargs["collection"] == "app.etzhayyim.shinka.validateEvolution"
        record = call_kwargs["record"]
        assert record["$type"] == "app.etzhayyim.shinka.validateEvolution"
        assert record["claimId"] == claim.claim_id
        assert record["adherentDid"] == claim.adherent_did
        assert record["proposedLevel"] == claim.proposed_level

    @pytest.mark.asyncio
    async def test_does_not_write_validate_evolution_on_failure(self):
        """pds.put_record is NOT called when validation fails."""
        claim = _make_claim(proposed_level=2)
        mock_mst = _make_mst_mock(attestation_count=0)
        mock_pds = _make_pds_mock()

        original_mst, original_pds = SM._mst_mod, SM._pds_mod
        SM._mst_mod, SM._pds_mod = mock_mst, mock_pds
        try:
            result = await SM.evolution_validation_cell(claim)
        finally:
            SM._mst_mod, SM._pds_mod = original_mst, original_pds

        assert result.valid is False
        mock_pds.put_record.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_validation_result_with_correct_fields(self):
        """ValidationResult has all expected fields."""
        claim = _make_claim(proposed_level=2)
        required = SM.WITNESS_MIN_BY_LEVEL[2]
        mock_mst = _make_mst_mock(attestation_count=required)
        mock_pds = _make_pds_mock()

        original_mst, original_pds = SM._mst_mod, SM._pds_mod
        SM._mst_mod, SM._pds_mod = mock_mst, mock_pds
        try:
            result = await SM.evolution_validation_cell(claim)
        finally:
            SM._mst_mod, SM._pds_mod = original_mst, original_pds

        assert isinstance(result, SM.ValidationResult)
        assert isinstance(result.valid, bool)
        assert isinstance(result.attestation_count, int)
        assert isinstance(result.required_count, int)
        assert isinstance(result.reason, str)
        assert len(result.reason) > 0

    @pytest.mark.asyncio
    async def test_threshold_table_per_level(self):
        """Each level (Lv1-5) uses the correct count threshold from WITNESS_MIN_BY_LEVEL.

        Lv6 is tested separately (count + Council gate).
        """
        # Only test Lv1-5 count-based path here; Lv6 has dedicated tests.
        lv1_to_5 = {k: v for k, v in SM.WITNESS_MIN_BY_LEVEL.items() if k <= 5}
        for level, expected_required in lv1_to_5.items():
            claim = _make_claim(proposed_level=level)
            # Provide exactly threshold - 1 (should fail on count).
            mock_mst = _make_mst_mock(attestation_count=expected_required - 1)
            mock_pds = _make_pds_mock()

            original_mst, original_pds = SM._mst_mod, SM._pds_mod
            SM._mst_mod, SM._pds_mod = mock_mst, mock_pds
            try:
                result = await SM.evolution_validation_cell(claim)
            finally:
                SM._mst_mod, SM._pds_mod = original_mst, original_pds

            assert result.valid is False, (
                f"Level {level}: expected valid=False with {expected_required - 1} < {expected_required}"
            )
            assert result.required_count == expected_required, (
                f"Level {level}: required_count should be {expected_required}"
            )

    # ── Lv6 Council eligibility gate tests ────────────────────────────────────

    @pytest.mark.asyncio
    async def test_lv6_fails_insufficient_count(self):
        """Lv6: invalid when attestation count < WITNESS_MIN_BY_LEVEL[6]=9."""
        claim = _make_claim(proposed_level=6)
        required_count = SM.WITNESS_MIN_BY_LEVEL[6]  # 9
        # 8 attestations, 2 of which are Council — count gate fires first.
        mock_mst = _make_mst_mock(attestation_count=required_count - 1, council_count=2)
        mock_pds = _make_pds_mock()

        original_mst, original_pds = SM._mst_mod, SM._pds_mod
        SM._mst_mod, SM._pds_mod = mock_mst, mock_pds
        try:
            result = await SM.evolution_validation_cell(claim)
        finally:
            SM._mst_mod, SM._pds_mod = original_mst, original_pds

        assert result.valid is False
        assert "insufficient witness count" in result.reason.lower()
        assert str(required_count - 1) in result.reason
        assert str(required_count) in result.reason

    @pytest.mark.asyncio
    async def test_lv6_fails_insufficient_council_cosigners(self):
        """Lv6: count OK but Council co-signers < COUNCIL_GATE_LV6=2 → invalid."""
        claim = _make_claim(proposed_level=6)
        required_count = SM.WITNESS_MIN_BY_LEVEL[6]  # 9
        # 9 attestations, only 1 Council co-signer (gate needs 2).
        mock_mst = _make_mst_mock(
            attestation_count=required_count,
            council_count=SM.COUNCIL_GATE_LV6 - 1,  # 1
        )
        mock_pds = _make_pds_mock()

        original_mst, original_pds = SM._mst_mod, SM._pds_mod
        SM._mst_mod, SM._pds_mod = mock_mst, mock_pds
        try:
            result = await SM.evolution_validation_cell(claim)
        finally:
            SM._mst_mod, SM._pds_mod = original_mst, original_pds

        assert result.valid is False
        assert "council lv6" in result.reason.lower() or "co-signer" in result.reason.lower()
        assert "count" in result.reason.lower() and "ok" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_lv6_valid_when_count_and_council_both_meet_threshold(self):
        """Lv6: valid when ≥9 attestations and ≥COUNCIL_GATE_LV6=2 Council co-signers."""
        claim = _make_claim(proposed_level=6)
        required_count = SM.WITNESS_MIN_BY_LEVEL[6]  # 9
        mock_mst = _make_mst_mock(
            attestation_count=required_count,
            council_count=SM.COUNCIL_GATE_LV6,  # exactly 2
        )
        mock_pds = _make_pds_mock()

        original_mst, original_pds = SM._mst_mod, SM._pds_mod
        SM._mst_mod, SM._pds_mod = mock_mst, mock_pds
        try:
            result = await SM.evolution_validation_cell(claim)
        finally:
            SM._mst_mod, SM._pds_mod = original_mst, original_pds

        assert result.valid is True
        assert result.required_count == SM.COUNCIL_GATE_LV6
        assert "valid" in result.reason.lower()
        mock_pds.put_record.assert_awaited_once()

    # ── Lv7 Council supermajority tests ───────────────────────────────────────

    @pytest.mark.asyncio
    async def test_lv7_invalid_with_3_council_votes(self):
        """Lv7: invalid when Council votes < COUNCIL_SUPERMAJORITY_LV7=4."""
        claim = _make_claim(proposed_level=7)
        # 3 Council votes — below supermajority of 4.
        mock_mst = _make_mst_mock(
            attestation_count=9,
            council_count=SM.COUNCIL_SUPERMAJORITY_LV7 - 1,  # 3
        )
        mock_pds = _make_pds_mock()

        original_mst, original_pds = SM._mst_mod, SM._pds_mod
        SM._mst_mod, SM._pds_mod = mock_mst, mock_pds
        try:
            result = await SM.evolution_validation_cell(claim)
        finally:
            SM._mst_mod, SM._pds_mod = original_mst, original_pds

        assert result.valid is False
        assert result.required_count == SM.COUNCIL_SUPERMAJORITY_LV7
        assert "supermajority" in result.reason.lower()
        mock_pds.put_record.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_lv7_valid_with_4_council_votes(self):
        """Lv7: valid when Council votes >= COUNCIL_SUPERMAJORITY_LV7=4 and window closed."""
        import datetime as _dt

        claim = _make_claim(proposed_level=7)
        # Set validated_at to 31 days ago (window closed) so we skip objection checks
        # and go straight to finalized.
        past_time = (
            _dt.datetime.now(tz=_dt.timezone.utc)
            - _dt.timedelta(days=31)
        )
        claim.validated_at = (
            past_time
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

        # 4 Council votes — meets supermajority.
        mock_mst = _make_mst_mock(
            attestation_count=9,
            council_count=SM.COUNCIL_SUPERMAJORITY_LV7,  # 4
        )
        mock_pds = _make_pds_mock()

        original_mst, original_pds = SM._mst_mod, SM._pds_mod
        SM._mst_mod, SM._pds_mod = mock_mst, mock_pds
        try:
            result = await SM.evolution_validation_cell(claim)
        finally:
            SM._mst_mod, SM._pds_mod = original_mst, original_pds

        assert result.valid is True
        assert result.required_count == SM.COUNCIL_SUPERMAJORITY_LV7
        assert "supermajority" in result.reason.lower()
        assert "window closed" in result.reason.lower()
        mock_pds.put_record.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_lv7_within_objection_window_no_objections_pending(self):
        """Lv7 within objection window + no objections → pending status."""
        import datetime as _dt

        claim = _make_claim(proposed_level=7)
        # Set validated_at to now (within window).
        claim.validated_at = (
            _dt.datetime.now(tz=_dt.timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

        # 4 Council votes (supermajority).
        mock_mst = _make_mst_mock(
            attestation_count=9,
            council_count=SM.COUNCIL_SUPERMAJORITY_LV7,
        )
        # Mock council_objections to return empty (no objections filed).
        mock_mst.council_objections = AsyncMock(return_value=[])
        mock_pds = _make_pds_mock()

        original_mst, original_pds = SM._mst_mod, SM._pds_mod
        SM._mst_mod, SM._pds_mod = mock_mst, mock_pds
        try:
            result = await SM.evolution_validation_cell(claim)
        finally:
            SM._mst_mod, SM._pds_mod = original_mst, original_pds

        assert result.valid is False  # Not final until window closes
        assert result.status == "pending"
        assert "objection window" in result.reason.lower()
        assert "until" in result.reason.lower()  # Window close timestamp
        # No put_record on pending (only on final valid).
        mock_pds.put_record.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_lv7_within_objection_window_with_objection_invalid(self):
        """Lv7 within objection window + objection filed → invalid."""
        import datetime as _dt

        claim = _make_claim(proposed_level=7)
        # Set validated_at to now (within window).
        claim.validated_at = (
            _dt.datetime.now(tz=_dt.timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

        # 4 Council votes (supermajority).
        mock_mst = _make_mst_mock(
            attestation_count=9,
            council_count=SM.COUNCIL_SUPERMAJORITY_LV7,
        )
        # Mock council_objections to return 1 objection.
        mock_mst.council_objections = AsyncMock(
            return_value=[
                {
                    "objector_did": "did:web:objector.etzhayyim.com",
                    "filed_at": _dt.datetime.now(tz=_dt.timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z"),
                    "reason": "insufficient-witness-quality",
                    "evidence_cid": None,
                }
            ]
        )
        mock_pds = _make_pds_mock()

        original_mst, original_pds = SM._mst_mod, SM._pds_mod
        SM._mst_mod, SM._pds_mod = mock_mst, mock_pds
        try:
            result = await SM.evolution_validation_cell(claim)
        finally:
            SM._mst_mod, SM._pds_mod = original_mst, original_pds

        assert result.valid is False
        assert result.status == "invalid"
        assert "objected" in result.reason.lower()
        mock_pds.put_record.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_lv7_past_objection_window_no_objections_valid(self):
        """Lv7 past objection window + no objections → valid (finalized)."""
        import datetime as _dt

        claim = _make_claim(proposed_level=7)
        # Set validated_at to 31 days ago (past window).
        past_time = (
            _dt.datetime.now(tz=_dt.timezone.utc)
            - _dt.timedelta(days=31)
        )
        claim.validated_at = (
            past_time
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )

        # 4 Council votes (supermajority).
        mock_mst = _make_mst_mock(
            attestation_count=9,
            council_count=SM.COUNCIL_SUPERMAJORITY_LV7,
        )
        # Mock council_objections (won't be called if window closed, but define it).
        mock_mst.council_objections = AsyncMock(return_value=[])
        mock_pds = _make_pds_mock()

        original_mst, original_pds = SM._mst_mod, SM._pds_mod
        SM._mst_mod, SM._pds_mod = mock_mst, mock_pds
        try:
            result = await SM.evolution_validation_cell(claim)
        finally:
            SM._mst_mod, SM._pds_mod = original_mst, original_pds

        assert result.valid is True
        assert result.status == "valid"
        assert "window closed" in result.reason.lower()
        assert "finalized" in result.reason.lower()
        # Final valid → put_record should be called.
        mock_pds.put_record.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_lv7_supermajority_fails_no_objection_window(self):
        """Lv7: supermajority fails (3 votes) → invalid, no objection window."""
        claim = _make_claim(proposed_level=7)
        # 3 Council votes — below supermajority of 4.
        mock_mst = _make_mst_mock(
            attestation_count=9,
            council_count=SM.COUNCIL_SUPERMAJORITY_LV7 - 1,  # 3
        )
        mock_pds = _make_pds_mock()

        original_mst, original_pds = SM._mst_mod, SM._pds_mod
        SM._mst_mod, SM._pds_mod = mock_mst, mock_pds
        try:
            result = await SM.evolution_validation_cell(claim)
        finally:
            SM._mst_mod, SM._pds_mod = original_mst, original_pds

        assert result.valid is False
        assert result.status == "invalid"
        assert "supermajority failed" in result.reason.lower()
        # No objection window entered because supermajority failed.
        mock_pds.put_record.assert_not_awaited()

    # ── Recency filter test ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_recency_filter_old_attestation_excluded(self):
        """Old attestation (>365 days) is excluded: mock returns empty list."""
        claim = _make_claim(proposed_level=2)
        # Mock returns an empty list (simulating all attestations filtered out
        # because council_attestation_details applies the recency window server-side).
        mock_mst = _make_mst_mock(attestation_count=0)
        mock_pds = _make_pds_mock()

        original_mst, original_pds = SM._mst_mod, SM._pds_mod
        SM._mst_mod, SM._pds_mod = mock_mst, mock_pds
        try:
            result = await SM.evolution_validation_cell(claim)
        finally:
            SM._mst_mod, SM._pds_mod = original_mst, original_pds

        assert result.valid is False
        assert result.attestation_count == 0
        # Confirm since_days=WITNESS_RECENCY_DAYS was passed to details.
        mock_mst.council_attestation_details.assert_awaited_once_with(
            claim.adherent_did,
            claim.proposed_level,
            since_days=SM.WITNESS_RECENCY_DAYS,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# B. EvolutionEmissionCell
# ═══════════════════════════════════════════════════════════════════════════════


class TestEvolutionEmissionCell:
    """Tests for evolution_emission_cell() — M2 implementation."""

    @pytest.mark.asyncio
    async def test_pins_evidence_cids_via_ipfs_pin_many(self):
        """ipfs.pin_many called with all evidence CIDs from the claim."""
        claim = _make_claim(evidence_cids=["bafybeig5ev1", "bafybeig5ev2", "bafybeig5ev3"])
        mock_pds = _make_pds_mock()
        mock_ipfs = _make_ipfs_mock()
        mock_l2 = _make_l2_mock()

        original_pds, original_ipfs, original_l2 = SM._pds_mod, SM._ipfs_mod, SM._l2_mod
        SM._pds_mod, SM._ipfs_mod, SM._l2_mod = mock_pds, mock_ipfs, mock_l2
        try:
            await SM.evolution_emission_cell(claim)
        finally:
            SM._pds_mod, SM._ipfs_mod, SM._l2_mod = original_pds, original_ipfs, original_l2

        mock_ipfs.pin_many.assert_awaited_once()
        pin_args = mock_ipfs.pin_many.call_args.args[0]
        assert "bafybeig5ev1" in pin_args
        assert "bafybeig5ev2" in pin_args
        assert "bafybeig5ev3" in pin_args

    @pytest.mark.asyncio
    async def test_anchors_to_base_l2(self):
        """l2.anchor called with the MST commit CID from pds.put_record."""
        claim = _make_claim()
        commit_cid = "bafymockcommitcid"
        mock_pds = _make_pds_mock(put_record_cid=commit_cid)
        mock_ipfs = _make_ipfs_mock()
        mock_l2 = _make_l2_mock(tx_hash="0xdeadbeef")

        original_pds, original_ipfs, original_l2 = SM._pds_mod, SM._ipfs_mod, SM._l2_mod
        SM._pds_mod, SM._ipfs_mod, SM._l2_mod = mock_pds, mock_ipfs, mock_l2
        try:
            await SM.evolution_emission_cell(claim)
        finally:
            SM._pds_mod, SM._ipfs_mod, SM._l2_mod = original_pds, original_ipfs, original_l2

        mock_l2.anchor.assert_awaited_once_with(commit_cid)

    @pytest.mark.asyncio
    async def test_returns_anchor_tx_hash(self):
        """evolution_emission_cell returns the Base L2 anchor tx hash."""
        claim = _make_claim()
        expected_tx = "0xdeadbeefcafebabe0000000000000000000000000000000000000000000000"
        mock_pds = _make_pds_mock()
        mock_ipfs = _make_ipfs_mock()
        mock_l2 = _make_l2_mock(tx_hash=expected_tx)

        original_pds, original_ipfs, original_l2 = SM._pds_mod, SM._ipfs_mod, SM._l2_mod
        SM._pds_mod, SM._ipfs_mod, SM._l2_mod = mock_pds, mock_ipfs, mock_l2
        try:
            result = await SM.evolution_emission_cell(claim)
        finally:
            SM._pds_mod, SM._ipfs_mod, SM._l2_mod = original_pds, original_ipfs, original_l2

        assert result == expected_tx

    @pytest.mark.asyncio
    async def test_writes_evolution_event_to_mst(self):
        """pds.put_record called with app.etzhayyim.shinka.evolutionEvent."""
        claim = _make_claim(proposed_level=3)
        mock_pds = _make_pds_mock()
        mock_ipfs = _make_ipfs_mock()
        mock_l2 = _make_l2_mock()

        original_pds, original_ipfs, original_l2 = SM._pds_mod, SM._ipfs_mod, SM._l2_mod
        SM._pds_mod, SM._ipfs_mod, SM._l2_mod = mock_pds, mock_ipfs, mock_l2
        try:
            await SM.evolution_emission_cell(claim)
        finally:
            SM._pds_mod, SM._ipfs_mod, SM._l2_mod = original_pds, original_ipfs, original_l2

        mock_pds.put_record.assert_awaited_once()
        call_kwargs = mock_pds.put_record.call_args.kwargs
        assert call_kwargs["collection"] == "app.etzhayyim.shinka.evolutionEvent"
        record = call_kwargs["record"]
        assert record["$type"] == "app.etzhayyim.shinka.evolutionEvent"
        assert record["adherentDid"] == claim.adherent_did
        assert record["newLevel"] == claim.proposed_level
        assert record["claimId"] == claim.claim_id
        # Required lexicon fields must be present
        required_fields = [
            "adherentDid", "previousLevel", "newLevel", "claimId",
            "validatedAt", "evidenceCids", "attestationDids", "l2AnchorTxHash",
        ]
        for field_name in required_fields:
            assert field_name in record, f"Missing required lexicon field: {field_name}"

    @pytest.mark.asyncio
    async def test_raises_if_pin_fails(self):
        """If ipfs.pin_many raises, evolution_emission_cell re-raises (all-or-nothing)."""
        claim = _make_claim(evidence_cids=["bafybeig5bad"])
        mock_pds = _make_pds_mock()
        mock_ipfs = _make_ipfs_mock(fail=True)
        mock_l2 = _make_l2_mock()

        original_pds, original_ipfs, original_l2 = SM._pds_mod, SM._ipfs_mod, SM._l2_mod
        SM._pds_mod, SM._ipfs_mod, SM._l2_mod = mock_pds, mock_ipfs, mock_l2
        try:
            with pytest.raises(RuntimeError, match="IPFS pin failed"):
                await SM.evolution_emission_cell(claim)
        finally:
            SM._pds_mod, SM._ipfs_mod, SM._l2_mod = original_pds, original_ipfs, original_l2

        # l2.anchor must NOT have been called after pin failure
        mock_l2.anchor.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_raises_if_l2_anchor_fails(self):
        """If l2.anchor raises, evolution_emission_cell re-raises (all-or-nothing)."""
        claim = _make_claim()
        mock_pds = _make_pds_mock()
        mock_ipfs = _make_ipfs_mock()
        mock_l2 = _make_l2_mock(fail=True)

        original_pds, original_ipfs, original_l2 = SM._pds_mod, SM._ipfs_mod, SM._l2_mod
        SM._pds_mod, SM._ipfs_mod, SM._l2_mod = mock_pds, mock_ipfs, mock_l2
        try:
            with pytest.raises(RuntimeError, match="L2 anchor failed"):
                await SM.evolution_emission_cell(claim)
        finally:
            SM._pds_mod, SM._ipfs_mod, SM._l2_mod = original_pds, original_ipfs, original_l2

    @pytest.mark.asyncio
    async def test_skips_pin_when_no_evidence_cids(self):
        """ipfs.pin_many is NOT called when claim.evidence_cids is empty."""
        claim = _make_claim(evidence_cids=[])
        mock_pds = _make_pds_mock()
        mock_ipfs = _make_ipfs_mock()
        mock_l2 = _make_l2_mock()

        original_pds, original_ipfs, original_l2 = SM._pds_mod, SM._ipfs_mod, SM._l2_mod
        SM._pds_mod, SM._ipfs_mod, SM._l2_mod = mock_pds, mock_ipfs, mock_l2
        try:
            await SM.evolution_emission_cell(claim)
        finally:
            SM._pds_mod, SM._ipfs_mod, SM._l2_mod = original_pds, original_ipfs, original_l2

        mock_ipfs.pin_many.assert_not_awaited()


# ═══════════════════════════════════════════════════════════════════════════════
# C. shinka_tick orchestration
# ═══════════════════════════════════════════════════════════════════════════════


def _make_full_mocks(
    *,
    attestation_count: int = 5,
    council_count: int = 0,
    anchor_tx: str = "0xabcdef",
    mst_evolution_records: list | None = None,
    mst_kyumei_records: list | None = None,
) -> tuple[MagicMock, MagicMock, MagicMock, MagicMock]:
    """Return (pds_mock, mst_mock, ipfs_mock, l2_mock) wired for shinka_tick."""
    mock_pds = _make_pds_mock()
    mock_mst = MagicMock()
    mock_ipfs = _make_ipfs_mock()
    mock_l2 = _make_l2_mock(tx_hash=anchor_tx)

    async def mock_query(collection: str, **kwargs: Any) -> list[dict]:
        if "evolutionEvent" in collection:
            return mst_evolution_records or []
        if "kyumeiSignal" in collection:
            return mst_kyumei_records or []
        return []

    mock_mst.query = mock_query
    attestation_list = _make_attestation_list(attestation_count, council_count)
    mock_mst.council_attestation_details = AsyncMock(return_value=attestation_list)
    mock_mst.council_attestation_count = AsyncMock(return_value=len(attestation_list))
    return mock_pds, mock_mst, mock_ipfs, mock_l2


class TestShinkaTick:
    """Tests for shinka_tick() orchestration — M2 implementation."""

    @pytest.mark.asyncio
    async def test_end_to_end_with_pending_evolution(self):
        """Full tick: observation → validation → emission → heartbeat (all mocked).

        Tests the happy path where the adherent has a pending evolution claim,
        has sufficient attestations, and emission succeeds.
        """
        adherent_did = "did:web:alice.etzhayyim.com"
        pending_claim = _make_claim(
            claim_id="claim-e2e-001",
            adherent_did=adherent_did,
            proposed_level=2,
            evidence_cids=["bafybeig5alice"],
        )
        anchor_tx = "0xdeadbeef0123"
        required = SM.WITNESS_MIN_BY_LEVEL[2]  # 3

        mock_pds, mock_mst, mock_ipfs, mock_l2 = _make_full_mocks(
            attestation_count=required,
            anchor_tx=anchor_tx,
        )

        original_pds = SM._pds_mod
        original_mst = SM._mst_mod
        original_ipfs = SM._ipfs_mod
        original_l2 = SM._l2_mod
        SM._pds_mod = mock_pds
        SM._mst_mod = mock_mst
        SM._ipfs_mod = mock_ipfs
        SM._l2_mod = mock_l2

        # Patch karma_hegemon_observation_cell to return a state with pending claim
        original_obs_cell = SM.karma_hegemon_observation_cell

        async def mock_observation(did: str) -> SM.AdherentState:
            return SM.AdherentState(
                did=did,
                sbt_token_id=1,
                last_evolution_at="2026-01-01T00:00:00Z",
                mood="neutral",
                last_heartbeat_ms=0,  # triggers all cadence flags
                proposed_evolution=pending_claim,
            )

        SM.karma_hegemon_observation_cell = mock_observation

        try:
            result = await SM.shinka_tick(adherent_did)
        finally:
            SM._pds_mod = original_pds
            SM._mst_mod = original_mst
            SM._ipfs_mod = original_ipfs
            SM._l2_mod = original_l2
            SM.karma_hegemon_observation_cell = original_obs_cell

        assert result["observed"] == 1
        assert result["validated"] == 1
        assert result["emitted"] == 1
        assert result["evolutionWritten"] is True
        assert result["baseLs2AnchorTx"] == anchor_tx
        assert result["heartbeatWritten"] is True
        assert result["errors"] == []
        assert result["adherentDid"] == adherent_did

    @pytest.mark.asyncio
    async def test_no_did_returns_early_with_heartbeat(self):
        """shinka_tick(None) logs intent and returns with heartbeat written."""
        mock_pds = _make_pds_mock()

        original_pds = SM._pds_mod
        SM._pds_mod = mock_pds
        try:
            result = await SM.shinka_tick(None)
        finally:
            SM._pds_mod = original_pds

        assert result["observed"] == 0
        assert result["validated"] == 0
        assert result["emitted"] == 0
        assert result["heartbeatWritten"] is True
        assert result["adherentDid"] is None

    @pytest.mark.asyncio
    async def test_observation_failure_emits_heartbeat_with_error(self):
        """If observation fails, heartbeat is written with error in errors list."""
        adherent_did = "did:web:broken.etzhayyim.com"
        mock_pds = _make_pds_mock()

        original_obs_cell = SM.karma_hegemon_observation_cell
        original_pds = SM._pds_mod

        async def failing_observation(did: str) -> SM.AdherentState:
            raise RuntimeError("MST unreachable")

        SM.karma_hegemon_observation_cell = failing_observation
        SM._pds_mod = mock_pds

        try:
            result = await SM.shinka_tick(adherent_did)
        finally:
            SM.karma_hegemon_observation_cell = original_obs_cell
            SM._pds_mod = original_pds

        assert result["observed"] == 0
        assert result["validated"] == 0
        assert result["emitted"] == 0
        assert len(result["errors"]) > 0
        assert "observation" in result["errors"][0]
        assert result["heartbeatWritten"] is True

    @pytest.mark.asyncio
    async def test_no_emission_when_validation_fails(self):
        """If validation returns valid=False, emission is not called."""
        adherent_did = "did:web:alice.etzhayyim.com"
        pending_claim = _make_claim(
            claim_id="claim-insufficient",
            adherent_did=adherent_did,
            proposed_level=3,
        )
        required = SM.WITNESS_MIN_BY_LEVEL[3]  # 5
        # Return fewer attestations than required
        mock_pds, mock_mst, mock_ipfs, mock_l2 = _make_full_mocks(
            attestation_count=required - 1,
        )

        original_pds = SM._pds_mod
        original_mst = SM._mst_mod
        original_ipfs = SM._ipfs_mod
        original_l2 = SM._l2_mod
        original_obs_cell = SM.karma_hegemon_observation_cell
        SM._pds_mod = mock_pds
        SM._mst_mod = mock_mst
        SM._ipfs_mod = mock_ipfs
        SM._l2_mod = mock_l2

        async def mock_observation(did: str) -> SM.AdherentState:
            return SM.AdherentState(
                did=did,
                sbt_token_id=2,
                last_evolution_at="2026-01-01T00:00:00Z",
                mood="neutral",
                last_heartbeat_ms=0,
                proposed_evolution=pending_claim,
            )

        SM.karma_hegemon_observation_cell = mock_observation

        try:
            result = await SM.shinka_tick(adherent_did)
        finally:
            SM._pds_mod = original_pds
            SM._mst_mod = original_mst
            SM._ipfs_mod = original_ipfs
            SM._l2_mod = original_l2
            SM.karma_hegemon_observation_cell = original_obs_cell

        assert result["validated"] == 1   # validation ran
        assert result["emitted"] == 0     # but no emission
        assert result["evolutionWritten"] is False
        assert result["baseLs2AnchorTx"] == ""
        # l2.anchor must NOT have been called
        mock_l2.anchor.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_heartbeat_written_true_in_output(self):
        """heartbeatWritten key is always True in a successful tick result."""
        mock_pds = _make_pds_mock()

        original_pds = SM._pds_mod
        SM._pds_mod = mock_pds
        try:
            result = await SM.shinka_tick(None)
        finally:
            SM._pds_mod = original_pds

        assert "heartbeatWritten" in result
        assert result["heartbeatWritten"] is True

    @pytest.mark.asyncio
    async def test_evolution_written_false_when_no_pending_claim(self):
        """No pending evolution claim → evolutionWritten=False."""
        adherent_did = "did:web:quiet.etzhayyim.com"
        mock_pds, mock_mst, mock_ipfs, mock_l2 = _make_full_mocks()

        original_pds = SM._pds_mod
        original_mst = SM._mst_mod
        original_ipfs = SM._ipfs_mod
        original_l2 = SM._l2_mod
        original_obs_cell = SM.karma_hegemon_observation_cell
        SM._pds_mod = mock_pds
        SM._mst_mod = mock_mst
        SM._ipfs_mod = mock_ipfs
        SM._l2_mod = mock_l2

        async def mock_observation(did: str) -> SM.AdherentState:
            # No proposed_evolution → heartbeat-only tick
            return SM.AdherentState(
                did=did,
                sbt_token_id=1,
                last_evolution_at="2026-01-01T00:00:00Z",
                mood="neutral",
                last_heartbeat_ms=0,
                proposed_evolution=None,  # no pending claim
            )

        SM.karma_hegemon_observation_cell = mock_observation

        try:
            result = await SM.shinka_tick(adherent_did)
        finally:
            SM._pds_mod = original_pds
            SM._mst_mod = original_mst
            SM._ipfs_mod = original_ipfs
            SM._l2_mod = original_l2
            SM.karma_hegemon_observation_cell = original_obs_cell

        assert result["evolutionWritten"] is False
        assert result["baseLs2AnchorTx"] == ""
        assert result["observed"] == 1


# ═══════════════════════════════════════════════════════════════════════════════
# D. Pure helper tests (_classify_mood, _resolve_cadence)
# ═══════════════════════════════════════════════════════════════════════════════


class TestClassifyMood:
    """Tests for _classify_mood() pure function."""

    def test_stress_ge_70_returns_stressed(self):
        axes = SM.JouchoAxes(joy=80, calm=80, stress=70, gratitude=80, focus=80)
        assert SM._classify_mood(axes) == "stressed"

    def test_joy_ge_60_returns_joyful(self):
        axes = SM.JouchoAxes(joy=60, calm=40, stress=20, gratitude=40, focus=40)
        assert SM._classify_mood(axes) == "joyful"

    def test_calm_ge_60_returns_calm(self):
        axes = SM.JouchoAxes(joy=40, calm=60, stress=20, gratitude=40, focus=40)
        assert SM._classify_mood(axes) == "calm"

    def test_gratitude_ge_60_returns_grateful(self):
        axes = SM.JouchoAxes(joy=40, calm=40, stress=20, gratitude=60, focus=40)
        assert SM._classify_mood(axes) == "grateful"

    def test_focus_ge_60_returns_focused(self):
        axes = SM.JouchoAxes(joy=40, calm=40, stress=20, gratitude=40, focus=60)
        assert SM._classify_mood(axes) == "focused"

    def test_all_below_threshold_returns_neutral(self):
        axes = SM.JouchoAxes(joy=40, calm=40, stress=20, gratitude=30, focus=40)
        assert SM._classify_mood(axes) == "neutral"

    def test_stress_overrides_joy(self):
        """stress≥70 takes priority over joy≥60."""
        axes = SM.JouchoAxes(joy=80, calm=80, stress=70, gratitude=80, focus=80)
        assert SM._classify_mood(axes) == "stressed"


class TestResolveCadence:
    """Tests for _resolve_cadence() pure function."""

    def test_joyful_with_large_elapsed_should_post_true(self):
        """Joyful mood + large elapsed → should_post=True (threshold 30m)."""
        state = SM.AdherentState(
            did="did:web:test.etzhayyim.com",
            sbt_token_id=1,
            last_evolution_at="2026-01-01T00:00:00Z",
            mood="joyful",
            last_heartbeat_ms=0,  # elapsed = now_ms (very large)
        )
        cadence = SM._resolve_cadence(state)
        assert cadence.should_post is True
        assert cadence.should_engage is True
        assert cadence.should_drill is False
        assert cadence.should_validate is False

    def test_stressed_mood_should_post_false(self):
        """Stressed mood → should_post=False regardless of elapsed."""
        state = SM.AdherentState(
            did="did:web:test.etzhayyim.com",
            sbt_token_id=1,
            last_evolution_at="2026-01-01T00:00:00Z",
            mood="stressed",
            last_heartbeat_ms=0,
        )
        cadence = SM._resolve_cadence(state)
        assert cadence.should_post is False
        assert cadence.should_engage is False
        assert cadence.should_drill is True  # drill fires for stressed
        assert cadence.should_validate is True

    def test_new_actor_all_flags_fire(self):
        """New actor (last_heartbeat_ms=0) → all time-based flags fire on first tick."""
        state = SM.AdherentState(
            did="did:web:new.etzhayyim.com",
            sbt_token_id=0,
            last_evolution_at="2026-01-01T00:00:00Z",
            mood="neutral",
            last_heartbeat_ms=0,
        )
        cadence = SM._resolve_cadence(state)
        # Neutral mode: all flags fire with large elapsed
        assert cadence.should_post is True
        assert cadence.should_engage is True
        assert cadence.should_drill is True
        assert cadence.should_validate is True
        assert cadence.should_analyze is True


# ═══════════════════════════════════════════════════════════════════════════════
# E. WITNESS_MIN_BY_LEVEL constant
# ═══════════════════════════════════════════════════════════════════════════════


class TestWitnessMinByLevel:
    """Tests for WITNESS_MIN_BY_LEVEL and Council gate constants (ADR-2605215400)."""

    def test_level_1_requires_2(self):
        assert SM.WITNESS_MIN_BY_LEVEL[1] == 2

    def test_level_3_requires_5(self):
        assert SM.WITNESS_MIN_BY_LEVEL[3] == 5

    def test_council_supermajority_lv7_is_4(self):
        """Lv7 gate is COUNCIL_SUPERMAJORITY_LV7=4 (≥4 of 5 Council votes)."""
        assert SM.COUNCIL_SUPERMAJORITY_LV7 == 4

    def test_council_gate_lv6_is_2(self):
        """Lv6 eligibility gate requires ≥COUNCIL_GATE_LV6=2 Council Lv6+ co-signers."""
        assert SM.COUNCIL_GATE_LV6 == 2

    def test_all_values_are_positive_integers(self):
        for level, count in SM.WITNESS_MIN_BY_LEVEL.items():
            assert isinstance(count, int), f"Level {level}: expected int, got {type(count)}"
            assert count > 0, f"Level {level}: count must be positive"

    def test_counts_are_monotonically_increasing(self):
        """Higher levels require more witnesses (monotone invariant)."""
        levels = sorted(SM.WITNESS_MIN_BY_LEVEL.keys())
        counts = [SM.WITNESS_MIN_BY_LEVEL[l] for l in levels]
        for i in range(1, len(counts)):
            assert counts[i] >= counts[i - 1], (
                f"Level {levels[i]} count {counts[i]} should be ≥ level {levels[i-1]} count {counts[i-1]}"
            )
