---
id: adr-2605111200-cf-worker-edge-only-no-rw-connection
title: "CF Worker = Edge-Only; RisingWave 接続は K8s Pod / Granian Server のみ"
status: active
doc_type: adr
topic: cf-worker-edge-only-rw-pod-only
authoritative: true
last_verified: 2026-05-14
phase_status: "Phase 1 complete 2026-05-11 (SDK fail-fast + 148 active wrangler bindings removed + 12 infra Workers temp-reverted). 2026-05-14: CF edge BFF inventory confirmed most Workers are SvelteKit thin shims forwarding XRPC/MCP to agentgateway; analytics-dashboard deployed as read-only CF Analytics exception. PDS pod cutover attempted via atproto-canary but rolled back because canary tunnel/origin returned HTTP 522. Phase 2 app actor handler migration remains in-progress. Phase 3 SDK code removal remains blocked on Phase 2 + ADR-2605111300 PDS pod migration."
priority: 9.5
axis: architecture
weight: 0.95
priority_note: "CRITICAL — CF Worker から RisingWave (Hyperdrive) への接続を全面禁止。DB I/O は K8s Pod / Granian / SpiffWorkflow worker のみ"
authoritative_for:
  - cf-worker-rw-connection-prohibition
  - hyperdrive-binding-removal-from-worker
  - kysely-direct-write-prohibition-in-worker
  - rw-server-side-only-access-rule
  - createKyselyDb-deprecation
related:
  - adr-0002-persistence-risingwave-only
  - adr-2604282300
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605081200-spiffworkflow-bpmn-engine-replacement
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
  - adr-2605111300-pds-to-pod-bun-container
supersedes:
  - adr-0081-worker-direct-hyperdrive-persistence
superseded_by: []
amends:
  - adr-2604282300
amended_by: []
---

# Goal

CF Worker から RisingWave (Hyperdrive 経由) への接続を **全面禁止** する。
domain write/read を含む全 DB I/O は K8s Pod 側 (LangGraph Server + Granian / SpiffWorkflow BPMN worker / Python worker pool) に集約する。

ADR-0081 (Worker-direct Hyperdrive Persistence) を **完全に supersede** する。
ADR-2604282300 が暗黙に許容していた T3 Worker の直接 DB write/read 例外も削除する。

# Scope

- 禁止対象: 全 CF Worker から `env.HYPERDRIVE` 経由の PostgreSQL 接続。
- 撤去対象: 全 `wrangler.jsonc` の `"hyperdrive"` binding。
- 廃止対象: `@etzhayyim/magatama-host-sdk` の `createKyselyDb()` / `setKyselyHyperdrive()` の "Worker 内 DB connection 生成" 機能。型エクスポートは残し、関数は throw 化する。
- 移行先: bpmn-dispatcher → LangGraph Server (`/runs`) / SpiffWorkflow BPMN worker / 既存 K8s pod (`zeebe-worker`, `claim-consumer-actor`, 等)。

# Executive Summary

| Concern | Before (ADR-0081) | After (this ADR) |
|---|---|---|
| Domain write | Worker → `createKyselyDb(env.HYPERDRIVE)` → RisingWave (1-RTT) | Worker → XRPC → bpmn-dispatcher → LangGraph/Spiff/pod → RisingWave |
| Domain read | Worker → `createKyselyDb` → RisingWave | Worker → XRPC → dispatcher → pod query → JSON response |
| Wrangler `hyperdrive` binding | 全 148 Worker に存在 | **全削除** |
| `createKyselyDb()` in Worker | 正規 API (91 ファイル使用) | **runtime throw** (`WorkerDBProhibitedError`) |
| 接続元 (RisingWave PG :4566) | CF edge + K8s pod 混在 | **K8s pod のみ** |
| SPoF | Hyperdrive origin pool + per-Worker isolate | K8s pod (replica + HPA + circuit breaker) |
| Audit/Observability | 各 Worker isolate に分散 | dispatcher 集約 (`x-internal-trust` + OCEL emit) |

