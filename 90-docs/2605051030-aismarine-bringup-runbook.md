---
id: runbook-2605051030-aismarine-bringup
title: "aismarine bring-up runbook (MarineTraffic-equivalent vessel tracking)"
status: active
doc_type: how-to
topic: maps-aismarine-pipeline
authoritative: true
last_verified: 2026-05-05
authoritative_for:
  - aismarine cutover steps
  - aismarine smoke verification
related:
  - adr-2605011500-maps-aismarine-pipeline
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-0048-risingwave-vultr-b2-primary
  - adr-0056-bpmn-as-actor
  - adr-2604282300
---

# aismarine bring-up runbook

**Status**: active — 2026-05-05
**Design source-of-truth**: [ADR-2605011500](/Users/junkawasaki/github/etzhayyim-root/90-docs/adr/2605011500-maps-aismarine-pipeline.md)

## Purpose

PR-A〜PR-E で実装した MarineTraffic 相当の AIS vessel-tracking pipeline を
本番 (RisingWave + Vultr K8s + maps.etzhayyim.com CF Worker + kami-geo Svelte) に
順次投入し、`maps.etzhayyim.com` 上で vessel layer が live になるまでの operator 手順
を固定する。

責務境界は 4 つ:

- **DB layer**: schema + lexicon (PR-A)
- **Compute layer**: pyzeebe primitives + BPMN (PR-B + PR-C)
- **Edge layer**: CF Worker XRPC (PR-D)
- **Streaming source**: K8s Deployment aisstream consumer (PR-D)
- **UI**: Svelte overlay + vessel detail panel (PR-E)

ADR-2605011500 が design SSoT。本 runbook は実行順とゲート条件のみ。

## Preconditions

### Required secrets (operator local)

```bash
# RisingWave + Hyperdrive (already provisioned)
export DATABASE_URL='postgres://root@45.32.79.245:4566/dev?sslmode=disable'
export etzhayyim_DATABASE_URL="$DATABASE_URL"
export etzhayyim_TOKEN='sk_live_...'

# aisstream.io API key (free tier; sign up at https://aisstream.io)
# Once obtained, register to macOS Keychain (Root-Only Rule):
security add-generic-password -s etzhayyim.comsstream -a API_KEY -w '<api-key>' -U
# Mirror to 1Password 'etzhayyim Japan株式会社' vault, title: etzhayyim.comsstream/API_KEY
```

### Required cluster context

```bash
kubectl config use-context vke-lax-mitama
kubectl get ns maps-bulk-ingest >/dev/null   # must exist (already in use by gtfs-jp)
kubectl get ns mitama-udf >/dev/null         # bpmn-dispatcher ClusterIP target
```

### Required tooling versions

- Node.js ≥ 20 / pnpm 9.x / `etzhayyim` CLI installed
- Python 3.11 / `uv` (for primitive tests)
- Docker Buildx with linux/amd64 emulation
- `gh` CLI authenticated to `ghcr.io/etzhayyim`

## Step-by-step bring-up

### 1. Apply RisingWave schema (PR-A)

```bash
cd 30-graph/graph-schema
pnpm db:migrate latest 2>&1 | tee /tmp/aismarine-mig.log
# Expected: 20260501170000_vertex_aismarine_phase1 applied,
#           20260501180300_seed_aismarine_bpmn_actors applied (PR-C seed).
```

If `pnpm db:migrate latest` is blocked by pre-existing kysely drift
(ADR-2604241342), fall back to:

```bash
30-graph/graph-schema/scripts/apply-pending.sh
```

Verify:

```bash
psql "$DATABASE_URL" -c "\d+ vertex_vessel"
psql "$DATABASE_URL" -c "\d+ vertex_vessel_position"
psql "$DATABASE_URL" -c "\d+ vertex_vessel_voyage"
psql "$DATABASE_URL" -c "\d+ edge_vessel_visited_port"
psql "$DATABASE_URL" -c "\d mv_vessel_latest_position"
psql "$DATABASE_URL" -c "\d mv_vessel_density_h3_r6"
psql "$DATABASE_URL" -c "SELECT vessel_type_class(70::smallint), vessel_flag_iso(431999000)"
# Expected: cargo | JP
```

