"""Tests for the noroshi ISAC/JCAS simulator (ADR-2606051600). Stdlib + pytest only."""

from __future__ import annotations

import pytest

from isac_sim import (
    C_LIGHT,
    IsacWaveform,
    Target,
    estimate_target,
    jcas_operating_point,
    report,
)

WF = IsacWaveform()


# ── waveform formulas ────────────────────────────────────────────────────────
def test_range_resolution_formula():
    assert WF.range_resolution_m == pytest.approx(C_LIGHT / (2 * WF.bandwidth_hz), rel=1e-12)


def test_velocity_resolution_formula():
    assert WF.velocity_resolution_mps == pytest.approx(
        WF.wavelength_m / (2 * WF.n_sym * WF.symbol_s), rel=1e-12
    )


# ── sensing recovery: target on exact bins is recovered exactly ──────────────
@pytest.mark.parametrize("k,l", [(4, 3), (10, 1), (1, 7), (20, 5)])
def test_target_on_bin_is_recovered(k, l):
    tgt = Target(range_m=k * WF.range_resolution_m, velocity_mps=l * WF.velocity_resolution_mps)
    est = estimate_target(WF, tgt)
    assert est.range_bin == k
    assert est.doppler_bin == l
    assert est.range_m == pytest.approx(tgt.range_m, rel=1e-6)
    assert est.velocity_mps == pytest.approx(tgt.velocity_mps, rel=1e-6)


def test_off_bin_target_recovered_within_one_resolution_cell():
    tgt = Target(range_m=4.4 * WF.range_resolution_m, velocity_mps=2.6 * WF.velocity_resolution_mps)
    est = estimate_target(WF, tgt)
    assert abs(est.range_m - tgt.range_m) <= WF.range_resolution_m
    assert abs(est.velocity_mps - tgt.velocity_mps) <= WF.velocity_resolution_mps


# ── JCAS power-split tradeoff ────────────────────────────────────────────────
def test_more_comms_power_raises_capacity():
    lo = jcas_operating_point(WF, 0.2)
    hi = jcas_operating_point(WF, 0.8)
    assert hi.capacity_gbps > lo.capacity_gbps


def test_more_comms_power_worsens_sensing_precision():
    # As ρ→1, less power for sensing ⇒ larger (worse) CRLB std.
    lo = jcas_operating_point(WF, 0.2)
    hi = jcas_operating_point(WF, 0.8)
    assert hi.range_std_m > lo.range_std_m
    assert hi.velocity_std_mps > lo.velocity_std_mps


def test_power_split_out_of_range_rejected():
    with pytest.raises(ValueError):
        jcas_operating_point(WF, 1.5)
    with pytest.raises(ValueError):
        jcas_operating_point(WF, -0.1)


def test_report_renders():
    txt = report()
    assert "ISAC" in txt
    assert "JCAS power-split tradeoff" in txt
    assert "never a person" in txt


def test_report_includes_pd_detection_curve():
    txt = report()
    assert "CA-CFAR detection probability" in txt
    assert "| noise σ | Pd |" in txt


# ── coverage: formulas, symbols, validation, edge cases ──────────────────────
def test_max_unambiguous_range_formula():
    assert WF.max_unambiguous_range_m == pytest.approx(C_LIGHT / (2 * WF.subcarrier_hz), rel=1e-12)


def test_qpsk_symbols_are_unit_magnitude():
    from isac_sim import _qpsk_symbol
    for n in range(8):
        for m in range(8):
            assert abs(_qpsk_symbol(n, m)) == pytest.approx(1.0, abs=1e-12)


def test_jcas_capacity_matches_shannon_closed_form():
    import math
    op = jcas_operating_point(WF, 0.5, tx_power_w=1.0, channel_gain_db=-90.0, noise_psd_dbm_hz=-174.0)
    b = WF.bandwidth_hz
    noise_w = 10 ** ((-174.0 - 30) / 10) * b
    snr = 0.5 * 1.0 * 10 ** (-90.0 / 10) / noise_w
    assert op.capacity_gbps == pytest.approx(b * math.log2(1 + snr) / 1e9, rel=1e-9)


