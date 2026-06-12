---
id: adr-2605080001-yatabase-yata-retail-cloud
renumbered_from: "2605080000"
title: etzhayyim Retail Cloud — yatabase + obj + yata + billing v2 (codename io-yatabase D12+)
status: proposed
doc_type: adr
topic: retail-cloud-provider
authoritative: true
last_verified: 2026-05-09
authoritative_for:
  - retail-cloud-billing-v2-pricing
  - yatabase-graph-database-product
  - obj-storage-product
  - yata-rust-crate-sdk
  - retail-cloud-tenant-isolation
  - io-yatabase-supabase-neo4j-baas-surface
related:
  - adr-0002-graph-storage-kotoba
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-0044-kotoba-udf-language-strategy
  - adr-0048-kotoba-vultr-b2-primary
  - adr-0056-bpmn-as-actor
  - adr-0087-kotodama-mcp-tool-facade
  - adr-0095-simplified-3layer-identity-rw-vault
  - adr-2604282300
  - adr-2605010000
  - adr-2605091400-mcp-as-cell-membrane-lexicon-xrpc-demotion
supersedes: []
superseded_by: []
---

# Goal

etzhayyim platform の余剰能力 (B2 Bandwidth Alliance の実質ゼロ egress、Kotoba/Datomic
shared cluster の compute、self-host RunPod LLM) を **retail cloud product** と
して外部顧客に再販する。3 つの製品 (yatabase / obj / yata) と 1 つの基盤
(billing v2) を 1 本の ADR で確定する。原価優位 (B2 storage = $0.006/GB-month、
egress = $0、LLM = self-host) を **公開価格には反映させず、sales 値引き原資と
して温存** することで、平均粗利 86-94% と最大 50% の値下げ余力を同時確保する。

# Scope

In:
- 課金軸 5 種 (storage / egress / LLM / GPU / API request) の単価 list 価格
- Plan 階層 6 種 (Free / Starter / Developer / Team / Business / Enterprise)
- Sales discount 原資階層 (年契約 / multi-year / 学生 / startup / channel partner / volume / migration / floor)
- 製品 1: **yatabase.etzhayyim.com** — Kotoba/Datomic-backed graph database (PG / SPARQL / Cypher / MCP)
- 製品 2: **obj.etzhayyim.com** — B2-backed S3-compatible object storage with auto-tiering / LLM tagging / vector embedding / Vault E2E
- 製品 3: **yata** Rust crate — canonical client SDK for yatabase
- 課金 metering schema (`vertex_billing_event` + 5 streaming MV)
- Tenant isolation 規約 (per-org RW database / B2 bucket / role / API key prefix)
- 段階導入 roadmap P1-P10 (M1-M9+)

Out:
- 既存 96 mitama actor / 内部利用 (`*.etzhayyim.com` で公開済の domain) の課金化 — internal-only として継続無料
- etzhayyim OLTP (Neon-style separated compute/storage Postgres) — 当面開発しない (RW を graph として売る方針に集約)
- LLM Gateway product (`llm.etzhayyim.com` の retail 化) — 別 ADR とする (RunPod cost / inference SLA は独立決定軸)
- 暗号資産 / token-gated 決済 — 当面 fiat (JPY / USD) のみ
- 多 region 展開 — LAX 1 拠点で start、加入数 trigger (P9) に従う

# Executive Summary

| 軸 | 選択 |
|---|---|
| 製品ライン | **yatabase / obj / yata の 3 本立て**、共通基盤は billing v2 |
| 表面価格 (list) | OpenAI / Vercel / Neo4j AuraDB と同等水準。粗利 90%+ で構築 |
| 原価 | B2 $0.006/GB-month + Vultr VKE shared $241/月 + RunPod self-host LLM |
| 値引き原資 | list 価格に対し **40% まで sales 自動承認、50% まで CFO 承認** |
| 通貨 | JPY base (etzhayyim 運営)、enterprise のみ USD/JPY 選択可 |
| 決済 | Stripe Japan + 適格請求書 (T9007028460042) |
| Tenant 分離 | RW database 単位 (`yata_<sha256(did)[:16]>`) + B2 bucket 単位 (`obj-<...>`) |
| Identity | API key 製品別 prefix `sk_live_yata_*` / `sk_live_obj_*` / 汎用 `sk_live_*` |
| Brand | **yatabase = 八咫 + database**, **yata crate = top-level Rust SDK** |
| Roadmap | P1 billing → P3 obj MVP → P4 yatabase MVP → P5 obj 強化 → P6 Cypher → P7 Stripe → P9 enterprise |

# Decision

## D1. 課金軸単価 (list 価格、JPY)

| 軸 | 単位 | 原価 | **list 価格** | 粗利率 | floor (sales -50%) |
|---|---|---|---|---|---|
| Storage | GB-month | ¥0.9 | **¥10** | 91% | ¥5 |
| Egress | GB | ¥0 | **¥15** (BWA 経由 ¥0) | 100% | ¥5 |
| LLM 入力 | 1K tokens | ¥0.015 | **¥0.50** | 97% | ¥0.20 |
| LLM 出力 | 1K tokens | ¥0.045 | **¥1.50** | 97% | ¥0.50 |
| GPU 6000 Ada | hour | ¥75 | **¥300** | 75% | ¥150 |
| GPU H100 80GB | hour | ¥450 | **¥1,500** | 70% | ¥800 |
| API request | 10K req | ¥0.045 | **¥2.0** | 98% | ¥1.0 |
| MCP tool call | 100 calls | ¥0.10 | **¥3.0** | 97% | ¥1.5 |
| DID mint | 個 | ¥30 | **¥300** | 90% | ¥150 |

## D2. Plan 階層 (共通)

| Plan | 月額 list | 主対象 |
|---|---|---|
| Free | ¥0 | 獲得、開発検証 |
| Starter | ¥1,980 | クレカ登録 friction 最小化 |
| Developer | ¥4,980 | 個人開発者、prosumer |
| Team | ¥19,800/seat (min 3) | SMB 開発チーム |
| Business | ¥98,000 | 中堅企業、専用サブドメイン |
| Enterprise | min ¥1,000,000 | 大企業、専用 cluster + DPA + SLA |

各 Plan の含有量は製品 (D3 / D4) ごとに別表で定める。

## D3. 製品 1: yatabase.etzhayyim.com (graph database)

**Position**: "Real-time graph database with streaming projections, OWL reasoning,
and AT Protocol federation. PG-compatible. Drop-in for BI tools, ORMs (read-only),
embedding stores."

**Architecture**:

```
Customer (psql / Cypher / SPARQL / XRPC / MCP / Bolt)
   ↓
yatabase.etzhayyim.com (CF Worker, edge)
   ├─ Auth: sk_live_yata_* → org_did
   ├─ Per-tenant DB routing: yata_<sha256(did)[:16]>
   ├─ Query language adapter
   │    ├─ SQL/PGQ → :4566 PG protocol pass-through
   │    ├─ SPARQL → translate via v_rdf_triple VIEW (既存 ADR-0044 / 2605010000 owl reasoner)
   │    ├─ Cypher → translate to SQL/PGQ (Phase 2, ~3K LoC parser + AST)
   │    └─ Bolt :7687 → Phase 3 (Neo4j driver 互換)
   ├─ Metering → vertex_billing_event
   └─ Origin: Vultr VKE LAX RW cluster (vhf-8c-32gb, $241/月 baseline)
        ├─ CREATE DATABASE yata_<hash> per org
        ├─ CREATE ROLE per org with USAGE on own DB only
        ├─ Quota enforcement (statement_timeout / dml_rate_limit / connection cap)
        └─ Reasoning: OWL EL/RL UDF + DL on-demand BPMN (既存 2605011200)
```

**Plan limits**:

| Plan | Nodes | Edges | State (GB) | MVs | Reasoning | Query CU/月 | 月額 |
|---|---|---|---|---|---|---|---|
| Free | 100K | 500K | 1 | 5 | EL only | 5 CU-h | ¥0 |
| Starter | 1M | 5M | 10 | 20 | EL + RL | 50 CU-h | ¥1,980 |
| Pro | 10M | 50M | 100 | 100 | EL + RL + QL | 500 CU-h | ¥4,980 |
| Business | 100M | 1B | 500 | 無制限 | + DL (HermiT, weekly) | 5,000 CU-h | ¥98,000 |
| Enterprise | 専用 RW cluster | — | — | — | + custom SHACL | — | min ¥500K |

**Overage**:
- Node 追加: ¥1,000 per million nodes-month
- Edge 追加: ¥500 per million edges-month
- State 超過: ¥10/GB-month
- Query compute: ¥300/CU-hour
- Reasoning DL run: ¥500/run
- Egress: ¥15/GB (BWA ¥0)

**正直な制約開示** (ADR-0036 / RW 制約):
- `ON CONFLICT` 不可 → PK implicit upsert を提示
- Write transaction 不可 → 単一 statement で完結
- `UNIQUE` / `FOREIGN KEY` 不可 → app-layer 検証
- Strict serializability 不可 → eventual consistency
- 「**Not for OLTP. For real-time analytics, knowledge graph, embeddings.**」を marketing copy / docs に明示

**MVP query language**: SQL/PGQ + SPARQL + XRPC + MCP (Cypher は Phase 2)。

## D4. 製品 2: obj.etzhayyim.com (object storage)

**Position**: "S3-compatible object storage with free egress (Bandwidth Alliance),
auto-tiering, built-in LLM tagging, vector embedding, and Vault zero-knowledge encryption."

**Architecture**:

```
Customer (boto3 / aws-sdk-js / mc / curl)
   ↓ S3 API (HTTPS, AWS SigV4 or sk_live_obj_*)
obj.etzhayyim.com (CF Worker, edge)
   ├─ Auth: SigV4 verify or sk_live_obj_* → org_did
   ├─ Rate limit (token bucket per org)
   ├─ Metering → vertex_billing_event
   ├─ Hot cache (R2 edge, 24h TTL, LRU)
   └─ Origin selector (per-bucket policy)
        ├─ Tier 1 HOT  → Vultr Object Storage (LAX, ~10ms)
        ├─ Tier 2 WARM → B2 Standard (BWA free egress)
        └─ Tier 3 COLD → B2 Archive (lifecycle move after 30d idle)

Side rails:
   ├─ Embedding worker: PUT → generate vec → vertex_obj_embedding
   ├─ Auto-tag worker: LLM classify image/doc → vertex_obj_tag
   └─ Federation: bucket DID = did:web:obj.etzhayyim.com:b:<bucket-id>
```

