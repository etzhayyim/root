---
id: adr-2605141900-mailer-gewp-implementation
title: "ADR-2605141900: mailer.etzhayyim.com — GEWP v1.0 Implementation"
status: accepted
doc_type: adr
topic: mailer-gewp-implementation
authoritative: true
last_verified: 2026-05-21
priority: 7.0
axis: architecture
weight: 0.70
priority_note: "mailer.etzhayyim.com (did:web:mailer.etzhayyim.com) を GEWP v1.0 Core Conformant + ext:atproto + ext:pregel にする実装 ADR (Phase 1-3 完了)"
authoritative_for:
  - mailer.etzhayyim.com の GEWP 送受信実装
  - pymagatama.gewp モジュール API
  - vertex_mailer_inbound_email / vertex_mailer_outbound_email の GEWP 列定義
  - Resend API を経由した GEWP 3-layer 送信方式
  - email-relay Worker の MIME 解析・attachment_json graph worker projection
  - mv_mailer_gewp_pending / mv_pregel_step_pending MV 定義
  - ext:pregel barrier (mv_pregel_step_pending の arrived_count == expected_count 判定)
depends_on:
  - adr-2605141800-etzhayyim-email-wire-protocol
  - adr-2605131800-pregel-triage-langgraph-email-intent-routing
  - adr-2605080000-distributed-cognitive-actor-system
related:
  - adr-0032-gmail-direct-ingest-yabai-classifier
---

# ADR-2605141900: mailer.etzhayyim.com — GEWP v1.0 Implementation

## Goal

`mailer.etzhayyim.com` (`did:web:mailer.etzhayyim.com`) を GEWP v1.0 **Core Conformant** + **ext:atproto** + **ext:pregel** として実装し、LLM agent 間・グループメール・人間とのメール通信を Pregel メッセージパッシングとして扱えるようにする。Phase 1–3 完了。

---

## Architecture

```
[送信側 agent / human]
  │
  ▼
send_gewp_message() / send_email()  (pymagatama.ingest.mailer)
  │
  ├─ pymagatama.gewp.compose_resend_payload()
  │    Layer 1: attachment  application/vnd.gewp+json  (canonical)
  │    Layer 2: <!-- GEWP:{base64url} --> in HTML body  (fallback)
  │    Layer 3: X-GEWP-* headers                        (hint)
  │
  ▼
Resend API  →  SMTP  →  受信者メールボックス

[受信側]
CF Email Routing → email-relay Worker
  → vertex_mailer_inbound_email (body_html / headers_json 保存)
  → parse_inbound_gewp()  (Layer 1 → Layer 2 → human.intent)
  → vertex_mailer_inbound_email.gewp_* 列を UPDATE
  → pregel_triage pipeline が gewp_thread_id でルーティング
```

---

## Resend API GEWP Mapping

Resend は raw MIME を直接制御できないため、以下の代替手段で 3-layer を実現する:

| GEWP Layer | Resend フィールド | 生存率 |
|---|---|---|
| Layer 1 (canonical) | `attachments[{filename:"gewp.json", content_type:"application/vnd.gewp+json"}]` | HIGH (添付ファイルは保存される) |
| Layer 2 (fallback) | `html` body 末尾の `<!-- GEWP:{base64url} -->` コメント | MEDIUM |
| Layer 3 (hint) | `headers: {"X-GEWP-Thread": ..., "X-GEWP-Step": ..., "X-GEWP-Type": ...}` | LOW (転送で消える) |

---

## 新規モジュール: `pymagatama.gewp`

| 関数 / クラス | 役割 |
|---|---|
| `GewpMessage` | GEWP ペイロードの dataclass |
| `GewpThread` / `GewpActor` / `GewpRecipient` | サブ dataclass |
| `new_message()` | GewpMessage 生成ヘルパー |
| `new_thread_id()` | `thd_{10hex}` 形式の thread ID 生成 |
| `to_dict()` / `to_json()` | シリアライズ |
| `compose_resend_payload()` | Resend API payload (3-layer 込み) を生成 |
| `parse_from_email()` | 受信メールから GEWP を抽出 (Layer 1 → Layer 2 → None) |

---

## `mailer.py` 変更点

### 追加: `send_gewp_message()`

