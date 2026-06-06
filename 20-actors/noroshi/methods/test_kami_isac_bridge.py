"""Tests for the noroshi×kami-autodrive ISAC sensor bridge (ADR-2606051600). Stdlib + pytest only."""

from __future__ import annotations

import pytest

from isac_sim import IsacWaveform
from kami_isac_bridge import ScenarioObject, run_scenario, track_object

WF = IsacWaveform()


def test_track_follows_closing_range():
    # object at 30·ΔR (well within R_max), closing at 2·Δv; short interval keeps it in view.
    obj = ScenarioObject("o1", range0_m=30 * WF.range_resolution_m,
                         velocity_mps=2 * WF.velocity_resolution_mps)
    track = track_object(WF, obj, frames=6, frame_dt_s=0.002)
    assert len(track) == 6
    # range decreases monotonically as the object closes
    ranges = [p.range_m for p in track]
    assert all(ranges[i] >= ranges[i + 1] for i in range(len(ranges) - 1))


def test_velocity_recovered_each_frame():
    v = 3 * WF.velocity_resolution_mps
    obj = ScenarioObject("o1", range0_m=30 * WF.range_resolution_m, velocity_mps=v)
    track = track_object(WF, obj, frames=4)
    for p in track:
        assert p.velocity_mps == pytest.approx(v, rel=1e-6)


def test_track_stops_when_object_passes_ego():
    # starts close, high closing speed → range hits zero quickly, track truncates.
    obj = ScenarioObject("fast", range0_m=2 * WF.range_resolution_m,
                         velocity_mps=50 * WF.velocity_resolution_mps)
    track = track_object(WF, obj, frames=20, frame_dt_s=0.05)
    assert len(track) < 20
    assert all(p.range_m > 0 for p in track)


def test_run_scenario_returns_track_per_object():
    objs = [
        ScenarioObject("a", range0_m=15 * WF.range_resolution_m, velocity_mps=WF.velocity_resolution_mps),
        ScenarioObject("b", range0_m=18 * WF.range_resolution_m, velocity_mps=2 * WF.velocity_resolution_mps),
    ]
    tracks = run_scenario(objs, WF, frames=3)
    assert set(tracks) == {"a", "b"}
    assert all(len(t) == 3 for t in tracks.values())


def test_object_starting_at_or_behind_ego_yields_empty_track():
    # range0 = 0 → already at the ego-craft; no frames sensed.
    obj = ScenarioObject("at-ego", range0_m=0.0, velocity_mps=WF.velocity_resolution_mps)
    assert track_object(WF, obj, frames=5) == []


def test_zero_velocity_object_keeps_constant_range():
    obj = ScenarioObject("static", range0_m=12 * WF.range_resolution_m, velocity_mps=0.0)
    track = track_object(WF, obj, frames=4)
    ranges = {round(p.range_m, 6) for p in track}
    assert len(ranges) == 1                          # range never changes
    assert all(p.doppler_bin == 0 for p in track)    # zero Doppler


def test_sense_frame_detects_all_objects_in_one_shot():
    from kami_isac_bridge import sense_frame
    objs = [
        ScenarioObject("a", range0_m=4 * WF.range_resolution_m, velocity_mps=2 * WF.velocity_resolution_mps),
        ScenarioObject("b", range0_m=14 * WF.range_resolution_m, velocity_mps=5 * WF.velocity_resolution_mps),
    ]
    dets = sense_frame(objs, WF)
    bins = {(d.range_bin, d.doppler_bin) for d in dets}
    assert bins == {(4, 2), (14, 5)}


def test_sense_frame_drops_objects_at_or_behind_ego():
    from kami_isac_bridge import sense_frame
    objs = [
        ScenarioObject("ahead", range0_m=6 * WF.range_resolution_m, velocity_mps=WF.velocity_resolution_mps),
        ScenarioObject("at-ego", range0_m=0.0, velocity_mps=WF.velocity_resolution_mps),
    ]
    assert len(sense_frame(objs, WF)) == 1


def test_report_renders_and_is_civilian():
    from kami_isac_bridge import report
    txt = report()
    assert "ISAC sensor" in txt
    assert "Civilian" in txt or "civilian" in txt