**Plan limits**:

| Plan | Storage 含 | Egress 含 | Class A | Class B | 月額 |
|---|---|---|---|---|---|
| Free | 5 GB | 50 GB | 100K | 1M | ¥0 |
| Starter | 50 GB | 500 GB | 1M | 10M | ¥1,980 |
| Pro | 500 GB | 5 TB | 10M | 100M | ¥4,980 |
| Business | 5 TB | 50 TB | 100M | 1B | ¥98,000 |
| Enterprise | 専用 pool | BWA 無制限 | — | — | min ¥1M |

**Overage**:
- Storage 追加: ¥10/GB-month
- Egress 追加: ¥15/GB (BWA 経由 ¥0)
- Class A: ¥10/1M req / Class B: ¥1/1M req

**API surface**:
- S3-compat REST: `https://<bucket>.obj.etzhayyim.com/<key>` (subdomain) + `https://obj.etzhayyim.com/<bucket>/<key>` (path)
- Native XRPC: `com.etzhayyim.apps.obj.{createBucket, putObject, getObject, listObjects, presignUrl, searchByEmbedding, listByTag, shareBucket, ...}`
- AWS SigV4 mapping: access key id = `etzhayyim_<key_id>`, secret = `sk_obj_<...>`

## D5. 製品 3: yata Rust crate (canonical SDK)

**Position**: "Rust-first, type-safe client for yatabase. proc-macro schema +
streaming MV subscription + MCP server export."

**Crate 構成** (`50-clients/rust/yata/`):

```
yata/
├── Cargo.toml                workspace
├── crates/
│   ├── yata/                 facade re-export (top-level user API)
│   ├── yata-core/            connection / auth / wire (tokio-postgres ベース)
│   ├── yata-schema/          #[derive(Vertex)] / #[derive(Edge)] runtime
│   ├── yata-derive/          proc-macros
│   ├── yata-query/           type-safe query builder (SQL/PGQ AST)
│   ├── yata-sparql/          SPARQL HTTP client + escape hatch
│   ├── yata-stream/          MV subscription (CDC over WS)
│   ├── yata-mcp/             MCP server export
│   └── yata-cli/             `yata` binary
└── examples/
    ├── 01-quickstart.rs
    ├── 02-streaming-mv.rs
    ├── 03-vector-graph-hybrid.rs
    ├── 04-owl-reasoning.rs
    └── 05-mcp-server.rs
```

**Public API skeleton**:

```rust
use yata::prelude::*;

#[derive(Vertex)]
#[yata(label = "person")]
struct Person {
    #[yata(pk)] id: String,
    name: String,
    age: i32,
    #[yata(vector(dim = 768))] embedding: Vec<f32>,
}

#[derive(Edge)]
#[yata(type = "knows", from = Person, to = Person)]
struct Knows { #[yata(pk)] id: String, since: DateTime<Utc>, weight: f32 }

let y = Yata::connect("yatabase://sk_live_yata_xxx@yatabase.etzhayyim.com/my-db").await?;
y.migrate::<(Person, Knows)>().await?;
y.insert(Person { /* ... */ }).await?;
let friends: Vec<Person> = y.from::<Person>().eq("id", "alice")
    .out::<Knows>().to::<Person>().limit(10).fetch().await?;
let rows = y.sparql("SELECT ?p WHERE { ?p :knows :alice }").await?;
y.reason(OwlProfile::Rl).await?;
```

**Cargo features**:
- `default = ["query", "sparql", "tokio-rt"]`
- `cypher` (Phase 2), `bolt` (Phase 3), `stream`, `mcp`, `derive`, `cli`
- `async-std-rt` (alternative to tokio)

**MSRV**: Rust 1.78 (stable, 2024 edition)
**License**: Apache-2.0 OR MIT (Rust 慣例 dual-license)
**Publish**: crates.io (`yata = "0.1"`) + monorepo subtree push to `github.com/etzhayyim/yata`

**他言語 SDK 派生** (Phase 2+):
- `yata-py` (PyO3 bindings)
- `yata-ts` (TypeScript / Deno, native pg + fetch)
- `yata-go` (jackc/pgx ベース)

## D6. Sales 値引き原資階層

```
List price (公開価格)              ¥4,980 (例: Developer)
  ├─ Annual prepay        -15%     ¥4,233
  ├─ Multi-year (3y)      -10%     ¥3,810
  ├─ 学生 / OSS            -50%     ¥2,490
  ├─ Startup credit (1年)  -100%   ¥0      (acquisition)
  ├─ Channel partner       -30%    ¥3,486  (reseller margin 30%)
  ├─ Volume (100+ seat)    -25%    ¥3,735
  ├─ Migration credit      -50%    ¥2,490  (S3 / Neo4j / OpenAI からの乗換)
  └─ Floor                          ¥1,500 (粗利 80% 死守)
```

**Sales 自動承認**: list の **40% まで** (CRM 連携 OK)。
**CFO 承認**: 40-50%。
**CEO 承認**: 50% 超 (敗戦処理 / 戦略 deal のみ)。

## D7. Billing 軸 metering schema (Kotoba/Datomic)

```sql
-- usage event (per request, per token, per byte)
vertex_billing_event:
  org_did, actor_did, ts_ms,
  metric (storage_gb_hour | egress_gb | llm_input_tokens | llm_output_tokens
          | gpu_hour | api_request | mcp_call | did_mint
          | yata_node_hour | yata_edge_hour | yata_query_cu_ms
          | yata_reasoning_run | obj_class_a | obj_class_b),
  qty, unit_cost_jpy_micro, list_price_jpy_micro,
  applied_discount_pct, billed_amount_jpy_micro,
  product (yata | obj | gateway | platform),
  ref_resource_did   -- bucket DID / database DID / actor DID

-- streaming MV
mv_billing_daily_org             -- 日次 roll-up
mv_billing_monthly_org           -- 月次 invoice draft
mv_billing_overage_alert         -- tier quota 80/100/150% 超過
mv_billing_margin_actual         -- 実粗利率モニタ (sales 値引き後)
mv_billing_quota_breach          -- hard cap 抵触 org
```

`applied_discount_pct` は per-org に持ち、CFO dashboard で「平均値引き率」「margin
floor 抵触 org 数」を監視する。

## D8. Tenant isolation 規約

| 製品 | 隔離単位 | 命名 | 権限境界 |
|---|---|---|---|
| yatabase | RW database | `yata_<sha256(did)[:16]>` | per-org PG ROLE、`REVOKE ALL ON DATABASE` 他 DB |
| obj | B2 bucket | `obj-<did_hash>-<bucket_name>` | sk_live_obj_* + IAM-style ACL |
| LLM (内部使用) | RunPod pod | shared | rate limit by org |
| Billing | RW shared | `billing` schema (etzhayyim internal) | etzhayyim 管理者のみ |

**禁則**:
- 顧客 DB から etzhayyim 内部 DB (`postgres` / `dev` / 96 mitama actor data) への参照不可
- 顧客 bucket から他テナント bucket への list / get 不可
- 顧客 sk_live_yata_* で billing / authz / authn API 呼出し不可

## D9. Brand / 命名

- **yatabase.etzhayyim.com** = product host (graph DB **+** integrated S3-compatible object storage, per D10)
- **yata** = top-level Rust crate name (crates.io)
- **pay.etzhayyim.com** = billing / invoice / sales console
- **etzhayyim Cloud** = umbrella retail product line name

Marketing tagline 候補:
- "Yatabase — see every relation. Live."
- "八咫の眼で、すべての関係を、いま見る"
- "etzhayyim Cloud — graph + storage + LLM, one bill, ten times cheaper egress"

## D10. Storage は yatabase に統合 (Supabase 型) — supersedes D4 (2026-05-08)

**転換**: `obj.etzhayyim.com` を独立製品として持たず、object storage を **yatabase の一級機能** として
統合する (Supabase の Postgres + Storage 統合パターン)。

理由:
- 顧客 mental model が単純化 (1 brand / 1 plan / 1 bill / 1 MCP / 1 API key prefix)
- graph と blob の **境界をまたぐ JOIN** が native に書ける (例: ある entity の blob 履歴を 1 SQL で取れる)
- streaming MV が **blob INSERT を起点に embedding / tag / lifecycle 自動化**できる
- billing / quota / metering が 1 つの軸 (storage_gb_hour + egress_gb) に統合される
- Supabase が同パターンで PMF を取った実績 (graph + storage 分離より retention 高い)

### 構造

```
Customer
  ↓ psql / SPARQL / S3 SigV4 / Supabase-shape REST / XRPC / MCP
yatabase.etzhayyim.com (CF Worker, edge)
  ├─ /pg                          → :5432 (RW PG protocol pass-through)
  ├─ /sparql                      → SPARQL translator
  ├─ /storage/v1/object/{b}/{k}   → Supabase-compat REST
  ├─ /s3/{b}/{k}                  → AWS SigV4 (boto3 / mc 互換)
  ├─ /xrpc/com.etzhayyim.apps.yata.*    → unified XRPC
  └─ /mcp                         → MCP Streamable HTTP
       ↓
   Per-tenant RW database `yata_<sha256(did)[:16]>`
   ├─ vertex_*                     顧客自由スキーマ (graph)
   ├─ vertex_yata_bucket           bucket メタ (org / region / encryption / tier_policy / versioning)
   ├─ vertex_yata_blob             blob メタ (size / etag / cid / storage_path / tier)
   ├─ vertex_yata_blob_version     versioning (object_id / version_id / is_delete_marker)
   ├─ vertex_yata_blob_acl         per-DID grant (read/write/admin)
   ├─ vertex_yata_blob_embedding   pgvector hybrid (auto-generated on PUT)
   ├─ vertex_yata_blob_tag         LLM auto-tag (image/doc classification)
   ├─ vertex_yata_multipart        in-progress multipart upload state
   └─ edge_yata_blob_referenced_by 顧客 vertex ↔ blob の任意リンク
       ↓
   Blob bytes
   ├─ Tier 1 HOT  → Vultr Object Storage (LAX, ~10ms)
   ├─ Tier 2 WARM → B2 Standard (BWA 経由 egress ¥0)
   └─ Tier 3 COLD → B2 Archive (lifecycle で 30d idle 後 auto-migrate)

Side rails (BPMN-as-actor, R/PT* timer-start):
   ├─ yata.storage.metering.rollup   R/PT1H per-org bytes_stored × tier 集計 → vertex_billing_event
   ├─ yata.storage.tier.migrate      cron 1d  30d idle blob を WARM→COLD へ
   └─ yata.storage.embedding.queue   R/PT5M  未 embedding blob を batch 処理
```

