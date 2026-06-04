# maps Sentinel L7 Pipeline — Deploy Runbook

- **Date**: 2026-04-27
- **ADR**: [ADR-2604271800](adr/2604271800-maps-l8-sentinel-pipeline.md)
- **Status**: ready (pending operator action)
- **Owner**: maps actor (`did:web:maps.etzhayyim.com`)

## What this deploys

Two BPMN processes + two pyzeebe primitives that turn the long-stubbed
`maps.satellite_*` commands into a live ingest + analysis pipeline:

- `com.etzhayyim.apps.maps.sentinelIngest` (timer R/PT24H) — Sentinel-2 L2A
  + Sentinel-1 GRD STAC search → `vertex_repo_record`
- `com.etzhayyim.apps.maps.sentinelAnalyze` (XRPC POST) — RunPod Serverless
  GPU analysis (changeDetection / landUse / sarFlood) → `vertex_repo_record`

## Pre-flight (gate, MUST PASS)

### Gate 1 — RisingWave health

The migration is `INSERT N rows` only (no DDL), but it touches
`vertex_bpmn_process_def` + `vertex_bpmn_lexicon_binding` which are
projection sources for the F5 watcher. Run the standard health gate:

```bash
bash 70-tools/scripts/ingest/rw-health-gate.sh
# Pass = exit 0.
# Fail = exit 1 with reason (SlowDown / RateLimited / NoSuchUpload /
#        write part timeout / recovery log / compute restart in last 30 min).
```

If FAIL: stop here. Re-run after RW returns to steady state. Do NOT
proceed with helm upgrade either — the worker pod restart races
against in-flight DDL on the same cluster.

### Gate 2 — Zeebe broker reachable

```bash
kubectl -n mitama-udf get pod zeebe-0 -o jsonpath='{.status.containerStatuses[0].ready}'
# Expect: true
kubectl -n mitama-udf logs zeebe-0 --tail=20 | grep -E 'leader|ready'
```

### Gate 3 — pre-existing migration drift

Out-of-band psql may have inserted rows the kysely migrator didn't
record (CLAUDE.md: "kysely migrator blocked by pre-existing drift").
Confirm the chain to the new migration is intact:

```bash
cd 30-graph/graph-schema
DATABASE_URL=$(security find-generic-password -s etzhayyim.rw -a ROOT_URL -w) \
  pnpm db:migrate:list | tail -10
# Expect the last applied to be 20260427200000_vertex_arms_firearm.
# If not: investigate before applying — out-of-band apply is the
# canonical recovery path (see ADR-2604241342).
```

## Deploy

### Step 1 — register secrets (one-time, idempotent)

```bash
# RunPod (analyze path). MAPS endpoint is distinct from yoro chat.
kubectl -n mitama-udf create secret generic maps-sentinel-runpod \
  --from-literal=RUNPOD_KEY="$(security find-generic-password -s etzhayyim.runpod -a API_KEY -w)" \
  --from-literal=RUNPOD_ENDPOINT_ID_MAPS="$(security find-generic-password -s etzhayyim.runpod -a ENDPOINT_ID_MAPS -w)" \
  --dry-run=client -o yaml | kubectl apply -f -

# Copernicus Dataspace (S-1 GRD path; optional, S-2 works without)
kubectl -n mitama-udf create secret generic maps-sentinel-copernicus \
  --from-literal=SENTINEL_HUB_CLIENT_ID="$(security find-generic-password -s etzhayyim.copernicus -a CLIENT_ID -w)" \
  --from-literal=SENTINEL_HUB_CLIENT_SECRET="$(security find-generic-password -s etzhayyim.copernicus -a CLIENT_SECRET -w)" \
  --dry-run=client -o yaml | kubectl apply -f -
```

If the Keychain entries don't exist yet, create them via
`security add-generic-password -s etzhayyim.runpod -a API_KEY -w '<value>' -U`
following CLAUDE.md `etzhayyim.{provider}` convention.

### Step 2 — apply the BPMN registry migration

```bash
cd 30-graph/graph-schema
DATABASE_URL=$(security find-generic-password -s etzhayyim.rw -a ROOT_URL -w) \
  pnpm db:migrate latest
# Expect: "Migration up was executed successfully" for
# 20260427210000_seed_maps_sentinel_bpmn_actors.
```

