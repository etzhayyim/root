"""Tests for the noroshi×watatsuna optical-network resilience join (ADR-2606051600). Stdlib + pytest."""

from __future__ import annotations

import pathlib

import pytest

from cable_endpoint import _lanes_for, load_graph, report, size_fleet

_SEED = (pathlib.Path(__file__).resolve().parents[2]
         / "watatsuna" / "data" / "seed-cable-graph.kotoba.edn")

pytestmark = pytest.mark.skipif(not _SEED.exists(), reason="watatsuna seed not present")


def test_loads_watatsuna_graph():
    g = load_graph()
    assert "cable.jupiter" in g["cables"]
    assert any(s.startswith("station.") for s in g["stations"])
    assert len(g["links"]) > 0


def test_lane_sizing_formula():
    # 250 Tb/s at 106.25 Gb/s/lane → ceil(250000/106.25) = 2353 lanes.
    assert _lanes_for(250.0, 106.25) == 2353
    assert _lanes_for(0.0, 106.25) == 1          # at least one lane
    assert _lanes_for(0.1, 106.25) == 1


def test_chokepoints_ranked_by_lane_demand():
    f = size_fleet()
    cps = f["chokepoints"]
    assert cps, "expected at least one chokepoint"
    # sorted descending by CPO lane demand
    assert all(cps[i]["lanes"] >= cps[i + 1]["lanes"] for i in range(len(cps) - 1))
    # luzon-strait is the seed's top capacity chokepoint → top transceiver demand too
    assert cps[0]["chokepoint"] == ":luzon-strait"


def test_per_cable_endpoint_power_is_realistic():
    f = size_fleet()
    # endpoint transceiver power should be sub-MW (kW range), not gigawatts.
    for c in f["per_cable"]:
        assert 0.0 < c.energy_kw < 1000.0


def test_report_frames_resilience_not_target_list():
    txt = report()
    assert "resilience" in txt.lower()
    assert "NEVER a target-list" in txt or "never" in txt.lower()
    assert ":luzon-strait" in txt


# ── coverage: status filter, missing seed, custom seed ───────────────────────
def test_missing_seed_raises_friendly_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_graph(tmp_path / "nope.edn")


def test_out_of_service_cable_is_skipped(tmp_path):
    seed = tmp_path / "tiny.edn"
    seed.write_text(
        '[{:cable/id "c.live" :cable/name "Live" :cable/design-capacity-tbps 100.0 '
        ':cable/status :in-service}\n'
        ' {:cable/id "c.dead" :cable/name "Dead" :cable/design-capacity-tbps 999.0 '
        ':cable/status :decommissioned}\n'
        ' {:station/id "s.a" :station/name "A" :station/chokepoint [:malacca]}\n'
        ' {:cable.link/id "lk1" :cable.link/cable "c.live" :cable.link/station "s.a"}\n'
        ' {:cable.link/id "lk2" :cable.link/cable "c.dead" :cable.link/station "s.a"}]\n',
        encoding="utf-8",
    )
    f = size_fleet(seed)
    names = {c.name for c in f["per_cable"]}
    assert "Live" in names and "Dead" not in names  # decommissioned excluded


def test_load_graph_parses_segments():
    assert len(load_graph()["segments"]) > 0


def test_segment_view_present_ranked_and_luzon_top():
    f = size_fleet()
    segs = f["chokepoints_via_segments"]
    assert segs and all(segs[i]["lanes"] >= segs[i + 1]["lanes"] for i in range(len(segs) - 1))
    assert segs[0]["chokepoint"] == ":luzon-strait"


def test_segment_view_attributes_a_crossing_without_a_tagged_landing(tmp_path):
    # A cable physically crosses :hormuz (a segment traverses it) but lands at an UNTAGGED station.
    # The station-tag view misses it; the authoritative segment view catches it (the added accuracy).
    seed = tmp_path / "hormuz.edn"
    seed.write_text(
        '[{:cable/id "c.gulf" :cable/name "Gulf" :cable/design-capacity-tbps 100.0 :cable/status :in-service}\n'
        ' {:station/id "s.plain" :station/name "Plain"}\n'
        ' {:cable.link/id "lk" :cable.link/cable "c.gulf" :cable.link/station "s.plain"}\n'
        ' {:cable.seg/id "sg" :cable.seg/cable "c.gulf" :cable.seg/traverses [:hormuz]}]\n',
        encoding="utf-8",
    )
    f = size_fleet(seed)
    station_cps = {c["chokepoint"] for c in f["chokepoints"]}
    segment_cps = {c["chokepoint"] for c in f["chokepoints_via_segments"]}
    assert ":hormuz" not in station_cps          # untagged landing → missed by station view
    assert ":hormuz" in segment_cps              # but the segment crossing is authoritative


def test_station_without_chokepoint_contributes_no_chokepoint_row(tmp_path):
    seed = tmp_path / "tiny.edn"
    seed.write_text(
        '[{:cable/id "c.x" :cable/name "X" :cable/design-capacity-tbps 50.0 :cable/status :in-service}\n'
        ' {:station/id "s.nocp" :station/name "NoCP"}\n'
        ' {:cable.link/id "lk" :cable.link/cable "c.x" :cable.link/station "s.nocp"}]\n',
        encoding="utf-8",
    )
    f = size_fleet(seed)
    assert f["chokepoints"] == []                 # no chokepoint tag → no aggregation row
    assert f["by_station_lanes"]["s.nocp"] > 0    # but the station still carries lanes
