---
id: adr-2604271800-maps-l8-sentinel-pipeline
title: "ADR: maps L8 Sentinel ingest + RunPod analysis pipeline"
status: accepted
doc_type: adr
topic: maps-sentinel-pipeline
authoritative: true
last_verified: 2026-04-28
authoritative_for:
  - maps-sentinel-ingest
  - maps-runpod-analysis
related:
  - adr-0056-bpmn-as-actor
  - adr-2604271600-projector-l7-langgraph-integration
  - adr-2604251830-shannon-optimal-layered-architecture
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-0044-kotoba-udf-language-strategy
  - adr-2604240946-yoro-autonomous-actor-hybrid-loop
---

# ADR-2604271800 — maps L8 Sentinel ingest + RunPod analysis pipeline

- **Status**: active
- **Date**: 2026-04-27
- **Deployed**: 2026-04-28
- **Owner**: maps actor (`did:web:maps.etzhayyim.com`)
- **Supersedes**: maps `satellite_*` command stubs (declared 2026-04-17, never wired)
- **Relates to**: ADR-0056 (BPMN-as-actor), ADR-2604271600 (projector L7 LangChain),
  ADR-2604251830 (Shannon-Optimal 8-Layer), ADR-0036 (Worker-direct Hyperdrive),
  ADR-0044 (Kotoba/Datomic UDF language strategy), ADR-2604240946 (yoro RunPod fallback)

## Context

`maps.etzhayyim.com` is the etzhayyim geospatial actor. Its `actor-manifest.jsonld`
declares `did:web:maps.etzhayyim.com:satellite` as a STAC source covering
Sentinel-1 / Sentinel-2 / Landsat / HLS / Cop-DEM / NAIP, plus the
commands `satellite_ingest` / `satellite_import_scene` /
`satellite_analyze` / `list_satellite_scenes`. The commands have never
been backed by a runtime: there is no BPMN process, no pyzeebe primitive,
no RunPod / Murakumo binding for SAR / optical analysis. As of 2026-04-27
the only maps BPMN files in `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/maps/` are 7
coverage / OSM / Wikipedia / Wikidata refresh jobs — none touch Sentinel.

Yoro proved the BPMN + pyzeebe + LangChain + RunPod stack
(ADR-2604271600 projector L7, ADR-2604240946 platformPulse R/PT4H).
maps does not yet share that L7 path. The user request 「maps.etzhayyim.com で
sentinel からの情報収集、分析は bpmn, pyzeebe, langchain, runpod でできて
いる？」 confirmed: not built. This ADR commits to building it as a
yoro-symmetric L7 pipeline.

## Decision

Build a **two-BPMN pipeline** for Sentinel ingest + analysis, mirroring
the yoro `platformPulse` (timer-start) and `respondToMention`
(XRPC-triggered) pair, registered through the standard
`vertex_bpmn_process_def` + `vertex_bpmn_lexicon_binding` path so the
F5 watcher in `bpmn-dispatcher` deploys to Zeebe automatically.

### 1. `sentinelIngest.bpmn` — timer-start `R/PT24H`

```
Start (timer R/PT24H)
  → Task_StacSearch       (maps.sentinel.stac.search)
  → Gateway_HasScenes     (XOR; skip when 0 hits)
  → Task_PersistScenes    (generic.db.insert, multi-instance over rows)
  → Task_Audit            (generic.audit.emit "com.etzhayyim.apps.maps.sentinel.ingest")
  → End
```

- AOI list: configured via env `MAPS_SENTINEL_AOIS` (geohash list,
  bootstrap default = 12 KAMI layer coordinator centroids from maps
  actor-manifest). Per-AOI bbox + 1-day window.
- STAC catalog: `https://earth-search.aws.element84.com/v1` (Sentinel-2
  L2A, free, no auth) + `https://catalogue.dataspace.copernicus.eu/stac`
  (Sentinel-1 GRD, free with Copernicus account).
- LangChain in primitive: prompt → STAC `POST /search` → JSON parse →
  filter cloud cover < 30% (S-2) / orbit pass (S-1).
- Persist to `vertex_repo_record` (collection
  `com.etzhayyim.apps.maps.satelliteScene`, no schema migration required).
  Phase 2 (separate ADR) promotes to a typed `vertex_satellite_scene`.

