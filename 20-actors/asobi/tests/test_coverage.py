#!/usr/bin/env python3
"""asobi 遊び — coverage-report tests (ADR-2606073200). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load  # noqa: E402
import coverage_report  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-asobi-graph.kotoba.edn"


def test_coverage_renders_and_is_honest():
    nodes, edges = load(SEED)
    md = coverage_report.report(nodes, edges)
    assert "coverage of all culture is ~0 by design" in md
    assert "Gap map" in md
    # both an open and an enclosed access category appear in a real seed
    assert "public-domain" in md and "proprietary" in md


def test_media_and_domains_present():
    nodes, _ = load(SEED)
    media = {n.get(":work/medium") for n in nodes.values() if n.get(":organism/kind") == ":work"}
    domains = {n.get(":practice/domain") for n in nodes.values() if n.get(":organism/kind") == ":practice"}
    assert ":music" in media and ":text" in media
    assert ":sport" in domains and ":music" in domains


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
