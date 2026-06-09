#!/usr/bin/env python3
"""itonami 営み — R7 KPI trend / drift tests (ADR-2606082300). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

import trend  # noqa: E402

HIST = ACTOR_DIR / "data" / "seed-ops-history.kotoba.edn"


def _trends():
    return trend.analyze_trends(trend.load_history(HIST))


def test_history_loads():
    recs = trend.load_history(HIST)
    assert len(recs) == 10  # 5 days × 2 scopes
    scopes = {r[":opsday/scope"] for r in recs}
    assert scopes == {":line.sarutahiko-a", ":st.cab-weld"}


def test_oee_degradation_detected():
    t = _trends()
    oee = t[":line.sarutahiko-a"][":opsday/oee"]
    assert oee["direction"] == ":degrading"   # 0.62 → 0.50
    assert oee["regression"] is True
    assert oee["slope"] < 0                    # least-squares slope is negative


def test_scrap_rise_is_degrading_lower_better_polarity():
    """scrap-rate is lower-better → a RISING series is degrading (polarity handled)."""
    t = _trends()
    scrap = t[":line.sarutahiko-a"][":opsday/scrap-rate"]
    assert scrap["last"] > scrap["first"]      # rising
    assert scrap["direction"] == ":degrading"  # rising is bad for a lower-better KPI
    assert scrap["regression"] is True


def test_flat_series_not_flagged():
    """energy-per-good is essentially flat → not a regression."""
    t = _trends()
    epg = t[":line.sarutahiko-a"][":opsday/energy-per-good"]
    assert epg["direction"] == ":flat"
    assert epg["regression"] is False


def test_station_scrap_is_top_regression():
    t = _trends()
    regs = trend.regressions(t)
    assert regs, "expected degrading series"
    # cab-weld scrap (0.10 → 0.22, +120%) is the largest relative regression
    top = regs[0]
    assert top[0] == ":st.cab-weld" and top[1] == ":opsday/scrap-rate"


def test_g2_rejects_worker_series(tmp_path=None):
    """G2: load_history must refuse an ops history that carries a person/worker series."""
    import tempfile, os
    bad = ('[{:opsday/day 0 :opsday/scope :line.a :worker/id "w1" :opsday/oee 0.5}]')
    fd, p = tempfile.mkstemp(suffix=".edn")
    try:
        os.write(fd, bad.encode("utf-8")); os.close(fd)
        try:
            trend.load_history(pathlib.Path(p))
        except ValueError as ex:
            assert "G2" in str(ex)
        else:
            raise AssertionError("a worker series must be rejected (G2)")
    finally:
        os.unlink(p)


def test_emit_transient_only():
    t = _trends()
    out = trend.emit(t, tx=3)
    assert ":trend/oee-direction" in out
    assert ":trend/scrap-rate-regression true" in out
    for line in out.splitlines():
        if line.startswith("[") and ":trend/" in line:
            assert ":derived]" in line and ":bond/is-transient true" in line, line
    assert ":add]" not in out


def test_determinism():
    a = trend.emit(_trends(), tx=1)
    b = trend.emit(_trends(), tx=1)
    assert a == b


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