### 2. `sentinelAnalyze.bpmn` — XRPC-triggered

```
Start (XRPC POST com.etzhayyim.apps.maps.sentinelAnalyze)
  → Task_LoadScene        (generic.db.select vertex_repo_record by scene URI)
  → Task_RunpodAnalyze    (maps.sentinel.runpod.analyze)
  → Task_PersistResult    (generic.db.insert vertex_repo_record)
  → Task_Audit
  → End
```

- Body: `{sceneUri, analysisType: changeDetection|landUse|sarFlood, baselineUri?}`.
- RunPod Serverless endpoint: configured per-instance via
  `RUNPOD_ENDPOINT_ID_MAPS` env (separate from yoro's
  `RUNPOD_ENDPOINT_ID`). Default model bundle: SAR flood detector
  (`sentinel1_flood_unet`) + optical change detector
  (`sentinel2_change_siamese`). Endpoint lives outside this repo;
  deployment is captured in `60-apps/etzhayyim-project-maps/runpod-endpoint/`
  in a follow-up.
- LangChain orchestration: prompt → COG URL retrieval → RunPod invoke
  → structured JSON parse → confidence calibration. Pure Python, no
  Kotoba/Datomic UDF needed (per ADR-0044: external IO + LLM + heavy lib =
  Python External / pymagatama, not SQL UDF).

### 3. pyzeebe primitives

`20-actors/magatama/py/src/pymagatama/primitives/maps_sentinel.py`:

| task type | purpose |
|---|---|
| `maps.sentinel.stac.search` | STAC POST search → scene list |
| `maps.sentinel.runpod.analyze` | LangChain wrapper around RunPod invoke |