# Decision

## 1. CF Worker からの RisingWave 接続を全面禁止

CF Worker (T1 / T2 / T3 / infra すべて) は `env.HYPERDRIVE` を **持たない**。
binding 自体を `wrangler.jsonc` から削除する。

```jsonc
// ❌ 禁止 (全 Worker)
"hyperdrive": [
  { "binding": "HYPERDRIVE", "id": "e84c0a2babe44fc7b74818e394b4b896" }
]

// ✅ 正 (DB I/O が必要なら XRPC で server side に投げる)
"services": [
  { "binding": "PDS_SERVICE", "service": "etzhayyim-pds-2603241700" }
  // bpmn-dispatcher / LangGraph endpoint も同様に service binding か fetch
]
```

## 2. SDK 側で fail-fast

`@etzhayyim/magatama-host-sdk/src/kysely.ts`:

```ts
export class WorkerDBProhibitedError extends Error {
  constructor() {
    super(
      "createKyselyDb is prohibited in CF Workers (ADR-2605111200). " +
      "CF Worker は edge-only。DB I/O は K8s pod (LangGraph Server / SpiffWorkflow / Granian) に dispatch すること。" +
      "移行先: bpmn-dispatcher → LangGraph /runs もしくは server XRPC endpoint。"
    );
    this.name = "WorkerDBProhibitedError";
  }
}

export function createKyselyDb(_hyperdrive?: Hyperdrive): never {
  throw new WorkerDBProhibitedError();
}

export function setKyselyHyperdrive(_hyperdrive: Hyperdrive | null | undefined): void {
  // no-op: binding は受け取るが何もしない (Worker 内に singleton は持たない)
}
```

型 (`KyselyDb`, `Hyperdrive`, `HyperdriveDialect`) は再エクスポートを維持する (server side で同じ型を使う場合の互換)。

## 3. Worker → Server への代替パス

CF Worker が DB I/O を必要とする場合は **必ず HTTP / XRPC で server side に dispatch する**:

| 用途 | 代替経路 |
|---|---|
| Domain write (`vertex_<actor>_<kind>`) | XRPC `com.etzhayyim.apps.<actor>.<method>` → bpmn-dispatcher → LangGraph `/runs` or SpiffWorkflow `/v1/instance` → pod → INSERT |
| Domain read | XRPC query method → bpmn-dispatcher → LangGraph node → SELECT → response |
| Social write (`app.bsky.*`) | `sdk.pds.dispatch({type:"app.bsky.feed.post",...})` (PDS pipethrough は維持) |
| Federation read | XRPC through PDS (unchanged) |
| Outbox / failed write archive | server-side 担当 (Worker 側の `archiveToOutbox` 経路は no-op に変更) |

## 4. 例外なし

ADR-2604282300 の "T3 = Worker 許可" 条項のうち、**DB I/O に関する例外は全廃**。
T3 が必要な理由 (CF 固有 binding / WebSocket / SSE / edge latency) は維持するが、
T3 Worker 内で `createKyselyDb()` を呼ぶことは禁止。

`com.etzhayyim.vault.*` (D1 zero-knowledge) と `com.etzhayyim.signal.*` (E2E prekey) は元から PDS pipethrough のため影響なし。

## 5. Phase 化 (soft-prune)

実装は段階的:

| Phase | 内容 | 状態 |
|---|---|---|
| **Phase 1 (本 ADR 同時)** | (a) SDK `createKyselyDb` throw 化、(b) 全 wrangler.jsonc から `hyperdrive` binding 削除、(c) 新 ADR commit | **immediate** |
| **Phase 2** | 91 ファイルの handler 実体を bpmn-dispatcher → LangGraph/Spiff/pod 経由に書き換え。`migrations` テーブルでファイル単位 tracking。 | 別 PR (per-actor) |
| **Phase 3** | `magatama-host-sdk` から `createKyselyDb` 関数本体と Hyperdrive dialect コード自体を削除 (全 callsite が移行済になったら) | 後続 PR |