GEWP 送信の専用関数。`gewp_thread_id` / `gewp_step` / `gewp_payload` を受け取り、3-layer MIME を Resend 経由で送信する。

### 追加: `parse_inbound_gewp()`

保存済み `vertex_mailer_inbound_email` レコードから GEWP を抽出し、`gewp_*` 列を UPDATE する。人間メールは `{"type": "human.intent"}` を返す。

### 変更: `_record_outbound()`

`gewp_thread_id` / `gewp_step` を `vertex_mailer_outbound_email` に記録。

---

## DB スキーマ変更

### `vertex_mailer_inbound_email` (追加列)

| 列 | 型 | 意味 |
|---|---|---|
| `gewp_thread_id` | VARCHAR | Pregel partition key。NULL = 非 GEWP メール |
| `gewp_step` | BIGINT | Pregel superstep counter |
| `gewp_type` | VARCHAR | pregel.message \| pregel.barrier \| human.intent |
| `gewp_performative` | VARCHAR | FIPA-ACL performative |

### `vertex_mailer_outbound_email` (追加列)

| 列 | 型 | 意味 |
|---|---|---|
| `gewp_thread_id` | VARCHAR | 送信した GEWP の thread ID |
| `gewp_step` | BIGINT | 送信した GEWP の step |

**Migration**: `20260514_0003_gewp_mailer_columns.py` (Alembic) + `20260514090000_gewp_mailer_columns.up.sql`

---

## Conformance レベル

| レベル | 実装状況 |
|---|---|
| **Core Conformant** | ✅ Layer 1 MIME part 送受信、Core Schema REQUIRED フィールド充足 |
| **Layer-2 Conformant** | ✅ HTML comment fallback の読み書き (email-relay MIME parser Phase 2 で完全対応) |
| **ext:pregel** | ⏳ barrier semantics は Phase 3 実装 (mv_pregel_step_pending) |
| **ext:atproto** | ✅ `sender.did` / `sender.handle` に AT Protocol DID を設定 |
| **ext:langgraph** | ✅ pregel_triage check_gewp/dispatch_gewp ノードで GEWP ルーティング完了 |

---

## Forbidden Patterns

| 禁止 | 理由 |
|---|---|
| `X-GEWP-*` ヘッダーのみで GEWP を受信したと判断する | 転送で消えるため。Layer 1 attachment が必須 |
| `<script type="application/ld+json">` を Layer 2 に使う | Gmail/Outlook が無条件削除 |
| `send_gewp_message()` で `gewp_payload=None` のまま agent 間通信する | payload 空は human.intent と区別できない |
| LLM model 名をハードコードする (`sender_model` フィールド) | `resolveModelId()` / `MURAKUMO_DEFAULT_MODEL` を使う |

---

## Phase 2 完了 (2026-05-14)

| 項目 | 実装ファイル | 内容 |
|---|---|---|
| email-relay Worker MIME 解析 | `50-infra/cloudflare/workers/email-relay/worker.ts` | `extractGewpAndHtml()` — Layer 1 attachment + Layer 2 HTML comment + HTML body 抽出。`attachmentJson` / `gewpLayer` / `bodyHtml` を PDS レコードに追加 (Phase 3 で `gewpPayloadJson` → `attachmentJson` にリネーム済) |
| attachment_json 列 | `20260514110000_vertex_mailer_attachment_json.up.sql` + alembic `20260514_0004` | `vertex_mailer_inbound_email.attachment_json VARCHAR` 追加 |
| GEWP pending MV | `20260514100000_mv_mailer_gewp_pending.up.sql` | `mv_mailer_gewp_pending` — `gewp_thread_id IS NOT NULL AND gewp_step IS NOT NULL` でフィルタ |
| pregel GEWP bridge | `pymagatama/pregel/graph.py` | `check_gewp` + `dispatch_gewp` ノード、`_route_after_parse()` ルーター。`parse_email → check_gewp → [GEWP: dispatch_gewp → END / human: classify_intent → ...]` |

## Phase 3 完了 (2026-05-14)

| 項目 | 実装ファイル | 内容 |
|---|---|---|
| graph worker projection fix | `50-infra/cloudflare/workers/email-relay/worker.ts` | PDS レコードフィールド `gewpPayloadJson` → `attachmentJson` にリネーム。`camelToSnake("attachmentJson")` = `attachment_json` で graph worker convention が正しく列へ projection する |
| ext:pregel barrier MV | `20260514160000_mv_pregel_step_pending.up.sql` + alembic `20260514_0005` | `mv_pregel_step_pending` — `(gewp_thread_id, gewp_step)` ごとに `pregel.barrier` メッセージ到着数を集計。`arrived_count == expected_count` でバリア充足判定 |

