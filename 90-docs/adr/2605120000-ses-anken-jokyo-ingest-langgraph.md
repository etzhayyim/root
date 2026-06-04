---
id: adr-2605120000-ses-anken-jokyo-ingest-langgraph
title: "ADR-2605120000: SES 案件・状況 LangGraph Ingest Pipeline"
status: accepted
doc_type: adr
topic: ses-anken-jokyo-ingest
authoritative: true
last_verified: 2026-05-19
phase_current: "5"
priority: 7.5
axis: architecture
weight: 0.7
priority_note: "SES (システムエンジニアリングサービス) 案件・状況を email / 手動 ingest → LLM 抽出 → graph 化する業務 pipeline。非公開 domain write のみ (non-federable)"
authoritative_for:
  - SES 案件・状況 ingest pipeline の LangGraph actor 定義
  - vertex_ses_* schema (案件 / 状況 / クライアント / エンジニア / run)
  - 6 NSID lexicon (com.etzhayyim.apps.ses.{ingestAnken,updateJokyo,getAnken,listAnken,listJokyo,coverage})
  - email → 案件 自動抽出 (LLM structured output)
  - 状況遷移モデル (提案中→選考中→契約→稼働中→終了)
depends_on:
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605080000-distributed-cognitive-actor-system
  - adr-2605080200-pydantic-l6-validation-contract
  - adr-2605080300-sqlalchemy-core-usage-contract
  - adr-2604282300
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
  - adr-2604251830-shannon-optimal-layered-architecture
  - adr-0095-simplified-3layer-identity-rw-vault
  - adr-0018-pii-tier3-cohort-first
  - adr-0041-pds-commit-content-addressed-pk
related:
  - adr-2605080800-manimani-langgraph-user-intake-routing
  - adr-2605091200-global-product-resident-ingest-langgraph
  - adr-0032-gmail-direct-ingest-yabai-classifier
---

# ADR-2605120000: SES 案件・状況 LangGraph Ingest Pipeline

## Goal

SES（システムエンジニアリングサービス）の **案件** (クライアント・要件・単価・期間 等) と **状況** (提案中 / 選考中 / 契約 / 稼働中 / 終了 の遷移) を、メール本文や手動入力から自動抽出し、RisingWave graph に永続化する ingest pipeline を確立する。

- 案件はメール（Outlook / Exchange ingest）または XRPC `ingestAnken` で投入できる
- LLM が案件の構造データ（クライアント名・スキル要件・単価・期間・担当エンジニア候補）を抽出する
- 状況は `updateJokyo` XRPC で随時更新し、遷移ログを append-only で保持する
- 全データは non-federable（AT Repo emit なし）、`actor_did` scope で RLS 管理

## Scope

### In scope (Phase A — 本 ADR で contract 確定)

- T3 actor `ses.etzhayyim.com` の CF Worker edge facade 定義
- LangGraph StateGraph 6 node (`parse_source` → `classify_anken` → `extract_details` → `update_jokyo` → `persist` → `emit_audit`)
- RisingWave schema: 5 vertex + 2 edge + 2 MV
- 6 NSID lexicon (`com.etzhayyim.apps.ses.*`)
- 状況遷移モデルと forbidden 遷移の定義
- Pydantic v2 state contract (ADR-2605080200 準拠)

### Out of scope

- ~~UI（yoro AppView 上の案件一覧 / 状況ボード）— Phase 4~~ → **Phase 4 完了** (ses.etzhayyim.com/anken)
- Outlook webhook 自動 ingest（cron pull は Phase 2 で追加）
- エンジニアマッチング推薦（案件 ↔ エンジニア embedding 類似度）— Phase B
- 請求書・契約書 PDF 抽出 — 別 ADR
- vault.etzhayyim.com E2E 暗号化 — Phase C

## Executive Summary

新規 T3 actor `ses.etzhayyim.com` を立ち上げる。CF Worker は edge facade（Hono + auth + XRPC）のみを持ち、business logic は LangGraph Server + Granian（ADR-2605080600）で実行する。

