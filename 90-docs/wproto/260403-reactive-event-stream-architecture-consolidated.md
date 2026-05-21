---
id: 260403-reactive-event-stream-architecture-consolidated
title: "Reactive Event Stream Architecture (Consolidated)"
status: active
doc_type: explanation
topic: reactive-event-stream-architecture
authoritative: true
last_verified: 2026-04-03
authoritative_for:
  - reactive event stream architecture for app workloads on gftd
  - firehose to app processing and subscriber delivery model
  - no polling and no do queue baseline for reactive delivery
related:
  - wrpc-stream-native
  - w-protocol-at-superset
  - data-gateway-consolidation
supersedes:
  - news-wrpc-stream-reactive
  - reactive-observe-firehose
superseded_by: []
---

# Reactive Event Stream Architecture (Consolidated)

## Goal

アプリ配信を polling/batch 起点から、AT firehose + wRPC/SSE の event-driven 起点へ統一する。  
Write/read/stream の経路を重複なく整理し、Shannon 冗長を抑えた単一モデルに収束する。

## Scope

- `ai.gftd.apps.*` の reactive 配信設計
- input (firehose), processing (app worker), output (subscriber stream) の標準経路
- DO/Queue 非依存の運用基準

## Decision

1. Input は `com.atproto.sync.subscribeRepos` firehose を標準とする。
2. Write authority は PDS (`com.atproto.repo.*`) のみ。app query は service proxy へ委譲。
3. Processing は app worker の `handle-commit` で実行し、batch command は廃止する。
4. Subscriber delivery は wRPC stream を第一選択、互換クライアントには SSE を提供する。
5. durable path は Pipeline + B2 とし、DO/Queue は baseline から除外する。

## Unified Architecture

```
Write:
  Client
    -> PDS /xrpc/com.atproto.repo.createRecord
    -> Pipeline.send (durable)
    -> mergeRecord (instant projection)
    -> Firehose event

Process:
  App Worker handle-commit
    -> evaluate / transform / route
    -> optional ATPost (single write model)

Deliver:
  Subscriber
    -> invoke-stream (wRPC preferred) or SSE
    -> governance gate + audit
```

## Routing Baseline

| NSID | 処理主体 | 備考 |
|---|---|---|
| `com.atproto.repo.*` | PDS direct | write authority / canonical CRUD |
| `com.atproto.sync.*` | PDS direct | firehose/sync |
| `ai.gftd.apps.*` | service proxy -> app worker | domain query / view logic |
| `ai.gftd.{convo,signal,rtc,files}.*` | PDS direct | platform service |

## Stream Delivery Modes

| Mode | Payload | 用途 |
|---|---|---|
| `invalidate` | label + key | default, minimal transfer |
| `delta` | changed rows | optimized clients |
| `snapshot` | full rows | simple clients |

Default は `invalidate`。必要時のみ `delta`/`snapshot` を選択する。

## Reliability Baseline (No DO/Queue)

- Durable write: Pipeline + B2 flush
- Recovery: B2 replay on restart
- Connection state: in-memory registry + reconnect-driven re-subscribe
- Backpressure: wRPC credit flow control

## Migration Guidance

1. batch polling command を `handle-commit` に置換
2. duplicate write (`WRecord` + `ATPost`) を単一 write に統合
3. app query を PDS 内実装から service proxy 経路へ移動
4. subscriber API を stream-first (wRPC/SSE fallback) に変更

## Notes

- 本文書は以下を統合した正本:
  - `90-docs/260324-news-wrpc-stream-reactive-design.md`
  - `90-docs/260324-reactive-observe-firehose-design.md`