### Plan limits 統合 (D2 を amend)

各 yatabase plan は **graph + storage 両方の含有量** を持つ:

| Plan | Nodes | Edges | DB State (GB) | MVs | **Storage (GB)** | **Egress (GB)** | Class A req | Class B req | 月額 list |
|---|---|---|---|---|---|---|---|---|---|
| Free | 100K | 500K | 1 | 5 | **5** | **50** | 100K | 1M | ¥0 |
| Starter | 1M | 5M | 10 | 20 | **50** | **500** | 1M | 10M | ¥1,980 |
| Pro | 10M | 50M | 100 | 100 | **500** | **5,000** | 10M | 100M | ¥4,980 |
| Business | 100M | 1B | 500 | 無制限 | **5,000** | **50,000** | 100M | 1B | ¥98,000 |
| Enterprise | 専用 | — | — | — | 専用 | BWA ∞ | — | — | min ¥1M |

Overage (D1 と整合):
- Storage 追加: ¥10/GB-month
- Egress 追加: ¥15/GB (BWA 経由 ¥0)
- Class A: ¥10/1M req (PUT/COPY/POST/LIST)
- Class B: ¥1/1M req (GET/HEAD)
- (graph 軸 node/edge/state/MV/reasoning は D3 のまま)

### API key prefix の縮約

D9 の `sk_live_obj_*` は **不採用 (P3 着手時に削除)**。`sk_live_yata_*` 1 本に統合。
P2 で実装した `enforceApiKeyProductScope` の `'obj'` 分岐は dead code として残るが、
発行はされない。`sk_live_yata_*` で `/storage/v1/*` も `/xrpc/com.etzhayyim.apps.yata.*` も全て通る。

### S3 互換 wire 仕様

- `PUT /s3/{bucket}/{key}` — AWS SigV4 (`X-Amz-*` headers)、`access_key=etzhayyim_<keyId>`,
  `secret=sk_yata_<...>` を内部で `sk_live_yata_*` API key にマップ
- `GET / HEAD / DELETE / LIST` も同様
- multipart upload (`POST ?uploads`, `PUT ?partNumber=N&uploadId=...`,
  `POST ?uploadId=...`, `DELETE ?uploadId=...`)
- presigned URL (`GET /s3/{bucket}/{key}?X-Amz-Signature=...`)

### Supabase-shape REST 並走

- `POST /storage/v1/object/{bucket}/{key}` — 単純 multipart/form-data upload
- `GET  /storage/v1/object/public/{bucket}/{key}` — public access (ACL=public)
- `GET  /storage/v1/object/sign/{bucket}/{key}?expiresIn=3600` — presigned
- `GET  /storage/v1/bucket` — list buckets
- `GET  /storage/v1/object/list/{bucket}?prefix=...&limit=...&offset=...`

### Edge-side caching

CF Worker R2 cache layer (24h TTL, LRU):
- GET hit on cached key → 0 origin RT
- PUT / DELETE → invalidate cache key
- public ACL blob は CF Cache API でも乗せ替え可能 (Phase 2)

### Streaming MV reactive 化

`vertex_yata_blob` への INSERT を契機に:
- `mv_yata_storage_by_org` が org × tier の bytes を更新 → billing rollup の入力
- `vertex_yata_blob_embedding` への upstream として **R/PT5M BPMN** が batch で処理 (queue scan)
- `vertex_yata_blob_tag` 同様

これにより graph 上の任意の vertex が blob を referenced_by 関係で持てば、blob の
ライフサイクル / 検索 / RAG が **graph query + vector search 1 本で完結**する。

### 既存 P1 / P2 への影響

- P1 の `vertex_billing_event` metric set に `obj_class_a` / `obj_class_b` が含まれて
  いるが、そのまま残す (collisionなし、yatabase storage の class A/B として使う)
- P2 の `sk_live_obj_*` infrastructure は dead code として残す (削除コストが小さい
  上、将来 obj 単独製品を別 plan で出す可能性に備える)
- D5 (yata Rust crate) には `Yata::storage` namespace を追加 (P5 で具体化):
  ```rust
  yata.storage.bucket("my-bucket").put("path/to.png", bytes).await?;
  let blob = yata.storage.bucket("my-bucket").get("path/to.png").await?;
  ```

### Migration plan

- Phase 3 (this commit): yatabase 統合 storage で MVP 出荷。`obj.etzhayyim.com` host は
  プロビジョンしない
- Phase 9+: もし enterprise 顧客が「pure object storage 製品」を要求した場合のみ、
  `obj.etzhayyim.com` を別 plan で復活。yatabase の storage namespace は同 schema を共有

## D11. Future Work — Storage operator-side hardening (planned)

P3 MVP 出荷後の強化項目 (別 ADR / migration entry で順次):

1. **Vault E2E** option per bucket (`encryption='vault-e2e'`) — `vault.etzhayyim.com` の
   member device key で client-side encrypt、yatabase 側は ciphertext のみ保管
2. **CDN edge cache** layer for public buckets (CF Cache API + custom origin)
3. **Lifecycle automation** — versioning / 自動 tier migration / TTL purge
4. **WORM mode** — compliance 用途、retention period 後まで delete 不可
5. **Cross-region replication** — Phase 9+ で多 region 展開時、blob を NRT/AMS にも複製

## D12. io-yatabase — Supabase + Neo4j BaaS surface expansion (codename, 2026-05-09)

**転換**: yatabase を「graph DB + storage を持つ retail cloud product」から
「**Supabase + Neo4j 互換の I/O graphdb BaaS**」へ surface 面で同一視できる水準
まで拡張する。codename を **`io-yatabase`** とする (I/O = Input/Output gateway、
yatabase = 八咫 + database)。

D1-D11 の **billing 軸 / Plan 階層 / tenant 分離 / 価格 / 原価優位 / yata crate
名 / host = `yatabase.etzhayyim.com` / 3-Tier Write / ADR-0036 Hyperdrive 直接書込 /
RW OLTP 制約開示 (ON CONFLICT / tx / UNIQUE 不可) は不変条件として継承**。
この章 (D12-D24) は **surface (wire format / endpoint 形状) を増やすだけで、
backend / billing / tenant 境界 / brand は分離しない**。

### 採用理由

- 既存 ecosystem の client (psql / cypher-shell / supabase-js / boto3 / Neo4j
  driver / postgrest-client / Apollo / Hasura migration / GoTrue) がそのまま動く
  surface compatibility を提供 → migration credit (D6) の正当性を強化
- AI agent / external principal 向けは **MCP (`/mcp`) を sole external surface**
  に固定 (ADR-2605091400 cell-membrane)。Cypher / SPARQL / Bolt / Realtime /
  PostgREST / GraphQL は **既存ツール救済の compatibility envelope** で、内部は
  XRPC + Hyperdrive に正規化される
- "io-yatabase" は work-stream codename。folder = `60-apps/etzhayyim-project-yatabase/`、
  host = `yatabase.etzhayyim.com`、crate = `yata` を rebrand しない (CAC / brand
  分散コスト回避)

### Surface map (io-yatabase 完成形)

| # | Surface | 用途 | Auth | Origin | Phase |
|---|---|---|---|---|---|
| S1 | `/storage/v1/object/{b}/{k}` (Supabase REST) | blob put/get/list/sign | `sk_live_yata_*` / atproto JWT | pyzeebe → B2/Vultr OS/R2 | P3 ✅ |
| S2 | `/s3/{b}/{k}` (AWS SigV4) | boto3 / mc 互換 | SigV4 (`access_key=etzhayyim_<keyId>`) | 同上 | P3.2 |
| S3 | `/sparql` (SPARQL 1.1) | RDF SELECT/CONSTRUCT/ASK | 同 S1 | RW :4566 + `v_rdf_triple` VIEW | P4 ✅ |
| S4 | `/xrpc/com.etzhayyim.apps.yata.*` | native XRPC (cytoplasmic) | 同 S1 | dispatcher → pyzeebe / Hyperdrive | P4 ✅ |
| S5 | `/pg` (PG protocol :5432) | psql / ORM read-only | role-mapped session | Vultr LB → PgBouncer → RW :4566 | P4 |
| S6 | **`/cypher`** (openCypher HTTP) | Neo4j-style graph query | 同 S1 | `kagami-cypher-compiler` → SQL/PGQ → RW | **P3.5 (new)** |
| S7 | **`bolt.yatabase.etzhayyim.com:7687`** (Bolt v4) | Neo4j driver / cypher-shell 互換 | Bolt HELLO + `sk_live_yata_*` | `yata-bolt` pool (Vultr VKE LAX, K8s LB L4) | **P3.6 (new)** |
| S8 | **`/realtime/v1/websocket`** (Phoenix channel wire) | Supabase Realtime 互換 streaming MV CDC | 同 S1 | RW MV change source → WS multiplexer (CF Worker DO) | **P3.7 (new)** |
| S9 | **`/rest/v1/{table}`** (PostgREST 互換) | auto-generated REST CRUD | 同 S1 | Hyperdrive + per-tenant role + SQL builder | **P3.8 (new)** |
| S10 | **`/graphql/v1`** | GraphQL query/mutation/subscription | 同 S1 | `pg_graphql` 風 schema introspection (RW VIEW based) | **P3.8 (new)** |
| S11 | **`/auth/v1/*`** (GoTrue 互換) | sign-up / token / OAuth callback | atproto OAuth canonical | atproto OAuth bridge → `sk_live_yata_*` mint | **P3.6 (new)** |
| S12 | **`/functions/v1/{name}`** | Edge Function invoke | 同 S1 | kotodama Invoke (L3/L7/L8) pass-through | **P3.9 (new)** |
| S13 | **`/mcp`** (Streamable HTTP, JSON-RPC 2.0) | AI agent / external principal sole surface | atproto JWT or `sk_live_yata_*` | MCP facade → tool registry (RW L4) | **P3.5 (new)** |
| S14 | **`studio.yatabase.etzhayyim.com`** | tenant operator UI | atproto OAuth (browser) | Svelte CSR + S1-S13 を fetch | **P3.10 (new)** |
| S15 | `/health`, `/_app/meta` | edge probe | public | CF Worker | P0 ✅ |