案件抽出は **LLM 主導** とする。Anthropic structured output で `AnkenExtraction` を返し、既存案件との同一性照合（クライアント名 + 期間の重複チェック）は SQL で行う。状況更新は `AnkenJokyo` append-only log に積み、最新状況は `mv_ses_anken_latest_jokyo` で提供する。

ADR-2605111200 に準拠し、CF Worker は `env.HYPERDRIVE` を持たない。全 domain write は XRPC → bpmn-dispatcher → LangGraph Server → asyncpg INSERT の経路に限定する。

## Decision

### Actor profile

| 項目 | 値 |
|---|---|
| host | `ses.etzhayyim.com` |
| DID | `did:web:ses.etzhayyim.com` |
| AT Protocol Layer | 9 Client App + Actor Worker |
| Tier | T3 (CF Worker = edge facade、LangGraph Server = execution) |
| Federable | **No** (domain write のみ、AT Repo emit なし) |
| PII tier | ADR-0018 Tier 3 (Preferences-equivalent、graph 行は actor_did scope RLS) |

### Layer 配置 (ADR-2604251830)

| Layer | 担当 |
|---|---|
| L1 Edge | `ses.etzhayyim.com` CF Worker — Hono dispatcher、auth middleware、XRPC facade のみ |
| L3 Routing | `bpmn-dispatcher.mitama-udf.svc.cluster.local:8080` (HMAC `x-internal-trust`) |
| L3 Execution | LangGraph Server + Granian (`mitama-ses-pool` Helm release) |
| L4 SSoT | `vertex_ses_{anken,jokyo,client,engineer,run}` + `edge_ses_{anken_client,anken_engineer}` |
| L6 Compute | Anthropic API (`tier=balanced` for extraction、`tier=fast` for classification) |

### LangGraph StateGraph (6 node)

```
                ┌─────────────────────────────────────┐
                │ START (XRPC ingestAnken / email src) │
                └───────────────┬─────────────────────┘
                                 ▼
                           parse_source
                   (email 本文 or raw_text → parsed_text)
                                 │
                                 ▼
                          classify_anken
                   ┌─────────────┴────────────┐
                   ▼                          ▼
              (既存案件に合致)          (新規案件)
                   │                          │
                   └─────────────┬────────────┘
                                 ▼
                          extract_details
                  (LLM structured output → AnkenExtraction)
                                 │
                                 ▼
                          update_jokyo
                  (状況が変化した場合のみ append)
                                 │
                                 ▼
                             persist
                  (asyncpg INSERT vertex_ses_* + edge_ses_*)
                                 │
                                 ▼
                           emit_audit
                       (OCEL 2.0 audit event)
                                 ▼
                                END
```

State は Pydantic v2 で型付け（ADR-2605080200）。`thread_id = sha256(actor_did + ts_ms + source_hash)`。

### 状況遷移モデル

```
提案中 → 選考中 → 契約 → 稼働中 → 終了
                ↓         ↓
             見送り      中途終了
```

| 遷移 | 許可 |
|---|---|
| 提案中 → 選考中 | ✓ |
| 提案中 → 見送り | ✓ |
| 選考中 → 契約 | ✓ |
| 選考中 → 見送り | ✓ |
| 契約 → 稼働中 | ✓ |
| 稼働中 → 終了 | ✓ |
| 稼働中 → 中途終了 | ✓ |
| 終了・見送り・中途終了 → 任意 | **禁止** (append-only log、再開は新規案件として ingest) |

`update_jokyo` ノードは forbidden 遷移をスキップし `jokyo_skipped=true` で run を完了させる（例外 raise なし）。

### Pydantic v2 State contract

