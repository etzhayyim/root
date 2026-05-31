"""Offline test for the NDL OAI-PMH metadata ingest worker.

Fixtures are REAL NDL OAI-PMH records captured 2026-05-31 from
``ndlsearch.ndl.go.jp`` (verb=ListRecords&metadataPrefix=oai_dc&
from=2024-01-01&until=2024-01-02) — see ADR-2605312000. This grounds the parser
against the real feed shape: header identifier ``R100000039-I{n}`` (a catalogue
key, NOT a digital PID), empty ``dc:identifier``, ``ndl-dl-open`` online setSpec,
and the real ``resumptionToken`` placement. ``ndl._http_get`` is monkeypatched so
the test runs with no network and no RW.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

tmp_dir = tempfile.TemporaryDirectory()
os.environ["ORGANISM_SQLITE_DIR"] = tmp_dir.name
os.environ["BELIEF_STORE_BACKEND"] = "at-ipfs-local"

sys.path.insert(0, str(Path("20-actors/magatama/py/src").absolute()))

from pymagatama.ingest import ndl  # noqa: E402

_OAI_OPEN = (
    '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" '
    'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
    "<responseDate>2026-05-31T20:14:29Z</responseDate>"
)

# REAL record 0 (digitised + open: setSpec ndl-dl-open; empty dc:identifier).
_REC_0 = (
    "<record><header>"
    "<identifier>oai:ndlsearch.ndl.go.jp:R100000039-I3388038</identifier>"
    "<datestamp>2024-01-01T15:39:40Z</datestamp>"
    "<setSpec>A00000</setSpec><setSpec>A00002</setSpec><setSpec>ARkannai</setSpec>"
    "<setSpec>book</setSpec><setSpec>ndl-dl</setSpec><setSpec>ndl-dl-doi</setSpec>"
    "<setSpec>ndl-dl-open</setSpec></header><metadata>"
    '<oai_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/">'
    "<dc:title>病院</dc:title>"
    "<dc:description>本タイトル等は最新号による</dc:description>"
    "<dc:publisher>医学書院</dc:publisher><dc:language>jpn</dc:language>"
    "</oai_dc:dc></metadata></record>"
)

# REAL record 1 (also ndl-dl-open; has dc:creator).
_REC_1 = (
    "<record><header>"
    "<identifier>oai:ndlsearch.ndl.go.jp:R100000039-I2747011</identifier>"
    "<datestamp>2024-01-01T15:39:40Z</datestamp>"
    "<setSpec>A00000</setSpec><setSpec>book</setSpec>"
    "<setSpec>ndl-dl</setSpec><setSpec>ndl-dl-open</setSpec></header><metadata>"
    '<oai_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/">'
    "<dc:title>税務経理</dc:title><dc:creator>時事通信社 [編]</dc:creator>"
    "<dc:publisher>時事通信社</dc:publisher><dc:language>jpn</dc:language>"
    "</oai_dc:dc></metadata></record>"
)

# Synthetic NON-online record (no ndl-dl-open) — must be filtered out.
_REC_OFFLINE = (
    "<record><header>"
    "<identifier>oai:ndlsearch.ndl.go.jp:R100000002-I9999999</identifier>"
    "<datestamp>2024-01-01T10:00:00Z</datestamp>"
    "<setSpec>A00000</setSpec><setSpec>book</setSpec></header><metadata>"
    '<oai_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/">'
    "<dc:title>非公開資料</dc:title></oai_dc:dc></metadata></record>"
)

# Real-shaped resumptionToken (cursor string from the live feed).
_REAL_TOKEN = "oai_dc/2024-01-01T00:00:00Z/2024-01-02T23:59:59Z//200/1704091180285_R100000039-I3388038"

PAGE_1 = (
    _OAI_OPEN + "<ListRecords>" + _REC_0 + _REC_OFFLINE
    + f"<resumptionToken>{_REAL_TOKEN}</resumptionToken>"
    + "</ListRecords></OAI-PMH>"
)
PAGE_2 = (
    _OAI_OPEN + "<ListRecords>" + _REC_1
    + "<resumptionToken></resumptionToken>"
    + "</ListRecords></OAI-PMH>"
)


def _install_fake_http():
    calls = {"n": 0}

    def fake_get(url: str, accept: str = "application/xml", timeout: float = 60.0) -> bytes:
        calls["n"] += 1
        if "resumptionToken=" in url and _REAL_TOKEN.split("/")[0] in url:
            return PAGE_2.encode("utf-8")
        return PAGE_1.encode("utf-8")

    ndl._http_get = fake_get  # type: ignore[assignment]
    return calls


async def test_ndl_oai_flow():
    calls = _install_fake_http()

    created = await ndl.task_ndl_create_run(mode="delta")
    assert created["ok"] and created["runId"], created
    run_id = created["runId"]

    plan = await ndl.task_ndl_oai_plan(setGroup="online", maxWindows=3)
    assert plan["ok"] and plan["plannedShards"] >= 1, plan
    first = plan["firstShard"]
    shard_key = first["shardKey"]

    lock = await ndl.task_ndl_acquire_cursor(runId=run_id, firstShard=first)
    assert lock["ok"] and lock["cursorVertexId"], lock

    fetched = await ndl.task_ndl_oai_fetch_window(
        runId=run_id,
        setGroup=first["setGroup"],
        metadataPrefix=first["metadataPrefix"],
        windowStart=first["windowStart"],
        windowEnd=first["windowEnd"],
        maxPages=25,
    )
    assert fetched["ok"], fetched
    # 2 pages, window complete; 2 ndl-dl-open items persisted (offline one filtered).
    assert fetched["complete"] is True, fetched
    assert fetched["pagesThisRun"] == 2, fetched
    assert fetched["itemsInserted"] == 2, fetched
    assert calls["n"] == 2, calls

    verify = await ndl.task_ndl_verify_visibility(
        setGroup=first["setGroup"],
        windowStart=first["windowStart"],
        windowEnd=first["windowEnd"],
    )
    assert verify["verified"] is True, verify
    assert verify["providerItemTotal"] == 2, verify

    advanced = await ndl.task_ndl_advance_cursor(runId=run_id, shardKey=shard_key, complete=True)
    assert advanced["ok"], advanced

    done = await ndl.task_ndl_complete_run(
        runId=run_id, status="completed", itemsInserted=fetched["itemsInserted"]
    )
    assert done["ok"], done

    # Resume idempotency: re-plan must skip the now-completed window.
    plan2 = await ndl.task_ndl_oai_plan(setGroup="online", maxWindows=3)
    assert all(s["shardKey"] != shard_key for s in plan2["shards"]), plan2

    # Field fidelity vs the REAL record shape.
    with ndl.sync_cursor() as cur:
        cur.execute(
            "SELECT ndl_id, title, publisher, digital_pid, manifest_url, set_specs, source_url "
            "FROM vertex_ndl_bib_item WHERE ndl_id = 'R100000039-I3388038'"
        )
        row = cur.fetchone()
    assert row is not None, "record R100000039-I3388038 not persisted"
    assert row[0] == "R100000039-I3388038", row          # ndl_id = header minus oai: prefix
    assert row[1] == "病院", row                          # title
    assert row[2] == "医学書院", row                       # publisher
    assert row[3] == "", f"digital_pid must be empty (bib id is NOT a PID): {row[3]!r}"
    assert row[4] == "", f"no bogus IIIF manifest from a bib id: {row[4]!r}"
    assert "ndl-dl-open" in row[5], row                    # set_specs preserved
    assert row[6] == "https://ndlsearch.ndl.go.jp/books/R100000039-I3388038", row[6]

    # The offline record must NOT be present.
    with ndl.sync_cursor() as cur:
        cur.execute("SELECT count(*) FROM vertex_ndl_bib_item WHERE ndl_id = 'R100000002-I9999999'")
        assert int((cur.fetchone() or [0])[0] or 0) == 0, "non-online record leaked past the setSpec filter"

    print("ndl_worker OAI-PMH metadata ingest tests passed (real-fixture grounded)!")


if __name__ == "__main__":
    asyncio.run(test_ndl_oai_flow())
