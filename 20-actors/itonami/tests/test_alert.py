#!/usr/bin/env python3
"""itonami 営み — R9 operational-alert tests (ADR-2606082300). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load, analyze  # noqa: E402
import alert  # noqa: E402

OPS = ACTOR_DIR / "data" / "seed-factory-ops.kotoba.edn"


def _eval():
    stations, ticks = load(OPS)
    return stations, alert.evaluate(stations, analyze(stations, ticks))


def _find(alerts, scope, kpi):
    return next((a for a in alerts if a["scope"] == scope and a["kpi"] == kpi), None)


def test_cab_weld_scrap_is_critical():
    """cab-weld scrap-rate 22.2% > 15% critical threshold."""
    _, alerts = _eval()
    a = _find(alerts, ":st.cab-weld", "scrap_rate")
    assert a is not None and a["severity"] == "critical"


def test_line_oee_is_warn():
    """line OEE 50% is between the 45% critical and 60% warn floor → warn."""
    _, alerts = _eval()
    a = _find(alerts, ":line.sarutahiko-a", "oee")
    assert a is not None and a["severity"] == "warn"


def test_healthy_station_has_no_alert():
    """marriage (OEE 81.5%, 0 scrap, low energy) should raise nothing."""
    _, alerts = _eval()
    assert all(a["scope"] != ":st.marriage" for a in alerts)


def test_paint_energy_and_idle_warn():
    _, alerts = _eval()
    assert _find(alerts, ":st.paint", "energy_per_good")["severity"] == "warn"  # 69.5 in (40,80)
    assert _find(alerts, ":st.paint", "idle_energy_frac")["severity"] == "warn"  # 0.162 in (.10,.25)


def test_severity_grading_boundaries():
    """polarity-aware grading: higher-better below-threshold, lower-better above-threshold."""
    assert alert._severity(0.40, alert.DEFAULT_THRESHOLDS["oee"]) == "critical"
    assert alert._severity(0.55, alert.DEFAULT_THRESHOLDS["oee"]) == "warn"
    assert alert._severity(0.70, alert.DEFAULT_THRESHOLDS["oee"]) is None
    assert alert._severity(0.20, alert.DEFAULT_THRESHOLDS["scrap_rate"]) == "critical"
    assert alert._severity(0.08, alert.DEFAULT_THRESHOLDS["scrap_rate"]) == "warn"
    assert alert._severity(0.01, alert.DEFAULT_THRESHOLDS["scrap_rate"]) is None


def test_thresholds_are_overridable():
    """G5: thresholds are config — a stricter OEE floor raises more alerts."""
    stations, ticks = load(OPS)
    res = analyze(stations, ticks)
    strict = {"oee": {"polarity": True, "warn": 0.99, "critical": 0.90}}
    alerts = alert.evaluate(stations, res, strict)
    # nearly every station OEE < 0.99 now → many warn/critical
    assert len(alerts) >= 8


def test_no_actuation_token_anywhere():
    """G1: an alert never halts/trips/e-stops — no such token may appear in output."""
    _, alerts = _eval()
    blob = (alert.report_md(alerts) + alert.emit(alerts)).lower()
    for forbidden in ("e-stop", "estop", "halt", "trip", "shutdown", "actuat", ":write"):
        assert forbidden not in blob, f"alert output leaked an actuation token: {forbidden}"


def test_emit_transient_only():
    _, alerts = _eval()
    out = alert.emit(alerts, tx=4)
    assert ":alert/scrap-rate :critical" in out
    for line in out.splitlines():
        if line.startswith("[") and ":alert/" in line:
            assert ":derived]" in line and ":bond/is-transient true" in line, line
    assert ":add]" not in out


def test_determinism():
    _, a = _eval()
    _, b = _eval()
    assert alert.emit(a) == alert.emit(b)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