### 不変条件 (D12 全 surface 共通)

| Rule | 出典 |
|---|---|
| **MCP `/mcp` のみが外部 AI / 外部 principal 向け sole surface** | ADR-2605091400 |
| Cypher / Bolt / Realtime / REST / GraphQL は internal cytoplasmic XRPC を ecosystem ツール向けに wire 互換包装したもの。新 lexicon は導入しない | ADR-2605091400 + 本 ADR §D4 |
| Domain write は Hyperdrive direct (ADR-0036)。`com.atproto.repo.createRecord` を `com.etzhayyim.apps.yata.*` で使わない | ADR-0036 + 60-apps/etzhayyim-project-yatabase/CLAUDE.md |
| Tenant 境界は `yata_<sha256(did)[:16]>` per-org RW DB + per-org PG ROLE | 本 ADR §D8 |
| RW OLTP 制約 (`ON CONFLICT` 不可、tx 不可、`UNIQUE` 不可、strict serializability 不可) は **全 surface で同様に開示**。PostgREST / GraphQL の wire response にも `Sql-Constraint-Mode: rw-eventual` ヘッダで明示 | 90-docs/260424-bsky-compat-kotoba-split.md |
| Auth は **atproto OAuth が canonical**。GoTrue 互換 shim (S11) は token mint だけ担当、内部 JWT は ES256 atproto session | ADR-2604231821 + 本 ADR §D8 |
| billing は既存 5 軸 (`storage_gb_hour` / `egress_gb` / `api_request` / `yata_query_cu_ms` / `yata_node_hour` / `yata_edge_hour`) に正規化。新 metric は導入しない | 本 ADR §D7 + §D22 |
| Bolt (S7) は **CF Worker の外** (TCP long-lived は Worker 30s/128MB 不可)。Vultr VKE LAX L4 LB に直結 | ADR-2604282300 |

## D13. S6 — `/cypher` openCypher HTTP

**Position**: 「Neo4j AuraDB から **driver 書き換えなしで移行** できる Cypher
HTTP endpoint」。kagami-cypher-compiler (in-tree, `30-graph/kagami-cypher-compiler/`)
が openCypher → SQL/PGQ AST に正規化済みなのを edge から呼ぶ。

### Wire (HTTP/JSON, Neo4j HTTP API 互換 subset)

```
POST /cypher HTTP/1.1
Host: yatabase.etzhayyim.com
Authorization: Bearer sk_live_yata_xxx
Content-Type: application/json

{
  "statements": [
    {
      "statement": "MATCH (p:Person {id:$id})-[:KNOWS*1..2]->(f:Person) RETURN f.name LIMIT 10",
      "parameters": { "id": "alice" },
      "resultDataContents": ["row"]
    }
  ]
}
```

```
HTTP/1.1 200 OK
Content-Type: application/json
Sql-Constraint-Mode: rw-eventual

{
  "results": [
    {
      "columns": ["f.name"],
      "data": [
        { "row": ["bob"], "meta": [null] },
        { "row": ["carol"], "meta": [null] }
      ],
      "stats": { "nodes_created": 0, "relationships_created": 0 }
    }
  ],
  "errors": []
}
```

### Forwarding

```
CF Worker (yatabase.etzhayyim.com) /cypher
  ├─ verify auth → org_did + dbName
  ├─ call kagami-cypher-compiler WASM (vendored to Worker bundle, ~280KB)
  │     openCypher AST → SQL/PGQ AST → RW SQL string
  ├─ pyzeebe primitive `yata.query.run` (mitama-yata-pool)
  │     HYPERDRIVE 接続 → SET statement_timeout = '30s' →
  │     SET dml_rate_limit = ... → execute
  ├─ result → Cypher row shape に再マップ
  └─ meter `yata_query_cu_ms` (executed cost), `api_request` (1)
```

### MVP 制約 (Phase 3.5)

- READ-ONLY 文 (`MATCH` / `RETURN` / `WITH` / `WHERE` / `ORDER BY` / `LIMIT` /
  `SKIP` / `UNION`) のみ
- WRITE (`CREATE` / `MERGE` / `SET` / `DELETE`) は **Phase 7 以降**。理由:
  RW の `ON CONFLICT` 不可制約に Cypher `MERGE` を写す追加 logic が必要
- 関数: `count`、`collect`、`size`、`toString`、`toLower`、`toUpper`、`type`、
  `id`、`labels`、`properties`、`exists`、`coalesce`、`length`、`nodes`、
  `relationships`
- Path pattern: `(a)-[:R]->(b)` / `(a)-[:R*1..3]->(b)` (variable-length up to 5
  hops)、`shortestPath` / `allShortestPaths` は **Phase 7**

### Comparison

| | yatabase `/cypher` | Neo4j AuraDB HTTP API |
|---|---|---|
| MATCH / RETURN | ✓ | ✓ |
| Variable-length path | ✓ (≤5 hops) | ✓ (unbounded) |
| WRITE (CREATE/MERGE) | Phase 7 | ✓ |
| Streaming MV subscribe | ✓ (S8 経由) | ✗ |
| pgvector hybrid (`vector_cosine`) | ✓ (`MATCH (n) WHERE vector_cosine(n.emb, $q) > 0.8`) | ✗ |
| Auth | Bearer / atproto JWT | Basic / Bearer |

## D14. S7 — Bolt v4 (`bolt.yatabase.etzhayyim.com:7687`)

**Position**: 「**cypher-shell / Neo4j Browser / neo4j-driver-{js,python,go,java}
が無改修で動く** binary protocol」。yata Rust crate の `yata-bolt` で server を
書き、Vultr VKE LAX `yata-bolt-pool` Deployment で動かす。

### Topology

```
Customer
  ↓ TCP :7687 (Bolt v4 / v5 wire, BoltSchemeV1 = HELLO/RUN/PULL/COMMIT/...)
DNS: bolt.yatabase.etzhayyim.com → Vultr LB (LAX, L4 TCP)
  ↓ load balance with consistent hashing on (db_name)
yata-bolt-pool (3 replica, 2 vCPU / 4 GB each, ~$30/月/replica)
  ├─ HELLO → verify { auth: { scheme: "bearer", credentials: "sk_live_yata_xxx" }}
  │            → resolve org_did + dbName via PDS service binding
  ├─ RUN(query, params, metadata) → kagami-cypher-compiler (native, not WASM)
  │            → SQL/PGQ → tokio-postgres :4566/yata_<hash>
  ├─ PULL(n)  → stream rows back as Bolt RECORD frames
  ├─ COMMIT/ROLLBACK → degraded (RW では 1 statement 単位、DISCARD のみ honor)
  └─ meter `yata_query_cu_ms` + `api_request` (per RUN)
```

### Wire compatibility

- Bolt **v4.4 / v5.0** (current Neo4j 5 driver default)
- BoltSchemeV1 (`HELLO` / `LOGON` / `LOGOFF` / `GOODBYE` / `RESET` / `RUN` /
  `BEGIN` / `COMMIT` / `ROLLBACK` / `DISCARD` / `PULL` / `ROUTE` / `TELEMETRY`)
- `BEGIN` / `COMMIT` は **degraded behavior** で受理 (single-statement scope に
  限定、複数 RUN は最後の COMMIT で全 RUN 結果を返す)。RW tx 不可制約 (D3) を
  HELLO の `server_meta.advertised_capabilities = ["read_only_tx", "single_stmt_tx"]`
  で client に通知
- `ROUTE` は固定 `routing_table = { servers: [{ addresses: ["bolt.yatabase.etzhayyim.com:7687"], role: "WRITE" }, ...], ttl: 300 }`

### TLS / cert

- `bolt+s://` (TLS 1.3) のみ。plaintext `bolt://` は 426 Upgrade Required で reject
- cert は CF Origin CA (yatabase.etzhayyim.com と同根) → LB SNI で `bolt.yatabase.etzhayyim.com`

### Pool sizing (M3 baseline)

- 3 replica × 2 vCPU = 6 vCPU 同時 RUN ~600 qps
- HELLO/LOGON は per-org PG ROLE に SET ROLE してから RUN execute → 接続再利用
  (PgBouncer transaction mode 経由)

## D15. S8 — `/realtime/v1/websocket` (Supabase Realtime 互換)

**Position**: 「supabase-js `realtime.channel(...)` が無改修で動く WS endpoint。
ただし subscribe 単位は **MV name + filter** に限定 (Supabase の `postgres_changes`
の上位互換、安全)」。

### Wire (Phoenix channel protocol)

```
GET /realtime/v1/websocket?apikey=sk_live_yata_xxx&vsn=2.0.0 HTTP/1.1
Upgrade: websocket
Sec-WebSocket-Protocol: phoenix

→ heartbeat 5s, message frame:
[ join_ref, ref, "realtime:mv_my_followers", "phx_join",
  { "config": { "broadcast": { "self": false }, "presence": { "key": "" },
    "postgres_changes": [
      { "event": "*", "schema": "public", "table": "mv_my_followers",
        "filter": "org_did=eq.did:erc725:..." } ] } } ]
```

### Forwarding model

```
Customer (supabase-js)
  ↓ WS /realtime/v1/websocket
CF Worker → Durable Object `RealtimeMux` (per dbName)
  ├─ phx_join → subscribe to RW MV `mv_<name>` change source
  ├─ DO maintains 1 RW psql conn `LISTEN mv_<name>_change`
  │   (RW notify 機構が無いため: BPMN R/PT1S poller が
  │    `SELECT * FROM mv_<name> WHERE _xmin > $last` で diff 抽出 →
  │    DO に POST /push)
  ├─ DO fan-out 各 subscriber WS に push
  ├─ heartbeat 30s (Worker WS は 100s で切断、reconnect 必要)
  └─ meter `api_request` (per heartbeat = 0.01, per change msg = 1)
```

