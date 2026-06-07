"""test_analyze.py — 高札 (kosatsu) analyze + social + ingest + bridge. ADR-2606072000."""
from __future__ import annotations

import json
import pathlib
import tempfile

from _edn import load_edn
from _t import expect_raises, run
import analyze
import bridge
import ingest
import social
from weave import weave

SEED = pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-designation-graph.kotoba.edn"


def _g():
    return weave(load_edn(SEED))


# ── analyze ───────────────────────────────────────────────────────────────────
def test_analyze_renders_md():
    md = analyze.render(_g())
    assert "競" not in md  # sanity: ascii-safe headers
    assert "Mirror, not a verdict" in md
    assert "Divergence" in md
    assert "Delisting timeline" in md


def test_analyze_main_writes_file():
    path = analyze.main()
    assert pathlib.Path(path).exists()
    assert "kosatsu" in pathlib.Path(path).read_text(encoding="utf-8")


# ── social (dry-run posts) ────────────────────────────────────────────────────
def test_social_posts_are_dry_run_mirror():
    ps = social.posts(_g())
    assert ps, "expected at least the summary post"
    for p in ps:
        assert p[":post/status"] == ":dry-run"
        assert p[":post/is-mirror"] is True
        assert p[":post/non-adjudicating-notice"] is True
        assert p[":post/server-held-key"] is False
        assert len(p[":post/sources"]) >= 2
        assert p[":post/body"].startswith("[mirror")


def test_social_has_contested_post():
    ps = social.posts(_g())
    subjects = [p[":post/subject"] for p in ps]
    assert any("contested" in s for s in subjects)


# ── ingest (offline; --live refused) ──────────────────────────────────────────
def test_ingest_live_refused():
    assert ingest.main(["ingest.py", "--live"]) == 2


def test_ingest_offline_normalizes_and_validates():
    payload = {
        "authorities": [{"id": "us-ofac", "kind": "state-treasury", "label": "OFAC",
                          "jurisdiction": "us", "stance": "IEEPA programs",
                          "sources": ["https://ofac.treasury.gov/"]}],
        "subjects": [{"id": "s1", "kind": "designated-entity", "label": "E1"}],
        "designations": [{"id": "d1", "asserter": "us-ofac", "subject": "s1",
                          "measure": "financial-sanction", "program": "EO X",
                          "status": "listed", "posted_at": 20230101,
                          "sources": ["https://ofac.treasury.gov/a", "https://ofac.treasury.gov/b"]}],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        p = f.name
    out = ingest.ingest_file(p)
    assert out["designations"][0][":designation/asserted-notice"] is True


def test_ingest_rejects_verdict_measure():
    payload = {"authorities": [], "subjects": [],
               "designations": [{"id": "d1", "asserter": "us-ofac", "subject": "s1",
                                 "measure": "criminal", "status": "listed", "posted_at": 20230101,
                                 "sources": ["https://ofac.treasury.gov/a", "https://ofac.treasury.gov/b"]}]}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        p = f.name
    expect_raises(lambda: ingest.ingest_file(p), contains="G2")


# ── bridge (cross-actor join keys) ────────────────────────────────────────────
def test_bridge_join_keys_advisory():
    keys = bridge.join_keys(_g())
    assert keys
    # subj-vessel-1 is currently listed → present; wallet/domain would route to tadori
    subs = {k["subject"] for k in keys}
    assert "subj-vessel-1" in subs
    for k in keys:
        assert "enforcement" in k["note"]  # the no-target reminder


def test_bridge_tsumugi_en_edges():
    edges = bridge.tsumugi_en_edges(_g())
    assert edges
    for e in edges:
        assert e["kind"] == "designation-power"
        assert e["from"] and e["to"]


if __name__ == "__main__":
    run("analyze", [(k, v) for k, v in sorted(globals().items())
                    if k.startswith("test_") and callable(v)])