If the runner is blocked by historical drift, fall back to the
out-of-band path documented in ADR-2604241342:

```bash
# 1. Hand-apply the INSERTs (they're INSERT … WHERE NOT EXISTS, idempotent)
psql "$DATABASE_URL" -f <(
  node --loader=ts-node/esm scripts/migrate.ts to 20260427210000 --dry-run-sql
)
# 2. Insert the kysely_migration row by hand
psql "$DATABASE_URL" -c "INSERT INTO kysely_migration(name,timestamp) VALUES('20260427210000_seed_maps_sentinel_bpmn_actors', NOW());"
```

### Step 3 — verify BPMN registry rows

```bash
psql "$DATABASE_URL" <<'SQL'
SELECT vertex_id, bpmn_process_id, status
FROM vertex_bpmn_process_def
WHERE vertex_id LIKE '%maps-sentinel%'
ORDER BY vertex_id;

SELECT vertex_id, nsid, bpmn_process_id, status
FROM vertex_bpmn_lexicon_binding
WHERE nsid LIKE 'com.etzhayyim.apps.maps.sentinel%'
ORDER BY nsid;
SQL
```

Expect exactly 2 process_def rows + 2 lexicon_binding rows, all
`status='active'`.

### Step 4 — wait for F5 watcher → Zeebe deploy

The bpmn-dispatcher watcher polls `vertex_bpmn_process_def` every 30 s
(`zeebeWorker.bindingTtlSec` in values.yaml). Watch the dispatcher logs:

```bash
kubectl -n mitama-udf logs -l app.kubernetes.io/name=bpmn-dispatcher --tail=50 -f \
  | grep -E 'maps_sentinel|deployed|watcher'
# Expect within 60s:
#   "deployed bpmn maps_sentinel_ingest v1"
#   "deployed bpmn maps_sentinel_analyze v1"
```

Confirm Zeebe sees them:

```bash
kubectl -n mitama-udf exec -i zeebe-0 -- \
  curl -s 'http://localhost:9600/actuator/zeebe/processes' \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print([p["bpmnProcessId"] for p in d if "maps_sentinel" in p["bpmnProcessId"]])'
# Expect: ['maps_sentinel_ingest', 'maps_sentinel_analyze']
```

### Step 5 — helm upgrade the worker pool

```bash
cd 50-infra/vultr/mitama-udf-pool
helm upgrade --install mitama-udf-pool . \
  --namespace mitama-udf \
  --values values.yaml
```

Watch the rollout:

```bash
kubectl -n mitama-udf rollout status deployment/zeebe-worker --timeout=180s
kubectl -n mitama-udf logs -l app.kubernetes.io/name=zeebe-worker --tail=50 \
  | grep -E 'maps.sentinel|registered tasks'
# Expect: "registered tasks: …, maps.sentinel.stac.search, maps.sentinel.runpod.analyze, …"
```

### Step 6 — smoke test ingest (S-2, no auth needed)

```bash
# Manual one-shot kick of the timer process (don't wait 24 h).
TOKEN=$(etzhayyim agent-token --lxm com.etzhayyim.apps.maps.sentinelIngest)
curl -sS -X POST "https://maps.etzhayyim.com/xrpc/com.etzhayyim.apps.maps.sentinelIngest" \
  -H "authorization: Bearer $TOKEN" \
  -H "content-type: application/json" \
  -d '{"timeRangeDays":1,"maxScenesPerAoi":2,"platforms":["sentinel-2-l2a"]}' \
  | tee /tmp/ingest.json | python3 -m json.tool
# Expect: {"runId":"sentinel-ingest-…","scenesIngested":N,"byPlatform":{"sentinel-2-l2a":N}}
```

Confirm rows landed:

```bash
psql "$DATABASE_URL" <<'SQL'
SELECT count(*) AS scenes,
       max(created_at) AS latest
FROM vertex_repo_record
WHERE collection = 'com.etzhayyim.apps.maps.satelliteScene';
SQL
```

### Step 7 — smoke test analyze (RunPod path)

Pick a scene URI from Step 6 and analyze it:

