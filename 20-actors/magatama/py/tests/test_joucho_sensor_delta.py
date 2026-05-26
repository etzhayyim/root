"""apply_sensor_delta unit cases (ADR-2605262400 §4.3 Wave-2).

Verifies the per-tick joucho 情緒 delta rules:
  - Tier-A observations raise `focus` (kyumei-koji)
  - Tier-C observations raise `focus` half as much
  - Leak attempts raise `stress` sharply (R9 pre-fire)
  - All deltas clamp to [0, 100]
"""

from __future__ import annotations

import pytest

from pymagatama.organism.joucho import (
    JouchoScores,
    apply_sensor_delta,
    determine_mood,
)


def test_no_observations_no_delta():
    base = JouchoScores(joy=42, calm=55, stress=20, gratitude=50, focus=50)
    out = apply_sensor_delta(base)
    assert out.joy == 42
    assert out.calm == 55
    assert out.stress == 20
    assert out.gratitude == 50
    assert out.focus == 50


def test_tier_a_observations_raise_focus():
    base = JouchoScores(focus=50)
    out = apply_sensor_delta(base, tier_a_obs_count=8)
    # 8 // 4 = 2 focus boost.
    assert out.focus == 52


def test_tier_a_focus_delta_saturates_at_20():
    base = JouchoScores(focus=50)
    out = apply_sensor_delta(base, tier_a_obs_count=200)
    # Saturating at 20 obs ⇒ 20 // 4 = 5 max from tier-A alone.
    assert out.focus == 55


def test_tier_a_observations_mildly_raise_calm():
    base = JouchoScores(calm=50)
    out = apply_sensor_delta(base, tier_a_obs_count=16)
    # 16 // 8 = 2 calm boost.
    assert out.calm == 52


def test_tier_c_observations_focus_half_strength():
    base = JouchoScores(focus=50)
    out = apply_sensor_delta(base, tier_c_obs_count=10)
    # tier-C: min(10, count) // 5 = 2.
    assert out.focus == 52


def test_combined_tier_a_and_tier_c_focus():
    base = JouchoScores(focus=50)
    out = apply_sensor_delta(base, tier_a_obs_count=8, tier_c_obs_count=10)
    # 8//4 = 2 (tier-A) + 10//5 = 2 (tier-C) = +4.
    assert out.focus == 54


def test_single_leak_attempt_raises_stress_sharply():
    base = JouchoScores(stress=20)
    out = apply_sensor_delta(base, leak_attempts=1)
    assert out.stress == 30  # +10 per leak


def test_three_leak_attempts_stack():
    base = JouchoScores(stress=20)
    out = apply_sensor_delta(base, leak_attempts=3)
    assert out.stress == 50  # +30 capped, well under 100


def test_leak_attempt_stress_caps_at_40():
    base = JouchoScores(stress=10)
    out = apply_sensor_delta(base, leak_attempts=100)
    assert out.stress == 50  # 10 + min(40, 100*10) = 10 + 40


def test_stress_delta_can_push_into_stressed_mood():
    """A single leak attempt on a calm-but-borderline organism flips mood."""
    base = JouchoScores(stress=65)
    assert determine_mood(base) != "stressed"  # under 70 threshold
    out = apply_sensor_delta(base, leak_attempts=1)
    assert out.stress == 75
    assert determine_mood(out) == "stressed"


def test_clamps_to_100():
    base = JouchoScores(focus=99)
    out = apply_sensor_delta(base, tier_a_obs_count=200, tier_c_obs_count=200)
    assert out.focus == 100  # 99 + 5 + 2 = 106 → clamped


def test_joy_and_gratitude_unchanged_in_wave2():
    """Wave-2 deliberately leaves joy + gratitude untouched."""
    base = JouchoScores(joy=70, gratitude=60)
    out = apply_sensor_delta(base, tier_a_obs_count=20, leak_attempts=2)
    assert out.joy == 70
    assert out.gratitude == 60
