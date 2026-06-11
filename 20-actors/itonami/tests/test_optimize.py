#!/usr/bin/env python3
"""itonami 営み — R1 optimization-proposal tests (ADR-2606082300). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load, analyze, RUN  # noqa: E402
import optimize  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-factory-ops.kotoba.edn"


def _load():
    stations, ticks = load(SEED)
    return stations, ticks, analyze(stations, ticks)


def test_idle_powerdown_recovers_only_a_fraction_of_idle_energy():
    stations, ticks, res = _load()
    e = optimize.idle_powerdown(res)
    # total idle energy across the line, recomputed independently from ticks
    total_idle = sum(float(tk[":tick/kwh"]) for tk in ticks if tk[":tick/state"] != RUN)
    assert abs(e["recoverable_kwh"] - total_idle * optimize.RECOVERABLE_IDLE_FRACTION) < 1e-9
    # recoverable is strictly less than total idle (we never claim 100%) and < line energy
    assert 0 < e["recoverable_kwh"] < total_idle + 1e-9
    assert 0.0 < e["energy_reduction_frac"] < 1.0


def test_energy_reduction_is_honest_not_inflated():
    """G5: our synthetic line has modest idle waste — the % must NOT be silently set to 10%."""
    stations, ticks, res = _load()
    e = optimize.idle_powerdown(res)
    # paint(45) + frame-weld down(8) = 53 idle kWh ; line = 825 kWh ; ×0.7 = 37.1 → ~4.5%
    assert 0.03 < e["energy_reduction_frac"] < 0.06, e["energy_reduction_frac"]
    assert e["top_station"] == ":st.paint"  # biggest single power-down win


def test_bottleneck_relief_lifts_line_to_second_worst():
    stations, ticks, res = _load()
    b = optimize.bottleneck_relief(res)
    sids = [s for s in res if not s.startswith("_")]
    oees = sorted(res[s]["oee"] for s in sids)
    assert b["bottleneck"] == ":st.frame-weld"
    assert abs(b["current_line_oee"] - oees[0]) < 1e-9
    assert abs(b["target_line_oee"] - oees[1]) < 1e-9  # 2nd-worst becomes the new gate
    assert b["oee_uplift_frac"] > 0


def test_relief_levers_never_propose_sub_takt_speedup():
    """G2: relief is availability/performance recovery within takt, never speed-up."""
    stations, ticks, res = _load()
    b = optimize.bottleneck_relief(res)
    text = " ".join(b["relief_levers"]).lower()
    assert "within takt" in text
    for forbidden in ("speed-up", "speedup", "faster than takt", "below takt", "worker"):
        assert forbidden not in text


def test_emit_proposals_all_transient():
    stations, ticks, res = _load()
    opt = optimize.optimize(stations, ticks, res)
    out = optimize.emit_proposals(opt, tx=4)
    assert ":ops/proposal-energy-reduction-frac" in out
    assert ":ops/proposal-bottleneck" in out
    for line in out.splitlines():
        if line.startswith("[") and ":ops/proposal" in line:
            assert ":derived]" in line and ":bond/is-transient true" in line, line
    # proposals are NEVER emitted as durable :add facts
    assert ":add]" not in out


def test_determinism():
    stations, ticks, res = _load()
    a = optimize.emit_proposals(optimize.optimize(stations, ticks, res), tx=1)
    s2, t2, r2 = _load()
    b = optimize.emit_proposals(optimize.optimize(s2, t2, r2), tx=1)
    assert a == b


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
