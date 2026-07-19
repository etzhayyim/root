# ipfs.etzhayyim.com — self-hosted Kubo on Vultr VKE

ADR-2604261936 reference deployment. Kubo (go-ipfs) v0.31.0 single-replica
StatefulSet, blocks on Backblaze B2 via `go-ds-s3`, gateway exposed through
caddy → Vultr LB → CF Worker (`etzhayyim-ipfs-proxy`) at `ipfs.etzhayyim.com`.

| Field | Value |
|---|---|
| Cluster | Vultr VKE (lax), namespace `ipfs` |
| Pod | StatefulSet `kubo`, replicas=1, image `ipfs/kubo:v0.31.0` |
| PVC | `kubo-repo-0`, 40 Gi, `vultr-block-storage-hdd-retain` (metadata only; Vultr block storage min size is 40 GiB) |
| Block store | B2 `s3://etzhayyim-nats/ipfs/blocks/` (us-west-004; shared bucket with RW Hummock per ADR-0048, isolated by prefix) |
| Gateway (in-cluster) | `http://kubo.ipfs.svc.cluster.local:8080` |
| API (in-cluster) | `http://kubo.ipfs.svc.cluster.local:5001` (NEVER public) |
| Swarm | NodePort 30401 (TCP+UDP) |
| TLS proxy | `caddy-ipfs-tls` Deployment, replicas=2, Vultr LB :443 |
| Public DNS | `ipfs.etzhayyim.com` (CF proxied) → Worker `etzhayyim-ipfs-proxy` |
| Origin DNS | `ipfs-origin.etzhayyim.com` (CF proxied) — port-rewrite rule to :8443 |

## Layout

```
50-infra/vultr/ipfs/
├── CLAUDE.md                this file
├── manifests/
│   ├── 00-namespace.yaml
│   ├── 10-statefulset.yaml  Kubo + init-container that envsubsts B2 keys into datastore_spec
│   ├── 20-service.yaml      ClusterIP gateway/api + NodePort swarm
│   ├── 40-tls-proxy.yaml    caddy + Vultr LB + self-signed cert
│   └── apply.sh             idempotent bring-up
├── config/
│   └── datastore_spec.json  go-ds-s3 + levelds spec template
└── scripts/
    └── init-config.sh       on-pod first-boot + reconcile
```

CF Worker proxy lives separately at
`50-infra/cloudflare/workers/ipfs-proxy/` (path-split auth).

## Bring-up (one-time)

Pre-reqs:

1. **B2 prefix** `s3://etzhayyim-nats/ipfs/blocks/` (no new bucket needed —
   the existing `etzhayyim-nats` bucket is shared with Kotoba/Datomic Hummock per
   ADR-0048 and isolated by prefix). The Keychain entry `etzhayyim.b2`
   (ACCESS_KEY_ID + SECRET_ACCESS_KEY) is already scoped to this `bucketId`
   with `writeFiles` / `deleteFiles` / `readFiles` capabilities — verify with:
   ```
   security find-generic-password -s etzhayyim.b2 -a ACCESS_KEY_ID -w >/dev/null && echo OK
   ```
   No new application key required.
2. **CF Origin Cert** (self-signed leaf valid 10 y for `ipfs-origin.etzhayyim.com`)
   — generate locally with `openssl` and store in Keychain:
   ```
   openssl req -x509 -newkey rsa:2048 -days 3650 -nodes \
     -subj '/CN=ipfs-origin.etzhayyim.com' \
     -addext 'subjectAltName=DNS:ipfs-origin.etzhayyim.com' \
     -keyout ipfs-origin.key -out ipfs-origin.crt
   security add-generic-password -U -s etzhayyim.cloudflare -a IPFS_ORIGIN_CERT_PEM -w "$(cat ipfs-origin.crt)"
   security add-generic-password -U -s etzhayyim.cloudflare -a IPFS_ORIGIN_CERT_KEY -w "$(cat ipfs-origin.key)"
   rm ipfs-origin.{crt,key}
   ```
3. **CF zone settings**: SSL mode = "Full" (the default for `etzhayyim.com`).
4. **CF Origin Rule**: when `http.host == "ipfs-origin.etzhayyim.com"` rewrite the
   origin port to `443` (Vultr LB), and let zone SSL handle TLS to caddy:8443.
5. **CF DNS**: add `ipfs.etzhayyim.com` (CNAME → CF proxied) and `ipfs-origin.etzhayyim.com`
   (A record → Vultr LB external IP, CF proxied). Both via `etzhayyim dns-sync`.