### MV-based subscription (Supabase 上位互換)

Supabase の `postgres_changes` は table への INSERT/UPDATE/DELETE を WAL
decoder で拾うが、yatabase は **streaming MV** がそもそも change source。
よって subscribe 対象は **table ではなく MV** に限定:

```js
const channel = supabase.channel('my-followers')
  .on('postgres_changes',
    { event: '*', schema: 'public', table: 'mv_my_followers',
      filter: `org_did=eq.${orgDid}` },
    (payload) => { console.log(payload) })
  .subscribe()
```

`table: '<not-an-mv>'` を subscribe しようとすると `phx_error` で
`{ reason: "yatabase: realtime requires an MV target. Define a streaming MV first." }`
を返す。これは **Supabase との非互換** だが、RW の semantics に正直で、客が
postgres ad-hoc table 監視に依存するアンチパターンを誘発しないため意図的に
divergent。

### Plan limits 追加 (D2 / D3 amend)

| Plan | 同時 WS conn | MV subscribe | msg/月 |
|---|---|---|---|
| Free | 50 | 5 | 100K |
| Starter | 500 | 20 | 1M |
| Pro | 5,000 | 100 | 10M |
| Business | 50,000 | 1,000 | 100M |
| Enterprise | 専用 DO pool | 無制限 | — |

Overage: WS msg 超過は `api_request` ¥2/10K に正規化 (新 metric なし)。

## D16. S9 — `/rest/v1/{table}` PostgREST 互換

**Position**: 「postgrest-client / supabase-js `from('table').select()` が無改修
で動く auto-generated REST CRUD」。

### Wire (PostgREST subset)

```
GET /rest/v1/vertex_yata_blob?org_did=eq.did:erc725:...&select=key,size,etag&limit=50&offset=0
  Authorization: Bearer sk_live_yata_xxx
  Prefer: count=exact, return=representation

→ 200 OK
  Content-Range: 0-49/237
  Sql-Constraint-Mode: rw-eventual
  [{"key":"a/b.png","size":12345,"etag":"..."}, ...]
```

```
POST /rest/v1/vertex_my_label
  Prefer: return=representation
  [{"vertex_id":"at://did:.../...","name":"alice","age":30}]
→ 201 Created
  [{"vertex_id":"at://did:.../...", ...}]
```

### Mapping

- URL `/rest/v1/{table}` → RW `yata_<hash>.public.<table>`
- query operators: `eq` / `neq` / `lt` / `lte` / `gt` / `gte` / `like` /
  `ilike` / `in` / `is` / `cs` (contains) / `cd` (contained-by) / `ov` (overlap)
  / `fts` (full-text search via vector cosine ≥ θ)
- `select=` → SQL `SELECT cols`
- `order=` → SQL `ORDER BY`
- `limit` / `offset` → SQL `LIMIT/OFFSET` (limit 必須、ない場合 default 50)
- `Prefer: count=exact` → COUNT(*) を別 query で実行 (Plan によっては rate limit)
- `Range: 0-49` (header) → `OFFSET 0 LIMIT 50` (LIMIT 必須 root rule に整合)

### 制約 (RW alignment)

- `?on_conflict=...` (PostgREST upsert) は **未サポート**。クライアントは PK
  implicit upsert を期待、server は PK 重複時 INSERT が silently no-op
  (delete-then-insert pattern を提供する `Prefer: yatabase-replace=true` を
  独自拡張で受理)
- `Prefer: tx=rollback` は **未サポート** (RW tx 不可)
- `RPC` (`/rest/v1/rpc/{fn}`) は **PostgREST stored function** をサポートしない。
  代わりに `/functions/v1/{name}` (S12) に委譲する 308 redirect を返す

### Auth / RLS

- `Authorization: Bearer sk_live_yata_*` → org_did 解決 → per-org PG ROLE で
  HYPERDRIVE 接続 → RLS policy が `actor_did = current_setting('jwt.claims.sub')`
  で row 制限 (ADR-0095)

## D17. S10 — `/graphql/v1` GraphQL endpoint

**Position**: 「Hasura / pg_graphql / Apollo client が無改修で動く auto-generated
GraphQL」。schema は RW `information_schema.tables` を introspect → SDL を
生成。

### Wire

```
POST /graphql/v1 HTTP/1.1
Authorization: Bearer sk_live_yata_xxx
Content-Type: application/json

{ "query": "query { vertexPersonCollection(filter:{age:{gt:18}}, first:10) { edges { node { id name age friends: edge_knows { node { name } } } } } }" }
```

### Schema generation

- `vertex_<label>` → GraphQL type `Vertex<Label>` + `vertex<Label>Collection` query
- `edge_<type>` → GraphQL type `Edge<Type>` + traversal field on adjacent vertex types
- streaming MV (`mv_<name>`) → GraphQL `subscription mv<Name>` (S8 wire 経由 WS)
- mutations: `insertInto<Label>` / `deleteFrom<Label>` (UPDATE は patch shape で
  RW DELETE+INSERT を generate)

### Engine

- `graphile-build-pg` / `pg_graphql` 路線でなく、**RW schema introspection ベースの
  custom resolver** (yata-graphql crate, native Rust on yata-bolt-pool 同居)。
  reason: pg_graphql は PostgreSQL extension で RW に load 不可

### Plan limits

- Free: 100 query/min、cost 1K complexity/query
- Starter: 1K query/min、cost 5K complexity
- Pro: 10K query/min、cost 50K complexity
- Business: 100K query/min、cost 無制限
- Enterprise: 専用 graph engine

`api_request` metric に正規化、新 metric なし。

## D18. S11 — `/auth/v1/*` GoTrue 互換 (atproto OAuth canonical)

**Position**: 「supabase-js `auth.signIn(...)` / `auth.signUp(...)` が動く GoTrue
互換 shim。実体は **atproto OAuth bridge** で、内部 JWT は ES256 atproto session
が canonical」。

### Endpoints (GoTrue subset)

| Path | 用途 | 内部実装 |
|---|---|---|
| `POST /auth/v1/signup` | email / password sign-up | atproto handle 自動払い出し + atproto OAuth `password` grant |
| `POST /auth/v1/token?grant_type=password` | password login | atproto OAuth password grant → ES256 JWT 返却 |
| `POST /auth/v1/token?grant_type=refresh_token` | token refresh | atproto OAuth refresh |
| `GET /auth/v1/authorize?provider=atproto` | OAuth flow start | atproto OAuth `authorization_code` redirect |
| `GET /auth/v1/callback` | OAuth callback | code → token 交換 |
| `POST /auth/v1/logout` | session revoke | atproto OAuth revocation (ADR-2604240914) |
| `GET /auth/v1/user` | get current user | atproto session JWT decode + `did_document` 解決 |
| `POST /auth/v1/admin/users` | admin user mgmt | enterprise plan のみ、atproto handle reserve |

### Token shape

GoTrue は `{ access_token, token_type, expires_in, refresh_token, user }`
shape を返すが、`access_token` は **ES256 atproto session JWT** (canonical)。
`sub` claim は `did:erc725:etzhayyim:260425:{contract}` (ADR-0095)、`aud` は
`yatabase.etzhayyim.com`。

### `sk_live_yata_*` mint flow

`/auth/v1/admin/api-keys` (auth admin) で session 経由に API key を発行。
発行先 PDS = `vertex_api_key` (本 ADR §D9 と整合)。

### Forbidden

- email/password を yatabase 側に保管禁止 — atproto PDS の OAuth `password`
  grant が唯一の credential store
- 2FA / WebAuthn は atproto OAuth + ERC725 + Coinbase Smart Wallet (root rule
  Identity Topology) の path に委譲、`/auth/v1/factors` は **501 Not Implemented**
  を返す (Phase 9 enterprise で実装)

## D19. S12 — `/functions/v1/{name}` Edge Functions

**Position**: 「supabase-js `functions.invoke('hello', { body })` が動く serverless
endpoint。実体は **kotodama Invoke pass-through**」。

### Forwarding

```
POST /functions/v1/{name} HTTP/1.1
  Authorization: Bearer sk_live_yata_xxx
  Content-Type: application/json
  { "body": ... }

CF Worker → kotodama.Invoke(targetDid, method, params)
  ├─ name → `did:web:yatabase.etzhayyim.com:fn:{name}` に解決
  ├─ governance gate (`RequireApproval` / `WithBPMNTask` / etc.)
  ├─ L3 dispatcher (~30s/128MB) → response 即時
  ├─ L7 BPMN long-running → 202 Accepted + correlation key
  └─ L8 k8s pod (browser/heavy compute) → SSE stream
```

### Function 登録

- 顧客 plan limit に従い `/functions/v1/admin/deploy` で zip 形式の TS
  source を upload
- kotodama `app.command()` 規約に準拠 (project actor composition)
- **MVP は read-only invoke のみ** (顧客 function は `vertex_<label>` write
  禁止、graph state を変更したい場合は MCP S13 経由)

### Plan limits

- Free: 10 fn / 100K invoke/月 / 100ms p50
- Starter: 100 fn / 1M invoke / 500ms
- Pro: 1,000 fn / 10M / 1s
- Business: 10,000 fn / 100M / 30s
- Enterprise: 専用 mitama-yata-pool

`api_request` (10K req per ¥2.0) + `yata_query_cu_ms` (CPU time) に正規化。

## D20. S13 — `/mcp` (CRITICAL — sole external surface for AI)

**Position**: 「**外部 AI / 外部 principal 向け sole external API**。Supabase 互換
surface (S6-S12) は ecosystem ツール救済の compatibility envelope であり、新規
AI integration は MCP のみ受け入れる」。**ADR-2605091400 cell-membrane
原則をそのまま適用**。

### Wire (Streamable HTTP, MCP 1.x)

