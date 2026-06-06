"""Tests for the noroshi active-alignment + laser-safety core (ADR-2606051600). Stdlib + pytest only."""

from __future__ import annotations

import pytest

from active_alignment import (
    CouplerModel,
    LaserSafetyError,
    LaserSpec,
    align,
    enable_laser,
    report,
)


# ── laser-safety interlock (the safety-critical gate) ────────────────────────
def test_class1_civilian_use_energises():
    enable_laser(LaserSpec(laser_class="1", use="alignment"))  # no raise


@pytest.mark.parametrize("use", ["weapon", "directed-energy", "dazzle", "fire-control"])
def test_weaponisation_uses_are_unrepresentable(use):
    with pytest.raises(LaserSafetyError):
        enable_laser(LaserSpec(laser_class="1", use=use))


def test_unknown_use_refused():
    with pytest.raises(LaserSafetyError):
        enable_laser(LaserSpec(laser_class="1", use="mystery"))


def test_hazardous_class_without_interlock_refused():
    with pytest.raises(LaserSafetyError):
        enable_laser(LaserSpec(laser_class="4", use="soldering", enclosure_interlock=False))


def test_hazardous_class_with_interlock_but_no_attestation_refused():
    with pytest.raises(LaserSafetyError):
        enable_laser(LaserSpec(laser_class="3B", use="trimming", enclosure_interlock=True))


def test_hazardous_class_fully_attested_energises():
    enable_laser(LaserSpec(
        laser_class="4", use="soldering",
        enclosure_interlock=True, safety_attestation_ref="attest:noroshi-lsm-001",
    ))  # no raise


# ── active alignment converges to the unknown peak ───────────────────────────
def test_align_finds_true_peak():
    model = CouplerModel(opt_x_um=2.3, opt_y_um=-1.7)
    res = align(model, LaserSpec())
    assert res.converged
    assert res.x_um == pytest.approx(model.opt_x_um, abs=0.1)
    assert res.y_um == pytest.approx(model.opt_y_um, abs=0.1)


def test_aligned_coupling_near_peak_efficiency():
    model = CouplerModel(peak_efficiency=0.80)
    res = align(model, LaserSpec())
    assert res.efficiency == pytest.approx(0.80, abs=0.01)
    assert res.loss_db < 1.0  # < 1 dB insertion loss at the peak


def test_align_refuses_before_probing_when_use_forbidden():
    with pytest.raises(LaserSafetyError):
        align(CouplerModel(), LaserSpec(use="weapon"))


def test_align_handles_offset_peak_far_from_start():
    model = CouplerModel(opt_x_um=-6.0, opt_y_um=5.5, mode_radius_um=6.0)
    res = align(model, LaserSpec(), start_x_um=0.0, start_y_um=0.0)
    assert res.x_um == pytest.approx(-6.0, abs=0.15)
    assert res.y_um == pytest.approx(5.5, abs=0.15)


def test_align_budget_exhaustion_is_bounded_and_flagged():
    # A tiny probe budget cannot converge → terminates, not-converged, within the budget.
    model = CouplerModel(opt_x_um=8.0, opt_y_um=-8.0)
    res = align(model, LaserSpec(), step_um=4.0, tol_um=1e-6, max_probes=12)
    # Termination is bounded: a started iteration may add up to 4 probes after the budget check.
    assert res.probes <= 12 + 4
    assert res.converged is False


def test_loss_db_is_monotonic_in_efficiency():
    assert CouplerModel.loss_db(0.9) < CouplerModel.loss_db(0.5) < CouplerModel.loss_db(0.1)


def test_loss_db_handles_zero_efficiency_without_crash():
    import math
    v = CouplerModel.loss_db(0.0)
    assert math.isfinite(v) and v > 100.0  # clamped, large, finite


