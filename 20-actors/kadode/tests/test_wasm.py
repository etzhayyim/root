#!/usr/bin/env python3
"""kadode 門出 — WASM component entry tests (ADR-2606112238). Pure stdlib, NETWORK-FREE."""
import sys, json, pathlib
ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "wasm"))
sys.path.insert(0, str(ACTOR_DIR / "methods"))
import app  # noqa: E402


def test_analyze_export_shape():
    out = json.loads(app.analyze())
    assert set(out) == {"routes", "ground_support", "risk_coverage"}
    # G1 in the WASM export: every negotiation-needing scenario routes to a negotiating actor
    for sid, r in out["routes"].items():
        if r["needs_negotiation"]:
            assert r["actor"] in ("labor-union", "lawyer", ":labor-union", ":lawyer"), \
                f"{sid} negotiation routed to {r['actor']}"


def test_datoms_export_is_eavt_edn():
    edn = app.datoms(7)
    assert edn.lstrip().startswith(";;") and " 7 :add]" in edn
    assert ":bond/is-transient true" in edn


def test_coverage_export_is_markdown():
    md = app.coverage()
    assert md.startswith("# kadode") and "holds for all scenarios" in md


def test_generate_export_renders_resignation():
    doc = app.generate("taishoku-todoke", json.dumps({"worker": "山田太郎", "date": "令和8年7月15日"}))
    assert "退職届" in doc and "民法627条" in doc


def test_relay_export_refuses_negotiation_scenario():
    out = json.loads(app.relay("sc.damages-threatened", json.dumps({"worker": "山田太郎"}),
                               "did:plc:worker", "employer-hash"))
    assert out["$type"] == "com.etzhayyim.kadode.escalation"
    assert out["relayed"] is False and out["escalateActor"] in (":labor-union", ":lawyer")


def test_relay_export_relays_non_negotiation_scenario():
    out = json.loads(app.relay("sc.permanent-cant-face", json.dumps({"worker": "山田太郎", "date": "令和8年7月15日"}),
                               "did:plc:worker", "employer-hash"))
    assert out["$type"] == "com.etzhayyim.kadode.resignationRelay"
    assert out["status"] == "drafted-unsent" and out["negotiates"] is False


def test_exports_deterministic():
    assert app.analyze() == app.analyze()
    assert app.datoms(1) == app.datoms(1)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