Registered through the existing pyzeebe worker pool (`zeebe-worker`
Deployment in `mitama-udf-pool` Helm chart). No new pod required —
yoro's RunPod call lives in CF Worker today, but maps lives in pyzeebe
because its analysis runs are minute-scale (well over CF's 30s budget).

### 4. K8s wiring

Extend `50-infra/vultr/mitama-udf-pool/values.yaml` `zeebeWorker.env`
with three optional secrets (all keyed off Bitwarden etzhayyim Vault, none
hardcoded):

- `RUNPOD_KEY` (shared with yoro's existing `RUNPOD_KEY` secret)
- `RUNPOD_ENDPOINT_ID_MAPS` (new, distinct from yoro's text endpoint)
- `SENTINEL_HUB_CLIENT_ID` / `SENTINEL_HUB_CLIENT_SECRET` (Sentinel-1
  Copernicus auth; Sentinel-2 via Element84 needs no auth)

LangChain + Sentinel SDK Python deps land in the existing
`pymagatama` image — incremental ~30 MB (`langchain-core` + `pystac` +
`shapely`). No new image, no new Deployment, no new HPA.

### 5. Lexicon contract

`00-contracts/lexicons/com/etzhayyim/apps/maps/`:
- `sentinelIngest.json` — procedure, body optional `{aois?, timeRangeDays?, maxScenesPerAoi?}`,
  response `{scenesIngested, runId}`.
- `sentinelAnalyze.json` — procedure, body
  `{sceneUri, analysisType, baselineUri?}`,
  response `{analysisUri, summary, confidence, modelVersion}`.

### 6. Graph projection

Phase 1: writes use `vertex_repo_record` with collection
`com.etzhayyim.apps.maps.satelliteScene` and `…satelliteAnalysis`. Avoids a
Kotoba/Datomic DDL during the recovery-sensitive Vultr+B2 cluster window
(see CLAUDE.md "Kotoba/Datomic Smooth Scaling Gate").

Phase 2 (separate ADR + migration): typed `vertex_satellite_scene`
(stac_id, platform, sensor, datetime, cloud_cover, bbox_geom, cog_url,
thumbnail_url) + `vertex_satellite_analysis` (scene_uri, analysis_type,
result_json, confidence, model_version, baseline_uri) + edges
`edge_scene_covers_aoi` / `edge_analysis_of_scene`. Held until live
cluster footprint is back inside RW license caps.

## Out of scope

- Building the RunPod endpoint itself (separate repo work, follows the
  yoro endpoint pattern).
- Phase 2 typed graph projection (separate ADR + migration).
- Sentinel-3 OLCI ocean colour / Sentinel-5P atmospheric chemistry —
  added once Phase 1 is steady.
- T1 MCP-Compose backwards-compat for `satellite_*` legacy command
  names — those were never live, so no deprecation cycle needed; new
  pipeline ships under canonical NSIDs.

## Compliance

- ADR-0056 BPMN-as-actor: ✓ same `INSERT N rows` regime
  (`vertex_bpmn_process_def` + `vertex_bpmn_lexicon_binding`).
- ADR-0036 Worker-direct Hyperdrive: ✓ no PDS pipethrough for domain
  writes; `generic.db.insert` is Hyperdrive-direct.
- ADR-0044 UDF language strategy: ✓ external IO + LLM = Python
  External (pyzeebe), not SQL UDF.
- ADR-2604261000 MCP tool registry: ✓ lexicons drop into
  `vertex_mcp_tool_def` via `sync-mcp-registry.py` automatically.
- Kotoba/Datomic Smooth Scaling Gate: ✓ Phase 1 introduces zero DDL.
- LLM Coding Guardrail (NSID placeholder): ✓ canonical NSIDs throughout.

## Implementation Status — 2026-04-28 (shipped)

### ✅ Phase 1 live

| Artifact | State |
|---|---|
| `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/maps/sentinelIngest.bpmn` | ✅ committed, seeded to `vertex_bpmn_process_def` |
| `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/maps/sentinelAnalyze.bpmn` | ✅ committed, seeded to `vertex_bpmn_process_def` |
| `20-actors/magatama/py/src/pymagatama/primitives/maps_sentinel.py` | ✅ `maps.sentinel.stac.search` + `maps.sentinel.runpod.analyze` |
| `20-actors/magatama/py/tests/test_maps_sentinel_primitives.py` | ✅ 36/36 passing |
| `70-tools/scripts/contract/lint-sentinel-drift.py` | ✅ 5-check CI guard |
| `ghcr.io/etzhayyim/pymagatama:0.2.37` | ✅ built + pushed linux/amd64 |
| `zeebe-worker` (mitama-udf) | ✅ rolled to 0.2.37, polling `maps.sentinel.*` |
| PR #1151 | ✅ `safe-deploy-and-fix-settler-ws` → `main` |

Persistence: Phase 1 BPMNs write to `vertex_repo_record` (collection
`com.etzhayyim.apps.maps.satelliteScene` / `…satelliteAnalysis`). No DDL
change required; the `generic.db.insert` task type is already wired.

### ✅ Phase 2 DDL pre-staged

`30-graph/graph-schema/migrations/20260427220000_vertex_satellite_typed_tables.ts`
applied to live Vultr Kotoba/Datomic after `rw-health-gate.sh` cleared:
- `vertex_satellite_scene` — 17 cols + 3 indexes (repo / platform / date_time)
- `vertex_satellite_analysis` — 17 cols + 3 indexes (repo / scene_uri / analysis_type)

Tables exist with 0 rows. BPMNs still write to `vertex_repo_record`
(Phase 1 path). Promote to Phase 2 by updating `maps_sentinel.py` to
use `createKyselyDb(env.HYPERDRIVE)` inserts into the typed tables
(per ADR-0036) and redeploying.

### 🔄 Deferred

| Item | Blocker |
|---|---|
| Promote BPMNs to write `vertex_satellite_scene` directly | Requires `maps_sentinel.py` Hyperdrive rewrite + Phase 2 BPMN update |
| Credentials — `RUNPOD_ENDPOINT_ID_MAPS` / Sentinel Hub auth | Separate secret provisioning in etzhayyim Vault |
| RunPod model endpoint (SAR flood + optical change) | Separate repo work (`60-apps/etzhayyim-project-maps/runpod-endpoint/`) |
| `mv_satellite_scene_latest_by_aoi` streaming MV | Low priority — query-time JOIN sufficient at current scene volume |
| Edge tables `edge_scene_covers_aoi` / `edge_analysis_of_scene` | After cluster footprint stabilises |
| Sentinel-3 / Sentinel-5P coverage | Phase 1 stability gate |
