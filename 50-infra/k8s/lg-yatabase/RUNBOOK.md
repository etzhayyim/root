# lg-yatabase deploy runbook

LangGraph Server (Granian / FastAPI) hosting BMC + marketing + sales graphs
for yatabase.etzhayyim.com. The pod is the **single writer** for `vertex_bmc_*` /
`edge_bmc_*` / `mv_bmc_*` (ADR-2605111200). yatabase CF Worker is a thin
HMAC forwarder (`src/bmc-forward.ts`) and never touches Hyperdrive for BMC.

## Prerequisites

1. **VKE context**
   ```bash
   kubectl config use-context vke-a61d513b-f9b7-4121-abb9-b53732aa5ec4
   kubectl -n mitama-udf get all   # sanity
   ```
2. **GHCR pull secret** in `mitama-udf` (one-time):
   ```bash
   export GHCR_TOKEN="$(gh auth token)"
   kubectl -n mitama-udf create secret docker-registry ghcr-pull \
     --docker-server=ghcr.io \
     --docker-username="$(gh api user -q .login)" \
     --docker-password="$GHCR_TOKEN" \
     --docker-email=ops@etzhayyim.com \
     --dry-run=client -o yaml | kubectl apply -f -
   ```
3. **RisingWave schema applied** — see `30-graph/graph-schema/sql_migrations/20260512000000_bmc_lean_iteration.up.sql`. If the cluster is in DDL backpressure (P29), wait for `rw-health-gate.sh` to return clean before retry.

## 1. Build + push image (remote BuildKit, linux/amd64)

```bash
# From repo root. Builds the lg-yatabase image with the updated bmc/* modules
# and bmc_iteration graph. Uses VKE BuildKit cache.
cd 60-apps/etzhayyim-project-yatabase/lg

docker buildx build \
  --builder etzhayyim-vke \
  --platform linux/amd64 \
  --build-context py=../../../20-actors/magatama/py \
  --cache-from type=registry,ref=ghcr.io/etzhayyim/build-cache:lg-yatabase \
  --cache-to   type=registry,ref=ghcr.io/etzhayyim/build-cache:lg-yatabase,mode=max \
  -t ghcr.io/etzhayyim/lg-yatabase:0.0.2-amd64 \
  --push .
```

## 2. Create / rotate the Secret

Pull RW_URL from macOS Keychain (root role for INSERT), DISPATCHER_INTERNAL_SECRET
from the shared CF Secrets Store, LG_YATABASE_API_KEY freshly minted.

```bash
RW_URL=$(security find-generic-password -s etzhayyim.rw -a ROOT_URL -w)
DSEC=$(op item get 'dispatcher_internal_secret' --fields label=credential 2>/dev/null \
       || security find-generic-password -s etzhayyim -a DISPATCHER_INTERNAL_SECRET -w)
LGK=$(uuidgen)
ORK=$(op item get 'openrouter_api_key' --fields label=credential 2>/dev/null || echo "")
SSK=$(op item get 'STRIPE_SECRET_KEY' --fields label=credential 2>/dev/null || echo "")

kubectl -n mitama-udf create secret generic lg-yatabase-secrets \
  --from-literal=RW_URL="$RW_URL" \
  --from-literal=DISPATCHER_INTERNAL_SECRET="$DSEC" \
  --from-literal=LG_YATABASE_API_KEY="$LGK" \
  --from-literal=OPENROUTER_API_KEY="$ORK" \
  --from-literal=STRIPE_SECRET_KEY="$SSK" \
  --dry-run=client -o yaml | kubectl apply -f -

# Remember the LG_YATABASE_API_KEY value — you'll need it for `wrangler secret put`
# on the yatabase Worker (so /runs auth matches).
echo "LG_YATABASE_API_KEY=$LGK"
```

## 3. Apply the deployment

```bash
kubectl apply -k 50-infra/k8s/lg-yatabase/

# Wait for rollout
kubectl -n mitama-udf rollout status deployment/lg-yatabase --timeout=120s

# Quick smoke
POD=$(kubectl -n mitama-udf get pod -l app.kubernetes.io/name=lg-yatabase -o jsonpath='{.items[0].metadata.name}')
kubectl -n mitama-udf logs "$POD" --tail=40
kubectl -n mitama-udf exec "$POD" -- curl -s localhost:8000/health
kubectl -n mitama-udf exec "$POD" -- curl -s localhost:8000/graphs
```

## 4. Expose to yatabase CF Worker

The Worker forwards `/xrpc/com.etzhayyim.apps.yata.bmc*` to `${LG_YATABASE_URL}/xrpc/...`.
Two production-grade paths:

### Path A — Cloudflare Tunnel (recommended)

```bash
cloudflared tunnel route dns <tunnel-id> lg-yatabase.internal.etzhayyim.com
# In the tunnel config:
#   ingress:
#     - hostname: lg-yatabase.internal.etzhayyim.com
#       service: http://lg-yatabase.mitama-udf.svc.cluster.local:8000
#     - service: http_status:404
```

Then on the Worker:
```bash
cd 60-apps/etzhayyim-project-yatabase
wrangler secret put LG_YATABASE_URL   # https://lg-yatabase.internal.etzhayyim.com
```

### Path B — bpmn-dispatcher passthrough (interim)

Route Worker BMC traffic through the existing dispatcher (no new tunnel) by
setting `LG_YATABASE_URL=https://dispatcher.etzhayyim.com/lg-yatabase` and adding
the corresponding ingress rule in `bpmn-dispatcher`. Trades a hop for zero
new infra.

## 5. Smoke

```bash
curl -sS https://yatabase.etzhayyim.com/health
curl -sS -H "authorization: Bearer sk_live_yata_..." \
  https://yatabase.etzhayyim.com/xrpc/com.etzhayyim.apps.yata.bmcGetState
curl -sS -X POST -H "authorization: Bearer sk_live_yata_..." \
  -H "content-type: application/json" \
  -d '{"dryRun":true}' \
  https://yatabase.etzhayyim.com/xrpc/com.etzhayyim.apps.yata.bmcIterate
```

Expected for the first call after fresh schema apply: `bmcGetState` returns
`{version:0, canvasJson:"{}", source:"seed"}`. `bmcIterate dryRun=true`
returns `{ok:true, picked:null, notes:"no active hypothesis; loop idle"}`.

## Cron

`lg/langgraph.json` declares `0 7 * * *` for the bmc_iteration graph. The
LangGraph Server reads this at startup. The yatabase CF Worker cron
`15 */6 * * *` was retired (P55, deps.toml).

## Rollback

```bash
kubectl -n mitama-udf rollout undo deployment/lg-yatabase
# or drop the deployment entirely:
kubectl delete -k 50-infra/k8s/lg-yatabase/
# Worker fallback when LG_YATABASE_URL unreachable:
# bmcForward returns 503 with `LG_YATABASE_URL not configured`.
# Operator can revert yatabase Worker to the pre-cutover commit if needed.
```
