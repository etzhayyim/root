"""test_analyze.py — 系図 (keizu) end-to-end membrane. ADR-2606066000."""
from __future__ import annotations

import json
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


_EMPTY_SEED = ('{:graph {:name "t" :visibility :public} '
               ':nodes [] :committees [] :rels [] :money [] :statements []}')


def test_empty_seed_report_renders_none_fallbacks():
    # the "(none in seed)" branches of _write_report only fire on an empty graph — exercise them
    with tempfile.TemporaryDirectory() as d:
        out = pathlib.Path(d)
        seed = out / "empty.edn"
        seed.write_text(_EMPTY_SEED, encoding="utf-8")
        res = analyze.run(seed_path=seed, out_dir=out)
        report = (out / "intel-report.md").read_text(encoding="utf-8")
        assert "(none in seed)" in report          # the empty-section fallbacks rendered
        assert "0 dangling reference(s)" in report  # empty graph has no dangling refs
        assert res["posts"] == []                   # no committee/money posts on an empty graph
        assert res["kanae_flows"]["flows"] == []    # nothing to export


def test_kanae_render_artifact_written():
    with tempfile.TemporaryDirectory() as d:
        out = pathlib.Path(d)
        res = analyze.run(out_dir=out)
        payload = json.loads((out / "kanae-render.json").read_text(encoding="utf-8"))
        assert payload["actor"] == "keizu" and payload["isMirror"] is True
        assert res["kanae_flows"]["flows"]            # fiscal flows exported
        assert res["kanae_flows"]["skipped_count"] >= 1   # political-donation skipped


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


def test_both_payee_and_payer_sides_reported():
    _, report, _ = _run()
    assert "by payee" in report and "by payer" in report


def test_connector_section_reported():
    _, report, _ = _run()
    assert "Cross-organ connector seats" in report


def test_by_jurisdiction_section_reported():
    _, report, _ = _run()
    assert "## By jurisdiction" in report


def test_statements_section_reported():
    _, report, _ = _run()
    assert "Statements (発言)" in report
    assert "never rated true/false" in report   # non-adjudicating framing


def test_integrity_line_reported_clean():
    _, report, _ = _run()
    assert "referential integrity: 0 dangling reference(s)" in report


def test_award_and_fund_section_is_non_adjudicating():
    _, report, _ = _run()
    assert "Award-and-fund co-occurrence" in report
    assert "NOT an allegation" in report   # G2 framing on the most sensitive section


def test_report_carries_no_verdict_language():
    from weave import VERDICT_TOKENS
    _, report, _ = _run()
    low = report.lower()
    # the report describes ties/shares; it must not assert wrongdoing
    for tok in ("corruption", "bribe", "guilty", "illegal", "汚職", "賄賂"):
        assert tok not in low, f"verdict token {tok!r} leaked into the report"
    assert VERDICT_TOKENS  # the closed list exists and is the single source


if __name__ == "__main__":
    run("analyze", [(k, v) for k, v in sorted(globals().items())
                    if k.startswith("test_") and callable(v)])
