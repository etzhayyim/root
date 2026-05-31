# 10-protocol

`10-protocol` は wire protocol / dispatch convention / client facade を集約する層です。

## 責務

- `xrpc/`: XRPC transport, auth, encode/decode, dispatch, app NSID 規約, command/query DSL の protocol core (`@etzhayyim/xrpc`)
- `wproto/`: W Protocol TS client — service API, Signal E2E, governance, stream (`@etzhayyim/wproto`)

## 依存関係

```text
@etzhayyim/xrpc
  └─ (no internal package deps)

@etzhayyim/wproto
  └─ @etzhayyim/xrpc
```

## 境界ルール

- protocol 層は runtime 実装 (`20-actors/*`) に依存しない
- protocol 層は contract 実装 (`00-contracts/magatama-host-contract`) に依存しない
- `xrpc` は protocol core として単独で完結させる
