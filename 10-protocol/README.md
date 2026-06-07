# 10-protocol

`10-protocol` は wire protocol / dispatch convention / client facade を集約する層です。

## 責務

- `xrpc/`: XRPC transport, auth, encode/decode, dispatch, app NSID 規約, command/query DSL の protocol core (`@etzhayyim/xrpc`)
- `signal/`: Signal Protocol E2E primitives (`@etzhayyim/signal`)

## 依存関係

```text
@etzhayyim/xrpc
  └─ (no internal package deps)

@etzhayyim/signal
  └─ @atproto/api
```

## 境界ルール

- protocol 層は runtime 実装 (`20-actors/*`) に依存しない
- protocol 層は contract 実装 (`00-contracts/kotodama-host-contract`) に依存しない
- `xrpc` は protocol core として単独で完結させる
