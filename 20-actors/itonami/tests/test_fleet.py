#!/usr/bin/env python3
"""itonami 営み — R10 multi-line fleet rollup tests (ADR-2606082300). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load  # noqa: E402
import fleet  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-fleet-ops.kotoba.edn"


def _rollup():
    stations, ticks = load(SEED)
    return stations, fleet.rollup(stations, ticks)


def test_two_lines_detected():
    stations, ticks = load(SEED)
    lines = fleet.split_lines(stations, ticks)
    assert set(lines) == {":line.sarutahiko-a", ":line.giemon-a"}
    # each line's ticks reference only its own stations
    for line, (lst, lt) in lines.items():
        for tk in lt:
            assert tk[":tick/station"] in lst


def test_per_line_oee_computed():
    _, f = _rollup()
    sa = f["per_line"][":line.sarutahiko-a"]
    gi = f["per_line"][":line.giemon-a"]
    assert 0 < sa["oee"] < gi["oee"]   # sarutahiko line is the weaker one
    assert gi["oee"] > 0.8             # giemon line is healthy


def test_worst_line_attended_first():
    """sarutahiko has a critical alert (cab scrap) + low OEE → ranked first."""
    _, f = _rollup()
    assert f["ranked"][0] == ":line.sarutahiko-a"
    assert f["plant"]["worst_line"] == ":line.sarutahiko-a"
    assert f["per_line"][":line.sarutahiko-a"]["critical"] >= 1
    assert f["per_line"][":line.giemon-a"]["critical"] == 0


def test_plant_aggregate_sums_lines():
    _, f = _rollup()
    p = f["plant"]
    assert p["n_lines"] == 2
    assert abs(p["good"] - sum(f["per_line"][l]["good"] for l in f["per_line"])) < 1e-9
    assert abs(p["kwh"] - sum(f["per_line"][l]["kwh"] for l in f["per_line"])) < 1e-9


def test_no_worker_dimension():
    """G2: the fleet ranks lines, never people."""
    stations, ticks = load(SEED)
    blob = str(stations) + str(ticks) + fleet.emit(fleet.rollup(stations, ticks))
    for forbidden in (":worker", ":person", ":operator"):
        assert forbidden not in blob


def test_emit_transient_only():
    _, f = _rollup()
    out = fleet.emit(f, tx=5)
    assert ":fleet/oee" in out and ":fleet/attend-first :line.sarutahiko-a" in out
    for line in out.splitlines():
        if line.startswith("[") and ":fleet/" in line:
            assert ":derived]" in line and ":bond/is-transient true" in line, line
    assert ":add]" not in out


def test_determinism():
    _, a = _rollup()
    _, b = _rollup()
    assert fleet.emit(a) == fleet.emit(b)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
