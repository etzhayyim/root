"""test_analyze.py — 潮目 (shionome) end-to-end membrane + empty-graph path. ADR-2606072200."""
from __future__ import annotations

import pathlib
import tempfile

import analyze
from _t import run


def test_run_produces_outputs():
    with tempfile.TemporaryDirectory() as d:
        out = pathlib.Path(d)
        res = analyze.run(out_dir=out)
        assert (out / "intel-report.md").exists()
        assert (out / "kanae-render.json").exists()
        assert (out / "capital-flow-graph.kotoba.edn").exists()
        assert res["concentration"]["regime"]["regime"] == "risk-on"
        assert len(res["posts"]) == 3


def test_report_has_no_trade_disclaimer():
    with tempfile.TemporaryDirectory() as d:
        out = pathlib.Path(d)
        analyze.run(out_dir=out)
        text = (out / "intel-report.md").read_text(encoding="utf-8")
        assert "トレードはしない" in text
        assert "risk-on" in text


def test_empty_graph_path():
    # an empty seed exercises the "(none in seed)" fallbacks + empty posts
    with tempfile.TemporaryDirectory() as d:
        seed = pathlib.Path(d) / "empty.edn"
        seed.write_text("{:graph {:name \"empty\"} :buckets [] :flows [] :snapshots []}", encoding="utf-8")
        out = pathlib.Path(d) / "out"
        res = analyze.run(seed_path=seed, out_dir=out)
        assert res["concentration"]["bucket_count"] == 0
        assert res["posts"] == []
        assert "(none in seed)" in (out / "intel-report.md").read_text(encoding="utf-8")


def test_kanae_flows_skip_count():
    res = analyze.run(out_dir=pathlib.Path(tempfile.mkdtemp()))
    assert res["kanae_flows"]["skipped_count"] == 3


if __name__ == "__main__":
    run("analyze", [(n, f) for n, f in sorted(globals().items())
                    if n.startswith("test_") and callable(f)])