```python
class SesIngestState(BaseModel):
    # Input
    source_kind: Literal["email", "manual"]
    raw_text: str
    actor_did: str
    org_did: str

    # parse_source output
    parsed_text: str | None = None
    source_email_subject: str | None = None
    source_email_from: str | None = None

    # classify_anken output
    anken_decision: Literal["existing", "new"] | None = None
    existing_anken_id: str | None = None

    # extract_details output
    extraction: "AnkenExtraction | None" = None

    # update_jokyo output
    jokyo_appended: bool = False
    jokyo_skipped: bool = False

    # persist output
    anken_vertex_id: str | None = None
    jokyo_vertex_id: str | None = None

    # run metadata
    run_id: str
    status: Literal["pending", "running", "completed", "completed_with_error", "failed"] = "pending"
    error_text: str | None = None
    model_ids_used: list[str] = []
    tokens_total: int = 0


class AnkenExtraction(BaseModel):
    client_name: str
    client_company: str | None = None
    skill_requirements: list[str]
    jokyo: Literal["提案中", "選考中", "契約", "稼働中", "終了", "見送り", "中途終了"]
    start_month: str | None = None          # YYYY-MM or None
    end_month: str | None = None
    rate_lower_yen: int | None = None       # 月額下限 (整数、ADR float 禁止)
    rate_upper_yen: int | None = None       # 月額上限
    work_location: str | None = None
    remote_ok: bool | None = None
    engineer_name: str | None = None        # 担当エンジニア候補
    notes: str | None = None               # ≤400 char
    confidence: float                       # 0.0..1.0
    rationale: str                          # ≤200 char
```

### Schema (RisingWave、ADR-2605111200 準拠 — asyncpg INSERT のみ)

```sql
-- 案件
vertex_ses_anken (PK content-addressed: sha256(actor_did + client_name + start_month))
  client_name        VARCHAR NOT NULL
  client_company     VARCHAR
  skill_csv          VARCHAR               -- skill_requirements を CSV flatten
  jokyo_current      VARCHAR NOT NULL      -- 最新状況 (MV と冗長だが書込時の snapshot)
  start_month        VARCHAR               -- YYYY-MM
  end_month          VARCHAR
  rate_lower_yen     INTEGER
  rate_upper_yen     INTEGER
  work_location      VARCHAR
  remote_ok          BOOLEAN
  notes              VARCHAR
  source_kind        VARCHAR NOT NULL      -- 'email' | 'manual'
  source_email_from  VARCHAR
  source_email_subject VARCHAR
  actor_did / org_did / at_did / created_at   -- ADR-0095

-- 状況ログ (append-only)
vertex_ses_jokyo (PK content-addressed: sha256(anken_vertex_id + jokyo + ts_ms))
  anken_vertex_id    VARCHAR NOT NULL FK
  jokyo              VARCHAR NOT NULL      -- 遷移後の状況
  jokyo_prev         VARCHAR              -- 遷移前の状況
  changed_by_did     VARCHAR              -- 操作者 DID
  notes              VARCHAR
  actor_did / org_did / at_did / created_at

-- クライアント (案件から名寄せ)
vertex_ses_client (PK content-addressed: sha256(actor_did + client_company_normalized))
  client_company_normalized VARCHAR NOT NULL
  display_name       VARCHAR
  anken_count        INTEGER
  actor_did / org_did / at_did / created_at

-- エンジニア候補マッピング
vertex_ses_engineer (PK content-addressed: sha256(actor_did + engineer_name_normalized))
  engineer_name_normalized VARCHAR NOT NULL
  display_name       VARCHAR
  actor_did / org_did / at_did / created_at

-- LangGraph run log
vertex_ses_run (PK = run_id = thread_id)
  anken_vertex_id    VARCHAR
  jokyo_vertex_id    VARCHAR
  source_kind        VARCHAR
  status             VARCHAR NOT NULL
  current_node       VARCHAR
  error_text         VARCHAR
  model_ids_json     VARCHAR              -- JSON array
  tokens_total       INTEGER
  started_at         TIMESTAMP
  finished_at        TIMESTAMP
  actor_did / org_did / at_did / created_at

-- エッジ
edge_ses_anken_client
  src_vid (anken) → dst_vid (client)
  actor_did / created_at

edge_ses_anken_engineer
  src_vid (anken) → dst_vid (engineer)
  is_primary         BOOLEAN
  actor_did / created_at

-- MV
mv_ses_anken_latest_jokyo
  -- SELECT DISTINCT ON (anken_vertex_id) ORDER BY created_at DESC
  -- 全案件の最新状況を返す (<5 秒リフレッシュ)

mv_ses_anken_active
  -- WHERE jokyo_current IN ('提案中','選考中','契約','稼働中')
  -- AND created_at > now() - INTERVAL '180 days'
  -- アクティブ案件のみ
```

