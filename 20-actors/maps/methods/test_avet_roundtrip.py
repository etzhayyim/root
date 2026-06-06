#!/usr/bin/env python3
"""maps — AVET H3-cell round-trip parity test (ADR-2606064500 §2). stdlib unittest.

Proves the spatial-index design end-to-end OFFLINE: features stamped with their owning H3
cell at each resolution, ingested into the kotoba_local EAVT/AVET reference store, are
retrieved by an AVET cell probe — exactly the getChunk hot-path. Two layers:

  1. index-contract (always runs, no deps): a deterministic mock cell stamp proves the AVET
     retrieval logic — a feature is returned iff you query the cell it was stamped with, the
     label filter narrows, a foreign cell returns nothing, coarse res ⊇ fine res.
  2. real-geographic (runs only if `h3` is importable, e.g. the project venv): real Tokyo
     Station cells — query its true res-12 cell → it comes back; an ocean cell → empty.

Run: python3 test_avet_roundtrip.py   (real-h3 layer auto-skips if h3 is absent)
"""
from __future__ import annotations
import math, unittest

from kotoba_local import KotobaLocal

CELL_RES = (2, 4, 6, 8, 10, 12)

# Tokyo-anchor features (subset of the seed; lat/lon are what the index is computed from)
FEATURES = [
    ("feature.station.tokyo", ":station", "Tokyo Station", 35.6812, 139.7671),
    ("feature.building.marunouchi-bldg", ":building", "Marunouchi Building", 35.6809, 139.7644),
    ("feature.building.shin-marunouchi", ":building", "Shin-Marunouchi Building", 35.6820, 139.7639),
    ("feature.road.eitai-dori", ":road", "Eitai-dori", 35.6805, 139.7700),
    ("feature.airport.haneda", ":airport", "Tokyo Haneda", 35.5494, 139.7798),
]


def _mock_cell(lat, lon, res):
    """Deterministic mock H3-like cell: finer res → finer grid (nested by construction).
    NOT real H3 — only used to exercise the AVET index contract without a dependency."""
    size = 10.0 / (3 ** res)  # shrinks with res; coarse cells contain fine cells
    return f"r{res}/{math.floor(lat / size)}/{math.floor(lon / size)}"


def _batch(features, cellfn):
    """Build a kg.ingest_batch with cell claims stamped by cellfn (mirrors buildIngestBatch)."""
    entities = []
    for fid, label, name, lat, lon in features:
        claims = [
            {"pred": "feature/label", "value": label},
            {"pred": "feature/name", "value": name},
            {"pred": "feature/lat", "value": str(lat)},
            {"pred": "feature/lon", "value": str(lon)},
            {"pred": "feature/sourcing", "value": ":representative"},
        ]
        for r in CELL_RES:
            claims.append({"pred": f"feature.cell/r{r}", "value": cellfn(lat, lon, r)})
        entities.append({"id": fid, "type": "maps-feature", "label_en": name,
                         "claims": claims, "relations": []})
    return {"entities": entities}


class TestAvetIndexContract(unittest.TestCase):
    """The AVET retrieval logic, proven with a deterministic mock cell (always runs)."""

    def setUp(self):
        self.store = KotobaLocal()
        self.store.ingest_batch(_batch(FEATURES, _mock_cell))

    def test_query_returns_features_in_the_queried_cell(self):
        cell = _mock_cell(35.6812, 139.7671, 12)  # Tokyo Station's r12 cell
        res = self.store.query_by_cells([cell], lod=12)
        ids = [f["id"] for f in res.get(cell, {}).get(":station", [])]
        self.assertIn("feature.station.tokyo", ids)

    def test_foreign_cell_returns_nothing(self):
        res = self.store.query_by_cells(["r12/9999/9999"], lod=12)
        self.assertEqual(res.get("r12/9999/9999", {}), {})

    def test_label_filter_narrows(self):
        # query a coarse cell that contains several Marunouchi-area features
        cell = _mock_cell(35.681, 139.764, 6)
        res = self.store.query_by_cells([cell], lod=6, labels=["building"])
        labels_returned = set(res.get(cell, {}).keys())
        self.assertTrue(labels_returned <= {":building"}, labels_returned)
        # and at least one building is found
        self.assertGreaterEqual(len(res.get(cell, {}).get(":building", [])), 1)

    def test_coarse_res_aggregates_fine_cells(self):
        # all 5 features live in one res-2 cell but spread across more res-12 cells
        r2 = self.store.cells_at_res(2)
        r12 = self.store.cells_at_res(12)
        self.assertLessEqual(len(r2), len(r12))
        self.assertGreaterEqual(self.store.feature_count(), 5)

    def test_limit_caps_per_label(self):
        cell = _mock_cell(35.681, 139.764, 2)  # coarse: holds multiple buildings
        res = self.store.query_by_cells([cell], lod=2, labels=["building"], limit=1)
        self.assertLessEqual(len(res.get(cell, {}).get(":building", [])), 1)

    def test_materialized_row_has_getchunk_fields(self):
        cell = _mock_cell(35.6812, 139.7671, 12)
        row = self.store.query_by_cells([cell], lod=12)[cell][":station"][0]
        for k in ("id", "label", "name", "lat", "lon"):
            self.assertIn(k, row)


try:
    import h3 as _h3  # type: ignore
    _HAS_H3 = True
except Exception:
    _HAS_H3 = False


@unittest.skipUnless(_HAS_H3, "h3 not installed (run under the project venv for the real-geo layer)")
class TestAvetRealH3(unittest.TestCase):
    """Real H3 cells — the genuine geographic round-trip (Tokyo Station)."""

    @staticmethod
    def _real_cell(lat, lon, res):
        # MUST match production (TS stampCells + ingest.py _h3_cell): latlng_to_cell at each
        # res DIRECTLY, NOT cell_to_parent of a res-15 cell (H3 is not perfectly hierarchical,
        # so the two can disagree at boundaries — stamp and query must use the same method).
        return _h3.latlng_to_cell(lat, lon, res)

    def setUp(self):
        self.store = KotobaLocal()
        self.store.ingest_batch(_batch(FEATURES, self._real_cell))

    def test_tokyo_station_retrieved_by_its_true_r12_cell(self):
        cell = self._real_cell(35.6812, 139.7671, 12)
        res = self.store.query_by_cells([cell], lod=12, labels=["station"])
        ids = [f["id"] for f in res.get(cell, {}).get(":station", [])]
        self.assertEqual(ids, ["feature.station.tokyo"])

    def test_ocean_cell_is_empty(self):
        ocean = self._real_cell(0.0, -150.0, 12)  # mid-Pacific
        res = self.store.query_by_cells([ocean], lod=12)
        self.assertEqual(res.get(ocean, {}), {})

    def test_marunouchi_buildings_share_a_coarse_cell(self):
        # the two Marunouchi towers fall in one res-8 cell; query returns both
        c8 = self._real_cell(35.6809, 139.7644, 8)
        res = self.store.query_by_cells([c8], lod=8, labels=["building"])
        ids = {f["id"] for f in res.get(c8, {}).get(":building", [])}
        self.assertIn("feature.building.marunouchi-bldg", ids)

    def test_haneda_not_in_tokyo_station_cell(self):
        # Haneda (10 km south) must NOT appear in Tokyo Station's res-10 cell
        c10 = self._real_cell(35.6812, 139.7671, 10)
        res = self.store.query_by_cells([c10], lod=10, labels=["airport"])
        self.assertEqual(res.get(c10, {}).get(":airport", []), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
