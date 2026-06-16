#!/usr/bin/env python3
"""aburi 炙り — coverage-report tests (ADR-2606161630). Pure stdlib."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

from analyze import load  # noqa: E402
import coverage_report  # noqa: E402

SEED = ACTOR_DIR / "data" / "seed-tracker-exposure.kotoba.edn"


def test_report_renders_all_spines():
    nodes, edges = load(SEED)
    md = coverage_report.report(nodes, edges)
    for spine in ("Surface-kind coverage", "Permission-kind coverage", "Collector-kind coverage",
                  "Collector-catalogue coverage", "Data-type-kind coverage", "Gap map"):
        assert spine in md, f"coverage report missing spine: {spine}"


def test_every_collector_catalogue_bucket_is_a_real_provenance():
    """G5: every catalogue bucket the report counts is a real public source (no invented source)."""
    valid = {":exodus", ":apple-privacy", ":play-data-safety", ":sellers-json", ":iab"}
    for k in coverage_report.CATALOGS:
        assert k in valid, f"coverage tracks a non-public catalogue bucket: {k}"


def test_backbone_kinds_present():
    """The covered backbone (the kinds the seed actually exercises) must be non-empty."""
    nodes, _ = load(SEED)
    surf = {n.get(":surface/kind") for n in nodes.values() if n.get(":organism/kind") == ":surface"}
    col = {n.get(":collector/kind") for n in nodes.values() if n.get(":organism/kind") == ":collector"}
    assert {":search", ":social", ":app-store"} <= surf, f"surface backbone thin: {surf}"
    assert {":ad-network", ":data-broker", ":analytics"} <= col, f"collector backbone thin: {col}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