6. **CF Workers Secrets Store**: provision the HMAC key for the Worker:
   ```
   wrangler secrets-store secret create 1824561668fe47cc9127d493961885af \
     --name ipfs_hmac --scopes workers \
     --value "$(openssl rand -hex 32)"
   security add-generic-password -s etzhayyim.cloudflare -a IPFS_HMAC -w "<the-same-value>" -U
   ```
   The local Keychain copy lets internal callers (PDS, claim-consumer)
   compute matching signatures.

Then apply:

```bash
bash 50-infra/vultr/ipfs/manifests/apply.sh
```

The script is re-runnable. ConfigMap and Secret use server-side `apply` so
updates land safely. PVC + identity key persist across rollouts.

## Deploy the Worker

```bash
cd 50-infra/cloudflare/workers/ipfs-proxy
pnpm install
CLOUDFLARE_ACCOUNT_ID=4da88288dc30d9ee257f319d3c33ecf0 \
CLOUDFLARE_API_TOKEN="$(security find-generic-password -s etzhayyim.cloudflare -a API_TOKEN -w)" \
  wrangler deploy
```

Smoke:

```bash
# Public — should serve the well-known empty-directory CID
curl -sSI https://ipfs.etzhayyim.com/ipfs/bafybeiczsscdsbs7ffqz55asqdf3smv6klcw3gofszvwlyarci47bgf354 | head

# Read API
curl -sS -X POST 'https://ipfs.etzhayyim.com/api/v0/version'

# Write API without HMAC → 401
curl -sS -X POST 'https://ipfs.etzhayyim.com/api/v0/pin/add?arg=bafy...' -w "\n%{http_code}\n"

# Write API with HMAC
BODY="$(printf 'arg=bafy...&recursive=true' )"
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$(security find-generic-password -s etzhayyim.cloudflare -a IPFS_HMAC -w)" -binary | xxd -p -c 999)
curl -sS -X POST 'https://ipfs.etzhayyim.com/api/v0/pin/add' \
  -H "X-etzhayyim-Ipfs-Auth: $SIG" \
  -H "content-type: application/x-www-form-urlencoded" \
  -d "$BODY"
```

## Operational notes

- **Pin SLA invariant**: never enable `Datastore.GCPeriod` or call
  `repo gc` while pinned content is pending B2 sync. Run GC manually after
  `ipfs pin verify` reports 0 missing blocks.
- **B2 key rotation**: rotate the application key by updating the
  `kubo-b2` Secret + restarting the StatefulSet. The init script re-reads
  `Datastore.Spec` on every boot, so the new key takes effect on first
  pod restart. There's no in-flight traffic loss because Kubo lazily
  authenticates per-request.
- **Identity key custody**: the peer-id private key lives in
  `$IPFS_PATH/config.Identity.PrivKey` on the PVC. Loss = the gateway gets
  a new peer-id and needs to re-bootstrap DHT presence (1-2 hours).
  Backup: `kubectl -n ipfs exec sts/kubo -- cat /data/ipfs/config | jq .Identity` →
  store in macOS Keychain `etzhayyim.ipfs/IDENTITY_PRIV_KEY`.
- **Memory**: the 4 Gi limit assumes `Swarm.ConnMgr.HighWater=400`. Bumping
  HighWater past ~600 has tipped over similar 4 Gi pods in the past;
  raise the pod limit before raising HighWater.
- **B2 rate limits**: ADR-0048 incident notes apply here too. If
  `mv_kaikei_*` or other RW MVs are mid-checkpoint storming B2, expect
  Kubo `s3.datastore.put` latency to spike. The rw-health-gate
  (`70-tools/scripts/ingest/rw-health-gate.sh`) covers Kotoba/Datomic only —
  there's no equivalent gate for Kubo today. Phase 2 work.
- **CSAM / abuse**: serving public CIDs is a content-moderation
  responsibility. Phase 1 inherits Cloudflare's
  blocklist (we sit behind their gateway implicitly), but a separate
  ADR (`ipfs-content-moderation`) should land before traffic crosses
  ~1 TB/mo egress.

## Restore drill (Phase 2 deliverable)

```bash
# Simulated PVC loss
kubectl -n ipfs delete pvc kubo-repo-kubo-0
kubectl -n ipfs delete pod kubo-0
# StatefulSet recreates pod + new PVC; init runs `ipfs init` fresh.
# Identity changes (new peer-id) — backed-up identity must be re-injected.
# Restore the saved private key:
NEW_PEER_KEY="$(security find-generic-password -s etzhayyim.ipfs -a IDENTITY_PRIV_KEY -w)"
kubectl -n ipfs exec sts/kubo -- ipfs config Identity.PrivKey "$NEW_PEER_KEY"
kubectl -n ipfs rollout restart sts/kubo
# Block data on B2 is unchanged — once the pod re-syncs the pinset (mfs root
# stored in the levelds slot of the freshly mounted PVC, so this needs the
# identity restored first to keep peer-id stable), all pinned CIDs resolve.
```

