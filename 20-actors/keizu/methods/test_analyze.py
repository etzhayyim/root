"""test_analyze.py — 系図 (keizu) end-to-end membrane. ADR-2606066000."""
from __future__ import annotations

import pathlib
import tempfile

import analyze
from _t import run


def _run():
    with tempfile.TemporaryDirectory() as d:
        out = pathlib.Path(d)
        res = analyze.run(out_dir=out)
        report = (out / "intel-report.md").read_text(encoding="utf-8")
        graph = (out / "relation-graph.kotoba.edn").read_text(encoding="utf-8")
        return res, report, graph


def test_runs_and_writes():
    res, report, graph = _run()
    assert res["concentration"]["node_count"] >= 15
    assert "keizu" in report
    assert ":rel/id" in graph


def test_report_is_mirror_and_non_adjudicating():
    _, report, _ = _run()
    assert "NOT a target-list" in report
    assert "Non-adjudicating" in report


def test_posts_are_dry_run():
    res, _, _ = _run()
    assert res["posts"], "expected at least one dry-run post"
    for p in res["posts"]:
        assert p[":post/status"] == ":dry-run"
        assert p[":post/server-held-key"] is False


def test_money_hhi_reported():
    _, report, _ = _run()
    assert "HHI=" in report


if __name__ == "__main__":
    run("analyze", [(k, v) for k, v in sorted(globals().items())
                    if k.startswith("test_") and callable(v)])
