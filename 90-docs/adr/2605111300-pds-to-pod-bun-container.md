---
id: adr-2605111300-pds-to-pod-bun-container
title: "atproto PDS を CF Worker から K8s Pod (Bun + Hono + cloudflared) へ移行"
status: accepted
doc_type: adr
topic: pds-runtime-migration
authoritative: true
last_verified: 2026-05-14
phase_status: "P1 complete (pod live, not handling external traffic yet). /_internal/create-social-post deployed and verified 2026-05-15 — Bun pod now used by lg-animeka publishEpisode via ClusterIP. P2 (canary smoke) blocked until atproto-canary.etzhayyim.com tunnel is healthy."
priority: 9.4
axis: architecture
weight: 0.92
priority_note: "CRITICAL — ADR-2605111200 を成立させる前提 = PDS が CF Worker から外れる必要がある。Bun container + CF Tunnel で持っていく。"
authoritative_for:
  - atproto-pds-runtime-location
  - pds-container-build-toolchain
  - pds-ingress-via-cloudflared-tunnel
  - pds-cf-binding-substitutes
  - pds-cutover-phasing
related:
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - adr-0014-self-hosted-did-plc
  - adr-0094-risingwave-stable-three-node-topology
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2604282300
supersedes: []
superseded_by: []
amends: []
amended_by: []
---

# Context

ADR-2605111200 が「CF Worker → RisingWave 接続を全面禁止」を定めたが、現在 `atproto.etzhayyim.com` を serve している **PDS Worker (`etzhayyim-pds-2603241700`, 38 ファイル / ~30k LOC) 自体が CF Worker** であり、commit log / record CRUD / DID document mirror / MCP registry など、Hyperdrive 経由で RisingWave に大量の write/read を発行している。

このため Phase 1 で `wrangler.jsonc` から hyperdrive binding を削除すると次回 `etzhayyim deploy` で本番が壊れる。一時 revert で凌いでいるが、ADR-2605111200 の不変条件を満たすには PDS 自体を K8s pod に移す必要がある。

設計選択肢:

1. **Bun container 化 (TS をそのまま)**: 38 ファイルの PDS code を Bun runtime + Hono router の container として pack。CF-specific binding (R2 / DO / Service / Hyperdrive / Secrets / KV) を Node 同等品に置換。 → **採用**
2. Python (Granian) で greenfield rewrite: ADR-2605080600 の L3 runtime と整合するが、AT Protocol commit signing / lexicon dispatch / MST repo の Python 実装が 1 から必要 (数ヶ月)。本 ADR では却下。
3. Sidecar 二刀流 (Python main + TS sidecar): inflight 複雑性が高すぎる。却下。

Ingress 選択肢:

1. **Cloudflare Tunnel (cloudflared sidecar)**: pod 内 cloudflared が outbound のみで CF edge に接続、`atproto.etzhayyim.com` の trafficを tunnel target に向ける。DNS / 証明書変更不要、DDoS 保護維持。 → **採用**
2. Vultr LoadBalancer + caddy TLS: 追加 cost ($10/mo) + DNS 変更 + Origin Cert 管理。geth で前例があるが PDS には不要なオーバーヘッド。却下。
3. CF Worker thin proxy + CF Tunnel inbound: hop +1 latency。本 ADR の意図 (Worker を edge-only にする) と矛盾。却下。

# Decision

## Target topology

```
   Public Internet (AT Protocol federation, browser, MCP client)
      │ HTTPS / WSS
      ▼
   Cloudflare Edge (DNS atproto.etzhayyim.com, DDoS, WAF, CF Tunnel terminator)
      │ outbound-only CF Tunnel
      ▼
┌─────────────────────────────────────────────────────────────┐
│ K8s Deployment: atproto-pds (namespace: atproto)             │
│                                                              │
│ ┌──────────────────────┐   ┌─────────────────────────────┐  │
│ │ Container: pds       │   │ Sidecar: cloudflared        │  │
│ │   Image: ghcr.io/    │   │   Image: cloudflare/        │  │
│ │     etzhayyim/        │   │     cloudflared:latest      │  │
│ │     atproto-pds:bun  │   │   Args: tunnel --no-autoup  │  │
│ │   Runtime: Bun 1.x   │   │     run --token $TUNNEL_TKN │  │
│ │   Entry: bun src/    │   │   Forwards: localhost:8787  │  │
│ │     index.ts (Hono)  │   │     → atproto.etzhayyim.com       │  │
│ │   Port: 8787         │◀──┤                             │  │
│ └────────┬─────────────┘   └─────────────────────────────┘  │
│          │                                                   │
│          ▼ pg over WireGuard or k8s ClusterIP                │
└──────────┼───────────────────────────────────────────────────┘
           │
           ▼
   RisingWave (Vultr LAX, 45.32.79.245:4566)
```