```bash
SCENE_URI=$(psql "$DATABASE_URL" -tAc "
  SELECT uri FROM vertex_repo_record
  WHERE collection='com.etzhayyim.apps.maps.satelliteScene'
  ORDER BY ts_ms DESC LIMIT 1")
TOKEN=$(etzhayyim agent-token --lxm com.etzhayyim.apps.maps.sentinelAnalyze)
curl -sS -X POST "https://maps.etzhayyim.com/xrpc/com.etzhayyim.apps.maps.sentinelAnalyze" \
  -H "authorization: Bearer $TOKEN" \
  -H "content-type: application/json" \
  -d "{\"sceneUri\":\"$SCENE_URI\",\"analysisType\":\"landUse\"}" \
  | python3 -m json.tool
# Expect: {"analysisUri":"at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.satelliteAnalysis/…",
#          "summary":"…","confidence":0.78,"modelVersion":"sentinel2_landuse_unet","runtimeMs":12345}
```

If RunPod isn't deployed yet: expect `confidence:0.0` and
`summary:"(no summary; runpod ok=False err=RUNPOD_ENDPOINT_ID_MAPS / RUNPOD_KEY not configured)"`.
That's the documented graceful-degrade path — the BPMN still completes,
the OCEL audit captures the gap. Move forward; analyze flips green
once the endpoint is live.

### Step 8 — observe one R/PT24H cycle

Skip if Step 6 already confirmed the path. Otherwise wait 24 h and
re-run the count query in Step 6. Expect monotone growth.

## Rollback

The migration writes `INSERT … WHERE NOT EXISTS` rows. The down()
function is reversible. To roll back:

```bash
# 1. Stop new BPMN dispatch by flagging the bindings inactive
psql "$DATABASE_URL" -c "
  UPDATE vertex_bpmn_lexicon_binding
  SET status='inactive'
  WHERE nsid LIKE 'com.etzhayyim.apps.maps.sentinel%';"

# 2. Helm rollback (worker pod reverts; new task types are simply
#    never registered. Already-registered task types degrade silently
#    when no worker subscribes — Zeebe holds jobs until timeout.)
helm rollback mitama-udf-pool 0 -n mitama-udf

# 3. (Optional) drop the rows entirely
DATABASE_URL=… pnpm db:migrate down  # one step
```

The lexicons themselves stay on disk — they are inert without a
binding row. Worker code reverts cleanly because the new primitives
are gated by an explicit `register()` call that the rollback removes.

## Failure modes (seen / expected)

| Symptom | Likely cause | Action |
|---|---|---|
| `bpmn-dispatcher` doesn't pick up new processes after 60 s | watcher cache TTL | restart `kubectl -n mitama-udf rollout restart deploy/bpmn-dispatcher` |
| Worker logs `KeyError: maps.sentinel.stac.search` on activation | helm upgrade didn't roll the pod | `kubectl -n mitama-udf rollout restart deploy/zeebe-worker` |
| `ingest` returns 200 with `scenesIngested:0` | AOI list rejected by STAC (CRS / bbox order) | inspect primitive logs `kubectl -n mitama-udf logs -l app.kubernetes.io/name=zeebe-worker | grep stac` |
| `analyze` returns 504 timeout | RunPod cold-start over 5 min | bump `RUNPOD_TIMEOUT_SEC` in values.yaml; re-deploy |
| Sentinel-1 always 0 hits | Copernicus secret missing or `productType` filter wrong | confirm `SENTINEL_HUB_CLIENT_*` env present in pod; check `_copernicus_token()` cache |
| `ingest` 401 from CF Worker XRPC layer | missing Service Auth, or NSID not registered in PDS routing | confirm `vertex_bpmn_lexicon_binding` row + `etzhayyim agent-token --lxm com.etzhayyim.apps.maps.sentinelIngest` returns a token |

## Out of scope

- RunPod endpoint provisioning (separate work, see
  `60-apps/etzhayyim-project-maps/runpod-endpoint/`)
- Phase 2 typed graph projection (`vertex_satellite_scene` /
  `vertex_satellite_analysis`) — held until RW is back inside license caps
- Sentinel-3 / Sentinel-5P sources — added once Phase 1 is steady
