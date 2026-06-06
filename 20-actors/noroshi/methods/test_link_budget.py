"""Tests for the noroshi optical link-budget core (ADR-2606051600). Stdlib + pytest only."""

from __future__ import annotations

import math

import pytest

from link_budget import (
    CPO_REFERENCE,
    PLUGGABLE_REFERENCE,
    LinkDesign,
    apd_sensitivity_dbm,
    compute,
    excess_noise_factor,
    q_factor_for_ber,
    receiver_sensitivity_dbm,
    report,
    with_ber_sensitivity,
)


def test_cpo_reference_link_closes_with_margin():
    b = compute(CPO_REFERENCE)
    assert b.closes
    assert b.margin_db > 0.0


def test_total_loss_is_sum_of_components():
    b = compute(CPO_REFERENCE)
    assert b.total_loss_db == pytest.approx(sum(b.breakdown.values()), abs=1e-6)


def test_received_power_is_launch_minus_loss():
    d = CPO_REFERENCE
    b = compute(d)
    assert b.received_dbm == pytest.approx(d.laser_power_dbm - b.total_loss_db, abs=1e-6)


def test_fibre_loss_scales_with_distance():
    short = compute(LinkDesign(name="s", fibre_m=1000.0))
    long = compute(LinkDesign(name="l", fibre_m=10000.0))
    assert long.breakdown["fibre"] > short.breakdown["fibre"]
    # 9 km extra @0.35 dB/km = 3.15 dB more loss.
    assert long.breakdown["fibre"] - short.breakdown["fibre"] == pytest.approx(9.0 * 0.35, abs=1e-6)


def test_long_span_eventually_fails_to_close():
    # A 200 km span at 0.35 dB/km adds 70 dB — far past the receiver sensitivity.
    b = compute(LinkDesign(name="too-long", fibre_m=200_000.0))
    assert not b.closes
    assert b.margin_db < 0.0


def test_cpo_beats_pluggable_on_energy_per_bit():
    cpo = compute(CPO_REFERENCE)
    plug = compute(PLUGGABLE_REFERENCE)
    assert cpo.energy_pj_per_bit < plug.energy_pj_per_bit


def test_zero_line_rate_rejected():
    with pytest.raises(ValueError):
        compute(LinkDesign(name="bad", line_rate_gbps=0.0))


def test_photocurrent_positive_and_finite():
    b = compute(CPO_REFERENCE)
    assert b.received_current_ua > 0.0
    assert math.isfinite(b.received_current_ua)


def test_report_renders_both_designs_and_advantage():
    txt = report()
    assert "cpo-2km-100g" in txt
    assert "pluggable-2km-100g" in txt
    assert "CPO energy advantage" in txt


# ── coverage: breakdown, closes/margin consistency, energy components ─────────
def test_breakdown_has_all_six_loss_components():
    b = compute(CPO_REFERENCE)
    assert set(b.breakdown) == {
        "modulator_il", "tx_grating_coupler", "rx_grating_coupler",
        "waveguide", "fibre", "connector",
    }


def test_closes_is_consistent_with_margin_sign():
    for d in (CPO_REFERENCE, PLUGGABLE_REFERENCE, LinkDesign(name="x", fibre_m=200_000.0)):
        b = compute(d)
        assert b.closes == (b.margin_db >= 0.0)


def test_energy_per_bit_includes_tx_rx_and_laser():
    # energy/bit must exceed the bare tx+rx electrical (laser wall-plug adds a positive term).
    b = compute(CPO_REFERENCE)
    assert b.energy_pj_per_bit > CPO_REFERENCE.tx_energy_pj_per_bit + CPO_REFERENCE.rx_energy_pj_per_bit


def test_higher_line_rate_lowers_laser_energy_per_bit():
    slow = compute(LinkDesign(name="slow", line_rate_gbps=50.0))
    fast = compute(LinkDesign(name="fast", line_rate_gbps=400.0))
    assert fast.energy_pj_per_bit < slow.energy_pj_per_bit  # laser cost amortised over more bits


