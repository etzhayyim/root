"""test_sources.py — 潮目 (shionome) public-source registry seed integrity. ADR-2606072200."""
from __future__ import annotations

import json
import pathlib

from _t import run

REG = pathlib.Path(__file__).resolve().parents[1] / "registry" / "sources.seed.json"
DENY = ("bloomberg", "refinitiv", "eikon", "factset", "capital iq", "capiq", "morningstar direct",
        "pitchbook", "四季報")


def _reg():
    return json.loads(REG.read_text(encoding="utf-8"))


def test_registry_loads():
    assert "sources" in _reg()


def test_at_least_ten_sources():
    assert len(_reg()["sources"]) >= 10


def test_every_source_unverified_seed_g8():
    for s in _reg()["sources"]:
        assert s["verificationStatus"] == "unverified-seed", s["sourceId"]


def test_every_source_has_required_fields():
    for s in _reg()["sources"]:
        for k in ("sourceId", "title", "jurisdiction", "authority", "datasetUrl", "mapsTo"):
            assert k in s and s[k], (s.get("sourceId"), k)


def test_no_commercial_terminal_source():
    blob = json.dumps(_reg(), ensure_ascii=False).lower()
    # the deny terms may appear only inside the _comment (which names them to prohibit them)
    comment = _reg().get("_comment", "").lower()
    for d in DENY:
        in_sources = blob.replace(comment, "")
        assert d not in in_sources, f"prohibited terminal {d!r} present as a source"


def test_source_ids_unique():
    ids = [s["sourceId"] for s in _reg()["sources"]]
    assert len(ids) == len(set(ids))


def test_mapsto_targets_known_kinds():
    ok_prefix = ("flow:", "snap:")
    for s in _reg()["sources"]:
        for m in s["mapsTo"]:
            assert m.startswith(ok_prefix), m


def test_covers_multiple_asset_classes():
    kinds = {s["sourceKind"] for s in _reg()["sources"]}
    # rates, equities/fund flows, commodities, crypto, real-estate represented
    assert len(kinds) >= 6


if __name__ == "__main__":
    run("sources", [(n, f) for n, f in sorted(globals().items())
                    if n.startswith("test_") and callable(f)])