## Container build (Bun + Hono)

- Base image: `oven/bun:1.1-alpine` (multi-arch arm64/amd64)
- Entry: `50-infra/cloudflare/workers/atproto/src/index.ts` の Hono `app.fetch` を `Bun.serve({fetch})` で wrap
- Build: `bun install --frozen-lockfile && bun build src/index.ts --target=bun --outfile=dist/server.js`
- 起動: `CMD ["bun", "dist/server.js"]`
- BuildKit remote (ADR `buildkit-k8s-remote-build`) 経由で `linux/amd64` build → `ghcr.io/etzhayyim/atproto-pds:<tag>` push

## CF binding substitutes

| CF Worker binding | Container 置換 | Env / Secret |
|---|---|---|
| `env.HYPERDRIVE` | `pg.Pool({ connectionString })` direct | `RISINGWAVE_URL` (k8s Secret) |
| `env.CACHE_R2` (R2 bucket) | S3 client → B2 endpoint | `B2_KEY_ID` / `B2_APPLICATION_KEY` / `B2_BUCKET` (k8s Secret) |
| `env.AUTH_SERVICE` (Worker→Worker service binding) | HTTP fetch to `auth.etzhayyim.com` or k8s ClusterIP | `AUTH_SERVICE_URL` |
| `env.GRAPH_QUERY_SERVICE` | 直接 pg query へ収束 (Worker hop 廃止) | n/a |
| `env.ROUTING_GATEWAY` (did:web resolution) | HTTP fetch to `gateway.etzhayyim.com` | `ROUTING_GATEWAY_URL` |
| `env.PLC_DIRECTORY` | HTTP fetch to `plc.etzhayyim.com` | `PLC_DIRECTORY_URL` |
| `env.VAULT_SERVICE` | HTTP fetch to `vault.etzhayyim.com` | `VAULT_SERVICE_URL` |
| `env.APPVIEW_SERVICE` | HTTP fetch to `bsky.etzhayyim.com` (or pod-local AppView when migrated) | `APPVIEW_SERVICE_URL` |
| `env.RESOURCE_FLOW_SERVICE` | HTTP fetch to bpmn-dispatcher | `BPMN_DISPATCHER_URL` |
| `env.IPFS_API` | HTTP fetch to `ipfs.etzhayyim.com` | `IPFS_API_URL` |
| Durable Object (rate-limit / cache) | Redis (`mitama-udf-pool` redis service) | `REDIS_URL` |
| Secrets Store | k8s Secret `atproto-pds-secrets` | (per-key env) |
| `env.PDS_SERVICE_AUTH_MINT_SECRET` (Secrets Store) | k8s Secret `atproto-pds-secrets` key `PDS_SERVICE_AUTH_MINT_SECRET` | string env var; `resolveSecret` handles both shapes |
| Cloudflare AI binding | HTTP fetch to `llm.etzhayyim.com` (ADR-2605010000) | `LLM_GATEWAY_URL` |

## Cloudflared tunnel

- 既存 `geth-rpc-proxy` で使用しているのと同じ pattern。
- CF dashboard で `atproto-etzhayyim-pds-tunnel` を作成、token を取得。
- k8s Secret `atproto-pds-tunnel-token` に格納。
- Sidecar コンテナが `cloudflared tunnel --no-autoupdate run --token $TUNNEL_TOKEN` で起動。
- `atproto.etzhayyim.com` を tunnel target `http://localhost:8787` に向ける public hostname rule を CF dashboard で設定。

