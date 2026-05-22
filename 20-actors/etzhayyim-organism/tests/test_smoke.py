"""Smoke test — runs one tick against the live repo without writing anywhere."""

from __future__ import annotations

from pathlib import Path

from etzhayyim_organism.cns import tick
from etzhayyim_organism.emitter import render_observation


REPO = Path(__file__).resolve().parents[3]


def test_tick_produces_total_in_range() -> None:
    r = tick(REPO)
    assert 0 <= r.total <= 100
    assert r.chosen_axis in r.readings
    assert all(0 <= reading.score <= 10 for reading in r.readings.values())


def test_render_observation_has_five_sections() -> None:
    r = tick(REPO)
    body = render_observation(r, source="test")
    for header in ("## 1. Observation", "## 2.", "## 3.", "## 4.", "## 5."):
        assert header in body