For now this is documented but not exercised — Phase 2 will land a
`50-infra/vultr/ipfs/scripts/restore-drill.sh` mirroring
`50-infra/vultr/kotoba/helm/dr-restore-drill.sh`.

## Cross-project hooks

- **PDS** (`50-infra/cloudflare/workers/atproto/`): Phase 1.5 will fire-and-forget
  `IPFS_API.fetch("/api/v0/pin/add?arg=<sha256-cid>")` after each
  `com.atproto.repo.uploadBlob`. Pin is best-effort; PDS continues even
  on Kubo outage.
- **claim-consumer** (`50-infra/cloudflare/workers/claim-consumer/`):
  Phase 1.5 pins `atRecordCid` from each `ClaimPosted` event so the
  staked claim's evidence stays content-addressed even if the original
  AT Record is later compacted. Service binding `IPFS_API` →
  `etzhayyim-ipfs-proxy`.
- **did:etzhayyim resolver** (`orgs/etzhayyim/com-etzhayyim-did-etzhayyim/resolver/`): Phase 3 — pin
  every genesis-op DAG-CBOR CID under a dedicated namespace (`/keys/did-etzhayyim-genesis`)
  and serve via `/ipfs/{cid}` for federation peers.

## Cost (target)

| Item | Monthly |
|---|---|
| Vultr LoadBalancer (TCP) | $10 |
| Pod resources (shared on `kotoba-pool-32gb`) | $0 incremental |
| PVC 5 Gi `vultr-block-storage-hdd-retain` | $0.50 |
| B2 storage (assume 100 GB Phase 1) | $0.50 |
| B2 egress to CF (Bandwidth Alliance) | $0 |
| CF Worker requests (Free tier ~10M/d covers gateway) | $0 baseline / $5 flat-rate if exhausted |
| **Total Phase 1** | **~$11–16/mo** |

ADR-0048 / ADR-2604251400 cost methodology (B2 + Bandwidth Alliance) carries.

## Phase 1.5 — PDS blob pin + evidence crawler integration (2026-04-28)

**Status**: code shipped; secret provisioning + migration required before activation.

### 1. Share IPFS_HMAC with PDS Worker

The IPFS_HMAC key is already set on `etzhayyim-ipfs-proxy`. Copy it to the PDS Worker:

```bash
# Read the existing key from Keychain (set during Phase 1 bring-up)
HMAC_VALUE="$(security find-generic-password -s etzhayyim.cloudflare -a IPFS_HMAC -w)"

# Provision on PDS Worker (wrangler 4.x)
CLOUDFLARE_API_TOKEN="$(security find-generic-password -s etzhayyim.cloudflare -a API_TOKEN -w)" \
  wrangler secret put IPFS_HMAC \
  --name etzhayyim-pds-2603241700 <<< "$HMAC_VALUE"
```

Then redeploy PDS (triggers the `IPFS_API` service binding + `IPFS_HMAC` secret to take effect):

```bash
cd 50-infra/cloudflare/workers/atproto
CLOUDFLARE_ACCOUNT_ID=4da88288dc30d9ee257f319d3c33ecf0 \
CLOUDFLARE_API_TOKEN="$(security find-generic-password -s etzhayyim.cloudflare -a API_TOKEN -w)" \
  wrangler deploy
```

### 2. Store IPFS_HMAC in Keychain for Python workers

```bash
security add-generic-password -U \
  -s etzhayyim.ipfs -a HMAC_KEY \
  -w "$(security find-generic-password -s etzhayyim.cloudflare -a IPFS_HMAC -w)"
```

This is used by both `capture_gyosei_sources_to_b2.py` and `ipfs_ingest.py` (LangServer worker).

### 3. Run the Kotoba/Datomic migration

```bash
cd 30-graph/graph-schema
pnpm db:migrate latest
# Adds ipfs_cid_document + ipfs_cid_thumbnail columns to vertex_gyosei_source_blob
```

### 4. Smoke test

```bash
# PDS blob → IPFS (after redeploy):
curl -sS https://atproto.etzhayyim.com/xrpc/com.atproto.repo.uploadBlob \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: image/webp" \
  --data-binary @some.webp | jq .
# → then check https://ipfs.etzhayyim.com/ipfs/<cid-returned> within ~5s

# Evidence crawler (one source):
cd 70-tools/evidence-crawler
python capture_gyosei_sources_to_b2.py \
  --source-id nta-2024-01 \
  --dry-run  # remove --dry-run for real run
```