## Cutover phases

| Phase | Action | Rollback |
|---|---|---|
| **P0 (本 ADR 同時)** | (a) ADR 承認、(b) k8s manifest scaffold commit、(c) PDS wrangler に HYPERDRIVE binding を temp revert | n/a (planning only) |
| **P1** | Bun-build pipeline 完成、`atproto-pds:bun-canary` image push、staging namespace で起動。`atproto-canary.etzhayyim.com` (別 hostname) に CF Tunnel。2026-05-14 時点では public canary が 522 のため未完了扱い。 | image delete / cloudflared rollback |
| **P2** | Sanity: AT Protocol federation handshake / repo CRUD / firehose subscribe / MCP discovery を canary で smoke-test。RW load 同等性を観測。P1 canary 200 が前提。 | wrangler は触っていない → prod 影響なし |
| **P3** | CF dashboard で `atproto.etzhayyim.com` の traffic を 1% → 10% → 50% → 100% に段階移行 (CF tunnel weighted target or Page Rule)。observability: latency / error / commit log replication lag | 重み戻し |
| **P4** | 100% pod 後、CF Worker `etzhayyim-pds-2603241700` を deploy 停止 (`wrangler delete` は最終段階) | CF Worker 再 deploy |
| **P5** | CF Worker 削除、 `50-infra/cloudflare/workers/atproto/` を `_archive/` に移動、ADR-2605111200 の "T3 infra carve-out" 例外を閉じる | (irreversible without rebuild) |

## Out of scope (deferred to later ADRs)

- AppView (`bsky.etzhayyim.com`) pod 化 — 同じ pattern が適用可能、別 ADR
- Graph projection worker pod 化 — 既に pyzeebe 経路あり、低優先度
- Signal / Chat Worker pod 化 — PDS pipethrough のみなので PDS 移行後でも残せる
- Murakumo Worker pod 化 — LLM gateway、ADR-2605010000 と整合する別 path

# Consequences

**Positive**:
- ADR-2605111200 の不変条件が成立 (CF Worker は RW 接続なし)
- PDS bundle 制約 (10 MB / 128 MB / 30s CPU) から解放、AT Protocol full library (`@atproto/repo` MST + heavy dependencies) を制約なく使える
- Cloudflared sidecar により DNS / 証明書 / DDoS 保護が変わらない
- 38 ファイルの TS code を rewrite せずに移行可能 (Bun は Node API compat)

**Negative**:
- 多週間の作業 (P1-P5 で 3-6 週間想定)
- CF Tunnel egress に依存 (tunnel down = PDS unreachable)。redundancy が必要なら 2 tunnel + CF traffic steering
- pod が WireGuard 経由で RW に接続する場合の network policy 設計が必要
- Bun runtime の Worker-API surface 互換性検証 (`R2Bucket`, `DurableObjectNamespace`, `Service` binding は全置換要)

# Implementation references

- Scaffolding: `50-infra/k8s/atproto-pds/` (本 ADR 同時 commit)
- Runbook: `50-infra/k8s/atproto-pds/RUNBOOK.md`
- 既存 cloudflared pattern: `50-infra/vultr/geth-private/manifests/` (geth-rpc-proxy)
- Migration tracking: `deps.toml [[migrations]] pds-to-pod-bun-container`

# 2026-05-14 Deployment Attempt Record

The session attempted the smallest possible production transition:

1. Build the existing SvelteKit PDS facade as a transparent edge proxy.
2. Deploy `atproto.etzhayyim.com` with `PDS_UPSTREAM_URL` targeting
   `https://atproto-canary.etzhayyim.com`.
3. Verify production XRPC/meta endpoints.

The deploy succeeded mechanically, but the upstream failed:

- `GET https://atproto.etzhayyim.com/xrpc/com.atproto.server.describeServer`
  returned a Cloudflare 522 page for `atproto-canary.etzhayyim.com`.
- `GET https://atproto.etzhayyim.com/_app/meta` did not return the expected PDS meta
  while the proxy was pointed at canary.

Production was rolled back immediately:

- attempted thin-proxy deploy version:
  `d5a5cb9e-77c1-4f5c-a2ba-178bf020c24a`;
