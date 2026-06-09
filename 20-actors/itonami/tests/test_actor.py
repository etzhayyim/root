#!/usr/bin/env python3
"""itonami 営み — R11 WASM actor entrypoint tests (ADR-2606082300). Pure stdlib."""
import sys
import json
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

import actor  # noqa: E402


def test_summary_is_valid_json_with_headline_signals():
    s = json.loads(actor.summary())
    assert "line_oee" in s and 0 <= s["line_oee"] <= 1
    assert s["bottleneck"] == ":st.frame-weld"
    assert s["fleet_attend_first"] == ":line.sarutahiko-a"
    assert s["top_alert"]["severity"] in ("warn", "critical")


def test_analyze_json_round_trips():
    a = json.loads(actor.analyze_json())
    assert "line" in a and "stations" in a and "recommend" in a
    assert ":st.frame-weld" in a["stations"]


def test_digest_json_has_narration_and_backend():
    d = json.loads(actor.digest_json())
    assert d["narration"] and isinstance(d["narration"], str)
    assert d["backend"] in ("murakumo", "fallback-deterministic")


def test_alert_json_counts_match():
    a = json.loads(actor.alert_json())
    assert a["counts"]["total"] == len(a["alerts"])
    assert a["counts"]["critical"] >= 1  # cab-weld scrap


def test_fleet_json_has_two_lines():
    f = json.loads(actor.fleet_json())
    assert f["plant"]["n_lines"] == 2
    assert f["plant"]["worst_line"] == ":line.sarutahiko-a"


def test_datoms_returns_edn_ground_state():
    out = actor.datoms(7)
    assert ":add]" in out and " 7 :add]" in out
    assert ":tick/state" in out and ":ops/oee" in out  # ground + derived


def test_infinite_floats_become_null_not_invalid_json():
    """energy/good can be inf for a 0-good station — must serialize as null, valid JSON."""
    a = json.loads(actor.analyze_json())  # would raise if inf leaked as Infinity? json allows it
    # explicit: our _clean maps inf → None
    assert actor._clean(float("inf")) is None
    assert actor._clean(float("nan")) is None


def test_no_worker_dimension_in_any_export():
    blob = (actor.summary() + actor.analyze_json() + actor.digest_json()
            + actor.alert_json() + actor.fleet_json() + actor.datoms()).lower()
    for forbidden in (":worker", ":person", ":operator", "employee"):
        assert forbidden not in blob


def test_determinism():
    assert actor.summary() == actor.summary()
    assert actor.datoms(1) == actor.datoms(1)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