Regenerate type bindings + drift gate:

```bash
DATABASE_URL="$DATABASE_URL" pnpm db:gen
DATABASE_URL="$DATABASE_URL" pnpm db:drift   # exit 0 = OK
git add src/database.ts && git commit -m "chore(graph-schema): regen for aismarine"
```

**Gate**: BPMN seed visible in `vertex_bpmn_process_def`:

```bash
psql "$DATABASE_URL" -c \
  "SELECT bpmn_process_id, status, source_path
     FROM vertex_bpmn_process_def
    WHERE bpmn_process_id LIKE 'maps_aismarine%'
    ORDER BY bpmn_process_id"
# Expected: 4 rows (consumer / voyage_detector / refresh_vessel_master / refresh_vessel_density)
```

### 2. Verify pyzeebe primitives (PR-B)

```bash
cd 20-actors/magatama/py
uv run pytest -q tests/test_aismarine_pure_helpers.py
# Expected: 29 passed
```

### 3. Build + push pymagatama image with new primitives

```bash
cd 20-actors/magatama/py
TAG="0.3.27-202605051030-amd64"
docker buildx build --platform linux/amd64 \
  -t ghcr.io/etzhayyim/pymagatama:$TAG --push .

# Roll out zeebe-worker
helm -n mitama-udf upgrade zeebe-worker \
  50-infra/vultr/risingwave/helm \
  --reuse-values \
  --set image.tag=$TAG --set image.fullRef=
kubectl -n mitama-udf rollout status deploy/zeebe-worker --timeout=180s
```

Verify the 6 task types are registered:

```bash
kubectl -n mitama-udf logs deploy/zeebe-worker --tail=200 | \
  grep -E 'aismarine\.(position|master|voyage|density|query)'
# Expected: 6 task subscriptions
```

### 4. F5 watcher deploys 4 BPMNs to Zeebe (PR-C)

```bash
# bpmn-dispatcher polls vertex_bpmn_process_def every 30s.
sleep 60
psql "$DATABASE_URL" -c \
  "SELECT bpmn_process_id, deployed_zeebe_key
     FROM vertex_bpmn_process_def
    WHERE bpmn_process_id LIKE 'maps_aismarine%'"
# Expected: deployed_zeebe_key non-null on all 4 rows.
```

If deploy fails, check the dispatcher log:

```bash
kubectl -n mitama-udf logs deploy/bpmn-dispatcher --tail=200 | grep aismarine
```

### 5. Build + push maps-bulk-ingest:1.3.0 (PR-D consumer)

The new consumer requires `websockets==13.1` + `aiohttp==3.10.10` (added to
`requirements.txt`). Bump image to `1.3.0`:

```bash
cd 60-apps/etzhayyim-project-maps/bulk-ingest
docker buildx build --platform linux/amd64 \
  -t ghcr.io/etzhayyim/maps-bulk-ingest:1.3.0 --push .
```

### 6. Deploy + scale the aismarine consumer

```bash
# Apply manifest (replicas=0 default — gate).
kubectl apply -f 60-apps/etzhayyim-project-maps/bulk-ingest/k8s/deployment-aismarine.yaml

# Inject AIS_STREAM_API_KEY from Keychain.
kubectl -n maps-bulk-ingest create secret generic aismarine-credentials \
  --from-literal=AIS_STREAM_API_KEY="$(security find-generic-password -s etzhayyim.comsstream -a API_KEY -w)" \
  --dry-run=client -o yaml | kubectl apply -f -

# bpmn-dispatcher-auth secret already exists (used by other workers); confirm:
kubectl -n maps-bulk-ingest get secret bpmn-dispatcher-auth -o name >/dev/null \
  || kubectl -n maps-bulk-ingest create secret generic bpmn-dispatcher-auth \
       --from-literal=internal-secret="$(kubectl -n mitama-udf get secret bpmn-dispatcher-auth -o jsonpath='{.data.internal-secret}' | base64 -d)"

# Scale up.
kubectl -n maps-bulk-ingest scale deploy/bulk-ingest-aismarine --replicas=1
kubectl -n maps-bulk-ingest rollout status deploy/bulk-ingest-aismarine --timeout=120s
```