# ── BER → receiver sensitivity model ─────────────────────────────────────────
def test_q_factor_matches_textbook_values():
    assert q_factor_for_ber(1e-9) == pytest.approx(6.0, abs=0.05)
    assert q_factor_for_ber(1e-12) == pytest.approx(7.03, abs=0.05)
    assert q_factor_for_ber(1e-3) == pytest.approx(3.09, abs=0.05)


def test_q_factor_monotone_in_ber():
    assert q_factor_for_ber(1e-12) > q_factor_for_ber(1e-9) > q_factor_for_ber(1e-3)


@pytest.mark.parametrize("bad", [0.0, -1e-9, 0.5, 0.9, 1.0])
def test_q_factor_rejects_out_of_range_ber(bad):
    with pytest.raises(ValueError):
        q_factor_for_ber(bad)


def test_stricter_ber_needs_more_power_higher_sensitivity_dbm():
    loose = receiver_sensitivity_dbm(1e-3, 106.25)
    strict = receiver_sensitivity_dbm(1e-12, 106.25)
    assert strict > loose  # less negative ⇒ needs more received power


def test_higher_line_rate_worsens_sensitivity():
    s_slow = receiver_sensitivity_dbm(1e-12, 25.0)
    s_fast = receiver_sensitivity_dbm(1e-12, 400.0)
    assert s_fast > s_slow  # more noise bandwidth ⇒ higher (worse) sensitivity


def test_sensitivity_rejects_non_positive_line_rate():
    with pytest.raises(ValueError):
        receiver_sensitivity_dbm(1e-12, 0.0)


def test_with_ber_sensitivity_sets_field_and_cpo_still_closes():
    d = with_ber_sensitivity(CPO_REFERENCE, 1e-12)
    assert d.rx_sensitivity_dbm == pytest.approx(receiver_sensitivity_dbm(1e-12, d.line_rate_gbps), abs=1e-3)
    assert compute(d).closes


# ── APD receiver: avalanche gain vs excess noise ─────────────────────────────
def test_excess_noise_factor_is_unity_at_unity_gain():
    for k in (0.0, 0.3, 0.5, 1.0):
        assert excess_noise_factor(1.0, k) == pytest.approx(1.0)


def test_excess_noise_factor_grows_with_gain_and_k():
    assert excess_noise_factor(20, 0.3) > excess_noise_factor(5, 0.3)
    assert excess_noise_factor(10, 0.5) > excess_noise_factor(10, 0.1)


def test_excess_noise_factor_k_zero_closed_form():
    assert excess_noise_factor(10, 0.0) == pytest.approx(2 - 1 / 10)


@pytest.mark.parametrize("m,k", [(0.5, 0.3), (10, -0.1), (10, 1.1)])
def test_excess_noise_factor_rejects_bad_inputs(m, k):
    with pytest.raises(ValueError):
        excess_noise_factor(m, k)


def test_apd_is_more_sensitive_than_pin():
    pin = receiver_sensitivity_dbm(1e-12, 106.25)
    apd = apd_sensitivity_dbm(1e-12, 106.25, gain_m=10, k_eff=0.3)
    assert apd < pin  # more negative dBm ⇒ more sensitive


def test_apd_reduces_to_pin_at_unity_gain():
    pin = receiver_sensitivity_dbm(1e-12, 106.25)
    apd = apd_sensitivity_dbm(1e-12, 106.25, gain_m=1.0)
    assert apd == pytest.approx(pin, abs=1e-9)


def test_apd_higher_excess_noise_gives_less_improvement():
    low_k = apd_sensitivity_dbm(1e-12, 106.25, gain_m=10, k_eff=0.1)
    high_k = apd_sensitivity_dbm(1e-12, 106.25, gain_m=10, k_eff=0.5)
    assert high_k > low_k  # worse material (more excess noise) ⇒ less sensitive