- rollback CF Worker PDS version:
  `3cda23e8-7e9c-406e-bace-9e7ed0617d0b`;
- post-rollback verification:
  `/_app/meta` returned 200 and
  `/xrpc/com.atproto.server.describeServer` returned 200.

This confirms the cutover blocker is not the edge proxy shape; it is the
`atproto-canary.etzhayyim.com` tunnel/origin readiness. Do not redeploy the thin
proxy to production until these gates pass:

```bash
kubectl -n atproto get pods,svc,deploy
kubectl -n atproto logs deploy/atproto-pds -c pds --tail=200
kubectl -n atproto logs deploy/atproto-pds -c cloudflared --tail=200
curl -i https://atproto-canary.etzhayyim.com/_app/meta
curl -i 'https://atproto-canary.etzhayyim.com/xrpc/com.atproto.server.describeServer'
```

Expected canary gate before any production cutover:

- canary returns HTTP 200 for `_app/meta`;
- canary returns AT Protocol server metadata for
  `com.atproto.server.describeServer`;
- cloudflared sidecar has an active tunnel and routes public hostname traffic to
  `http://atproto-pds.atproto.svc.cluster.local:8787`;
- pds container can reach RisingWave and required service substitutes.

# 2026-05-15 Internal Endpoint Activation Record

The Bun pod is now used in production for internal writes by `lg-animeka`'s
`publishEpisode` graph, without yet handling any external `atproto.etzhayyim.com`
traffic. This is the first real write load on the pod.

## `/_internal/create-social-post` (HMAC-authenticated)

Added to `50-infra/cloudflare/workers/atproto/src/app.ts`:

```
POST /_internal/create-social-post
x-bpmn-auth: HMAC-SHA256(PDS_SERVICE_AUTH_MINT_SECRET, request_body)
Body: { repo, text, embedUri?, embedTitle?, embedDescription? }
→ comAtprotoRepoCreateRecord(env, repo, "app.bsky.feed.post", record)
→ { uri, cid }
```

This handler is registered at line 520 of `app.ts` and is included in the
`bun-canary` image rebuilt 2026-05-15. The CF Worker deployment of the same
handler returns HTTP 500 (`HYPERDRIVE binding required`) because the CF Worker
is edge-only (ADR-2605111200); the Bun pod has `HYPERDRIVE` via
`RISINGWAVE_URL` and succeeds.

## Secrets

`PDS_SERVICE_AUTH_MINT_SECRET` added to k8s Secret `atproto-pds-secrets` in
namespace `atproto` (same key value as `pds-service-auth-mint/secret` in
`mitama-udf`). Referenced in `deployment.yaml` env block. The `resolveSecret`
helper in `auth/verify.ts` handles both `{get()}` (CF Secrets Store) and
`string` (plain env var from Bun `...process.env`) transparently.

## Build note

Remote BuildKit (`etzhayyim-vke-local` driver, pod `etzhayyim-vke0-*` in namespace
`buildkit`, port-forwarded to `localhost:1234`) rebuilt `bun-canary` after
updating the pnpm lockfile for `50-infra/cloudflare/workers/atproto/svelte/`.
The `etzhayyim-vke` Kubernetes driver is not installed; use the `etzhayyim-vke-local`
remote driver with port-forward instead.

## Verification

```
POST http://atproto-pds.atproto.svc.cluster.local:8787/_internal/create-social-post
→ 200 { uri: "at://did:web:animeka.etzhayyim.com/app.bsky.feed.post/3mluhfalehc2g", cid: "..." }
episode ep-1776928323916-1 → status='announced'
```

# References

- ADR-2605111200 (CF Worker edge-only): 本 ADR の根拠
- ADR-0014 (self-hosted did:plc): PLC directory 連携は HTTP fetch に置換
- ADR-0094 (RisingWave 3-node topology): RW endpoint
- ADR-2605080600 (LangGraph Server + Granian L3): app actor 経路、PDS とは独立
- `bun.sh` runtime: AT Protocol PDS で実際に動作する Node API subset を持つ
- `cloudflared` Helm chart pattern: `50-infra/vultr/geth-private/`