### XRPC surface (6 lexicon)

| NSID | kind | 用途 |
|---|---|---|
| `com.etzhayyim.apps.ses.ingestAnken` | procedure | email 本文 or raw_text を投入 → run_id を返す |
| `com.etzhayyim.apps.ses.updateJokyo` | procedure | 既存案件の状況を手動更新 |
| `com.etzhayyim.apps.ses.getAnken` | query | anken_id → 案件詳細 + 状況ログ |
| `com.etzhayyim.apps.ses.listAnken` | query | actor scope の案件一覧 (status filter 付き) |
| `com.etzhayyim.apps.ses.listJokyo` | query | anken_id の状況遷移ログ全件 |
| `com.etzhayyim.apps.ses.coverage` | query | health snapshot (案件数 / 状況別集計 / 直近 24h delta) |

### CF Worker scaffold

```
60-apps/etzhayyim-project-ses/
├─ magatama.jsonld          T3 dispatcher actor
├─ wrangler.jsonc           ses.etzhayyim.com/* + PDS_SERVICE / AUTHN_SERVICE binding (HYPERDRIVE なし)
├─ package.json
├─ tsconfig.json
├─ CLAUDE.md
└─ src/
   ├─ app.ts                Hono entry + auth middleware + 6 NSID route
   └─ dispatcher.ts         HMAC 署名 + caller context header 注入
```

### LangGraph Server (K8s)

```
20-actors/magatama/py/src/pymagatama/ses/
├─ __init__.py
├─ state.py              SesIngestState + AnkenExtraction (Pydantic v2); source_kind includes 'email_cron'
├─ graph.py              6-node StateGraph(SesIngestState)
├─ extractor.py          Anthropic structured output で AnkenExtraction 生成
├─ classifier.py         既存案件との照合 (SQL SELECT + LLM confidence)
├─ jokyo.py              状況遷移バリデーション + append
├─ persistence.py        asyncpg INSERT (5 vertex + 2 edge)
├─ outlook_pull.py       Graph API client_credentials token + differential fetch
│                        (vertex_m365_sync_state cursor, vertex_id=sha256(upn|data_kind))
│                        + HTML strip + SES LangGraph ainvoke per message (Phase 3)
│                        + delete-after-ingest: DELETE /users/{upn}/messages/{id}
│                        on success path only; failure is warn-only (Phase 5)
├─ cron_main.py          CronJob entrypoint: python -m pymagatama.ses.cron_main (Phase 3)
└─ server.py             Granian-ready FastAPI + ingestAnken / updateJokyo endpoint
                         + POST /cron/outlook-pull (Phase 3 manual trigger)
                         + POST /mcp (JSON-RPC 2.0 — listAnken / getAnken / listJokyo, Phase 4)
                         + /health returns phase:'3' + m365_creds_configured
```

### AppView (Phase 4)

```
60-apps/etzhayyim-project-ses/
├─ wrangler.jsonc          SES_MCP_URL = "" (set to ses-api.etzhayyim.com after tunnel infra)
└─ svelte/src/
   ├─ lib/
   │  ├─ contracts/ses-mcp.ts     SES_MCP_TOOLS const + SesMcpToolName + I/O types
   │  └─ server/mcp.ts            callSesMcpTool() — JSON-RPC 2.0 → /mcp
   └─ routes/
      ├─ anken/
      │  ├─ +page.server.ts       SSR load: listAnken (jokyo filter, pagination)
      │  └─ +page.svelte          案件一覧 dark-theme table + jokyo badge
      └─ anken/[id]/
         ├─ +page.server.ts       SSR load: getAnken (detail + jokyo log)
         └─ +page.svelte          案件詳細 + 状況遷移タイムライン
```

**Routing note**: `ses-langgraph` は ClusterIP のみ。AppView が live になるには Cloudflare Tunnel ingress rule `ses-api.etzhayyim.com → ses-langgraph.mitama-udf.svc:8000` + DNS CNAME が必要。`SES_MCP_URL` 未設定時は `/anken` が 503 エラーバナーを表示（AppView 自体は起動可）。

