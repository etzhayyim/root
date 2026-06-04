# maps-osm-ingest — K8s Jobs + Weekly CronJob

OSM PBF → RisingWave `vertex_osm_element` / `edge_osm_way_node` /
`edge_osm_relation_member` streaming ingest. Option B (direct-to-graph)
topology — no B2 blob intermediate for query, B2 only holds resume
checkpoints. Rationale in `deps.toml [[migrations]] maps-forward-topology-raw-to-webgpu`.

## Manifests

| File | Purpose | Runtime |
|---|---|---|
| `job-japan-dryrun.yaml` | Japan (~2GB PBF) validation before planet | ~45-60 min |
| `job-planet-bootstrap.yaml` | First planet ingest (one-shot) | ~12-24h |
| `cronjob.yaml` | Weekly refresh (Sun 03:00 UTC) | ~8-12h per run, after bootstrap |

## Bootstrap sequence (first-run)

The existing LKE cluster (`etzhayyim-risingwave`, id=589404, sg-sin-2) runs
a single GPU node (`g2-gpu-rtx4000a1-l`) hosting RisingWave + TEI + Ollama.
The planet ingest Job needs 40-56 GiB RAM and would starve those workloads,
so we **add a temporary node pool, run the Job there, then delete the pool**.

### Prerequisites (one-time)

Environment:
```bash
export LINODE_API_KEY="$LINODE_API_KEY_251205"   # already in your shell env
export KUBECONFIG="$(mktemp)"
curl -sH "Authorization: Bearer $LINODE_API_KEY" \
  https://api.linode.com/v4/lke/clusters/589404/kubeconfig \
  | python3 -c 'import sys,json,base64;print(base64.b64decode(json.load(sys.stdin)["kubeconfig"]).decode())' \
  > "$KUBECONFIG"
```

1. **Build + push image** (skip if already pushed):
   ```bash
   cd 70-tools/maps-osm-ingest
   docker build --platform linux/amd64 -t ghcr.io/etzhayyim/maps-osm-ingest:latest .
   docker push ghcr.io/etzhayyim/maps-osm-ingest:latest
   ```

2. **Create secrets** (RISINGWAVE_URL only — B2 no longer required):
   ```bash
   kubectl -n maps create secret generic maps-osm-ingest-secrets \
     --from-literal=RISINGWAVE_URL="postgres://root@risingwave-frontend.risingwave:4566/dev"
   ```

### Step-by-step: add ephemeral pool, run ingest, tear down

```bash
# 1. Add a temporary g6-standard-16 node pool (16 vCPU / 64 GiB, $0.576/h ≈ $14/24h)
POOL_ID=$(curl -s -XPOST -H "Authorization: Bearer $LINODE_API_KEY" \
  -H 'content-type: application/json' \
  -d '{"type":"g6-standard-16","count":1,"tags":["osm-ingest","ephemeral"]}' \
  'https://api.linode.com/v4/lke/clusters/589404/pools' | python3 -c 'import sys,json;print(json.load(sys.stdin)["id"])')
echo "new pool id: $POOL_ID"

# 2. Wait ~3-5 min for node to become Ready
kubectl get nodes -w   # Ctrl-C when the new node shows Ready

# 3. Taint the new node so only our Job lands there
NEW_NODE=$(kubectl get nodes -l '!node-class' -o jsonpath='{.items[?(@.metadata.labels.lke\.linode\.com/pool-id=="'$POOL_ID'")].metadata.name}')
kubectl label  node "$NEW_NODE" workload=osm-ingest
kubectl taint  node "$NEW_NODE" workload=osm-ingest:NoSchedule

# 4. Dry-run (Japan, ~45-60 min)
kubectl apply -f 50-infra/k8s/maps-osm-ingest/job-japan-dryrun.yaml
kubectl -n maps logs -f job/maps-osm-ingest-japan-dryrun
# Validate with the SQL at the bottom of job-japan-dryrun.yaml

# 5. Planet bootstrap (only after dry-run PASS, ~12-24h)
kubectl apply -f 50-infra/k8s/maps-osm-ingest/job-planet-bootstrap.yaml
kubectl -n maps logs -f job/maps-osm-ingest-planet-bootstrap
# Expect ~10.2B rows in vertex_osm_element, ~11B in edge_osm_way_node

# 6. Tear down the ephemeral pool (cost stops here)
kubectl -n maps delete job maps-osm-ingest-japan-dryrun maps-osm-ingest-planet-bootstrap
curl -XDELETE -H "Authorization: Bearer $LINODE_API_KEY" \
  "https://api.linode.com/v4/lke/clusters/589404/pools/$POOL_ID"
```

