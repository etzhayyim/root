"""Offline test for the open-data KG cutover parity harness.

Tests the pure `diff_snapshots` core (the cutover-gate logic) and the etzhayyim
SQLite reader against a populated temp ingest_kg_open.db. The RW side and the
kotoba side are not exercised (no KOTOBA_URL / no live kotoba here) — they are guarded
and run only by an operator post-G1.
"""

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import parity_check as pc  # noqa: E402


def test_diff_parity_ok():
    rw = {"wikidata": pc.Snapshot("wikidata", {"Q1", "Q2"}),
          "crossref": pc.Snapshot("crossref", {"a1", "b2"})}
    etz = {"wikidata": pc.Snapshot("wikidata", {"Q1", "Q2"}),
           "crossref": pc.Snapshot("crossref", {"a1", "b2"})}
    rep = pc.diff_snapshots(rw, etz)
    assert rep["parity_ok"] is True, rep
    assert rep["sources"]["wikidata"]["count_diff"] == 0, rep


def test_diff_detects_drift():
    rw = {"wikidata": pc.Snapshot("wikidata", {"Q1", "Q2", "Q3"})}      # RW has Q3 extra
    etz = {"wikidata": pc.Snapshot("wikidata", {"Q1", "Q2", "Q9"})}     # etz has Q9 extra
    rep = pc.diff_snapshots(rw, etz)
    assert rep["parity_ok"] is False, rep
    s = rep["sources"]["wikidata"]
    assert s["missing_in_etz"] == 1 and s["missing_in_etz_sample"] == ["Q3"], s  # Q3 in RW not etz
    assert s["missing_in_rw"] == 1 and s["missing_in_rw_sample"] == ["Q9"], s    # Q9 in etz not RW
    assert s["parity_ok"] is False, s


def test_missing_source_one_side():
    rw = {"crossref": pc.Snapshot("crossref", {"a1"})}
    etz: dict = {}  # etzhayyim has not ingested crossref yet
    rep = pc.diff_snapshots(rw, etz)
    assert rep["parity_ok"] is False, rep
    assert rep["sources"]["crossref"]["missing_in_etz"] == 1, rep


def test_read_etz_sqlite():
    tmp = tempfile.TemporaryDirectory()
    db_path = os.path.join(tmp.name, "ingest_kg_open.db")
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE vertex_kg_entity (vertex_id TEXT PRIMARY KEY, id TEXT, source_id TEXT)")
        conn.executemany(
            "INSERT INTO vertex_kg_entity (vertex_id, id, source_id) VALUES (?,?,?)",
            [("v1", "Q156034", "wikidata"), ("v2", "Q35476", "wikidata"),
             ("v3", "deadbeef00000000", "crossref")],
        )
    snaps = pc.read_etz_sqlite(["wikidata", "crossref", "openstreetmap"], tmp.name)
    assert snaps["wikidata"].ids == {"Q156034", "Q35476"}, snaps["wikidata"].ids
    assert snaps["crossref"].count == 1, snaps["crossref"].count
    assert snaps["openstreetmap"].count == 0, "absent source → empty snapshot, not error"

    # end-to-end: a real etz snapshot vs a synthetic RW snapshot that matches it
    rw = {"wikidata": pc.Snapshot("wikidata", {"Q156034", "Q35476"}),
          "crossref": pc.Snapshot("crossref", {"deadbeef00000000"}),
          "openstreetmap": pc.Snapshot("openstreetmap", set())}
    rep = pc.diff_snapshots(rw, snaps)
    assert rep["parity_ok"] is True, rep


def test_missing_rw_url_raises():
    try:
        pc.read_rw(["wikidata"], rw_url=None)
        old = os.environ.pop("KOTOBA_URL", None)
        assert old is None, "test env unexpectedly had KOTOBA_URL"
        raise AssertionError("expected RuntimeError when KOTOBA_URL is absent")
    except RuntimeError as e:
        assert "KOTOBA_URL" in str(e), e


if __name__ == "__main__":
    os.environ.pop("KOTOBA_URL", None)
    test_diff_parity_ok()
    test_diff_detects_drift()
    test_missing_source_one_side()
    test_read_etz_sqlite()
    test_missing_rw_url_raises()
    print("kg-parity harness tests passed (diff core + sqlite reader + guards)!")
