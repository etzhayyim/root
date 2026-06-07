---
id: 260320-kotodama-cloudflare-worker-rpc-optimization
title: Kotodama Cloudflare Worker RPC Optimization
status: active
doc_type: reference
topic: worker-rpc-transport
authoritative: true
last_verified: 2026-03-20
authoritative_for:
  - worker internal transport selection between rpc and http service bindings
related:
  - 260320-kotodama-cloudflare-containers-evaluation
  - 260320-kotodama-cloudflare-containers-evaluation
supersedes: []
superseded_by: []
---

# Kotodama Cloudflare Worker RPC Optimization

## Purpose

`kotodama` を Cloudflare Worker backend で最適化する際、**Service Binding** と **Workers RPC** をどう使い分けるかを整理する。

Worker backend を `kotodama` の default runtime とし、Container を fallback とする評価は
[90-docs/260320-kotodama-cloudflare-containers-evaluation.md](/Users/junkawasaki/etzhayyim/etzhayyim-root/90-docs/260320-kotodama-cloudflare-containers-evaluation.md)
を参照。

ここでいう Workers RPC は、Cloudflare の `WorkerEntrypoint` / `RpcTarget` ベースの RPC であり、内部実装は Cap'n Proto RPC 系だが、利用者は JavaScript/TypeScript メソッド呼び出しとして扱う。

## Verified Platform Facts

2026-03-20 時点で確認した Cloudflare の公式情報に基づく。

- Service bindings は Worker 間通信の基盤であり、RPC と HTTP の 2 つの呼び方を提供する
- Cloudflare は RPC を「大半の use case に推奨」としている
- Service bindings はデフォルトで同一サーバ・同一スレッド実行になりうる
- Workers RPC は JavaScript-native RPC で、Cloudflare 公式 docs では `WorkerEntrypoint` / `RpcTarget` を使う
- Workers RPC は Cap'n Proto RPC ベース
- Workers RPC は promise pipelining を持つ
- Workers RPC は Smart Placement を現在は無視する
- Workers RPC には 32 MiB serialized limit がある
- RPC stub は lifecycle/disposal を考慮する必要がある
- **Workers RPC は Worker (V8 isolate) 間専用。Cloudflare Containers (独立 Linux sandbox, gVisor) では使用不可** — Container は V8 isolate 外で動作するため、Cap'n Proto zero-copy (16B overhead, same-thread/same-server) は構造的に不能。Worker → Container 通信は HTTP fetch (container binding, ~1-5ms same-colo) が唯一の手段

## Design Decision

Cloudflare Worker backend では、次の原則を採用する。

### 1. Service Binding is the transport envelope

Worker 間接続の canonical transport は Service Binding とする。

- private internal connectivity
- public URL 不要
- per-binding permission model
- local-first execution

### 2. Workers RPC is the default control-plane call path

次の条件では Workers RPC を第一選択にする。

- payload が小さい
- typed method call が自然
- app-to-app / service-to-service の command/query が主体
- 低レイテンシが重要
- same-account private worker call である

例:

- auth context 解決
- capability check
- metadata lookup
- lightweight graph query orchestration
- miniapp/backend 間の typed internal API

### 3. HTTP over Service Binding is the data-plane / streaming path

次の条件では `binding.fetch()` を使う。

- stream が必要
- large payload の可能性がある
- HTTP semantics がそのまま価値を持つ
- opaque proxy として扱いたい
- 既存 fetch/Request/Response path を再利用したい

例:

- file/blob transfer
- large query result
- static asset access
- protocol-preserving internal proxy
- compatibility path for non-RPC services

## Why This Split Fits Kotodama

`kotodama` は guest から見れば capability-based runtime であり、Worker backend ではこれを TypeScript host layer が受ける。

このとき:

- control-plane capability call は RPC に向く
- data-plane capability call は HTTP/fetch に向く

よって Worker backend の host adapter は、`kotodama capability` ごとに default transport を持つべきである。

## Capability Routing Policy

| Capability category | Default Worker transport | Notes |
|---|---|---|
| authn / authz | Workers RPC | 小 payload、typed call 向き |
| identity / capability / governance | Workers RPC | same-thread locality の恩恵が大きい |
| small graph metadata query | Workers RPC | orchestrator call 向き |
| large graph result / export | HTTP Service Binding | 32 MiB limit と streaming を考慮 |
| messaging command dispatch | Workers RPC | typed envelope dispatch 向き |
| blob / asset / static file | HTTP Service Binding | `Request/Response` と stream が自然 |
| browser/rendering proxy | HTTP Service Binding | protocol-preserving path を維持 |
| telemetry emit | Workers RPC | 軽量 fire-and-forget に向くが `waitUntil` 設計必須 |

## Runtime Architecture

```text
MiniApp / Front Door Worker
  -> Service Binding
     -> Backend Worker
        -> WorkerEntrypoint RPC methods for control plane
        -> fetch() endpoints for data plane / streaming
        -> TypeScript kotodama host adapter
           -> capability registry
           -> generated JS glue
           -> component.wasm
```

## Named WorkerEntrypoints

Worker backend の control-plane surface は named `WorkerEntrypoint` に分割する。

初期レイアウト:

- `CoreEntrypoint`
- `GraphEntrypoint`
- `MessagingEntrypoint`