Phase 1 後、未移行 Worker は handler 内 `createKyselyDb` 呼び出し時に **runtime で throw する**。これは意図的な fail-fast。型/コンパイルは通る (`env.HYPERDRIVE` が undefined になるだけ) ので deploy 自体は通る。

# Rationale

1. **SPoF 削減**: 148 Worker isolate × Hyperdrive origin pool の組み合わせを廃して、K8s pod replica + HPA + ServiceMonitor + circuit breaker の 1 系統に統合。
2. **観測性**: dispatcher で全 mutating request を audit / OCEL emit できる。Worker isolate ごとに散らばっていた write 観測が集約される。
3. **CF Worker 制約からの解放**: 30s CPU / 128MB / 10MB bundle / single-thread はビジネスロジックには厳しい。Pod 側に出せば Python + heavy lib + retry/cursor が自由。
4. **ADR-2604282300 / 2605080600 整合**: 両 ADR が "Edge は薄く、business logic は pod" を既に宣言済み。本 ADR は DB connection の最後の例外を閉じる。
5. **2026-04-19 graph-worker stall incident の再発防止強化**: ADR-0081 は "Worker-direct" で stall を回避したが、Worker isolate からの直接書き込みは観測性が低い。bpmn-dispatcher 経由なら timing/retry が中央で見える。

# Consequences

**Positive**
- CF Worker bundle 縮小 (`kysely` + `pg` package 除去で数 MB 軽量化)
- DB connection 数の予測可能性向上 (pod replica count = 上限)
- ADR-2604282300 / 2605080600 と完全整合 (T3 carve-out 削除)
- 新 actor 追加時の選択肢が 1 つに収束: dispatcher 経由

**Negative**
- Phase 2 で 91 ファイルの handler refactor が必要 (per-actor PR)
- Worker → pod 1 hop 追加 (典型 +20-50ms in-region, dispatcher 内 cluster)
- Phase 1 直後は未移行 Worker が runtime throw する → 該当 actor の domain write が一時的に止まる

**移行優先順位 (Phase 2)**: traffic の多い順 = `60-apps/etzhayyim-project-{yoro,mangaka,maps,news,yatabase}/appview/*` から。

# Migration Plan (Phase 2 per-actor checklist)

Per `60-apps/etzhayyim-project-<actor>/appview/.../src/app.ts`:

1. Identify `createKyselyDb(env.HYPERDRIVE)` callsites → list domain collections involved
2. For each domain write:
   - Add `com.etzhayyim.apps.<actor>.<method>` lexicon (if not exists) として bpmn-dispatcher route 化
   - Worker handler は `parseLexiconInput()` + `await fetch(BPMN_DISPATCHER_URL, ...)` または `sdk.pds.xrpc(...)` 経由に書き換え
   - server-side (LangGraph node / Spiff task / pyzeebe primitive) で INSERT を実装
3. For each domain read:
   - 同様に server-side endpoint に問い合わせる query method 化
4. `wrangler.jsonc` の `hyperdrive` binding は **Phase 1 で既に削除されている**ので追加作業なし
5. Test: `pnpm exec vitest run` + smoke (XRPC live call) + `etzhayyim deploy`

`deps.toml [[migrations]]` の `worker-direct-hyperdrive-per-actor` を `reverse-direction` でリネームし、status を `in-progress` に戻す。

# References