Standalone K8s manifests: `50-infra/k8s/lg-ses/` (ServiceAccount + Deployment + Service + CronJob)
ClusterIP: `lg-ses.mitama-udf.svc.cluster.local:8000`
Image: `ghcr.io/etzhayyim/lg-ses:{version}-amd64` (Dockerfile: `20-actors/magatama/py/Dockerfile.ses`)
Helm release (legacy): `50-infra/vultr/mitama-ses-pool/` (superseded by standalone manifests)

### Forbidden patterns

| 禁止 | 代替 |
|---|---|
| CF Worker で asyncpg / SQLAlchemy を直接 import | LangGraph Server (mitama-ses-pool) 経由のみ |
| `env.HYPERDRIVE` binding を wrangler.jsonc に追加 | ADR-2605111200 — Worker は RW 接続なし |
| `sdk.pds.createRecord` / `sdk.pds.dispatch` で `com.etzhayyim.apps.ses.*` 書込 | asyncpg INSERT のみ (non-federable) |
| LLM model 名ハードコード | `resolveModelId()` / `MURAKUMO_DEFAULT_MODEL` |
| 状況の上書き (UPDATE) | append-only INSERT のみ (delete-then-insert も禁止) |
| `jokyo` に float 型フィールドを使う | AT Protocol Lexicon 制約 — 単価は `integer` (円単位) |
| `.onConflict()` / `ON CONFLICT` | PK content-addressed なので不要。重複は同一 hash = 冪等 |
| 終了・見送り・中途終了からの状況遷移 | forbidden 遷移 → `jokyo_skipped=true` で静かにスキップ |

## Rationale

### email → 案件 を LLM structured output で抽出する理由

SES 案件メールは送信元・フォーマットが多様（人材会社、直接クライアント、社内転送）。正規表現や固定テンプレートでは抽出率が低い。Anthropic structured output（`AnkenExtraction`）を使えば:
- 多様なフォーマットに対応
- `confidence` フィールドで不確実な抽出を後処理で弾ける
- `rationale` で抽出根拠をトレース可能

### 状況を append-only log で保持する理由

UPDATE による上書きはデータの鮮度と来歴を失う。案件の状況遷移（特に「見送り」「中途終了」の経緯）はビジネス判断の根拠になるため全履歴を保持する。MV `mv_ses_anken_latest_jokyo` で最新状況を <5 秒で提供できるため、UI 側は append-only であることを意識しなくてよい。

### LangGraph Server を選ぶ理由

intra-job で LLM call が ≥2 (classifier + extractor)、かつ `update_jokyo` の forbidden 遷移スキップロジックが StateGraph の conditional edge で自然に表現できる。BPMN-as-actor だと分岐が冗長になり、状況遷移バリデーションが compensation task で書きにくい。

## Exceptions

- **[Phase 3 完了 2026-05-14]** `source_kind='email_cron'` を `state.py` の Literal に追加済み。`outlook_pull.py` で Graph API client_credentials + differential fetch (cursor = `vertex_m365_sync_state`, `vertex_id=sha256(upn|data_kind)[:16]`)。CronJob `ses-outlook-cron` (*/15 Asia/Tokyo, concurrencyPolicy: Forbid) が `mitama-udf` namespace に稼働。
- **[Phase 4 コード完了 2026-05-14]** `server.py` に `POST /mcp` 追加 (version 0.3.0)。3 MCP tools (listAnken / getAnken / listJokyo)、`sync_cursor()` + `asyncio.to_thread()`、LIMIT/OFFSET インライン展開、`jokyo_current` は correlated subquery (`mv_ses_anken_latest_jokyo` MV 依存なし)。`jokyo_prev` 列は `vertex_ses_jokyo` に存在しないため `None` を返す（schema gap、Phase B-2 以降の対処対象）。Svelte AppView `/anken` + `/anken/[id]` route 実装済み。**live 化には Cloudflare Tunnel ingress rule `ses-api.etzhayyim.com → ses-langgraph.mitama-udf.svc:8000` + DNS CNAME + `SES_MCP_URL` 設定 + image rebuild + helm upgrade が必要**。
- **[Phase 5 完了 2026-05-19]** `outlook_pull.py` に `_delete_message()` 追加 — 成功パスのみ `DELETE /users/{upn}/messages/{id}` (Graph API)。失敗は warning ログで非 fatal (cursor は前進)。戻り値に `deleted` カウンタ追加。**Mail.ReadWrite** application permission が Azure AD 側で必要 (Mail.Read のみだと 403、warn で無視される)。`Dockerfile.ses` 新規作成。`deployment.yaml`: image tag `0.3.0` → `0.4.0-amd64`、env var 名を `M365_*` → `AZURE_*` に修正 (server.py は `AZURE_TENANT_ID/CLIENT_ID/CLIENT_SECRET` を読む)。`cronjob.yaml`: `suspend: true` → `suspend: false` で 15 分 cron 常駐開始。`ghcr.io/etzhayyim/lg-ses:0.4.0-amd64` build 済み (remote BuildKit etzhayyim-vke-local)。health: `{m365_creds_configured:true, phase:'3'}`。
- エンジニアマッチング推薦を Phase B で追加する場合は `edge_ses_anken_engineer` の `confidence` 列を追記し、別 ADR を参照させる

