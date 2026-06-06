"""test_sources.py — 系図 (keizu) public-source registry well-formedness + deny-list. ADR-2606066000.

Validates registry/sources.seed.json: required fields, valid kinds + mapsTo targets, the
unverified-seed safety state (G8), and the no-commercial-gov-intel deny-list (Charter Rider §2(e),
N5) — the structural gate keizu inherits from danjo G8.
"""
from __future__ import annotations

import json
import pathlib

from _t import run

REG = pathlib.Path(__file__).resolve().parents[1] / "registry" / "sources.seed.json"

SOURCE_KINDS = {"procurement", "budget", "political-finance", "committee-roster", "statements"}
MAPSTO_PREFIXES = {"node", "committee", "rel", "money", "statement"}
REQUIRED = ("sourceId", "title", "jurisdiction", "sourceKind", "authority", "datasetUrl",
            "legalBasis", "mapsTo", "verificationStatus")

# Charter Rider §2(e) / N5 — commercial gov-intelligence terminals are PROHIBITED as sources.
DENY = ("govwin", "bloomberg", "politico pro", "e&e news", "fiscalnote", "cq roll call",
        "四季報", "capital iq", "capiq", "refinitiv", "factset", "pitchbook", "crunchbase",
        "lexisnexis", "westlaw")


def _reg():
    return json.loads(REG.read_text(encoding="utf-8"))


def test_registry_parses_and_nonempty():
    r = _reg()
    assert r["sources"], "registry has no sources"
    assert r.get("freshnessWindowDays", 0) > 0


def test_every_source_has_required_fields():
    for s in _reg()["sources"]:
        for f in REQUIRED:
            assert s.get(f), f"{s.get('sourceId')!r} missing {f}"


def test_source_kinds_valid():
    for s in _reg()["sources"]:
        assert s["sourceKind"] in SOURCE_KINDS, (s["sourceId"], s["sourceKind"])


def test_mapsto_targets_valid():
    for s in _reg()["sources"]:
        targets = s["mapsTo"] if isinstance(s["mapsTo"], list) else [s["mapsTo"]]
        for t in targets:
            assert t.split(":")[0] in MAPSTO_PREFIXES, (s["sourceId"], t)


def test_all_unverified_seed():
    # G8 — nothing is verified yet, so no live ingest may run (safety default)
    for s in _reg()["sources"]:
        assert s["verificationStatus"] == "unverified-seed", s["sourceId"]


def test_urls_present_and_httpish():
    for s in _reg()["sources"]:
        assert s["datasetUrl"].startswith("http"), s["sourceId"]


def test_no_commercial_gov_intel_terminal():
    # Charter Rider §2(e) / N5 — the deny-list must not appear in any source's url/title/authority
    blob = json.dumps(_reg(), ensure_ascii=False).lower()
    hits = [d for d in DENY if d in blob]
    assert not hits, f"prohibited commercial gov-intel terminal in registry: {hits}"


def test_global_coverage():
    # the registry is global (the chosen scope) — multiple jurisdictions present
    juris = {s["jurisdiction"] for s in _reg()["sources"]}
    assert {"jp", "us", "eu"} <= juris, juris


if __name__ == "__main__":
    run("sources", [(k, v) for k, v in sorted(globals().items())
                    if k.startswith("test_") and callable(v)])