- ADR-0081 (Worker-direct Hyperdrive Persistence) — **superseded by this ADR**
- ADR-2604282300 (CF Worker Edge Layer) — **amended**: T3 DB write carve-out removed
- ADR-2605080600 (LangGraph Server + Granian L3 Runtime) — migration target
- ADR-2605081200 (SpiffWorkflow BPMN engine replacement) — BPMN-native migration target
- ADR-0002 (RisingWave single persistence) — unchanged
- `20-actors/magatama/sdk/magatama-host-sdk/src/kysely.ts` — throw 化
- `50-infra/k8s/{shigotoba-jobs-actor,claim-consumer-actor,medical-coverage-ingester,intel-dependency-worker,lg-yatabase}/` — 既存 pod-side RW connection precedent

# Operational Prerequisites (2026-05-11 / yatabase BMC cut-over learnings)

Phase 2 で migrate する actor 全部 に共通する infra gating 条件。yatabase BMC cycle (P55, `60-apps/etzhayyim-project-yatabase/deps.toml [product.lean_cycles.cycle_20260511_08]`) でハマった事象を将来の cut-over に伝えるための注記。

1. **NATS JetStream streams MUST exist before RisingWave compute restart.**
   RW catalog に `CREATE TABLE ... WITH (connector='nats', stream='X', ...)` が登録されていても、NATS server に該当 stream が存在しないと RW source reader が 1s retry を回し続け、foreground DDL queue 全体が permanent block する (Hummock barrier coordination が `stream NOT_FOUND` 例外で advance しない)。修復: nats-box pod 経由で空 stream を作成 (`nats stream add NAME --subjects 'subj.>' --storage memory|file ...`)。`max_file_store=0` の cluster は `--storage memory` 必須。

2. **runpod / Virtual Kubelet node が join すると DaemonSet 伝播が壊れる.**
   VK は `NoSchedule` taint を持っていても DaemonSet pods が Pending stuck し、`calico-node` / `kube-proxy` / `csi-vultr-node` / `konnectivity-agent` の Desired/Ready が乖離する。既存 long-lived pod (cloudflared など) が新規 ClusterIP Service / podIP に到達できない (`dial tcp ... i/o timeout`)。修復: `kubectl delete node <vk>` + DaemonSet pods 強制削除。Virtual Kubelet を本格運用する場合は DaemonSet 側に `nodeAffinity` で VK を exclude するパッチが必要。

3. **compactor crashloop は schema apply の隠れた gating.**
   Level 0 SST 数が 100+ / 数 GB に達すると compactor が OOM-restart を繰り返す。外部からは "DDL queue empty + SlowDown 無し + actors all RUNNING" に見えるが新規 CREATE TABLE が **無音で hang** する。`SHOW JOBS` の progress が 0% のまま no-error。修復: compactor の memory limit 拡張 + L0 → L1 compaction 完了待ち。`kubectl -n risingwave logs <meta-pod> | grep "Level 0 has"` で監視。

4. **`asyncpg` から RW へ繋ぐ pool は `connection_class` で UNLISTEN を no-op に上書き必須.**
   asyncpg の `Connection._reset()` が pool release 毎に `UNLISTEN *;` を発行する。RW は LISTEN/UNLISTEN 未対応で `sql parser error: expected statement, found: UNLISTEN` を返し connection が壊れる。実装例: `60-apps/etzhayyim-project-yatabase/lg/lg_yatabase/bmc/db.py` の `_RwConnection(asyncpg.Connection)` で `async def reset(self, *, timeout=None) -> None: return None` を override。

5. **Dockerfile が uvicorn を CMD で呼ぶ場合、pyproject.toml に `uvicorn[standard]` + `fastapi` を declarative に追加.**
   transitive dep に依存すると image build は通るが起動時に `executable not found in $PATH` で crashloop する (langgraph はランタイム dep として uvicorn を強制しない)。

6. **AT Lexicon の index 定義に `column DESC` は使わない.**
   RisingWave は ASC index しかサポートせず、`CREATE INDEX ... ON tbl (col DESC)` は accepted されるが FOREGROUND DDL のまま無限 hang する。降順 scan が必要な場合は plain ASC index にし、planner の backward scan に任せる。MV `ORDER BY ... DESC` (DISTINCT ON の latest 抽出など) は OK — index definition との切り分けに注意。

