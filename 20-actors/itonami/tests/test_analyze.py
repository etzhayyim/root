#!/usr/bin/env python3
"""itonami 営み — operations-KPI + Datom-emit tests (ADR-2606082300). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load, analyze, RUN  # noqa: E402
import datom_emit  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-factory-ops.kotoba.edn"


def test_load_nontrivial():
    stations, ticks = load(SEED)
    assert len(stations) == 8, f"expected 8-cell line, got {len(stations)}"
    assert len(ticks) == 24, f"expected 8×3 scan-cycle ticks, got {len(ticks)}"
    for tk in ticks:
        assert tk[":tick/station"] in stations, f"dangling tick station {tk[':tick/station']}"
        assert tk[":tick/state"] in (":run", ":idle", ":down")


def test_oee_in_unit_interval():
    """OEE and each factor must be a well-formed fraction in [0,1]."""
    stations, ticks = load(SEED)
    res = analyze(stations, ticks)
    for sid in (s for s in res if not s.startswith("_")):
        r = res[sid]
        for k in ("availability", "performance", "quality", "oee"):
            assert 0.0 <= r[k] <= 1.0 + 1e-9, f"{sid}.{k} = {r[k]} outside [0,1]"
        # OEE is the product of its three factors
        prod = r["availability"] * r["performance"] * r["quality"]
        assert abs(r["oee"] - prod) < 1e-9, f"{sid} OEE != A×P×Q"


def test_availability_bottleneck_is_frame_weld():
    """frame-weld has a DOWN interval → it must be the OEE bottleneck (G1 routed finding)."""
    stations, ticks = load(SEED)
    res = analyze(stations, ticks)
    rec = res["_recommend"]
    assert rec["bottleneck"]["station"] == ":st.frame-weld", \
        f"bottleneck mis-identified: {rec['bottleneck']}"
    # availability MUST equal run_s / planned_s, computed independently
    fw = res[":st.frame-weld"]
    assert abs(fw["availability"] - (2 * 3600) / (3 * 3600)) < 1e-9


def test_energy_per_good_target_is_paint():
    """paint draws the most kWh per good unit → the FOX energy-cut lever points there."""
    stations, ticks = load(SEED)
    res = analyze(stations, ticks)
    rec = res["_recommend"]
    assert rec["energy_target"]["station"] == ":st.paint", \
        f"energy target mis-identified: {rec['energy_target']}"
    # paint also carries the largest idle-energy burn (powered while not producing)
    assert rec["idle_energy_target"]["station"] == ":st.paint"
    assert res[":st.paint"]["idle_kwh"] == 45.0


def test_quality_target_is_cab_weld_and_routes_to_vision():
    """cab-weld has the highest scrap-rate → routed to vision inspection, never the worker."""
    stations, ticks = load(SEED)
    res = analyze(stations, ticks)
    rec = res["_recommend"]
    assert rec["quality_target"]["station"] == ":st.cab-weld"
    cw = res[":st.cab-weld"]
    # 2 scrap / 9 cycles
    assert abs(cw["scrap_rate"] - 2.0 / 9.0) < 1e-9
    assert abs(cw["quality"] - 7.0 / 9.0) < 1e-9


def test_no_worker_dimension_anywhere():
    """G2: per-worker monitoring is structurally unrepresentable. No :worker/* may appear."""
    stations, ticks = load(SEED)
    res = analyze(stations, ticks)
    out = datom_emit.emit(stations, ticks, res, tx=3)
    for blob, name in ((str(stations), "stations"), (str(ticks), "ticks"), (out, "datoms")):
        assert ":worker" not in blob and ":person" not in blob, \
            f"{name} leaked a person/worker dimension (G2 violation)"


def test_line_rollup_gated_by_weakest_station():
    """A serial line's OEE is its bottleneck — line OEE == min station OEE."""
    stations, ticks = load(SEED)
    res = analyze(stations, ticks)
    sids = [s for s in res if not s.startswith("_")]
    assert abs(res["_line"]["oee"] - min(res[s]["oee"] for s in sids)) < 1e-9
    # line energy/good is total kWh over total good
    tot_kwh = sum(res[s]["kwh"] for s in sids)
    tot_good = sum(res[s]["good"] for s in sids)
    assert abs(res["_line"]["energy_per_good"] - tot_kwh / tot_good) < 1e-9


def test_idle_energy_only_counts_non_producing_states():
    """idle_kwh must aggregate ONLY ticks whose state is not :run (the cut lever)."""
    stations, ticks = load(SEED)
    res = analyze(stations, ticks)
    for sid in (s for s in res if not s.startswith("_")):
        expect = sum(float(tk[":tick/kwh"]) for tk in ticks
                     if tk[":tick/station"] == sid and tk[":tick/state"] != RUN)
        assert abs(res[sid]["idle_kwh"] - expect) < 1e-9, f"{sid} idle_kwh mismatch"


def test_datom_emit_ground_and_transient():
    stations, ticks = load(SEED)
    res = analyze(stations, ticks)
    out = datom_emit.emit(stations, ticks, res, tx=7)
    assert ":add]" in out, "no ground :add datoms"
    assert ":tick/state" in out, "scan-cycle tick datoms missing"
    assert ":ops/oee" in out, "derived OEE datom missing"
    assert ":bond/is-transient true" in out
    assert " 7 :add]" in out
    # every KPI/routing line MUST be flagged :derived (G3 — not a fact)
    for line in out.splitlines():
        if line.startswith("[") and (":ops/" in line):
            assert ":derived]" in line, f"KPI not flagged transient: {line}"


def test_determinism():
    stations, ticks = load(SEED)
    a = datom_emit.emit(stations, ticks, analyze(stations, ticks), tx=1)
    s2, t2 = load(SEED)
    b = datom_emit.emit(s2, t2, analyze(s2, t2), tx=1)
    assert a == b, "Datom emit is not deterministic"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
