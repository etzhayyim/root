#!/usr/bin/env python3
"""tanemaki 種蒔き — WASM component entry tests (ADR-2606122000). Pure stdlib, NETWORK-FREE."""
import sys, json, pathlib
ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "wasm"))
sys.path.insert(0, str(ACTOR_DIR / "methods"))
import app  # noqa: E402


def test_analyze_export_shape():
    out = json.loads(app.analyze())
    assert set(out) == {"orgs", "criteria", "decidedBy"}
    assert out["decidedBy"] == "1-sbt-1-vote"  # G1 surfaces in the export itself
    # G1 in the WASM export: no conflicted org is proposable
    for oid, r in out["orgs"].items():
        if r["conflicts"]:
            assert r["route"] == ":excluded", f"{oid} conflicted but {r['route']}"
        assert r["synthetic"] is True  # G6


def test_datoms_export_is_eavt_edn():
    edn = app.datoms(7)
    assert edn.lstrip().startswith(";;") and " 7 :add]" in edn
    assert ":bond/is-transient true" in edn


def test_coverage_export_is_markdown():
    md = app.coverage()
    assert md.startswith("# tanemaki") and "holds for all orgs" in md


def test_scorecard_export_is_advisory():
    md = app.scorecard("org.osslib")
    assert "参考意見" in md and "1 SBT = 1 vote" in md and "FICTIONAL" in md


def test_propose_export_refuses_excluded_org():
    out = json.loads(app.propose("org.surveil-vendor", 0, ":grant", ""))
    assert out["refused"] is True and "REFUSAL" in out["reason"]


def test_propose_export_refuses_investment_instrument():
    out = json.loads(app.propose("org.foodbank", 0, ":equity", ""))
    assert out["refused"] is True and "G2" in out["reason"]


def test_propose_export_builds_advisory_record():
    out = json.loads(app.propose("org.foodbank", 5_000_000_000, ":grant", "食料再分配 commons"))
    assert out["$type"] == "com.etzhayyim.tanemaki.grantProposal"
    assert out["advisory"] is True and out["bindsFund"] is False
    assert out["status"] == "drafted-unsent" and out["decidedBy"] == "1-sbt-1-vote"


def test_exports_deterministic():
    assert app.analyze() == app.analyze()
    assert app.datoms(1) == app.datoms(1)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