```
POST /mcp HTTP/1.1
Authorization: Bearer sk_live_yata_xxx (or atproto session JWT)
Content-Type: application/json
Accept: text/event-stream, application/json

{ "jsonrpc":"2.0", "id":1, "method":"initialize",
  "params": { "protocolVersion":"2025-06-18", "capabilities":{} } }
```

### Tool surface (auto-generated from XRPC + L4 registry)

`com.etzhayyim.apps.yata.*` lexicon の `func` 全件 + `kotodama.jsonld profile.capabilities`
が自動で MCP tool になる (root rule + ADR-0087 kotodama MCP facade と同方式)。

| Tool category | tool name 例 | underlying XRPC |
|---|---|---|
| Graph query | `yata.graph.cypher` | `/cypher` (S6) |
| Graph query | `yata.graph.sparql` | `/sparql` (S3) |
| Graph query | `yata.graph.sql` | `/rest/v1/{table}` (S9) |
| Storage | `yata.storage.put` / `.get` / `.list` / `.presign` | `/storage/v1/object/*` (S1) |
| Vector | `yata.vector.search` | `vector_cosine` UDF |
| Realtime | `yata.realtime.subscribe` | `/realtime/v1/websocket` (S8) |
| Reasoning | `yata.reasoning.run` | OWL EL/RL/QL/DL UDF (D3) |
| Schema | `yata.schema.list` / `.describe` | RW `information_schema` |

### Auth

- `tools/list` / `resources/list` / `initialize` / `ping` は public (rate-limit のみ)
- `tools/call` は ES256 atproto session JWT or `sk_live_yata_*` 必須
- `tools/call` の per-org per-method rate limit は `mcp_call` metric (本 ADR
  §D1) で課金 + throttle

### Discovery

- `https://yatabase.etzhayyim.com/.well-known/mcp.json`
- `https://yatabase.etzhayyim.com/.well-known/agent.json` (a2a / agent card)

### Internal-only XRPC ban (cell-membrane 適用)

ADR-2605091400 に従い、**外部 AI agent は XRPC `/xrpc/com.etzhayyim.apps.yata.*` を
直接叩かない**。XRPC は cytoplasmic (S4) 内部通信専用。客の AI integration は
全部 MCP を通す。違反検知:

- `Authorization: Bearer sk_live_yata_*` で `/xrpc/com.etzhayyim.apps.yata.*` を叩いた
  request は受理するが、response header `Deprecation: true` + `Sunset: 2026-12-31`
  + `Link: </mcp>; rel="successor-version"` を必ず付ける
- 2026-12-31 以降は `sk_live_yata_*` の XRPC direct access は **403 Forbidden**

## D21. S14 — `studio.yatabase.etzhayyim.com` (tenant operator UI)

**Position**: 「Supabase Studio 相当の Web UI。tenant operator (org admin) が
Browser で table / query / storage / auth / functions / realtime を運用」。

### Topology

```
studio.yatabase.etzhayyim.com (CF Pages, Svelte CSR)
  ├─ atproto OAuth login (browser PKCE flow)
  ├─ session JWT を localStorage 保管 (XSS 対策で SubtleCrypto wrap)
  └─ S1-S13 を fetch
       /storage/v1, /sparql, /cypher, /rest/v1, /graphql/v1,
       /functions/v1, /realtime/v1, /mcp
```

### Sidebar (Supabase Studio 構成模倣)

| ペイン | 提供機能 |
|---|---|
| **Table** | RW table list / row CRUD (S9 経由) / schema view |
| **SQL** | psql 風 editor (S5 経由 read-only) |
| **Cypher** | Cypher editor + 結果 graph viz (S6 経由) |
| **SPARQL** | SPARQL editor + RDF triple table (S3 経由) |
| **Storage** | bucket explorer / blob upload / presign URL mint (S1) |
| **Auth** | user list / session revoke / role mgmt (S11 admin) |
| **Functions** | function deploy / log tail (S12) |
| **Realtime** | MV subscribe debugger (S8) |
| **MCP** | tool list / `tools/call` debugger (S13) |
| **Settings** | API key mint / billing / plan upgrade (本 ADR §D9) |

### Embedded — yata Web client

`yata-web` (yata crate workspace 追加 sub-crate, Phase 5+) が `wasm-bindgen`
target で Studio に embed される。Browser から S6/S8/S13 を call。

## D22. Billing 軸の正規化 (D7 amend)

D12 で増えた surface も新 metric を持たない。既存軸への正規化:

| Surface | 正規化 metric | 単位 |
|---|---|---|
| S6 `/cypher` | `yata_query_cu_ms` + `api_request` | per RUN |
| S7 Bolt `:7687` | `yata_query_cu_ms` + `api_request` | per RUN |
| S8 `/realtime/*` | `api_request` (heartbeat=0.01, msg=1) | per WS message |
| S9 `/rest/v1/*` | `api_request` + `yata_query_cu_ms` | per HTTP req |
| S10 `/graphql/v1` | `api_request` + `yata_query_cu_ms` | per query (cost-weighted) |
| S11 `/auth/v1/*` | `api_request` (sign-up = 1, token refresh = 0.1) | per req |
| S12 `/functions/v1/*` | `api_request` + `yata_query_cu_ms` (CPU) | per invoke |
| S13 `/mcp` | `mcp_call` (本 ADR §D1, 既存) + `yata_query_cu_ms` (tool 実行 cost) | per `tools/call` |
| S14 Studio | `api_request` (内部 fetch を S1-S13 で計測済) | — |

`vertex_billing_event.product` は依然として `yata` 一本に集約。`ref_resource_did`
で surface を区別する場合は `did:web:yatabase.etzhayyim.com:surface:{S6...S13}` を入れる。

## D23. Roadmap update (Implementation Roadmap §amend)

既存 P1-P12 に新 surface を割り当て直す。**P4a-P4f を P4 (yatabase MVP) と
P5 (yata crate 0.1 publish) の間に挿入** (P5 が新 sub-crate を含めるため、
surface が先に入っていなくてはならない)。

| Phase | 期間 | 成果物 (delta) |
|---|---|---|
| **P4a: MCP `/mcp` (S13) + Cypher `/cypher` MVP (S6)** | M3 | MCP facade Worker + kagami-cypher-compiler を CF Worker に WASM bundle、READ-ONLY Cypher 動作確認、`/.well-known/mcp.json` |
| **P4b: Bolt :7687 (S7) + Auth `/auth/v1/*` (S11)** | M3-M4 | yata-bolt server crate + Vultr K8s LB → bolt.yatabase.etzhayyim.com TLS 終端、cypher-shell smoke test、GoTrue 互換 shim、atproto OAuth bridge |
| **P4c: Realtime `/realtime/v1/*` (S8)** | M4 | DO `RealtimeMux` + RW MV poller BPMN、supabase-js `realtime.channel().on('postgres_changes', ...)` smoke |
| **P4d: PostgREST `/rest/v1/*` (S9) + GraphQL `/graphql/v1` (S10)** | M4-M5 | postgrest-client smoke、yata-graphql crate (RW schema introspection)、Apollo client smoke |
| **P4e: Edge Functions `/functions/v1/*` (S12)** | M5 | kotodama.Invoke pass-through、`/functions/v1/admin/deploy` で zip upload、5 example fn |
| **P4f: Studio UI `studio.yatabase.etzhayyim.com` (S14)** | M5 | Svelte CSR + 10 sidebar pane + atproto OAuth login |
| (existing P5-P12 は M3-M9+ のまま、P4a-P4f を blocker としない) | — | — |

P7 (Cypher translator) は P4a で MVP 投入したため、**Phase 7 の scope を WRITE
support + path algorithm (`shortestPath` / PageRank / community) に縮小**。
P11 (Bolt) は P4b で前倒し済 → Phase 11 は **Bolt v5 binary protocol Phase
2 (server-side cursor / batch fetch)** に scope 変更。

## D24. yata Rust crate 拡張 (D5 amend)

新 surface に対応する yata crate sub-crate 追加:

| Sub-crate | 用途 | Phase |
|---|---|---|
| `yata-cypher` | openCypher → SQL/PGQ AST (kagami-cypher-compiler の Rust 公開 wrapper) | P3.5 |
| `yata-bolt` | Bolt v4/v5 server + client | P3.6 |
| `yata-realtime` | Phoenix channel WS client + server | P3.7 |
| `yata-rest` | PostgREST compatibility wire (server emit + client) | P3.8 |
| `yata-graphql` | RW schema → GraphQL SDL + resolver | P3.8 |
| `yata-auth` | GoTrue 互換 shim (server-only sub-crate) | P3.6 |
| `yata-functions` | kotodama.Invoke pass-through binding | P3.9 |
| `yata-mcp` | MCP server export (既存予定、ADR §D5 に既出) | P3.5 (前倒し) |
| `yata-web` | wasm-bindgen target for Studio embedding | P3.10 |

公開 API (Rust, P3.5+ baseline):

```rust
use yata::prelude::*;

let y = Yata::connect("yatabase://sk_live_yata_xxx@yatabase.etzhayyim.com/my-db").await?;

// S3 SPARQL
let rows = y.sparql("SELECT ?p WHERE { ?p :knows :alice }").await?;

// S6 Cypher (NEW)
let rows = y.cypher("MATCH (p:Person)-[:KNOWS]->(f) RETURN f.name LIMIT 10")
            .param("id", "alice").fetch().await?;

// S7 Bolt (NEW, alternative wire)
let bolt = y.bolt().await?;  // bolt+s://bolt.yatabase.etzhayyim.com:7687
let rows = bolt.run("MATCH (n) RETURN n LIMIT 1").await?;

// S8 Realtime (NEW)
let mut sub = y.realtime("mv_my_followers")
              .filter("org_did", Eq("did:erc725:..."))
              .subscribe().await?;
while let Some(change) = sub.next().await { /* ... */ }

// S9 PostgREST 互換 (NEW, REST envelope を query builder で透過化)
let rows: Vec<Person> = y.rest::<Person>().filter_eq("name", "alice").fetch().await?;

// S13 MCP (NEW, AI agent としての yata)
let mcp = y.mcp_server().await?;
mcp.serve(("0.0.0.0", 9000)).await?;
```

# Comparison

## yatabase vs 商用 graph DB

