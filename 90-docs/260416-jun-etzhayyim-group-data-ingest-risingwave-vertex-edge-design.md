---
id: jun-etzhayyim-group-data-ingest-kotoba-vertex-edge-design-260416
title: "jun@etzhayyim.com 全量取り込み設計 — Kotoba/Datomic / Vertex / Edge"
status: active
doc_type: explanation
topic: personal-workspace-ingest
authoritative: true
last_verified: 2026-04-16
authoritative_for:
  - jun@etzhayyim.com の非 Microsoft 系データ取り込み設計
  - Kotoba/Datomic 上の Vertex / Edge モデル
  - full backfill + incremental sync + cursor 運用
related:
  - adr-0018-pii-tier3-cohort-first
  - adr-0019-atproto-native-identifier-topology
  - kagami-p10v2-graphar-native-design
supersedes: []
superseded_by: []
---

# Goal

`jun@etzhayyim.com` に紐づく業務データを、Microsoft 取り込み済み前提で **追加ソースを統合**し、Kotoba/Datomic 上で横断検索・時系列分析・エージェント利用可能な形にする。

# Scope

- **In**:
  - Google Workspace (Gmail / Calendar / Drive / People)
  - 監査用 ingest job / cursor / lag 可視化
  - Vertex / Edge テーブル設計と MV 設計
- **Out**:
  - Microsoft 側の再実装
  - UI 実装
  - 外部 SaaS 個別コネクタ (Notion/Slack 等) の本実装

# Executive Summary

- 取り込みは **2 段階**: `raw append-only` → `normalized vertex/edge upsert`。
- 一意キーは `provider + tenant + object_type + object_id (+ version)` で統一。
- Microsoft と Google を同一グラフに載せるため、`vertex_workspace_*` / `edge_workspace_*` の provider-neutral モデルを採用。
- 増分同期は cursor (`historyId` / `syncToken` / `deltaLink`) を `vertex_workspace_cursor` に保存。

# Decision

## 1) Ingest Topology

```
Google APIs (Gmail/Calendar/Drive/People)
  → adapter worker (OAuth2 refresh token)
    → vertex_workspace_raw_event (append-only)
      → normalizer (idempotent)
        → vertex_workspace_* / edge_workspace_*
          → mv_workspace_* (lag/activity/actionability)
```

## 2) Vertex Schema (Kotoba/Datomic)

### Core

- `vertex_workspace_account`
  - 1 row = 1 account mapping (`jun@etzhayyim.com` + provider tenant)
- `vertex_workspace_cursor`
  - source ごとの増分 cursor / checkpoint
- `vertex_workspace_raw_event`
  - source payload 原本 (for replay / audit)
- `vertex_workspace_sync_job`
  - 実行単位の成功/失敗/件数

### Business Objects

- `vertex_workspace_message`
  - mail message (Microsoft/Google 共通)
- `vertex_workspace_thread`
  - conversation/thread
- `vertex_workspace_event`
  - calendar event
- `vertex_workspace_contact`
  - people/contact
- `vertex_workspace_file`
  - drive file/folder
- `vertex_workspace_file_revision`
  - file version history

## 3) Edge Schema (Kotoba/Datomic)

- `edge_workspace_account_has_message` (`account → message`)
- `edge_workspace_message_in_thread` (`message → thread`)
- `edge_workspace_message_from_contact` (`message → contact`)
- `edge_workspace_message_to_contact` (`message → contact`)
- `edge_workspace_account_has_event` (`account → event`)
- `edge_workspace_event_attendee_contact` (`event → contact`)
- `edge_workspace_account_has_file` (`account → file`)
- `edge_workspace_file_shared_with_contact` (`file → contact`)
- `edge_workspace_file_has_revision` (`file → file_revision`)

## 4) Identifier Rules

- `vertex_id`:
  - `ws:{provider}:{tenant}:{type}:{native_id}`
  - 例: `ws:google:etzhayyim.com:message:18c9f...`
- `src_vid/dst_vid` は上記 `vertex_id` をそのまま利用。
- 同一実体の provider 跨ぎ統合は `edge_workspace_same_as` (Phase 2) で追加。

## 5) Materialized Views

- `mv_workspace_sync_lag`
  - source ごとの最終成功時刻、遅延秒、失敗連続回数
- `mv_workspace_activity_daily`
  - 日次アクティビティ (mail/event/file) 集約
