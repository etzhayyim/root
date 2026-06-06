---
id: adr-2606064500-maps-kotoba-native-substrate-migration
title: "ADR-2606064500: maps — kotoba-native substrate migration (vertex_spatial → Datom log, H3-cell AVET spatial index)"
status: proposed
doc_type: adr
topic: maps-kotoba-native-migration
authoritative: true
last_verified: 2026-06-06
priority: 5.0
axis: architecture
weight: 0.55
priority_note: ""
authoritative_for:
  - maps.etzhayyim.com spatial substrate migration off RisingWave/Hyperdrive onto the kotoba Datom log
  - the H3-cell-as-Datom + AVET spatial-index design for kotoba geospatial reads
  - maps actor kotoba-native ontology, lexicons, ingest/analyze methods, migration phases
depends_on:
  - "2606041827"
  - "2605262130"
  - "2605312345"
  - "2605215000"
  - "2605231525"
  - "2605241500"
  - "2605192200"
related:
  - "2604271800"
  - "2604280900"
  - "2605011500"
  - "2605215100"
  - "2605312200"
  - "2606011500"
supersedes: []
superseded_by: []
---

# ADR-2606064500: maps — kotoba-native substrate migration

**Status**: proposed
**Date**: 2026-06-06
**Deciders**: Jun Kawasaki

# Context

The question *「maps.etzhayyim.com を kotoba に refactor」* sits on a hard substrate
violation. **maps is the single largest RisingWave/Hyperdrive dependency left in the
monorepo.** Its appview Worker (`60-apps/etzhayyim-project-maps/appview/maps-ui-uqpel6i6`)
is **100% Hyperdrive-bound**: all 172 XRPC commands read/write a RisingWave `vertex_spatial`
table (plus `vertex_osm_element`, `edge_osm_way_node`, `vertex_legal_entity`,
`vertex_registry`, `vertex_maps_trip/stop_time`, `vertex_maps_gsplat_*`), and five K8s
bulk-ingest dumpers `INSERT` into RisingWave over `psycopg2`.

This directly violates **ADR-2605262130** (kotoba Datom log is first-class canonical state;
NO RisingWave / centralized SQL) and **ADR-2605312345** (the Datom log, not a projection,
is the canonical home of state). It is the same violation **watari 渡り** (ADR-2606041827)
already corrected for the *moving-craft* slice — watari superseded the legacy
`maps.aismarine` / `maps.aircraft_live` RisingWave pipelines with a kotoba-native
`moving-craft-ontology` (live ship/aircraft *position fixes* as an append-only as-of log).

**watari fixed the DYNAMIC half. This ADR fixes the STATIC half** — the placed geographic
features (Place, Road, Building, River, AdminArea, Port, Airport, Station, legal entities,
registries, transit, satellite scenes) that live in `vertex_spatial` and friends. Together
the two ontologies retire the entire maps RisingWave footprint.

## Why this is hard (and why watari's pattern doesn't transfer unchanged)

watari's read path is an **offline aggregate** (`analyze.py` over a bounded seed). maps'
read path is a **live hot-path with a latency budget**: `cmdGetChunk` must return per-cell
GeoJSON in **<50 ms** for the maps-3d walkable streamer and the 2D vector overlay. The legacy
query —

```sql
SELECT * FROM vertex_spatial
WHERE label IN (:labels) AND lng BETWEEN :w AND :e AND lat BETWEEN :s AND :n
LIMIT :cap
```

— rode a composite `(label, lat, lng)` BTREE (empty-bbox 2.1 s → 50 ms after the index,
per the maps CLAUDE.md). **kotoba has no SQL and no R-tree/GiST.** So the central design
question the user posed — *「getChunk の <50ms bbox 検索をどう kotoba-native で実現するか」* —
must be answered before any code moves.

# Decision

## §1 — Generalize watari: one kotoba-native ontology for all static features

New vocabulary **`00-contracts/schemas/maps-spatial-ontology.kotoba.edn`** (`:feature/*`).
The 51 legacy `vertex_spatial` node labels collapse onto a single `:feature/*` entity with a
`:feature/label` keyword discriminator (`:place :road :building :admin-area :port …`).
Geometry is carried as JSON-encoded GeoJSON (`:feature/geometry`) plus a centroid
(`:feature/lat` `:feature/lon`); extrusion height / levels are first-class. The legacy
`props` JSON bag survives as `:feature/props` (read-through only, **never** a query key —
query keys are promoted to first-class attrs). Topology edges (`edge_osm_way_node`, ownership
chains, route→stop) become `:feature.rel/*` ref datoms so **VAET** answers "what references
X" with no join. The 32-scheme geo-alias model becomes `:geo.alias/*`.

