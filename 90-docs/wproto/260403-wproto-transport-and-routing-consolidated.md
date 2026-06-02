---
id: 260403-wproto-transport-and-routing-consolidated
title: "W Protocol Transport and Routing (Consolidated)"
status: active
doc_type: explanation
topic: wproto-transport-routing
authoritative: true
last_verified: 2026-04-03
authoritative_for:
  - w protocol stream transport baseline
  - wit to transport binding generation policy
  - xrpc service-proxy routing boundary
related:
  - 260317-w-protocol-design
  - w-protocol-at-superset
supersedes:
  - wrpc-stream-native
  - 260324-source-graph-hybrid-design
  - xrpc-cqrs-service-proxy
superseded_by: []
---

# W Protocol Transport and Routing (Consolidated)

## Goal

W Protocol の transport/binding/routing を 1 つの正本に集約し、重複した設計ドキュメント更新を止める。

## Scope

- stream transport (`invoke-stream` / `handle-stream`)
- WIT から transport binding 生成
- XRPC routing 境界 (PDS direct vs service proxy)

## Decision

1. Stream transport は wRPC stream-native を標準とする。
2. binding は WIT を SSoT として自動生成する。
3. routing は `com.atproto.repo.*` を PDS direct、`com.etzhayyim.apps.*` を service proxy とする。

## Transport Baseline

- Internal: Workers RPC (0-hop)
- External: XRPC HTTP (`/xrpc/{NSID}`)
- Stream: credit-based backpressure
- Governance: host-side gate before dispatch

## Binding Baseline

- WIT interface から host/import/type binding を生成
- 手書き switch / string mapping は新規追加しない
- drift は生成物差分で検出する

## Routing Baseline

| Prefix | Path | Responsibility |
|---|---|---|
| `com.atproto.repo.*` | PDS direct | write authority / canonical CRUD |
| `com.atproto.sync.*` | PDS direct | sync and firehose |
| `app.bsky.*` | PDS direct (repo policy scope) | AT standard query surface |
| `com.etzhayyim.apps.*` | service proxy -> app worker | app domain query logic |

## Migration Rule

1. stream 処理は `invoke-stream` / `handle-stream` へ寄せる
2. transport mapping の手書き実装は generated binding に置換する
3. app query は PDS 内実装を避け service proxy 側へ移す

## Superseded Docs

以下は本書に統合済み。

- `90-docs/260323-wrpc-stream-native-design.md`
- `90-docs/260324-wrpc-wit-binding-generation-design.md`
- `90-docs/260324-xrpc-cqrs-service-proxy-design.md`