@pytest.mark.parametrize("bad", [
    IsacWaveform(n_sub=0), IsacWaveform(n_sym=0),
    IsacWaveform(subcarrier_hz=0.0), IsacWaveform(symbol_s=-1.0),
])
def test_degenerate_waveform_rejected(bad):
    with pytest.raises(ValueError):
        estimate_target(bad, Target(range_m=10.0, velocity_mps=0.0))
    with pytest.raises(ValueError):
        jcas_operating_point(bad, 0.5)


def test_zero_rcs_target_still_returns_an_estimate():
    # α=0 → flat grid; a peak bin is still selected (no crash), magnitude ~0.
    est = estimate_target(WF, Target(range_m=4 * WF.range_resolution_m, velocity_mps=0.0, rcs=0.0))
    assert est.peak_magnitude == pytest.approx(0.0, abs=1e-6)


def test_stationary_target_lands_on_zero_doppler_bin():
    est = estimate_target(WF, Target(range_m=6 * WF.range_resolution_m, velocity_mps=0.0))
    assert est.doppler_bin == 0
    assert est.velocity_mps == pytest.approx(0.0, abs=1e-9)


# ── multi-target sensing (CLEAN extraction; matures N4) ──────────────────────
def test_estimate_targets_recovers_all_well_separated_targets():
    from isac_sim import estimate_targets
    tg = [
        Target(range_m=4 * WF.range_resolution_m, velocity_mps=2 * WF.velocity_resolution_mps),
        Target(range_m=12 * WF.range_resolution_m, velocity_mps=5 * WF.velocity_resolution_mps),
        Target(range_m=20 * WF.range_resolution_m, velocity_mps=1 * WF.velocity_resolution_mps),
    ]
    bins = {(e.range_bin, e.doppler_bin) for e in estimate_targets(WF, tg)}
    assert bins == {(4, 2), (12, 5), (20, 1)}


def test_estimate_targets_single_matches_estimate_target():
    from isac_sim import estimate_targets
    t = Target(range_m=7 * WF.range_resolution_m, velocity_mps=3 * WF.velocity_resolution_mps)
    multi = estimate_targets(WF, [t])[0]
    single = estimate_target(WF, t)
    assert (multi.range_bin, multi.doppler_bin) == (single.range_bin, single.doppler_bin)


def test_estimate_targets_empty_list_returns_empty():
    from isac_sim import estimate_targets
    assert estimate_targets(WF, []) == []


def test_estimate_targets_top_n_caps_results():
    from isac_sim import estimate_targets
    tg = [Target(range_m=(4 + 6 * i) * WF.range_resolution_m,
                 velocity_mps=2 * WF.velocity_resolution_mps) for i in range(3)]
    assert len(estimate_targets(WF, tg, top_n=2)) == 2


def test_estimate_targets_guard_prevents_double_detection():
    # one target, ask for 2 peaks: the guard cell suppresses its own neighbourhood, so the second
    # pick cannot be the same bin.
    from isac_sim import estimate_targets
    t = Target(range_m=10 * WF.range_resolution_m, velocity_mps=4 * WF.velocity_resolution_mps)
    picks = estimate_targets(WF, [t], top_n=2)
    assert len({(p.range_bin, p.doppler_bin) for p in picks}) == 2

    from isac_sim import _validate_waveform  # validation still applies to the multi path
    with pytest.raises(ValueError):
        estimate_targets(IsacWaveform(n_sub=0), [t])


# ── CFAR detection in noise (deterministic, seeded) ──────────────────────────
def _two_targets():
    return [
        Target(range_m=4 * WF.range_resolution_m, velocity_mps=2 * WF.velocity_resolution_mps),
        Target(range_m=14 * WF.range_resolution_m, velocity_mps=5 * WF.velocity_resolution_mps),
    ]