Provenance is preserved verbatim: `:feature/source-did` keeps the path-based multi-DID
(`did:web:maps.etzhayyim.com:registry:gleif`, …), and **sourcing honesty** (G5, watari
precedent) is mandatory: every feature is `:authoritative | :representative | :synthesized`.

## §2 — The spatial index: **H3-cell-as-Datom + AVET** (the load-bearing decision)

kotoba's four arrangements include **AVET** — *predicate + object → subjects* (~18 µs p50 on
10 k entities). **When the object is an H3 cell, AVET *is* a spatial index.** So at ingest
time every feature stores its owning H3 cell at each resolution the client queries:

```
:feature.cell/r2  :feature.cell/r4  :feature.cell/r6
:feature.cell/r8  :feature.cell/r10 :feature.cell/r12
```

computed once from the feature centroid via h3-js `cellToParent(latLngToCell(lat,lon,15), res)`.
This mirrors the app's existing `zoomToLod` ladder (zoom `<3/3/6/10/14/17+` → res
`2/4/6/8/10/12`); r12 (≈9 m edge) is the maps-3d walkable streaming cell.

`cmdGetChunk` then resolves **without any bbox scan**:

```
for each requested cell C at res = lod:
    subjects ← AVET( :feature.cell/r{lod} , C )      # one index probe
    filter subjects by :feature/label ∈ labels       # AVET( :feature/label , … ) ∩
    materialize :feature/geometry + props for the survivors
```

Cost is **O(requested cells × labels)**, never O(features) — strictly better than the legacy
bbox scan, and it eliminates the centroid-rerouting over-fetch cleanup the SQL path needed
(the cell IS the bucket). This is the kotoba-native answer to the <50 ms requirement: the
hot-path is index probes on content-addressed arrangements, not a range scan. (Chosen over
the alternative — store raw `lat/lon` doubles like watari and AVET-range-scan — because a
range scan degrades to O(features-in-band) and re-imports the very problem the H3 ladder
removes. The H3 ladder is the user-selected approach.)

## §3 — The migration leverage point: one data-access adapter, not 172 rewrites

All 172 commands funnel through **`getDb().selectFrom("vertex_spatial")…`** /
**`.insertInto("vertex_spatial")…`**. Rather than hand-port 172 handlers, the migration
replaces the *shared primitive*: a kotoba-backed adapter
**`src/kotoba-spatial.ts`** exposing the narrow surface the commands use —

- `queryByCells(cells, labels, limit)` → AVET cell probes (the §2 hot-path) → feature rows
- `ingestFeatures(features)` → H3-cell-stamp → `kg.ingest_batch` (the write path)
- `getFeature(id)` → `kg.entity` point lookup (EAVT)

The adapter reaches kotoba over the same XRPC surface the apex Worker already uses
(`com.etzhayyim.apps.kotobase.kg.entity` for reads, `…kg.ingest_batch` for writes,
`KOTOBA_ENDPOINT` env), and follows the apex Worker's **3-tier fail-open** precedent
(ADR-2606013800): kotoba first → RisingWave fallback *during the transition window only* →
empty. This makes the cut-over **additive and reversible**: with `KOTOBA_ENDPOINT` set,
reads/writes prefer kotoba; unset, the legacy path is untouched. RisingWave/Hyperdrive is
deleted only at §6/R3, after parity is proven live.

## §4 — Write path & no-server-key

Bulk-ingest dumpers and `seedBuildings` write through `methods/ingest.py` →
`kg.ingest_batch` (mirrors watari/kamado). Tenant writes are **CACAO-gated, member/operator-
signed** — the maps Worker holds **no server key** (ADR-2605231525); ingest is an
operator/community-DID-signed batch, never a platform-held credential. RisingWave's
append-only DELETE+re-INSERT idempotency is replaced by the Datom log's natural
content-addressed identity (`:feature/id` unique-identity → upsert-by-assertion; superseded
features are *appended* `:feature/status :superseded`, never deleted — 非終末論).

## §5 — Narration & 3D rendering are unchanged