### 7. Deploy maps Worker + Svelte UI (PR-D + PR-E)

```bash
cd 60-apps/etzhayyim-project-maps/appview/maps-ui-uqpel6i6
etzhayyim build       # bundles src/app.ts (XRPC) + svelte/build (overlay)
etzhayyim deploy      # account-level CF Worker, maps.etzhayyim.com
```

## Smoke verification (first 30 minutes)

Run all checks sequentially. Each check has an expected positive result and
a documented failure-mode pointer.

### S1. Consumer connected to aisstream.io

```bash
kubectl -n maps-bulk-ingest logs -f deploy/bulk-ingest-aismarine --tail=100 | \
  grep -E 'connected|disconnect'
# Expected within 10s: "aisstream connected, subscribed global no-filter"
```

Failure: `RuntimeError: AIS_STREAM_API_KEY is required` → step 6 secret not
applied. `RuntimeError: AISMARINE_INTERNAL_SECRET is required` → step 6
`bpmn-dispatcher-auth` mirror missing.

### S2. Position rows landing in RisingWave

```bash
sleep 60
psql "$DATABASE_URL" -c \
  "SELECT COUNT(*) FROM vertex_vessel_position
    WHERE ts_ms > extract(epoch from now())*1000 - 60000"
# Expected: > 100 (global feed; quiet hours bottom ~50/min)
```

Failure: 0 rows over 5 min →
- check consumer log for `position flush 4xx` (auth issue)
- check `bpmn-dispatcher` log for `aismarine.position.batchInsert` 5xx
- check `zeebe-worker` log for FLUSH errors (RW_DDL_GUARD trips when
  `flush=True`; primitive defaults `flush=False` per CLAUDE.md fix)

### S3. mv_vessel_latest_position freshness

```bash
psql "$DATABASE_URL" -c \
  "SELECT COUNT(*) AS active,
          MAX(ts_ms) AS latest_ms,
          extract(epoch from now())*1000 - MAX(ts_ms) AS lag_ms
     FROM mv_vessel_latest_position"
# Expected: active > 1000, lag_ms < 30000 after 5 min uptime.
```

### S4. CF Worker XRPC live

```bash
# Singapore Strait — busiest waterway globally.
curl -s 'https://maps.etzhayyim.com/xrpc/com.etzhayyim.apps.maps.aismarine.queryVesselsBbox?bbox=103.6&bbox=1.0&bbox=104.2&bbox=1.5&limit=100' \
  | jq '.total, .features | length'
# Expected: total > 50 within 10 min of consumer start.
```

### S5. Vessel detail end-to-end

```bash
# Pick any MMSI from S2.
MMSI=$(psql "$DATABASE_URL" -tAc \
  "SELECT mmsi FROM mv_vessel_latest_position ORDER BY ts_ms DESC LIMIT 1")
curl -s "https://maps.etzhayyim.com/xrpc/com.etzhayyim.apps.maps.aismarine.getVesselDetail?mmsi=$MMSI" \
  | jq '.vessel.mmsi, (.recentTrack | length)'
# Expected: same MMSI + > 0 track points
```

### S6. Voyage detector first fire (R/PT5M)

