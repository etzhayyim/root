"""Tests for the noroshi fibre-optic loop core — lay → align → splice (ADR-2606051600).

Stdlib + pytest only. Reuses the EXISTING noroshi aligner (active_alignment.align) and the shared
infra-robotics substrate; nothing here re-implements Hooke-Jeeves or the laser-safety gate.
"""

from __future__ import annotations

import pytest

from active_alignment import CouplerModel, LaserSafetyError, LaserSpec
from fibre_loop import (
    SPLICE_LOSS_MAX_DB,
    CableLayPlant,
    FibreSegmentResult,
    SpliceResult,
    lay_align_splice,
    lay_segment,
    splice,
    splice_loss_db,
    to_datoms,
)
from _substrate import SafetyError


# ── LAY: cross-track tracking converges ──────────────────────────────────────
def test_lay_converges_to_route():
    res = lay_segment(route_xte0=2.0)
    assert res.track_converged
    assert abs(res.final_xte_m) < 1e-2          # driven onto the planned route
    assert res.settling_seconds > 0


def test_lay_rejects_drift_to_zero_steady_state():
    # A non-zero constant drift must be integrated out by the PI term (no offset).
    res = lay_segment(route_xte0=-3.0, drift=0.2)
    assert res.track_converged
    assert abs(res.final_xte_m) < 1e-2


def test_lay_plant_is_a_plant():
    p = CableLayPlant(e=1.0)
    assert p.measure() == 1.0
    p.step(command=-1.0, dt=0.1)               # negative steering reduces +e
    assert p.measure() < 1.0


def test_lay_non_civilian_use_raises():
    with pytest.raises(SafetyError):
        lay_segment(route_xte0=1.0, use="weapon")


# ── SPLICE: loss model + acceptance ──────────────────────────────────────────
def test_splice_loss_grows_with_offset():
    assert splice_loss_db(0.0, 0.0) < splice_loss_db(2.0, 0.0) < splice_loss_db(5.0, 0.0)


def test_splice_loss_grows_with_cleave_angle():
    assert splice_loss_db(0.0, 0.0) < splice_loss_db(0.0, 1.0) < splice_loss_db(0.0, 3.0)


def test_splice_loss_is_quadratic_in_offset():
    # Doubling the lateral offset quadruples the offset-loss contribution.
    l1 = splice_loss_db(1.0, 0.0)
    l2 = splice_loss_db(2.0, 0.0)
    assert l2 == pytest.approx(4.0 * l1, rel=1e-6)


def test_splice_loss_uses_magnitude():
    assert splice_loss_db(-2.0, -1.0) == splice_loss_db(2.0, 1.0)


def test_splice_passes_when_well_aligned():
    res = splice(lateral_offset_um=0.4, cleave_angle_deg=0.3)
    assert isinstance(res, SpliceResult)
    assert res.loss_db <= SPLICE_LOSS_MAX_DB
    assert res.passed


def test_splice_fails_when_offset_large():
    res = splice(lateral_offset_um=12.0, cleave_angle_deg=0.0)
    assert res.loss_db > SPLICE_LOSS_MAX_DB
    assert not res.passed


# ── laser-safety inherited from the REUSED aligner (G5 / N1) ─────────────────
def test_weapon_laser_use_cannot_be_energised_in_the_loop():
    # The loop calls the existing align()/enable_laser() gate; a weapon use raises before any probe.
    with pytest.raises(LaserSafetyError):
        lay_align_splice(
            route_xte0=2.0,
            member_sig="m:ed25519:demo",
            witness_sigs=["did:web:robot-a", "did:web:robot-b"],
            laser=LaserSpec(use="weapon"),
        )


def test_hazardous_laser_without_interlock_refused_in_the_loop():
    with pytest.raises(LaserSafetyError):
        lay_align_splice(
            route_xte0=2.0,
            member_sig="m:ed25519:demo",
            witness_sigs=["did:web:robot-a", "did:web:robot-b"],
            laser=LaserSpec(laser_class="4", use="alignment", enclosure_interlock=False),
        )


# ── G7 no-server-key gate ────────────────────────────────────────────────────
def test_server_signature_refused():
    with pytest.raises(SafetyError):
        lay_align_splice(
            route_xte0=2.0,
            member_sig="m:ed25519:demo",
            witness_sigs=["did:web:robot-a", "did:web:robot-b"],
            server_sig="s:platform:sig",
        )


def test_missing_member_signature_refused():
    with pytest.raises(SafetyError):
        lay_align_splice(
            route_xte0=2.0,
            member_sig="",
            witness_sigs=["did:web:robot-a", "did:web:robot-b"],
        )


# ── N1 civilian-use gate on the composed loop ────────────────────────────────
def test_non_civilian_use_raises_on_full_loop():
    with pytest.raises(SafetyError):
        lay_align_splice(
            route_xte0=2.0,
            member_sig="m:ed25519:demo",
            witness_sigs=["did:web:robot-a", "did:web:robot-b"],
            use="fire-control",
        )


# ── full happy path ──────────────────────────────────────────────────────────
def test_full_lay_align_splice_happy_path():
    seg = lay_align_splice(
        route_xte0=2.0,
        member_sig="m:ed25519:demo",
        witness_sigs=["did:web:robot-a", "did:web:robot-b"],
    )
    assert isinstance(seg, FibreSegmentResult)
    assert seg.track_converged
    assert seg.align_converged
    assert seg.splice_passed
    assert seg.witness_ok
    assert seg.overall_ok is True
    assert seg.server_held_key is False    # G7
    assert seg.dry_run is True             # G8
    assert seg.representative is True       # G10
    assert seg.coupling_loss_db > 0.0


def test_overall_not_ok_when_witness_quorum_fails():
    seg = lay_align_splice(
        route_xte0=2.0,
        member_sig="m:ed25519:demo",
        witness_sigs=["did:web:robot-a"],   # quorum < 2 (G8)
    )
    assert seg.witness_ok is False
    assert seg.overall_ok is False


def test_overall_not_ok_when_splice_fails():
    seg = lay_align_splice(
        route_xte0=2.0,
        member_sig="m:ed25519:demo",
        witness_sigs=["did:web:robot-a", "did:web:robot-b"],
        splice_offset_um=15.0,              # forces splice loss over threshold
    )
    assert seg.splice_passed is False
    assert seg.overall_ok is False


# ── datom projection ─────────────────────────────────────────────────────────
def test_to_datoms_carries_charter_invariants():
    seg = lay_align_splice(
        route_xte0=2.0,
        member_sig="m:ed25519:demo",
        witness_sigs=["did:web:robot-a", "did:web:robot-b"],
    )
    d = to_datoms(seg, "fibre-seg-001")
    assert d[":fibre.segment/id"] == "fibre-seg-001"
    assert d[":fibre.segment/server-held-key"] is False   # G7
    assert d[":fibre.segment/dry-run"] is True            # G8
    assert d[":fibre.segment/representative"] is True      # G10
    assert d[":fibre.segment/overall-ok"] is True