7. **B2 SlowDown 503 は RW cold-start cache refill storm で trigger.**
   `[storage.cache_refill] data_refill_levels=0-6` 設定 (`50-infra/vultr/risingwave/helm/values.yaml`) で defense-in-depth。bulk ingest 中は `SET dml_rate_limit` 必須。詳細: `50-infra/vultr/risingwave/deps.toml [risingwave_vultr.incident_2026_04_25]`。

8. **dispatcher Cloudflare 502 は app 変更前に tunnel pod の node readiness を見る.**
   2026-05-14 に `dispatcher.etzhayyim.com` が Cloudflare 502 を返したが、nginx ingress / Vultr LB 直叩き
   (`--resolve dispatcher.etzhayyim.com:443:108.61.207.153`) は `HTTP/2 200 {"status":"ok"}` だった。
   原因は `cloudflared-bpmn-dispatcher` が `NotReady` の `risingwave-pool-58gb-e693733cc5dd`
   node 上に残り、origin lookup が `lookup bpmn-dispatcher.mitama-udf.svc.cluster.local: i/o timeout`
   になっていたこと。修復は app / Worker 変更ではなく、cloudflared Deployment を
   `osm-ingest-pool` へ nodeSelector で固定し、`workload=osm-ingest:NoSchedule` taint を toleration
   すること。復旧後は `https://dispatcher.etzhayyim.com/health` が 200、trust header なしの mailer XRPC は
   502 ではなく期待どおり 401 になった。永続化: `50-infra/vultr/cloudflared/bpmn-dispatcher-tunnel.yaml`。

# Operational Update (2026-05-14)

`analytics.etzhayyim.com` was serving the generic SvelteKit placeholder even though
the repository already contained a real analytics dashboard implementation. The
deployed Worker entrypoint is SvelteKit (`svelte/.svelte-kit/cloudflare/_worker.js`),
so the placeholder `+page.svelte` was the effective production surface. The
dashboard was moved into the SvelteKit route and deployed as
`etzhayyim-analytics-dashboard` version
`0fa2d98d-22b6-4572-82e0-debd72be2336`.

This remains ADR-compliant as a **read-only edge observability exception**:

- no RisingWave / Hyperdrive binding;
- no business-domain write path;
- `/api/data` reads Cloudflare GraphQL with `CF_API_TOKEN` / `CF_ZONE_ID`;
- operational XRPC/MCP defaults point to `mcp.etzhayyim.com`, not `atproto.etzhayyim.com`.

The same session inventory confirmed the intended Worker shape:

- the normal deployed entrypoint is SvelteKit edge BFF;
- `/xrpc/[...path]` shims forward JSON-RPC MCP calls to
  `AGENTGATEWAY_MCP_ROUTER_URL` or `MCP_ROUTER_URL`;
- canonical public MCP routing is
  `https://mcp.etzhayyim.com/xrpc/com.etzhayyim.mcp.message`;
- legacy non-Svelte / Worker-local logic remains a migration target and must be
  treated as exception debt, not a new precedent.

PDS is the remaining production-critical exception. A thin `atproto.etzhayyim.com`
proxy to `atproto-canary.etzhayyim.com` was built and deploy-tested, but the canary
origin returned HTTP 522. Production was immediately rolled back to the CF
Worker PDS version that serves:

- `GET https://atproto.etzhayyim.com/_app/meta` -> 200;
- `GET https://atproto.etzhayyim.com/xrpc/com.atproto.server.describeServer` -> 200.

Therefore this ADR is still authoritative, but PDS enforcement is gated on
ADR-2605111300 P1/P2: the k8s pod and Cloudflare Tunnel for
`atproto-canary.etzhayyim.com` must be healthy before `atproto.etzhayyim.com` can become a
thin edge proxy or be removed from Cloudflare Workers.