Total cost for first-run: ~$15-20 (one pool-day of g6-standard-16).

### Weekly autopilot

`cronjob.yaml` handles weekly refreshes on Sun 03:00 UTC. For each run,
the same pool-add/taint/run/delete sequence should be automated by a
GitHub Actions workflow (future `.github/workflows/maps-osm-ingest.yml`).

---

## Legacy (CronJob-only) notes

Weekly full-replace ingest of the OSM planet PBF into RisingWave.

- Namespace: `maps`
- Schedule: `0 3 * * 0` (Sun 03:00 UTC)
- Source DID: `did:web:maps.etzhayyim.com:planet`
- Image: `ghcr.io/etzhayyim/maps-osm-ingest:<tag>`
- Node class requirement: Linode `g7-premium-16` or similar (16 vCPU, 32 GiB).
  The job requests 8 CPU / 16 Gi and peaks near 12 CPU / 24 Gi during decode.

## Secrets

Create `maps-osm-ingest-secrets` in `maps` namespace:

```bash
kubectl -n maps create secret generic maps-osm-ingest-secrets \
  --from-literal=PBF_URL="https://planet.openstreetmap.org/pbf/planet-latest.osm.pbf" \
  --from-literal=RISINGWAVE_URL="postgres://root@risingwave-frontend.risingwave:4566/dev" \
  --from-literal=R2_ENDPOINT="https://<acct>.r2.cloudflarestorage.com/<bucket>" \
  --from-literal=R2_CHECKPOINT_BUCKET="<bucket>" \
  --from-literal=R2_ACCESS_KEY_ID="<redacted>" \
  --from-literal=R2_SECRET_ACCESS_KEY="<redacted>"
```

## Deploy

```bash
kubectl apply -f 50-infra/k8s/maps-osm-ingest/cronjob.yaml
```

## One-shot trigger

```bash
kubectl -n maps create job --from=cronjob/maps-osm-ingest maps-osm-ingest-manual-$(date +%s)
```

## Logs

```bash
kubectl -n maps logs -l app.kubernetes.io/name=maps-osm-ingest --tail=200 -f
```

Structured JSON logs are picked up by the cluster fluent-bit → Grafana Loki.

## Verify ingestion

```bash
psql "postgres://root@risingwave-frontend.risingwave:4566/dev" <<'SQL'
SELECT COUNT(*) AS n
FROM vertex_osm_element
WHERE source_did = 'did:web:maps.etzhayyim.com:planet';

SELECT osm_type, COUNT(*) AS n
FROM vertex_osm_element
WHERE source_did = 'did:web:maps.etzhayyim.com:planet'
GROUP BY osm_type;
SQL
```

Expected planet scale (as of 2025):
- `osm_type='n'` ≈ 9.1 B rows
- `osm_type='w'` ≈ 1.0 B rows
- `osm_type='r'` ≈ 12 M rows
- `edge_osm_way_node` ≈ 11 B rows
- `edge_osm_relation_member` ≈ 150 M rows

## Tuning

- `--parallelism` — decoder rayon threads; raise for >16 vCPU nodes.
- `--batch-size` — rows per COPY batch; 100k is a good default for RisingWave.
- If the writer stalls, check `risingwave_meta_actor_barrier_latency` and the
  `compute` node memory — the COPY ingress generates many incremental rows
  to streaming MVs.

## Rollback

The CronJob can be suspended safely:

```bash
kubectl -n maps patch cronjob maps-osm-ingest -p '{"spec":{"suspend":true}}'
```

Idempotent design means retries never corrupt graph state.