The KAMI 3D renderer (`kami-app-maps3d`, ADR-2606011500) consumes `getChunk` GeoJSON exactly
as before — the substrate swap is invisible above the adapter. Any LLM narration stays
**Murakumo-only** (ADR-2605215000). The Gsplat/Mapillary 3DGS pipeline (ADR-2605312200) and
the kotoba asset-linkage already established for Shibuya are the model the static features now
join.

## §6 — Migration phases (honest)

- **R0 (this ADR — foundation, design-only + offline-verified):** ontology; `:feature/*`
  seed (`:representative`, Tokyo Station anchor); `methods/ingest.py` (vertex_spatial export
  → `:feature/*` + H3 cells → `kg.ingest_batch`, live push **gated**) + `methods/analyze.py`
  (Earth-coverage report — answers *「どれぐらい coverage できているか」* directly off the
  Datom log); `src/kotoba-spatial.ts` adapter + `cmdGetChunk` rewired to prefer kotoba
  (fail-open); kotoba-native lexicons + MIGRATION-NOTES; tests. **No live kotoba endpoint
  wired, no RisingWave removed.**
- **R1 (hot-path live):** stand up `KOTOBA_ENDPOINT` for maps; backfill `vertex_spatial` →
  `:feature/*` via `ingest.py`; flip `cmdGetChunk` to kotoba-primary; prove <50 ms parity on
  the Tokyo anchor.
- **R2 (write path + dumpers):** port the five bulk-ingest dumpers + `seedBuildings` +
  transit/registry/satellite ingest to `kg.ingest_batch`. RisingWave goes read-only.
- **R3 (removal):** delete the `HYPERDRIVE` binding, the `vertex_*` migrations, and the
  Kysely path. maps is kotoba-only. Update ADR status → accepted.

# Gates

- **G1 kotoba-native** — canonical state = Datom log; no SQL/RisingWave/Lance as the store.
- **G2 H3-AVET spatial index** — reads are AVET cell probes, not bbox scans; cells are
  ingest-time `cellToParent`, never recomputed per query.
- **G3 sourcing honesty** — every feature `:authoritative|:representative|:synthesized`;
  coverage never fabricated (absence = "not yet ingested").
- **G4 no-server-key** — ingest is member/operator-DID-signed (ADR-2605231525); the Worker
  holds no platform key.
- **G5 Murakumo-only** — any narration via the Murakumo fleet (ADR-2605215000).
- **G6 fail-open transition** — kotoba-primary with RisingWave fallback only until R3; the
  cut is additive and reversible.
- **G7 outward-gated** — live `kg.ingest_batch` push + live external source fetch require
  operator attestation (env gate); R0 ships offline `:representative` only.
- **G8 no-git-lfs** — bulk geometry/COG → DataLad → IPFS under `80-data/maps`.
- **G9 a feature is a placed thing, never a person** — user-post geolocation records the
  post's place, never pattern-of-life (watari G4 carried forward).

# Honest R0

This ADR lands the **load-bearing foundation**, not a finished migration. What is real now:
the ontology, the H3-AVET design, an offline-verified ingest+analyze over a bounded
`:representative` seed, the TS adapter, the rewired `getChunk` (kotoba-preferring, fail-open),
lexicons, and tests. What is **not** done: no live `KOTOBA_ENDPOINT` for maps; no
`vertex_spatial` backfill; RisingWave/Hyperdrive still present and serving (the fail-open
fallback); the bulk dumpers + the long tail of the 172 commands still emit SQL (they migrate
by routing through the adapter in R1–R2, but only `getChunk` is rewired in R0). The 3D Earth
coverage itself is unchanged by this ADR — it remains the Tokyo-anchored walker
(ADR-2605312200 lineage); this work changes *what stores the features*, not *how much of the
Earth is loaded*.

# Consequences

**Positive:** removes the monorepo's largest substrate violation; one kotoba-native model for
all geo state (static `:feature/*` + dynamic watari `:craft/*` compose over shared H3 cells
and chokepoint keywords); the H3-AVET index is strictly cheaper than the bbox scan and gives
a free, honest Earth-coverage metric (`coverage/cell-count-r6`); no-server-key write path.

**Negative / risk:** kotoba geospatial AVET at planet scale is unproven under the <50 ms
budget (R1 must measure, not assume); the six-resolution cell stamp multiplies write fan-out
6× per feature (acceptable — cells are 8-byte strings, the index is the point); a full
172-command cut is multi-PR (R2–R3) and the fail-open fallback means RisingWave lingers until
R3, so the violation is *contained and on a path to zero*, not instantly gone.