- `mv_workspace_action_queue`
  - unread + 近日 event + 未返信 thread の action 候補
- `mv_workspace_contact_strength`
  - 連絡頻度から contact 強度を算出

## 6) Cursor Strategy (Google Workspace)

`jun@etzhayyim.com` の Google 側は source ごとに cursor を分離する。

| source_kind | API / cursor | 保存先 | 失効時の扱い |
|---|---|---|---|
| `gmail` | `historyId` (users.history.list) | `vertex_workspace_cursor.cursor_token` | `404 historyId too old` で full resync |
| `gcal` | `syncToken` (events.list incremental) | 同上 | `410 Gone` で full resync |
| `gdrive` | `startPageToken` + `changes.list` pageToken | 同上 | token invalid で `changes.getStartPageToken` から再開 |
| `people` | `syncToken` (people.connections.list) | 同上 | `EXPIRED_SYNC_TOKEN` で full resync |

実装規約:

- `scope_key = "{provider}:{tenant}:{source_kind}:{account_id}"` を固定キーにして idempotent 更新。
- 1 job 成功ごとに `cursor_before/cursor_after` を `vertex_workspace_sync_job` に保存。
- cursor 更新は `rows_written > 0` だけでなく **API 呼び出し成功時**に進める (空差分でも進める)。
- `status='degraded'` を設定する条件:
  - 連続 3 回失敗
  - `last_success_at` が 30 分超過
  - token refresh 失敗

## 7) Microsoft ↔ Google same_as Rules

`edge_workspace_same_as` は段階的に確信度付きで生成する。

### Rule Set

1. **Message**
   - High confidence: `internet_message_id` 一致
   - Medium: `subject_normalized + sender_email + sent_at(±120s)` 一致
2. **Event**
   - High: `iCalUID` 一致
   - Medium: `organizer + start_at + end_at + title_normalized` 一致
3. **Contact**
   - High: primary email 完全一致
   - Medium: phone(E164) + display_name 正規化一致
4. **File**
   - High: `sha256/checksum + size_bytes` 一致
   - Medium: `name_normalized + modified_at(±300s) + owner_email` 一致

### Confidence Policy

- `confidence >= 0.98`: 自動リンク (`match_method='exact'`)
- `0.90 <= confidence < 0.98`: 自動リンク (`match_method='heuristic'`, `needs_review=true`)
- `< 0.90`: link 不作成、候補のみ `vertex_workspace_raw_event.props` に保持

### Invariants

- 同一 provider 内 (`google↔google`, `microsoft↔microsoft`) には `edge_workspace_same_as` を作らない。
- `src_vid < dst_vid` の lexical order を強制し重複 edge を防ぐ。
- `same_as` 作成時は `edge_id = "ws:same_as:{sha256(src_vid|dst_vid)}"`。

# Comparison

- **raw-only**: replay は簡単だが検索コストが高く、agent 利用に不向き。
- **normalized-only**: 障害時の再現性が低く、source 差分検証が難しい。
- **採用**: raw + normalized の二層。監査性と運用性の両立。

# Exceptions

- 添付ファイル本文は初期は保持しない (`metadata only`)。容量閾値を超える場合は object storage 参照へ逃がす。
- PII 高感度フィールド (電話番号/住所/自由入力メモ) は Tier 3 扱いで最小化・必要時のみ復号参照。

# Implementation Plan

1. Migration 追加 (`vertex_workspace_*`, `edge_workspace_*`, `mv_workspace_*`)
   - `20260416123000_workspace_ingest_vertices.ts`
   - `20260416123100_workspace_ingest_edges.ts`
   - `20260416123200_workspace_ingest_mvs.ts`
2. Google adapter で full backfill (`jun@etzhayyim.com`)
3. cursor 増分同期 (5-15 分周期)
4. Microsoft 既存データとの `same_as` 解決
5. action queue を projector / agent tool に接続

# Ops Notes

- Kubernetes リソースは `default` namespace 禁止。
- 推奨 namespace:
  - `external-adapter-prod` (adapter worker)
  - `external-adapter-stg` (staging)
  - `kotoba` (DB 本体)

# References

- `60-apps/etzhayyim-project-external-service-adapter/PROJECT.jsonld`
- `90-docs/adr/0018-pii-tier3-cohort-first.md`
- `90-docs/260407-kagami-p10v2-graphar-native-design.md`
