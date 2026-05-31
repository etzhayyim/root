---
id: adr-2605312200-shibuya-digital-twin-kotoba-asset-linkage-and-mapillary-3dgs
title: "ADR-2605312200: Shibuya digital-twin iter 2 — object→kotoba EAVT asset linkage + Mapillary→3DGS pipeline wiring"
status: accepted
doc_type: adr
topic: shibuya-digital-twin-kotoba-and-3dgs
authoritative: true
last_verified: 2026-05-31
priority: 5.5
axis: architecture
weight: 0.5
priority_note: "Iteration 2 of the Shibuya street digital twin (ADR-2605311900): expand OSM to point assets (poles/lamps/signals/trees/hydrants), register EVERY object as a kotoba (datomic) EAVT entity with asset attributes (:asset/kind :asset/installYear :asset/company :asset/costJpy — OSM-derived where present, else deterministically SYNTHESIZED and provenance-flagged), make each on-screen asset clickable → its EAVT record shown in the HUD; and stand up the Mapillary→COLMAP→3DGS acquisition front (mapillary_fetch.py) feeding the existing trainGsplatFromMapillary GPU pipeline. The GPU splat training + in-app GsplatAdapter render-wire are explicitly deferred (offline/no trained PLY)."
authoritative_for:
  - Shibuya point-asset OSM ingestion + kotoba EAVT asset-registry transaction format
  - asset attribute schema (:asset/*) + synthesized-vs-OSM provenance flagging
  - clickable asset → kotoba object data binding in kami-app-shibuya
  - Mapillary acquisition front (mapillary_fetch.py) → trainGsplatFromMapillary wiring
depends_on:
  - adr-2605311900-shibuya-street-digital-twin-osm-citymesh-fullphysics-sim
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605092800-gsplat-preview-qc
related:
  - adr-2605311800-kami-genesis-3d-spatial-articulation-and-contact-solver
supersedes: []
superseded_by: []
---

# ADR-2605312200: Shibuya digital-twin iter 2 — kotoba asset linkage + Mapillary→3DGS

**Status**: accepted
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

ADR-2605311900 stood up the Shibuya full-physics sim from OSM (buildings + roads
+ agents). Two follow-ups were requested: (1) make it **more detailed via 3DGS**,
and (2) link **every on-screen object — down to a single pole — to kotoba
datomic data** with attributes like 設置年数 / 会社 / 費用.

Constraints (honest): installYear / company / cost are **not in OSM** (they are
proprietary asset-management data); OSM carries position / kind / occasional
`operator` / `start_date` / `height`. Photoreal 3DGS needs captured imagery +
COLMAP SfM + gsplat GPU training — the repo already has that pipeline
(`app.etzhayyim.apps.maps.trainGsplatFromMapillary`, ADR-2605092800; "maprealy"
= Mapillary), but it is an offline GPU job, not runnable in a code session.

# Decision

## 1. Point assets + kotoba EAVT asset registry (delivered)

The Overpass extract now also pulls node features (street_lamp, power=pole,
traffic_signals, natural=tree, fire_hydrant, bench, vending_machine, telephone,
…). `osm_to_citymesh.py` emits, in addition to the scene JSON, a **kotoba /
datomic EDN transaction** (`*.assets.edn`) + **schema** (`*.assets.schema.edn`)
registering EVERY object (building / road / point) as an asset entity:

    {:db/id "shibuya/n252674261" :asset/osmId 252674261 :asset/kind "traffic_signals"
     :geo/lat … :geo/lng … :geo/x … :geo/y … :asset/installYear 2019
     :asset/company "警視庁 交通管制" :asset/costJpy 3762500
     :asset/dataProvenance "synthesized-demo"}

Provenance is explicit: position / kind / OSM `operator`→`:asset/company` /
`start_date`→`:asset/installYear` / `height` are **real (OSM, ODbL)**; the rest
are **deterministically synthesized from the OSM id** (plausible, reproducible)
and flagged `:asset/dataProvenance "synthesized-demo"` so a real municipal asset
DB can overwrite them. Loadable via the kotoba EAVT store (`kotoba-datomic`
`transact`). Shibuya snapshot: 144 buildings + 318 roads + 39 point objects =
**501 EAVT entities** (3 OSM-provenance, 498 synthesized).

## 2. Clickable asset → kotoba object data (delivered)

`kami-app-shibuya` renders each point asset as its own pickable batch keyed by
its kotoba entity id, coloured by kind. A click resolves the id → the asset's
record and publishes it to `window.__shibuya_pick`; `shibuya.htm` shows a panel
(種別 / 会社 / 設置年 / 費用 / kotoba id) with a provenance note (実OSM vs 合成デモ).
This closes the loop "画面のポール → kotoba object データ".

## 3. Mapillary → 3DGS pipeline front (wired + documented; training offline)

`70-tools/scripts/sim/mapillary_fetch.py` is the image-acquisition front: it
pulls Mapillary Graph-API v4 image metadata (id / geometry / compass / thumb)
for a bbox and writes a manifest that feeds the existing
`app.etzhayyim.apps.maps.trainGsplatFromMapillary` procedure (COLMAP SfM →
gsplat training on a GPU pod → PLY → B2 → `vertex_maps_gsplat_asset`). Without
`MAPILLARY_TOKEN` it prints the schema + exact training invocation and exits 0,
so the path is documented even offline. The trained PLY is rendered by the
existing `kami-pipelines::GsplatAdapter` (ADR-2605092800).

# Consequences

**Positive**

- Every on-screen object is now a queryable kotoba EAVT entity with asset
  attributes — a real digital-twin asset registry, not just geometry.
- The 3DGS detail path is concretely wired to the repo's existing Mapillary
  training pipeline, ready to render once a PLY is trained.

**Negative / honest limitations**

- installYear / company / costJpy are **synthesized demo values** for 498/501
  entities (clearly flagged); only 3 carry real OSM provenance. A real asset DB
  is needed for authoritative values.
- The EDN transaction is committed as a **file**; live ingest into a running
  kotoba `:8077` is not performed here.
- **3DGS is not yet visible**: COLMAP+gsplat training is an offline GPU job and
  no trained Shibuya PLY exists; the in-app `GsplatAdapter` render-wire (and a
  `MAPILLARY_TOKEN`) are the remaining steps. Procedural splatification was
  explicitly rejected (would not add real detail).
- Street-lamps / power-poles are sparse in this OSM bbox (real coverage); the
  39 objects are what OSM actually maps there.

# Verification (directly observed)

- `cargo test -p kami-app-shibuya` → **5 passed; 0 failed** (incl. scene loads
  39 kotoba-linked objects, each with attrs + valid provenance + render helpers).
- `osm_to_citymesh.py` → 144 b / 318 r / 39 objects; **501 kotoba EAVT entities**
  (`*.assets.edn` + `.schema.edn`).
- `mapillary_fetch.py` (no token) → prints pipeline + exits 0.
- `wasm-pack build kami-app-shibuya --target web --release` → ok.

# Alternatives Considered

1. **Procedural splatification for instant 3DGS.** Rejected by the founder —
   would not add real detail; the Mapillary→gsplat path is the real route.
2. **Per-attribute provenance keys.** Deferred — a single
   `:asset/dataProvenance` keeps the transaction compact; OSM-real fields are
   distinguishable by value.
3. **Live kotoba :8077 transact.** Deferred — a committed EDN file is
   reproducible and reviewable; live ingest is an ops step.

# References

- ADR-2605311900 (Shibuya full-physics sim iter 1)
- ADR-2605092800 (gsplat preview/QC + trainGsplatFromMapillary)
- ADR-2605262130 (kotoba substrate; EAVT / datomic)
- `70-tools/scripts/sim/{osm_to_citymesh.py, mapillary_fetch.py}`
- `70-tools/e7m-sim/scenes/shibuya/{shibuya_scramble.scene.json, .assets.edn, .assets.schema.edn}`
- `40-engine/kami-engine/kami-app-shibuya/src/lib.rs`