# ── two-stage coarse acquisition + fine refinement ───────────────────────────
def test_two_stage_acquires_a_far_narrow_peak_that_single_stage_misses():
    from active_alignment import align, align_two_stage
    model = CouplerModel(opt_x_um=60.0, opt_y_um=-50.0, mode_radius_um=2.0)
    single = align(model, LaserSpec())
    assert single.efficiency < 0.01          # gradient underflow → single-stage stalls at origin
    two = align_two_stage(model, LaserSpec())
    assert two.converged
    assert two.efficiency == pytest.approx(model.peak_efficiency, abs=0.01)
    assert two.x_um == pytest.approx(60.0, abs=0.1) and two.y_um == pytest.approx(-50.0, abs=0.1)


def test_coarse_scan_lands_inside_the_lobe():
    from active_alignment import coarse_scan
    model = CouplerModel(opt_x_um=30.0, opt_y_um=20.0, mode_radius_um=3.0)
    x, y, eff, probes = coarse_scan(model, LaserSpec(), span_um=40.0)
    assert eff > 0.0                          # acquired some coupling
    assert probes > 1


def test_coarse_scan_respects_laser_safety_before_probing():
    from active_alignment import coarse_scan
    with pytest.raises(LaserSafetyError):
        coarse_scan(CouplerModel(), LaserSpec(use="weapon"))


def test_coarse_scan_rejects_non_positive_span_or_step():
    from active_alignment import coarse_scan
    with pytest.raises(ValueError):
        coarse_scan(CouplerModel(), LaserSpec(), span_um=0.0)
    with pytest.raises(ValueError):
        coarse_scan(CouplerModel(), LaserSpec(), step_um=-1.0)


def test_two_stage_still_converges_on_an_easy_peak():
    from active_alignment import align_two_stage
    model = CouplerModel(opt_x_um=2.3, opt_y_um=-1.7)
    res = align_two_stage(model, LaserSpec())
    assert res.converged
    assert res.efficiency == pytest.approx(model.peak_efficiency, abs=0.01)


# ── spiral acquisition (expanding-square, early-stop) ────────────────────────
def test_spiral_uses_far_fewer_probes_than_raster():
    from active_alignment import coarse_scan, spiral_search
    model = CouplerModel(opt_x_um=10.0, opt_y_um=8.0, mode_radius_um=3.0)
    _, _, _, sp = spiral_search(model, LaserSpec())
    _, _, _, rp = coarse_scan(model, LaserSpec())
    assert sp < rp                            # early-stop on first signal beats exhaustive raster


def test_spiral_respects_laser_safety():
    from active_alignment import spiral_search
    with pytest.raises(LaserSafetyError):
        spiral_search(CouplerModel(), LaserSpec(use="weapon"))


def test_spiral_rejects_non_positive_span_or_step():
    from active_alignment import spiral_search
    with pytest.raises(ValueError):
        spiral_search(CouplerModel(), LaserSpec(), span_um=-1.0)
    with pytest.raises(ValueError):
        spiral_search(CouplerModel(), LaserSpec(), step_um=0.0)


def test_two_stage_spiral_converges_with_fewer_probes_than_raster():
    from active_alignment import align_two_stage
    model = CouplerModel(opt_x_um=10.0, opt_y_um=8.0, mode_radius_um=3.0)
    spiral = align_two_stage(model, LaserSpec(), acquire="spiral")
    raster = align_two_stage(model, LaserSpec(), acquire="raster")
    assert spiral.converged
    assert spiral.efficiency == pytest.approx(model.peak_efficiency, abs=0.01)
    assert spiral.probes < raster.probes


def test_two_stage_spiral_still_acquires_a_far_narrow_peak():
    from active_alignment import align_two_stage
    model = CouplerModel(opt_x_um=60.0, opt_y_um=-50.0, mode_radius_um=2.0)
    res = align_two_stage(model, LaserSpec(), acquire="spiral")
    assert res.converged
    assert res.efficiency == pytest.approx(model.peak_efficiency, abs=0.01)


def test_align_two_stage_rejects_bad_acquire_mode():
    from active_alignment import align_two_stage
    with pytest.raises(ValueError):
        align_two_stage(CouplerModel(), LaserSpec(), acquire="zigzag")


def test_report_renders():
    txt = report()
    assert "active alignment" in txt
    assert "IEC 60825" in txt
