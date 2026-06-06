# atproto-pds RUNBOOK (ADR-2605111300)

Operational runbook for the K8s pod replacement of the PDS CF Worker (`etzhayyim-pds-2603241700`).

## Status (2026-05-14)

- **P0 — planning ADR + scaffolding**: done (2026-05-11)
- **P1 — Bun image build, canary deploy**: done (2026-05-14) — image `ghcr.io/etzhayyim/atproto-pds:bun-canary`, k8s Deployment in `atproto` ns, CF Tunnel `ce620136-d8cf-49cf-b247-477de89a1be7`
- **P2 — sanity / smoke tests on canary**: done (2026-05-14) — resolveHandle ✓, describeServer ✓, /_app/meta ✓ (via port-forward; CF Worker wildcard route intercepts atproto-canary.etzhayyim.com directly — P3 traffic split will address routing)
- **P3 — traffic split via CF Tunnel weighting**: not started
- **P4 — 100% pod, CF Worker stopped**: not started
- **P5 — CF Worker deleted, T3 carve-out closed**: not started

### P1 Learnings

- `createKyselyDb` was unconditionally throwing in the SDK (ADR-2605111200). Fixed with `isCFWorker()` guard (`caches && WorkerGlobalScope`) so Bun/Node pods work (ADR-2605111300). CF Workers still throw.
- `ghcr-pull` imagePullSecret must be created in `atproto` namespace from current docker credentials.
- Kotoba/Datomic service is `kotoba.kotoba.svc.cluster.local:4566` (NOT `kotoba-frontend`). User=`root`, no password.
- Metastore credentials (`kotoba` user, `wXIqw7pXSUxBmsD9Lx3TtGVP5yqPO6Qm`) are for the metastore PostgreSQL, not the RW data plane.
- CF Tunnel public hostname (`atproto-canary.etzhayyim.com`) is shadowed by PDS Worker's wildcard route — direct access via port-forward works. P3 must modify CF Worker routes or add canary-specific route.

## Build (Phase P1)

```bash
# Wrapper around 70-tools/scripts/buildkit/remote-build.sh (etzhayyim-vke builder).
50-infra/k8s/atproto-pds/build.sh                  # → ghcr.io/etzhayyim/atproto-pds:bun-canary
50-infra/k8s/atproto-pds/build.sh v1               # → ghcr.io/etzhayyim/atproto-pds:bun-v1
50-infra/k8s/atproto-pds/build.sh canary --load    # local Docker only (smoke run)
```

Expect ~6-10 min first build (dep install + bun build of ~30k LOC). Subsequent
builds reuse the registry cache `ghcr.io/etzhayyim/build-cache:atproto-pds-bun`
and finish in ~2-3 min.

### Local smoke run

```bash
50-infra/k8s/atproto-pds/build.sh canary --load
docker run --rm -p 8787:8787 \
  -e KOTOBA_URL=postgres://root@host.docker.internal:14566/dev?sslmode=disable \
  -e PLC_DIRECTORY_URL=https://plc.etzhayyim.com \
  -e AUTH_SERVICE_URL=https://auth.etzhayyim.com \
  -e APPVIEW_SERVICE_URL=https://bsky.etzhayyim.com \
  -e ROUTING_GATEWAY_URL=https://gateway.etzhayyim.com \
  -e VAULT_SERVICE_URL=https://vault.etzhayyim.com \
  -e BPMN_DISPATCHER_URL=http://localhost:8080 \
  -e IPFS_API_URL=https://ipfs.etzhayyim.com \
  -e LLM_GATEWAY_URL=https://llm.etzhayyim.com \
  ghcr.io/etzhayyim/atproto-pds:bun-canary

# In another terminal
curl -i http://localhost:8787/_app/meta
```

## Tunnel setup (manual, once)

1. CF dashboard → Zero Trust → Networks → Tunnels → Create a tunnel
2. Name: `atproto-etzhayyim-pds`
3. Public hostname: `atproto-canary.etzhayyim.com` → `http://atproto-pds.atproto.svc.cluster.local:8787` (during P1-P3), then add `atproto.etzhayyim.com` in P3
4. Copy tunnel token → `kubectl -n atproto create secret generic atproto-pds-tunnel-token --from-literal=token=<token>`

