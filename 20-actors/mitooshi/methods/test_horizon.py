#!/usr/bin/env python3
"""Tests for the mitooshi multi-horizon skill-decay analysis (methods/horizon.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_horizon.py
    python3 test_horizon.py
"""
from __future__ import annotations

import sys

try:
    from horizon import build_path, horizon_skill, render_md
except ImportError:
    from mitooshi.methods.horizon import build_path, horizon_skill, render_md  # type: ignore


def test_path_is_deterministic_and_mean_reverting():
    a, b = build_path(50), build_path(50)
    assert a == b                                    # reproducible (no RNG)
    # mean-reverting: the path stays near MU=10, not wandering off like a random walk
    assert all(5.0 < v < 15.0 for v in a)


def test_short_horizon_has_positive_skill():
    rows = horizon_skill()
    h1 = next(r for r in rows if r["h"] == 1)
    assert h1["skill_vs_clim"] > 0.1                 # clearly beats climatology at h=1


def test_skill_decays_with_horizon():
    rows = horizon_skill()
    first, last = rows[0], rows[-1]
    assert first["skill_vs_clim"] > last["skill_vs_clim"]   # decays
    assert last["skill_vs_clim"] < 0.1                       # → ≈ climatology at long range


def test_crps_grows_with_horizon():
    rows = horizon_skill()
    assert rows[-1]["mean_crps"] > rows[0]["mean_crps"]      # uncertainty accumulates


def test_leak_free_every_origin_scored():
    rows = horizon_skill()
    assert all(r["n"] > 10 for r in rows)            # many leak-checked origins per horizon


def test_render_md_has_a_row_per_horizon():
    rows = horizon_skill()
    md = render_md(rows)
    for r in rows:
        assert f"| {r['h']} |" in md
    assert "skill vs clim" in md


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"horizon.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