## Runtime Operations Note (2026-05-14)

`mailer.etzhayyim.com` の API surface (`/api/stats`, `/api/emails`) は
`DISPATCHER_URL` 経由で dispatcher XRPC を読む。2026-05-14 の Cloudflare
502 は mailer / GEWP 実装の不具合ではなく、`dispatcher.etzhayyim.com` の
cloudflared origin pod が `NotReady` node 上に残ったことによる ingress 障害だった。

復旧手順は ADR-2605111200 の Operational Prerequisites #8 に従う:
`cloudflared-bpmn-dispatcher` を安定 node pool (`osm-ingest-pool`) に pin し、
必要な taint を toleration する。復旧確認は以下を最低条件にする。

| Probe | Expected |
|---|---|
| `GET https://dispatcher.etzhayyim.com/health` | `200 {"status":"ok"}` |
| `GET https://dispatcher.etzhayyim.com/xrpc/com.etzhayyim.apps.mailer.stats` without trust header | `401 missing x-internal-trust header` |
| `GET https://mailer.etzhayyim.com/api/stats` | `200` |
| `GET https://mailer.etzhayyim.com/api/emails?limit=1` | `200` |

---

## Conformance レベル (最終)

| レベル | 実装状況 |
|---|---|
| **Core Conformant** | ✅ Layer 1 MIME part 送受信、Core Schema REQUIRED フィールド充足 |
| **Layer-2 Conformant** | ✅ HTML comment fallback の読み書き |
| **ext:pregel** | ✅ barrier semantics: `mv_pregel_step_pending` で step ごとの全頂点到着追跡 |
| **ext:atproto** | ✅ `sender.did` / `sender.handle` に AT Protocol DID を設定 |
| **ext:langgraph** | ✅ pregel_triage check_gewp/dispatch_gewp ノードで GEWP ルーティング完了 |

---

## Phase 4 / Ops Fix (2026-05-21)

| 項目 | 内容 |
|---|---|
| `RESEND_API_KEY` 未注入 | `bpmn-dispatcher` pod に `RESEND_API_KEY` が設定されておらず `sendEmail` が全件 `"RESEND_API_KEY not configured"` で失敗していた |
| 修正 1: k8s Secret 作成 | `kubectl create secret generic mailer-resend-creds -n mitama-udf --from-literal=RESEND_API_KEY=...` (Keychain `etzhayyim.resend/API_KEY` から取得) |
| 修正 2: Deployment patch | `bpmn-dispatcher` に `secretKeyRef: {name: mailer-resend-creds, key: RESEND_API_KEY, optional: true}` を追加し rollout |
| `vertex_mailer_outbound_email` schema 未適用 | `20260514090000_gewp_mailer_columns.up.sql` が live RisingWave に未適用のため `outboundRecordError: Column gewp_thread_id not found` が発生していた |
| 修正 3: schema migration 手動適用 | `ALTER TABLE vertex_mailer_outbound_email ADD COLUMN IF NOT EXISTS gewp_thread_id VARCHAR` + `ADD COLUMN IF NOT EXISTS gewp_step BIGINT` を RisingWave に直接実行 |
| e2e 確認 | `sendEmail` → `messageId: cb014970-...` 配信成功、`outboundRecordError` 消滅 |

---

## References

- ADR-2605141800 (GEWP v1.0 open standard)
- ADR-2605131800 (pregel triage LangGraph)
- `20-actors/magatama/py/src/pymagatama/gewp.py`
- `20-actors/magatama/py/src/pymagatama/ingest/mailer.py`
- `20-actors/magatama/py/alembic/versions/20260514_0003_gewp_mailer_columns.py`
- `20-actors/magatama/py/alembic/versions/20260514_0005_mv_pregel_step_pending.py`
- `30-graph/graph-schema/sql_migrations/20260514090000_gewp_mailer_columns.up.sql`
- `30-graph/graph-schema/sql_migrations/20260514160000_mv_pregel_step_pending.up.sql`
