# maps3d — photogrammetry pipeline pods

CPU-only Mapillary + COLMAP + LangGraph workers that drive the BPMN at
`00-contracts/bpmn/com/etzhayyim/maps3d/processTile.bpmn`. All four pods run
in the existing Vultr LKE cluster (namespace `maps3d`) and connect to
AgentGateway MCP in namespace `mitama-udf`.

## Pods

| Pod | Image | LangServer tools |
|---|---|---|
| `maps3d-mapillary-fetcher` | `ghcr.io/etzhayyim/maps3d-worker:latest` | `maps3d.fetchMapillary` |
| `maps3d-colmap-worker` | `ghcr.io/etzhayyim/maps3d-colmap-worker:latest` | `maps3d.colmapTile`, `maps3d.simplifyAndExport` |
| `maps3d-langgraph-curator` | `ghcr.io/etzhayyim/maps3d-worker:latest` | `maps3d.curateImages`, `maps3d.replanReconstruction` |
| `maps3d-langgraph-actor-link` | `ghcr.io/etzhayyim/maps3d-worker:latest` | `maps3d.visionAnnotate`, `maps3d.linkActor` |

## Bring up

Single-command idempotent script:

```bash
50-infra/k8s/maps3d/deploy.sh                # full sequence
50-infra/k8s/maps3d/deploy.sh --dry-run      # validate only, no side effects
50-infra/k8s/maps3d/deploy.sh --migrate-only # apply RW DDL only
50-infra/k8s/maps3d/deploy.sh --build-only   # rebuild + push images
50-infra/k8s/maps3d/deploy.sh --apply-only   # re-apply manifests, skip build
50-infra/k8s/maps3d/deploy.sh --smoke-only   # re-run Layer 2 against existing pods
```

Phases (each has `--skip-{phase}`):

1. **migrate** — `pnpm db:migrate latest` after `rw-health-gate.sh` pre-flight
2. **build + push** — both Dockerfiles via `docker buildx --platform=linux/amd64 --push`
3. **secrets** — namespace + `maps3d-secrets` + `ghcr-pull` (idempotent upserts)
4. **apply** — all 4 Deployments + `wait --for=condition=available --timeout=300s`
5. **smoke** — runs `70-tools/scripts/test/maps3d-bpmn-integration.py` end-to-end

Credentials are resolved from env vars (preferred) or macOS Keychain
(`etzhayyim.rw / ROOT_URL`, `etzhayyim.mapillary / ACCESS_TOKEN`,
`etzhayyim.murakumo / API_KEY`, `etzhayyim.b2 / KEY_ID`, `etzhayyim.b2 / APPLICATION_KEY`,
`gh auth token` for GHCR).