| | yatabase | Neo4j AuraDB | TigerGraph Cloud | ArangoGraph | Amazon Neptune | Stardog Cloud |
|---|---|---|---|---|---|---|
| 月額 start | **¥0** | $65 | enterprise | $0.30/h | $0.10/h | enterprise |
| Streaming MV | **✓** | ✗ | ✗ | ✗ | ✗ | ✗ |
| OWL reasoning | **✓** (EL/RL/QL/DL) | ✗ | ✗ | ✗ | ✗ | ✓ |
| SHACL validation | **✓** | ✗ | ✗ | ✗ | ✗ | ✗ |
| SPARQL | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ |
| Cypher (Phase 2) | ✓ | ✓ | ✗ | ✗ | ✓ | ✗ |
| pgvector hybrid | **✓** | △ | △ | △ | ✗ | ✗ |
| AT Protocol federation | **✓** | ✗ | ✗ | ✗ | ✗ | ✗ |

→ **「streaming + reasoning + federation」3 拍子揃った商用 graph DB は他にない**。

## obj vs 商用 object storage

| | obj | AWS S3 | R2 | B2 raw | Wasabi |
|---|---|---|---|---|---|
| Storage 単価 | ¥10/GB | ¥3.5/GB + egress | ¥2.3/GB | ¥0.9/GB | ¥0.9/GB |
| Egress (Internet) | ¥15/GB | ¥13.5/GB | ¥0 | ¥1.5/GB | ¥0 |
| BWA 内 egress | **¥0** | ✗ | — | ¥0 | — |
| 自動 tier | ✓ | ✓ (有償) | ✗ | ✗ | ✗ |
| LLM auto-tag | **✓** | ✗ | ✗ | ✗ | ✗ |
| Vector embedding | **✓** | ✗ | ✗ | ✗ | ✗ |
| Vault E2E | **✓** | ✗ | ✗ | ✗ | ✗ |
| AT Proto federation | **✓** | ✗ | ✗ | ✗ | ✗ |

→ list 価格 ¥10/GB は B2 raw の 11 倍だが、**LLM tag + embedding + Vault + federation** バンドル価値で正当化。

## 粗利シミュレーション (1,000 paying customer mix)

```
Free          10,000   ¥0/month       MRR ¥0           cost ¥300,000   GP -¥300,000
Starter          500   ¥1,980         ¥990,000         ¥60,000        ¥930,000
Developer        300   ¥4,980         ¥1,494,000       ¥105,000       ¥1,389,000
Team              80   ¥59,400 (3 seat avg) ¥4,752,000 ¥672,000       ¥4,080,000
Business          15   ¥98,000        ¥1,470,000       ¥180,000       ¥1,290,000
Enterprise         5   ¥1,500,000     ¥7,500,000       ¥900,000       ¥6,600,000
─────────────────────────────────────────────────────────────────────────────
total                                 ¥16,206,000      ¥2,217,000     ¥13,989,000
                                      年商 ¥194M       原価 ¥27M       年粗利 ¥168M
```

平均粗利率 **86%**。Enterprise 5 社が MRR 46% を占める集中度なので、enterprise sales
には **値引き原資 50% を予め用意**しておく。

# Consequences

## Positive

- **粗利 86-94%** を確保しつつ、競合値下げ攻撃に **50% 追加値下げ余力**
- B2 / RW の既存原価優位を retail 価格でなく **value-add (LLM / federation /
  reasoning) で正当化**できる構造
- yatabase が **streaming graph + reasoning** という未占有 niche を取れる
- yata crate が monorepo subtree → crates.io 公開で **外部開発者の入り口**になる
- obj が AT Protocol federation を sell する distribution channel になる
- billing v2 が sales / channel / partner program の **承認 workflow を schema 化**
  → CFO dashboard で値引き総量が見える

## Negative / Risk

- **RW の OLTP 制約** (ON CONFLICT 不可、tx 不可、UNIQUE 不可) を顧客が誤期待する
  → docs / marketing copy に **「Not for OLTP」を明示**、Plan 表でも analytics 用途と
  明記
- **Cypher translator (~3K LoC)** が Phase 2 で詰む可能性 → MVP は SQL/PGQ + SPARQL
  に絞り、Cypher は需要が見えてから
- **Multi-tenant noisy neighbor**: shared RW cluster で 1 org の重い query が他 org を
  starve → per-role `statement_timeout = 30s` + concurrent connection cap + `dml_rate_limit`
  で抑制、Business plan 以降は dedicated namespace に分離
- **B2 SlowDown / rate limit**: ADR-0048 の 2026-04-25 incident で経験済 → 顧客 PUT が
  burst したとき自分の internal traffic を阻害する可能性 → per-org rate limit を obj
  Worker で先に絞る、`etzhayyim-iceberg` 系 internal bucket とは account 分離も検討
- **Free tier の経済性**: 10K free user × ¥30/月原価 = ¥300K/月 → Developer 0.5%
  conversion (50 人 × ¥4,980) で ¥250K → 当面赤字。Conversion を 1% 以上に押し上げる
  product-led growth が前提
- **LLM 推論コスト**: ADR-2605010000 で RunPod 6000 Ada 1 pod ($0.5-1/h amortized) が
  SSoT。月 100M token (Pro plan 含有量) × 30 customer × 80% 使用率 = 月 2.4B token →
  GPU 占有率と queue 深さの観測が必要、突き抜けたら H100 pod 追加 (cost に H100 単価
  ¥450/h を盛り込み済)

## Operational

- New helm release 2 つ追加: `yatabase-edge` (CF Worker は外側だが proxy / metering
  が pod 化される箇所) + `obj-edge`
- 既存 `mitama-udf-pool` には billing 専用 zeebe-worker profile を 1 つ追加 (ADR-0056
  pattern、shosha / shinshi 同形)
- 1Password vault に `etzhayyim cloud retail` フォルダ新設 → Stripe key / 適格請求書発行
  証 / DPA template / channel partner agreement
- CLAUDE.md `[platform.products]` に yatabase / obj / yata 3 entry を追加 (この ADR
  approve 後)

# Alternatives Considered

## Alt-1: etzhayyim OLTP (Neon-style separated compute/storage Postgres) も同時に出す

**Rejected**: pageserver fork (Neon OSS は Apache 2.0 だが Rust ~50K LoC の運用負担)
+ branching / auto-suspend 実装が当面 ROI 低い。yatabase で graph + analytics に集中、
OLTP は需要が現場から上がってきたら別 ADR で起票。

## Alt-2: list 価格を原価+30% で出す (低価格訴求)

**Rejected**: 競合値下げ時に追加値下げ余地がなくなる。原価優位を表に出す代わりに、
**value-add (federation / reasoning / streaming MV / LLM bundle) で価格正当化** する
方が長期粗利を守れる。R2 が egress 0 円で押した結果 storage を上げざるを得なくなった
教訓を踏まえる。

## Alt-3: yata crate を TypeScript-first にする

**Rejected**: TypeScript SDK は需要が大きいが、**Rust が canonical (型安全 + proc-macro
schema + MCP server + CLI binary 1 本)** で他言語派生を作る方が長期的に整合する。yata-ts
は Phase 2 で native 実装、yata-py は PyO3 で Rust core を再利用。

## Alt-4: 全部 1 つの umbrella product `etzhayyim Cloud` にして製品分離しない

**Rejected**: yatabase (graph) と obj (storage) は **顧客像が異なる** (graph = AI agent
developer / data scientist、obj = web app developer / video creator)。別ブランドで sales
narrative を分離する方が CAC 効率が良い。billing は共通基盤、製品は分離が最適。

## Alt-5: Cypher を MVP に含める

**Rejected**: openCypher parser ~3K LoC + AST → SQL/PGQ translator ~5K LoC の実装は
Phase 2 規模。MVP は **SPARQL + SQL/PGQ + XRPC + MCP** で出し、Cypher は Neo4j 移行
需要が顕在化してから build。

## Alt-6: etzhayyim Vector / etzhayyim Search を別製品として分離

**Rejected**: pgvector は yatabase に内包、search (BM25 / hybrid retrieval) は
yatabase の MV / SQL query で十分カバー。分離は粗利を稀釈する。

# Implementation Roadmap

| Phase | 期間 | 成果物 |
|---|---|---|
| **P1: Billing 基盤** | M1-M2 | `vertex_billing_event` + 5 MV + 8 lexicons (`com.etzhayyim.apps.billing.*`) + 5 BPMN actors + `mitama-billing-pool` helm |
| **P2: API key 製品別 prefix** | M2 | authn/authz Worker 拡張で `sk_live_yata_*` / `sk_live_obj_*` / 汎用 `sk_live_*` を分離、ROLE binding |
| **P3: obj.etzhayyim.com MVP** | M2-M3 | `obj.etzhayyim.com` Worker (S3-compat REST + XRPC) + B2 backend + per-org bucket provisioning + tier policy + metering |
| **P4: yatabase.etzhayyim.com MVP** | M3 | `yatabase.etzhayyim.com` Worker + multi-tenant DB provisioning + SQL/PGQ pass-through + SPARQL translator + XRPC + MCP |
| **P5: yata crate 0.1 公開** | M3-M4 | `50-clients/rust/yata/` workspace + `yata-core` + `yata-schema` + `yata-derive` + `yata-query` + `yata-sparql` + `yata-cli` + 5 example、crates.io publish |
| **P6: obj 強化** | M4 | LLM auto-tag worker + embedding worker (BPMN actor)、Vault E2E option、CDN R2 cache layer |
| **P7: yatabase Cypher translator** | M4-M6 | openCypher parser + AST → SQL/PGQ translator (~8K LoC)、`yata-cypher` sub-crate |
| **P8: Stripe + 適格請求書** | M5 | Stripe wiring + per-org customer + 月次 invoice BPMN + 適格請求書 (T9007028460042) PDF render |
| **P9: Sales discount + channel** | M5-M6 | per-org discount field + admin UI + reseller program (30% margin) + CFO 承認 workflow |
| **P10: Enterprise (専用 cluster + DPA + SLA)** | M6+ | dedicated `yatabase-pro-<customer>` helm release 自動化、DPA / 適格請求書、99.9% SLA、24/7 oncall |
| **P11: yatabase Bolt :7687** | M9+ | binary protocol (Neo4j driver 互換)、`yata-bolt` server + client |
| **P12: 他言語 SDK** | M9+ | yata-py (PyO3) / yata-ts (native pg + fetch) / yata-go (pgx) |

