"""Tests for hikari microgrid operational loop.

    cd 20-actors/hikari/methods
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest
"""

from __future__ import annotations

import pytest

from _substrate import SafetyError
from microgrid import commission_microgrid, rocof, to_datoms


def test_microgrid_restores_frequency_after_load_step():
    res = commission_microgrid(load_step_kw=140.0)
    assert res.freq_restored
    assert res.final_freq_hz == pytest.approx(50.0, abs=2e-2)
    assert res.final_generation_kw == pytest.approx(140.0, abs=1.0)  # gen tracks load
    assert 0.0 <= res.final_soc <= 1.0
    assert res.settling_seconds > 0


def test_microgrid_handles_load_shed_direction():
    # A load drop (below the 100 kW base) is also rejected back to 50 Hz.
    res = commission_microgrid(load_step_kw=60.0)
    assert res.freq_restored
    assert res.final_generation_kw == pytest.approx(60.0, abs=1.0)


@pytest.mark.parametrize("use", ["weapon", "fire-control", "mining"])
def test_non_civilian_use_refused(use):
    with pytest.raises(SafetyError):
        commission_microgrid(load_step_kw=120.0, use=use)


def test_normal_load_step_does_not_trip_rocof():
    # +60 kW step: primary droop arrests the dive, ROCOF stays under the trip.
    res = commission_microgrid(load_step_kw=160.0)
    assert res.rocof_max_hz_per_s >= 0.0
    assert res.rocof_tripped is False


def test_islanding_scale_step_trips_rocof():
    # +80 kW (near-doubling) is an islanding-scale transient: the guard trips.
    res = commission_microgrid(load_step_kw=180.0)
    assert res.rocof_tripped is True
    assert res.freq_restored  # still recovers in sim, but the relay flags it


def test_rocof_helper_detects_fast_transient():
    fast = [(0.0, 50.0, 0.0), (0.01, 47.0, 0.0)]  # 3 Hz in 10 ms = 300 Hz/s
    assert rocof(fast, window_s=0.01) == pytest.approx(300.0)


def test_datoms_are_aggregate_and_dry_run():
    res = commission_microgrid(load_step_kw=140.0)
    d = to_datoms(res, "microgrid-001")
    assert d[":microgrid/dry-run"] is True
    assert d[":microgrid/representative"] is True
    assert d[":microgrid/freq-restored"] is True