```bash
sleep 360
kubectl -n mitama-udf logs deploy/zeebe-worker --tail=500 | \
  grep 'aismarine.voyage.detectWindow'
# Expected: at least 1 successful job within 6 min.

psql "$DATABASE_URL" -c \
  "SELECT COUNT(*) FROM vertex_vessel_voyage"
# Often 0 on first fire (depends on whether vessels were arriving in port
# during the 5-min window). Re-check after 1h — should be > 0.
```

### S7. Frontend vessel layer

Navigate to `https://maps.etzhayyim.com/` in a browser:

- zoom 0–7: blue translucent hex polygons appear over Singapore Strait,
  English Channel, Tokyo Bay, etc. (density layer)
- zoom ≥ 8: individual vessel circles, color-coded by `type_class` (green
  = cargo, red = tanker, blue = passenger, …)
- click any vessel → top-right panel populates with name / MMSI / IMO /
  flag / dimensions / last seen / voyage

Failure: panel shows `loading…` then nothing → check browser DevTools
Network tab for `aismarine.getVesselDetail` 4xx/5xx response.

## Rollback

Each step is independently reversible.

| Step | Rollback |
|---|---|
| 7 (Worker / UI) | `etzhayyim deploy --rollback` to previous version (CF deploy preserves history) |
| 6 (consumer) | `kubectl -n maps-bulk-ingest scale deploy/bulk-ingest-aismarine --replicas=0` (idempotent; data already written stays) |
| 5 (image) | revert `:1.3.0` tag, redeploy `:1.2.0` (pre-aismarine baseline) |
| 4 (BPMN) | `psql -c "UPDATE vertex_bpmn_process_def SET status='disabled' WHERE bpmn_process_id LIKE 'maps_aismarine%'"` — F5 watcher un-deploys |
| 3 (zeebe-worker) | `helm rollback` to previous revision (6 task types remain registered but un-fired) |
| 2 / 1 | migration `down()` not used in production — leave schema in place; tables are append-only and consume disk only |

Full kill-switch: `kubectl -n maps-bulk-ingest scale deploy/bulk-ingest-aismarine --replicas=0`. Within 60 s no new positions land; existing data is read-only and harmless.

## Cost & quota notes

- aisstream.io: free tier, no rate limit on receive (only on `BoundingBoxes`
  filter changes). Phase 1 is global no-filter.
- RisingWave write rate: ~100–500 msg/s typical, bursts to ~2 K msg/s at
  port-arrival times (Singapore, Rotterdam). `SET dml_rate_limit = 5000`
  in primitive throttles before B2 SlowDown threshold (ADR-0048
  incident_2026_04_25).
- Disk: `vertex_vessel_position` accumulates ~10–40 M rows/day at full
  global feed. Hummock cold-tiers to B2 automatically. Phase 1 has no TTL;
  Phase 2 (out of scope) can add `created_date < now() - 90d` purge.
- Cloudflare Worker: 4 read XRPC handlers, ~5–20 ms p50 (Hyperdrive +
  streaming MV). No new Worker deployed — existing maps-ui surface
  extended.

## References

- ADR-2605011500 — design SSoT
- `30-graph/graph-schema/migrations/20260501170000_vertex_aismarine_phase1.ts`
- `30-graph/graph-schema/migrations/20260501180300_seed_aismarine_bpmn_actors.ts`
- `00-contracts/lexicons/com/etzhayyim/apps/maps/aismarine/`
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/maps/aismarine/`
- `20-actors/magatama/py/src/pymagatama/primitives/aismarine.py`
- `60-apps/etzhayyim-project-maps/bulk-ingest/workers/aismarine_consumer.py`
- `60-apps/etzhayyim-project-maps/bulk-ingest/k8s/deployment-aismarine.yaml`
- `60-apps/etzhayyim-project-maps/appview/maps-ui-uqpel6i6/src/app.ts` (handlers)
- `60-apps/etzhayyim-project-maps/appview/maps-ui-uqpel6i6/svelte/src/lib/aismarine-overlay.ts`
