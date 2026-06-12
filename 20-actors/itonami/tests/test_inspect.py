#!/usr/bin/env python3
"""itonami 営み — R2 vision-inspection hand-off tests (ADR-2606082300). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load, analyze  # noqa: E402
import inspect as vis  # noqa: E402  (our module, not stdlib `inspect`)

OPS = ACTOR_DIR / "data" / "seed-factory-ops.kotoba.edn"
DET = ACTOR_DIR / "data" / "seed-vision-detections.kotoba.edn"


def _load():
    stations, ticks = load(OPS)
    res = analyze(stations, ticks)
    det = vis.load_detections(DET)
    return stations, res, det


def test_detections_load_and_carry_no_person():
    """G2 / manako: detections are object-only — no person/face/biometric/worker field."""
    _, _, det = _load()
    assert len(det) >= 9
    for d in det:
        keys = " ".join(d.keys())
        for forbidden in (":worker", ":person", ":face", ":biometric", ":operator"):
            assert forbidden not in keys, f"detection leaked {forbidden}: {d}"
        assert d[":detect/verdict"] in (":pass", ":rework", ":scrap")


def test_request_targets_highest_scrap_station():
    stations, res, det = _load()
    req = vis.inspection_request(stations, res, det)
    assert req["station"] == ":st.cab-weld"  # the R0 quality_target
    assert req["routed_to"] == "actor:manako"
    # elevated scrap → 100% sampling
    assert req["sample_rate"] == 1.0


def test_request_constraints_enforce_manako_invariants():
    stations, res, det = _load()
    req = vis.inspection_request(stations, res, det)
    joined = " ".join(req["constraints"]).lower()
    assert "no biometric" in joined or "no person" in joined
    assert "on-device" in joined
    assert "no auto-reject" in joined  # G1 — advisory, never actuates


def test_reconcile_pareto_top_defect_is_porosity():
    stations, res, det = _load()
    rec = vis.reconcile(det, res)
    cw = rec[":st.cab-weld"]
    # 3 porosity vs 1 spatter vs 1 misalignment → porosity dominates
    assert cw["top_defect"] == ":weld-porosity"
    assert dict(cw["defect_pareto"])[":weld-porosity"] == 3


def test_vision_scrap_cross_checks_scan_cycle():
    """The detector's scrap count must reconcile with the scan-cycle scrap count (2)."""
    stations, res, det = _load()
    rec = vis.reconcile(det, res)
    cw = rec[":st.cab-weld"]
    assert cw["scancycle_scrap"] == 2
    assert cw["scrap"] == 2
    assert cw["scrap_agrees"] is True


def test_emit_transient_only():
    stations, res, det = _load()
    req = vis.inspection_request(stations, res, det)
    rec = vis.reconcile(det, res)
    out = vis.emit(req, rec, tx=5)
    assert ":ops/inspect-routed-to :actor.manako" in out
    assert ":quality/top-defect" in out
    for line in out.splitlines():
        if line.startswith("[") and (":ops/" in line or ":quality/" in line):
            assert ":derived]" in line and ":bond/is-transient true" in line, line
    assert ":add]" not in out


def test_determinism():
    stations, res, det = _load()
    a = vis.emit(vis.inspection_request(stations, res, det), vis.reconcile(det, res), tx=1)
    s2, r2, d2 = _load()
    b = vis.emit(vis.inspection_request(s2, r2, d2), vis.reconcile(d2, r2), tx=1)
    assert a == b


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