def test_cfar_noiseless_detects_exactly_the_true_targets():
    from isac_sim import detect_cfar
    bins = {(e.range_bin, e.doppler_bin) for e in detect_cfar(WF, _two_targets(), noise_sigma=0.0)}
    assert bins == {(4, 2), (14, 5)}


def test_cfar_detects_true_targets_under_noise():
    from isac_sim import detect_cfar
    dets = detect_cfar(WF, _two_targets(), noise_sigma=0.3, threshold_factor=4.0, seed=1)
    bins = {(e.range_bin, e.doppler_bin) for e in dets}
    assert {(4, 2), (14, 5)} <= bins


def test_cfar_is_reproducible_for_a_given_seed():
    from isac_sim import detect_cfar
    a = detect_cfar(WF, _two_targets(), noise_sigma=0.5, threshold_factor=4.0, seed=7)
    b = detect_cfar(WF, _two_targets(), noise_sigma=0.5, threshold_factor=4.0, seed=7)
    assert [(e.range_bin, e.doppler_bin) for e in a] == [(e.range_bin, e.doppler_bin) for e in b]


def test_cfar_higher_threshold_controls_false_alarms():
    from isac_sim import detect_cfar
    loose = detect_cfar(WF, _two_targets(), noise_sigma=1.0, threshold_factor=2.0, seed=3)
    strict = detect_cfar(WF, _two_targets(), noise_sigma=1.0, threshold_factor=10.0, seed=3)
    assert len(strict) <= len(loose)
    assert len(strict) <= 2 + 1  # at the high threshold, essentially only the true targets survive


def test_cfar_empty_and_noiseless_returns_no_detections():
    from isac_sim import detect_cfar
    assert detect_cfar(WF, [], noise_sigma=0.0) == []


@pytest.mark.parametrize("sigma,factor", [(-0.1, 4.0), (0.3, 0.0), (0.3, -1.0)])
def test_cfar_rejects_bad_parameters(sigma, factor):
    from isac_sim import detect_cfar
    with pytest.raises(ValueError):
        detect_cfar(WF, _two_targets(), noise_sigma=sigma, threshold_factor=factor)


# ── Pd vs SNR detector characterisation (small waveform for speed) ───────────
_SWF = IsacWaveform(n_sub=16, n_sym=8)
_STGT = Target(range_m=4 * _SWF.range_resolution_m, velocity_mps=2 * _SWF.velocity_resolution_mps)


def test_pd_is_one_at_low_noise():
    from isac_sim import detection_probability
    assert detection_probability(_SWF, _STGT, noise_sigma=0.0, trials=8) == 1.0


def test_pd_degrades_at_high_noise():
    from isac_sim import detection_probability
    assert detection_probability(_SWF, _STGT, noise_sigma=6.0, trials=8) < 1.0


def test_pd_vs_snr_is_monotone_non_increasing():
    from isac_sim import pd_vs_snr
    curve = pd_vs_snr(_SWF, _STGT, sigmas=[0.0, 1.0, 3.0, 6.0], trials=8)
    pds = [pd for _, pd in curve]
    assert all(pds[i] >= pds[i + 1] for i in range(len(pds) - 1))
    assert pds[0] == 1.0 and pds[-1] < 1.0


def test_pd_is_reproducible():
    from isac_sim import detection_probability
    a = detection_probability(_SWF, _STGT, noise_sigma=2.0, trials=8)
    b = detection_probability(_SWF, _STGT, noise_sigma=2.0, trials=8)
    assert a == b


def test_detection_probability_rejects_zero_trials():
    from isac_sim import detection_probability
    with pytest.raises(ValueError):
        detection_probability(_SWF, _STGT, noise_sigma=1.0, trials=0)