将来拡張候補:

- `AuthEntrypoint`
- `GovernanceEntrypoint`
- `StorageEntrypoint`
- `TelemetryEntrypoint`
- `ExtensionEntrypoint`

初期 3 分割の理由は、最小コストで次を切り分けられるためである。

- generic core helpers
- graph/cypher control plane
- messaging / W Protocol / extension messaging plane

registry には各 capability interface に対して次を保持する。

- `worker_transport`
- `worker_entrypoint`

これをもとに Worker host table と TS host manifest を生成または検証する。

## Relationship to Shared Kotodama Design

Worker backend は dual-backend design の WorkerExecutor を担う。

- shared: `component.wasm`, WIT contract, capability registry, conformance
- Worker-specific: `WorkerEntrypoint`, Service Binding, JS glue, TypeScript host adapter

このため、Worker backend 最適化では **registry-driven host table** を使う (TS native default。historical sandbox runtime では wasmtime Linker 相当)。

## Current Repository Direction

現時点で repository には次の土台が入っている。

- shared capability registry: `40-engine/kotoba/crates/kotoba-kotodama/kotodama-capability-registry`
- Wasmtime linker が registry を参照
- Cloudflare Worker crate が registry snapshot を JSON で返せる
- Worker 側に `WorkerComponentState` / `WorkerHostTable` の skeleton がある

これにより、次の段階として TypeScript host generator を入れられる状態になっている。

## Optimization Plan

## Phase 1: Registry-Driven Worker Host Table

Worker host adapter は capability registry を入力として、`WorkerEntrypoint` method surface と `fetch()` route surface を生成または検証する。

必要な出力:

- core capability host table
- extension capability host table
- control-plane RPC map
- data-plane HTTP map

## Phase 2: Named Entrypoints by Capability Domain

Cloudflare は named `WorkerEntrypoint` をサポートする。これを利用して capability domain ごとに entrypoint を分ける。

例:

- `CoreEntrypoint`
- `MessagingEntrypoint`
- `GraphEntrypoint`
- `GovernanceEntrypoint`

利点:

- permission boundary を分けやすい
- API surface を縮小できる
- TypeScript `Service<...>` を capability domain ごとに生成できる

## Phase 3: Promise Pipelining for Chained Control Calls

Workers RPC は promise pipelining を持つため、次のような chain を 1 round trip 寄りにできる。

- auth resolve -> principal object -> capability check
- graph service -> handle object -> follow-up method

この性質を利用して、Worker backend の control-plane call は object-returning RPC API と相性がよい。

ただし:

- object lifecycle と stub disposal を管理する
- 長寿命 stub を持ちっぱなしにしない

## Phase 4: Explicit Stub Disposal

Cloudflare docs に従い、RPC stub は `using` か明示 dispose を前提にする。

`kotodama` 側ルール:

- request scope を超える stub 保持を禁止
- TS host adapter が disposable object を返す場合は wrapper で disposal policy を統一
- conformance test で resource leak を検知する

## Phase 5: Keep Streaming on HTTP

RPC は 32 MiB serialized limit があるため、次は fetch path に残す。

- large Arrow/JSON export
- blob transfer
- static asset return
- browser/rendering output

つまり「全部 RPC 化」はしない。

## Concrete Policy for `kotodama`

### Default rule

- internal typed call: Workers RPC
- stream or large payload: HTTP Service Binding

### YATA / graph path

Worker backend の graph access は 2 層化する。

- small control/query dispatch: RPC
- bulk result / export / scan: HTTP

### Messaging path

- envelope dispatch / metadata: RPC
- attachment/blob body: HTTP or object storage binding

### MiniApp backend calls

MiniApp -> backend Worker は、Connect facade 経由を維持しつつ、その内部 fan-out では Workers RPC を優先する。

## What Must Not Be Done

- Worker backend に Wasmtime-specific assumptions を持ち込まない
- all capability traffic を HTTP に寄せて typed internal API を失わない
- all capability traffic を RPC に寄せて large payload/streaming path を壊さない
- Smart Placement で RPC locality まで最適化される前提で設計しない

## Required Next Implementation Steps

1. capability registry から Worker host TS manifest を生成する
2. capability ごとに `rpc` / `http` transport hint を registry に追加する
3. named `WorkerEntrypoint` layout を定義する
4. `/_kotodama/capabilities` を TS host generator の入力として使う
5. dual-backend conformance suite に Worker RPC path を追加する

## References

- Cloudflare Service Bindings overview: <https://developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings/>
- Cloudflare Workers RPC overview: <https://developers.cloudflare.com/workers/runtime-apis/rpc/>
- Cloudflare Service Bindings RPC / `WorkerEntrypoint`: <https://developers.cloudflare.com/workers/runtime-apis/bindings/service-bindings/rpc/>
- Cloudflare RPC lifecycle: <https://developers.cloudflare.com/workers/runtime-apis/rpc/lifecycle/>
- Cloudflare RPC visibility/security model: <https://developers.cloudflare.com/workers/runtime-apis/rpc/visibility/>
- Cloudflare RPC TypeScript typing: <https://developers.cloudflare.com/workers/runtime-apis/rpc/typescript/>
- Cloudflare blog, JavaScript-native RPC: <https://blog.cloudflare.com/javascript-native-rpc/>