## Migration plan

| Phase | scope | trigger | status |
|---|---|---|---|
| **Phase 0 — 本 ADR (contract 確定)** | doc + registry 登録のみ | 本 PR マージ | **done** |
| Phase 1 — Foundation | 5 vertex + 2 edge + 2 MV migration / 6 lexicon JSON / CF Worker scaffold / state.py + graph.py 骨組み | schema migration green | **done** |
| Phase 2 — Live extraction | extractor.py + classifier.py + persistence.py 実装 + Helm `mitama-ses-pool` deploy | email ingest → 案件 1 件着地 | **done** |
| Phase 3 — Outlook cron pull | outlook_pull.py + cron_main.py + ses-outlook-cron CronJob + image `ses-phase3-202605141100-amd64` | 2026-05-14 — helm upgrade revision 3 | **done** |
| Phase 3B — checkpointer + confidence | RisingWaveCheckpointSaver 配線 (SES_CHECKPOINTER=on) + edge_ses_anken_engineer.confidence FLOAT + image `ses-phase3b-202605141400-amd64` | 2026-05-14 — helm upgrade revision 4 | **done** |
| Phase B-2 — embedding skill match | vertex_ses_engineer_skill 新設 + engineer embedding 生成 + skill overlap similarity score → `confidence` 上書き | 任意実施 | pending |
| **Phase 4 — AppView UI + /mcp endpoint** | server.py POST /mcp (listAnken/getAnken/listJokyo) + Svelte /anken + /anken/[id] + callSesMcpTool() + SES_MCP_URL | 2026-05-14 — code done; live requires tunnel infra | **done (pending tunnel)** |
| **Phase 5 — delete-after-ingest + CronJob 常駐** | `_delete_message()` in outlook_pull.py (Mail.ReadWrite required) + `Dockerfile.ses` 新規 + deployment.yaml env var fix (M365_* → AZURE_*) + `suspend: false` + image `0.4.0-amd64` | 2026-05-19 — deployed, CronJob running | **done** |

## References

- ADR-2605080600 (LangGraph Server + Granian L3 Runtime)
- ADR-2605080000 (Distributed Cognitive Actor System)
- ADR-2605080200 (Pydantic v2 L6 Validation Contract)
- ADR-2605080300 (SQLAlchemy Core Usage Contract)
- ADR-2604282300 (CF Worker = Edge Layer)
- ADR-2605111200 (CF Worker Edge-Only — no RW connection)
- ADR-2604251830 (Shannon-Optimal 8-Layer Architecture)
- ADR-0095 (3-Layer Identity + RW canonical columns)
- ADR-0018 (PII Tier3 Cohort-First)
- ADR-0041 (Content-addressed PK)
- ADR-2605080800 (manimani LangGraph User Intake — 同型 T3 actor の先行例)
- ADR-0032 (Gmail Direct Ingest — email ingest パターンの先行例)