## Secrets (manual via Vault)

Provision via `etzhayyim vault` (preferred) or directly:

```bash
kubectl -n atproto apply -f 50-infra/k8s/atproto-pds/secrets-template.yaml
# Then edit each Secret to inject real values from Vault (CF Secrets Store → Vault mirror).
```

Required keys: `KOTOBA_URL`, `B2_KEY_ID`, `B2_APPLICATION_KEY`, `SS_REPO_SIGNING_KEK`, `SS_SIGNING_KEY`, tunnel `token`.

## Deploy (Phase P1)

```bash
kubectl create namespace atproto --dry-run=client -o yaml | kubectl apply -f -
kubectl -n atproto apply -f 50-infra/k8s/atproto-pds/service.yaml
kubectl -n atproto apply -f 50-infra/k8s/atproto-pds/deployment.yaml

# Wait for rollout
kubectl -n atproto rollout status deploy/atproto-pds --timeout=10m
```

## Smoke (Phase P2)

```bash
# Health (via tunnel)
curl https://atproto-canary.etzhayyim.com/_app/meta | jq

# AT Protocol identity resolution
curl 'https://atproto-canary.etzhayyim.com/xrpc/com.atproto.identity.resolveHandle?handle=jun.etzhayyim.com'

# Repo describe
curl 'https://atproto-canary.etzhayyim.com/xrpc/com.atproto.repo.describeRepo?repo=did:web:jun.etzhayyim.com'

# Firehose subscribe (websocket)
wscat -c 'wss://atproto-canary.etzhayyim.com/xrpc/com.atproto.sync.subscribeRepos?cursor=0'
```

Compare each response shape against the live CF Worker PDS (`https://atproto.etzhayyim.com/...`). Document deltas in `_deltas.md`.

## Traffic cutover (Phase P3)

CF dashboard → Traffic → Origin rules / Page rules:

1. Initial 1%: header-based or specific path (e.g. `/_app/health`) to pod-side
2. 10% via weighted random
3. 50% then 100%

Monitor:

- `atproto.etzhayyim.com` 5xx rate (CF Analytics)
- `atproto-pds` pod 5xx (Prometheus, k8s ServiceMonitor)
- Kotoba/Datomic write rate (no spikes / no stalls)
- AT Protocol firehose lag (commit replication, separate dashboard)

Rollback at any point: revert traffic weights to CF Worker.

## Worker shutdown (Phase P4)

```bash
# Disable the CF Worker (do NOT delete yet — keep for instant rollback)
cd 50-infra/cloudflare/workers/atproto
wrangler deployments list
# Mark current as "disabled" via CF dashboard (Workers → Triggers → disable routes)
```

Wait 7 days for any orphan callers. Then proceed to P5.

## Worker deletion (Phase P5)

```bash
# Final: delete the CF Worker entirely (irreversible)
cd 50-infra/cloudflare/workers/atproto
wrangler delete
# Move source to archive
git mv 50-infra/cloudflare/workers/atproto _archive/retired-cf-workers/atproto-2605111300/
```

Then close ADR-2605111200's "T3 infra carve-out" exception (commit follow-up).

## Rollback table

| Phase | Rollback action |
|---|---|
| P1 image | `kubectl -n atproto delete deploy atproto-pds` |
| P2 staging | n/a (canary only) |
| P3 traffic split | CF dashboard → weight back to 0% pod |
| P4 worker disabled | Re-enable CF Worker via dashboard |
| P5 worker deleted | Restore from archive + redeploy CF Worker (not instant, ~10 min) |

## Open issues

- Bun runtime compat with `@atproto/repo` (MST CAR signing): test in P1
- `R2Bucket` adapter shim is placeholder; full S3 client needed for `CACHE_R2`
- WebSocket (firehose `subscribeRepos`) Bun support: verify
- DurableObject rate-limit logic must be reimplemented as Redis-based counter