Manual phase reference (if you'd rather drive each step yourself):

```bash
# 2/3. images
docker buildx build --platform=linux/amd64 \
  -t ghcr.io/etzhayyim/maps3d-worker:latest \
  -f 50-infra/k8s/maps3d/workers/Dockerfile \
  50-infra/k8s/maps3d/workers --push
docker buildx build --platform=linux/amd64 \
  -t ghcr.io/etzhayyim/maps3d-colmap-worker:latest \
  -f 50-infra/k8s/maps3d/workers/Dockerfile.colmap \
  50-infra/k8s/maps3d/workers --push

# 5. manifests
kubectl apply -f 50-infra/k8s/maps3d/
```

## BPMN registration

The migration `30-graph/graph-schema/migrations/20260426010000_maps3d_photogrammetry.ts`
seeds `vertex_bpmn_process_def` + `vertex_bpmn_lexicon_binding`. BPMN XML remains
a contract/audit artifact; execution is pod-side LangServer through AgentGateway MCP.

Trigger a tile manually:

```bash
curl -X POST http://dispatcher.etzhayyim.com:8080/xrpc/com.etzhayyim.apps.maps3d.processTile \
  -H "content-type: application/json" \
  -d '{"tileH3":"8a2a1072b59ffff"}'
```

## Health probes

Every pod runs a tiny asyncio TCP listener on `:8080` (in `_common.py`)
that returns HTTP 200 on any GET. The k8s `livenessProbe` pings it
every 30 s — if the LangServer event loop is deadlocked or the process has
crashed, the probe times out and k8s restarts the pod. The
`colmap-worker` adds a `startupProbe` (5 min grace) so the heavy
open3d / b2sdk import doesn't trigger an early restart, and stretches
liveness `timeoutSeconds` to 15 s so a brief GIL-bound moment during
`patch_match_stereo` doesn't kill an in-flight reconstruction.

## CI

`.github/workflows/maps3d.yml` runs three independent jobs in parallel
on every PR touching maps3d files (and on push to `main`):

- `static-validation` — runs Layer 1 (`maps3d-static-validation.py`)
- `worker-units` — runs `python -m unittest workers.test_colmap workers.test_replan_policy`
- `engine-units` — runs `cargo test -p kami-app-maps3d --lib`

Cargo registry + workspace target dir are cached by `Cargo.lock` hash.

## Tests

Three layers, runnable independently:

| Layer | What | Needs | Run |
|---|---|---|---|
| 1 | Static validation — lexicon JSON shape, BPMN XML structure, BPMN ↔ Lexicon ↔ Worker NSID cross-refs, migration DDL contains required tables. | nothing | `70-tools/scripts/test/maps3d-static-validation.py` |
| 2 | BPMN flow integration — POST `/xrpc/com.etzhayyim.apps.maps3d.processTile`, poll `vertex_maps3d_tile` until `status=done`, assert `mesh_uri` populated + audit row recorded. | dispatcher.etzhayyim.com + AgentGateway MCP + 4 pods + RisingWave (RW_URL via Keychain) | `70-tools/scripts/test/maps3d-bpmn-integration.py` |
| 3 | Engine — `MeshTileAdapter` GLB parse roundtrip without wgpu (synthetic triangle GLB built in-memory; tests POSITION extraction, NORMAL fallback, COLOR_0 fallback, garbage rejection). | `cargo` only | `cargo test -p kami-app-maps3d --lib` |
| 3b | COLMAP worker — error classification, output parsers, pipeline driver short-circuits (TOO_FEW_MATCHES at mapper, timeout on first step, sparse-only fallback). Uses an injectable subprocess runner so no COLMAP binary is required. | python3 only | `cd 50-infra/k8s/maps3d && python3 -m unittest workers.test_colmap` |
| 3c | Bounded-retry replanner policy — TIMEOUT/DENSE_OOM → sparse-only retry; BUNDLE_DIVERGED → retry as-is; TOO_FEW_MATCHES → requestMore; attempt ≥ 2 → downgradeOsm. Never returns `abort` from the COLMAP-failure branch. | python3 only | `cd 50-infra/k8s/maps3d && python3 -m unittest workers.test_replan_policy` |

Layer 1 catches drift between contract files and worker code at zero cost. Add it to CI as a pre-merge gate. Layer 2 is the smoke test after every k8s deploy. Layer 3 runs in `cargo test` and is the regression net for the engine adapter.

## Phase 2 status

These workers ship as **scaffold stubs** — handlers return mock data so
the BPMN contract + AgentGateway MCP + dispatcher integration can be validated
end-to-end before the heavy ML/CV bits are wired up. Real integrations
land in follow-up PRs:

| Pod | Real-integration TODO |
|---|---|
| mapillary-fetcher | `https://graph.mapillary.com/images` v4 query, B2 SHA-256 cache |
| colmap-worker | ✅ **DONE** — real COLMAP CPU subprocess pipeline (feature_extractor → exhaustive_matcher → mapper → image_undistorter → patch_match_stereo → stereo_fusion → delaunay_mesher), Open3D quadric_decimation + saturated vertex-color GLB export, B2 PUT for raw `.ply` and final `.glb`, per-step timeout enforcement via SIGTERM→SIGKILL on the process group, structured error_code classification |
| langgraph-curator | LangGraph (score_quality → score_coverage → llm_dedupe → decide_count) backed by Murakumo Vision |
| langgraph-actor-link | LangGraph (wikidata_search → gleif_lookup → osm_operator → llm_disambiguate) + edge writes via Hyperdrive Kysely |

Throughput (real): ~1 tile / 45 min on a 2-core colmap-worker; Tokyo
landmark backfill (~2,000 tiles) ≈ 60 days end-to-end with one pod.
Add replicas to the `colmap-worker` Deployment to scale linearly.