# Open Questions

| # | 論点 | 既定推奨 | 確定タイミング |
|---|---|---|---|
| 1 | proxy 層 (yatabase) | PgBouncer transaction mode | P4 着手前 |
| 2 | 多 region 展開 trigger | LAX 1 拠点で start、加入 500/2,000/10,000 で増設 | P9 |
| 3 | obj の Tier 1 (HOT) を Vultr Object Storage にするか | Yes (LAX ~10ms)、Free / Starter は B2 直で OK | P3 |
| 4 | Free tier auto-suspend (yatabase) | 7 日アクセスなしで PG ROLE 一時停止、再アクセスで自動再開 | P4 |
| 5 | Stripe vs Pay.jp | Stripe (Japan tax + 海外決済両対応) | P8 |
| 6 | metering 粒度 | per-request (RW で MV 集計、`ts_ms` partition) | P1 |
| 7 | Cypher MVP 含む? | 否 (Phase 2 後送り) | P4 / P7 |
| 8 | OWL DL (HermiT) を Free に開放? | 否 (Pro 以上、CPU 重い JVM pod) | P4 |
| 9 | 通貨 | JPY base、enterprise のみ USD/JPY 選択 | P8 |
| 10 | yata crate license | Apache-2.0 OR MIT (Rust 慣例 dual-license) | P5 |
| 11 | yata crate MSRV | Rust 1.78 (stable, 2024 edition) | P5 |
| 12 | yata 公開 repo | monorepo subtree push to `github.com/etzhayyim/yata` | P5 |
| 13 | 商標 | "yatabase" / "yata" / "etzhayyim Cloud" の TM 出願 (J/US/EU) | P9 (enterprise 直前) |
| 14 | DPA template | ISO 27001 + GDPR + 改正個人情報保護法準拠 | P10 |

# References

- ADR-0002 Kotoba/Datomic-backed graph storage (P10v2 GraphAr-native columnar)
- ADR-0036 Worker-direct Hyperdrive persistence (originator of `vertex_<actor>_<kind>` 規約)
- ADR-0044 Kotoba/Datomic UDF language strategy (graph reasoning impl 基盤)
- ADR-0048 Kotoba/Datomic primary cutover Linode → Vultr+B2 (cost basis)
- ADR-0056 BPMN-as-actor (billing rollup の実装パターン)
- ADR-0087 kotodama MCP tool facade (yata MCP server export の prior art)
- ADR-0095 3-Layer Identity + RW canonical columns (`org_did` / `actor_did` / `at_did` schema)
- ADR-2604282300 CF Worker = edge layer + Zeebe + RW UDF (yatabase / obj edge worker の責務分離)
- ADR-2605010000 RunPod 6000 Ada unified pod (LLM 原価基準)
- ADR-2605011200 graph-expand BPMN LLM edge inference (graph reasoning bridge)
- ADR-2605091400 MCP-as-cell-membrane / Lexicon+XRPC demotion (D12+ S13 `/mcp` を sole external surface に固定する根拠)
- 30-graph/kagami-cypher-compiler/ (D13 S6 `/cypher` の openCypher → SQL/PGQ 変換器、in-tree 既存)
- 90-docs/260424-bsky-compat-kotoba-split.md (RW OLTP 制約の権威ソース)

# Appendix A. yata crate Cargo.toml workspace skeleton

```toml
[workspace]
resolver = "2"
members = [
    "crates/yata",
    "crates/yata-core",
    "crates/yata-schema",
    "crates/yata-derive",
    "crates/yata-query",
    "crates/yata-sparql",
    "crates/yata-stream",
    "crates/yata-mcp",
    "crates/yata-cli",
]

[workspace.package]
version      = "0.1.0"
edition      = "2024"
rust-version = "1.78"
license      = "Apache-2.0 OR MIT"
repository   = "https://github.com/etzhayyim/yata"
homepage     = "https://yatabase.etzhayyim.com"
authors      = ["etzhayyim <jun@etzhayyim.com>"]

[workspace.dependencies]
tokio          = { version = "1", features = ["full"] }
tokio-postgres = "0.7"
tokio-rustls   = "0.26"
rustls         = "0.23"
serde          = { version = "1", features = ["derive"] }
serde_json     = "1"
chrono         = { version = "0.4", features = ["serde"] }
uuid           = { version = "1", features = ["v4", "serde"] }
reqwest        = { version = "0.12", features = ["json", "rustls-tls"], default-features = false }
tokio-tungstenite = "0.24"
rmcp           = "0.2"
clap           = { version = "4", features = ["derive"] }
thiserror      = "2"
async-trait    = "0.1"
```

# Appendix B. yatabase Worker tenant routing pseudocode

```typescript
// 50-infra/cloudflare/workers/yatabase/src/index.ts (sketch)
export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const auth = await verifyApiKey(req, env);  // sk_live_yata_* → org_did
    const org = await resolveOrg(auth.orgDid, env);
    const dbName = `yata_${sha256Hex(org.did).slice(0, 16)}`;

    await meter(env, {
      orgDid: org.did, metric: "api_request", qty: 1,
      product: "yata", refResource: dbName,
    });

    if (req.url.pathname === "/sparql") {
      return handleSparql(req, env, dbName, org);
    }
    if (req.url.pathname === "/cypher") {
      return handleCypher(req, env, dbName, org);  // Phase 2
    }
    if (req.url.pathname.startsWith("/xrpc/com.etzhayyim.apps.yata.")) {
      return handleXrpc(req, env, dbName, org);
    }
    if (req.url.pathname === "/mcp") {
      return handleMcp(req, env, dbName, org);
    }
    return new Response("Not Found", { status: 404 });
  }
}
```
PG protocol (:5432) は CF Worker の外、Vultr LB + PgBouncer 経由で同じ
`yata_<hash>` DB に直接到達 (ADR-2604282300 / RW shared cluster)。

# Appendix C. obj Worker tenant routing pseudocode

```typescript
// 50-infra/cloudflare/workers/obj/src/index.ts (sketch)
export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const auth = await verifyAuth(req, env);  // SigV4 or sk_live_obj_*
    const { bucket, key } = parseS3Path(req);
    const policy = await loadBucketPolicy(env, bucket);  // tier / encryption / acl

    await meter(env, {
      orgDid: policy.orgDid,
      metric: req.method === "GET" ? "obj_class_b" : "obj_class_a",
      qty: 1, product: "obj", refResource: bucket,
    });

    const origin = selectOrigin(policy.tier, policy.region);  // vultr / b2-std / b2-archive
    const resp = await fetchFromOrigin(origin, bucket, key, req);

    if (req.method === "GET" && resp.body) {
      const bytes = parseInt(resp.headers.get("content-length") ?? "0");
      await meter(env, { orgDid: policy.orgDid, metric: "egress_gb",
                         qty: bytes / 1e9, product: "obj", refResource: bucket });
    }
    return resp;
  }
}
```

## D25. Service-establishment baseline — 32-step customer journey (2026-05-13)

The forward regression contract for yatabase is the durable
end-to-end customer journey at
`70-tools/scripts/yatabase-customer-journey.mjs`. From 2026-05-13
onward the service is considered "established" iff this journey is
**32 PASS · 0 SOFT · 0 FAIL · journey=GREEN** against live
`https://yatabase.etzhayyim.com`.

Every cycle that ships a new customer-facing surface must add an
assertion to this script and turn it from `n` PASS to `n+1` PASS
before being declared shipped. Cycles that only fix internals
(without expanding the surface a paying customer can rely on) do not
add a step but must keep all existing steps GREEN.

### Coverage as of P107 (2026-05-13)

| Surface family | Steps | Notes |
|---|---|---|
| Auth lifecycle | 1, 9b, 9c, 9d, 9e, 9b.d | signup, whoami, attach-email (verify-gated), recover (no enumeration), redeem (bad token), invite+revoke (KV-revoked) |
| Billing | 7, 8 | signed Stripe webhook → plan flip free→starter |
| Plan + quota | 2 | quota.used = 0 baseline |
| Metering | 9 | `byMetric=2 api_request.totalQty>=3` |
| Cypher engine | 3a, 3b, 3c, 3c.b, 3c.c, 3d, 3e, 3f | CREATE/MATCH/SET, WHERE (string CONTAINS/STARTS WITH/ENDS WITH + numeric + AND), edges + traversal, incoming + DELETE_EDGE, MERGE + two-hop + idempotency |
| MCP | 4, 5 | tools/list (public), tools/call yata.graph.cypher |
| Storage | 6, 6b (P105), 6c | PUT, full lifecycle (list → sign → anonymous GET → DELETE → post-delete-404), S3 SigV4 compat |
| Tenant isolation | 3b.2 | tenant B blind to tenant A across cypher + storage + audit |
| Webhooks | 3c.d | register, mutation surface, delete (secret shown once, redacted thereafter) |
| Observability | 9b.c, 9c.b, 9f, 9g (P106) | members, outbox, audit, schema (cypherLabels[] + Journey anchor) |
| Browser contract | 9h (P107) | OPTIONS preflight on /cypher, /mcp, /storage, /api/schema |
| Data rights | 10, 11 | export (CCPA / GDPR / 改正個人情報保護法 §33), erasure + auth tombstone |

### Cycle ledger (P105–P107)

| Cycle | Date | Surface added | Result |
|---|---|---|---|
| P105 | 2026-05-13 | Storage lifecycle (step 6b: list, sign, anonymous GET, DELETE, post-delete-404) | 29 → 30 PASS |
| P106 | 2026-05-13 | `/api/schema` introspection (step 9g: cypherLabels[] + Journey anchor + totalNodes) | 30 → 31 PASS |
| P107 | 2026-05-13 | CORS preflight (step 9h: OPTIONS on /cypher, /mcp, /storage, /api/schema; Origin echo, methods, authorization in allow-headers) | 31 → 32 PASS |

### Invariant

If the journey turns red against live production, the responsible
on-call action is to identify the regression and either roll the
relevant deploy back or pin the breaking change. No yatabase deploy
should be declared shipped without re-running this script.
