# maps — legacy RisingWave → kotoba-native migration map (ADR-2606064500)

The `com.etzhayyim.maps.kg.*` lexicons + `maps-spatial-ontology.kotoba.edn` supersede the
legacy maps RisingWave/Hyperdrive store. This file maps the old surfaces to the new ones.
It is the static-feature counterpart of `com/etzhayyim/watari/MIGRATION-NOTES.md` (which
already migrated the *moving-craft* slice — live ship/aircraft fixes).

## Substrate

| | Legacy | kotoba-native (this ADR) |
|---|---|---|
| Canonical store | RisingWave `vertex_spatial` (+ `vertex_osm_element`, `edge_osm_way_node`, `vertex_legal_entity`, `vertex_registry`, `vertex_maps_trip/stop_time`, `vertex_maps_gsplat_*`) via Hyperdrive | kotoba Datom log (`:feature/*`, `:feature.rel/*`, `:geo.alias/*`) |
| Spatial index | `(label, lat, lng)` BTREE; bbox `SELECT` | H3-cell-as-Datom + **AVET** (`:feature.cell/rN`); per-cell index probe |
| Read | `getDb().selectFrom("vertex_spatial").where(...).execute()` | `src/kotoba-spatial.ts` `queryByCells()` → AVET probe |
| Write | `getDb().insertInto("vertex_spatial").onConflict().execute()` + dumper `psycopg2` | `kg.ingest_batch` (member/operator-signed, no-server-key) |
| Identity / provenance | `vertex_id` PK + `source_did` column | `:feature/id` unique-identity + `:feature/source-did` (path DID preserved) |
| 51 node labels | the `label` column (Place/Road/Building/…) | `:feature/label` keyword discriminator |
| `props` JSON bag | `props` text column | `:feature/props` (read-through; query keys promoted to first-class attrs) |
| Topology edges | `edge_*` tables | `:feature.rel/*` ref datoms (VAET reverse traversal) |
| 32-scheme geo identity | `GeoAlias` / `vertex_spatial` rows | `:geo.alias/*` |

## Lexicon mapping

| Legacy lexicon | kotoba-native | Note |
|---|---|---|
| `com.etzhayyim.apps.maps.getChunk` | `com.etzhayyim.maps.kg.queryChunk` | H3-cell AVET probe; same GeoJSON output shape, adds `servedBy` |
| `com.etzhayyim.apps.maps.tileGeoJson` | `com.etzhayyim.maps.kg.queryChunk` | bbox→cells at ingest; one read surface |
| `com.etzhayyim.apps.maps.seedBuildings` | `com.etzhayyim.maps.kg.registerFeature` (batched) | write → `kg.ingest_batch`; idempotency via `:feature/id` unique-identity, not DELETE+INSERT |
| `com.etzhayyim.apps.maps.register*` (47 record kinds) | `com.etzhayyim.maps.kg.registerFeature` | all collapse onto `:feature/*` + `:feature/label` |
| `com.etzhayyim.apps.maps.aismarine` / `aircraftLive` | `com.etzhayyim.watari.*` | already migrated (ADR-2606041827) |

## Status

R0 (ADR-2606064500): ontology + adapter + `queryChunk` rewired kotoba-first (fail-open to
RisingWave) + offline-verified `ingest.py`/`analyze.py`. The legacy `com.etzhayyim.apps.maps.*`
surfaces remain live and serve through the RisingWave fallback until R3 removes Hyperdrive.
Do not delete the legacy lexicons before R3 (parity must be proven live first).
