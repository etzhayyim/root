#!/usr/bin/env python3
"""itonami 営み — R5 throughput / line-balance plan tests (ADR-2606082300). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load, analyze  # noqa: E402
import plan as P  # noqa: E402

OPS = ACTOR_DIR / "data" / "seed-factory-ops.kotoba.edn"


def _load():
    stations, ticks = load(OPS)
    return stations, analyze(stations, ticks)


def test_capacity_is_uptime_over_takt():
    stations, res = _load()
    cap = P.station_capacity(stations, res)
    for sid, c in cap.items():
        expect = res[sid]["run_s"] / res[sid]["planned_s"] * res[sid]["planned_s"] / c["takt"]
        assert abs(c["capacity_run"] - res[sid]["run_s"] / c["takt"]) < 1e-9
        assert c["capacity_planned"] >= c["capacity_run"] - 1e-9


def test_throughput_bottleneck_is_paint():
    """Lowest takt-capacity wins: paint (7200/1500 = 4.8) is the throughput bottleneck."""
    stations, res = _load()
    plan = P.line_plan(stations, res)
    assert plan["throughput_bottleneck"] == ":st.paint"
    assert abs(plan["units_per_window_gross"] - 7200 / 1500) < 1e-9  # 4.8


def test_throughput_bottleneck_differs_from_oee_bottleneck():
    """The useful insight: the OEE-worst and throughput-worst stations are DIFFERENT."""
    stations, res = _load()
    plan = P.line_plan(stations, res)
    oee_bn = res["_recommend"]["bottleneck"]["station"]
    assert oee_bn == ":st.frame-weld"
    assert plan["throughput_bottleneck"] != oee_bn


def test_daily_scaling_uses_documented_hours():
    stations, res = _load()
    p16 = P.line_plan(stations, res, hours=16)
    p8 = P.line_plan(stations, res, hours=8)
    # half the hours → half the daily output
    assert abs(p16["units_per_day_gross"] - 2 * p8["units_per_day_gross"]) < 1e-9


def test_relief_recovers_paint_idle_window():
    """Recovering paint's idle window: 4.8 → 7.2 units/window (+50%)."""
    stations, res = _load()
    plan = P.line_plan(stations, res)
    relief = P.relief_plan(stations, res, plan)
    assert abs(relief["current_units_per_window"] - 4.8) < 1e-9
    assert abs(relief["recovered_units_per_window"] - 7.2) < 1e-9
    assert abs(relief["uplift_frac"] - 0.5) < 1e-9


def test_relief_lever_is_availability_within_takt_not_speedup():
    """G2: the lever must be availability recovery within takt, never a sub-takt speed-up."""
    stations, res = _load()
    relief = P.relief_plan(stations, res)
    lever = relief["lever"].lower()
    assert "within takt" in lever and "availability" in lever
    for forbidden in ("speed-up", "speedup", "below takt", "faster than takt", "worker"):
        assert forbidden not in lever


def test_emit_transient_only():
    stations, res = _load()
    plan = P.line_plan(stations, res)
    relief = P.relief_plan(stations, res, plan)
    out = P.emit(plan, relief, tx=6)
    assert ":ops/throughput-bottleneck" in out and ":ops/units-per-day-good" in out
    for line in out.splitlines():
        if line.startswith("[") and ":ops/" in line:
            assert ":derived]" in line and ":bond/is-transient true" in line, line
    assert ":add]" not in out


def test_determinism():
    stations, res = _load()
    a = P.emit(P.line_plan(stations, res), P.relief_plan(stations, res))
    s2, r2 = _load()
    b = P.emit(P.line_plan(s2, r2), P.relief_plan(s2, r2))
    assert a == b


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
