"""Offline test for the open-data KG ingest worker (wikidata + crossref).

Fixtures are REAL response shapes captured 2026-05-31 from the live endpoints
(query.wikidata.org/sparql and api.crossref.org/works) — see ADR-2605312100 — so
the parser is grounded against the real feeds. `kg_open._http_get` is
monkeypatched so the test runs with no network and no RW.
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

tmp_dir = tempfile.TemporaryDirectory()
os.environ["ORGANISM_SQLITE_DIR"] = tmp_dir.name
os.environ["BELIEF_STORE_BACKEND"] = "at-ipfs-local"

sys.path.insert(0, str(Path("20-actors/magatama/py/src").absolute()))

from pymagatama.ingest import kg_open  # noqa: E402

# REAL wikidata SPARQL JSON shape (item uri → Q-number; itemLabel with xml:lang).
# Row 3 carries an email → must be dropped by the PII screen.
_WIKIDATA_JSON = json.dumps({
    "results": {"bindings": [
        {"item": {"type": "uri", "value": "http://www.wikidata.org/entity/Q156034"},
         "itemLabel": {"xml:lang": "ja", "type": "literal", "value": "パイオニア"}},
        {"item": {"type": "uri", "value": "http://www.wikidata.org/entity/Q35476"},
         "itemLabel": {"xml:lang": "en", "type": "literal", "value": "Toyota"}},
        {"item": {"type": "uri", "value": "http://www.wikidata.org/entity/Q999999"},
         "itemLabel": {"xml:lang": "en", "type": "literal", "value": "contact me@example.com"}},
    ]}
})

# REAL crossref REST JSON shape (DOI + title[] list).
_CROSSREF_JSON = json.dumps({
    "message": {"items": [
        {"DOI": "10.1007/978-3-658-17671-6_18-1", "title": ["Soziale Innovation"],
         "author": [{"family": "Doe"}], "published": {}},
        {"DOI": "10.1000/xyz123", "title": ["A Second Work"], "author": [], "published": {}},
        {"DOI": "", "title": ["No DOI — dropped"]},  # no DOI → extractor returns None
    ]}
})

# REAL OSM Overpass JSON shape (node + tags with name:ja / place).
_OSM_JSON = json.dumps({
    "elements": [
        {"type": "node", "id": 57542483, "lat": 35.64, "lon": 139.69,
         "tags": {"name": "目黒区", "name:ja": "目黒区", "name:en": "Meguro", "place": "city"}},
        {"type": "node", "id": 265018692, "lat": 35.68, "lon": 139.76,
         "tags": {"name": "東京都", "name:ja": "東京都", "name:en": "Tokyo", "place": "city"}},
        {"type": "node", "id": 999, "lat": 0, "lon": 0, "tags": {"place": "city"}},  # no name → dropped
    ]
})


def _install_fake_http():
    def fake_get(url: str, accept: str = "application/json", timeout: float = 180.0,
                 data: bytes | None = None) -> bytes:
        if "overpass" in url:
            return _OSM_JSON.encode("utf-8")
        if "wikidata" in url or "sparql" in accept:
            return _WIKIDATA_JSON.encode("utf-8")
        return _CROSSREF_JSON.encode("utf-8")

    kg_open._http_get = fake_get  # type: ignore[assignment]


async def test_kg_open_flow():
    _install_fake_http()

    created = await kg_open.task_kgopen_create_run(sourceId="wikidata")
    assert created["ok"] and created["runId"], created
    run_id = created["runId"]

    plan = await kg_open.task_kgopen_plan()
    # gBiz is out of scope (not migrated); the worker carries only the 3 verified
    # clean-public sources.
    assert set(plan["knownSources"]) == {"wikidata", "crossref", "openstreetmap"}, plan
    assert set(plan["verifiedSources"]) == {"wikidata", "crossref", "openstreetmap"}, plan
    assert "japan_company_registry" not in plan["knownSources"], plan

    # ── wikidata ──
    lock = await kg_open.task_kgopen_acquire_cursor(runId=run_id, sourceId="wikidata")
    assert lock["ok"], lock
    wd = await kg_open.task_kgopen_fetch_source(runId=run_id, sourceId="wikidata")
    assert wd["ok"], wd
    assert wd["rawFetched"] == 3, wd
    assert wd["piiDropped"] == 1, f"PII row (email) must be screened: {wd}"
    assert wd["inserted"] == 2, wd

    # ── crossref ──
    cr = await kg_open.task_kgopen_fetch_source(runId=run_id, sourceId="crossref")
    assert cr["ok"], cr
    assert cr["inserted"] == 2, f"the no-DOI item must be dropped: {cr}"

    # ── openstreetmap ──
    osm = await kg_open.task_kgopen_fetch_source(runId=run_id, sourceId="openstreetmap")
    assert osm["ok"], osm
    assert osm["inserted"] == 2, f"the nameless node must be dropped: {osm}"

    verify_wd = await kg_open.task_kgopen_verify_visibility(sourceId="wikidata")
    assert verify_wd["verified"] and verify_wd["entityTotal"] == 2, verify_wd
    verify_cr = await kg_open.task_kgopen_verify_visibility(sourceId="crossref")
    assert verify_cr["entityTotal"] == 2, verify_cr

    await kg_open.task_kgopen_advance_cursor(runId=run_id, sourceId="wikidata", complete=True)
    done = await kg_open.task_kgopen_complete_run(runId=run_id, inserted=4)
    assert done["ok"], done

    # Field fidelity vs the real shapes.
    with kg_open.sync_cursor() as cur:
        cur.execute("SELECT qid, type, label_ja, label_en, license, extractor, confidence "
                    "FROM vertex_kg_entity WHERE qid = 'Q156034'")
        wd_row = cur.fetchone()
        cur.execute("SELECT qid, type, label_en, source_id FROM vertex_kg_entity "
                    "WHERE qid = 'doi:10.1007/978-3-658-17671-6_18-1'")
        cr_row = cur.fetchone()
    assert wd_row is not None, "wikidata Q156034 not persisted"
    assert wd_row[0] == "Q156034" and wd_row[2] == "パイオニア" and wd_row[3] is None, wd_row  # ja label
    assert wd_row[4] == "CC0" and wd_row[5] == "sparql-v1" and abs(wd_row[6] - 0.95) < 1e-9, wd_row
    assert cr_row is not None and cr_row[1] == "schema:ScholarlyArticle", cr_row
    assert cr_row[2] == "Soziale Innovation" and cr_row[3] == "crossref", cr_row

    with kg_open.sync_cursor() as cur:
        cur.execute("SELECT type, label_ja, label_en, license FROM vertex_kg_entity "
                    "WHERE qid = 'osm:node57542483'")
        osm_row = cur.fetchone()
    assert osm_row is not None, "osm 目黒区 not persisted"
    assert osm_row[0] == "schema:City" and osm_row[1] == "目黒区" and osm_row[2] is None, osm_row
    assert osm_row[3] == "ODbL", osm_row

    print("kg_open worker tests passed (real-fixture grounded: wikidata + crossref + openstreetmap)!")


if __name__ == "__main__":
    asyncio.run(test_kg_open_flow())
