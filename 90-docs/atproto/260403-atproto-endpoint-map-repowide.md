# ATProto Endpoint Map (Repo-wide)

更新日: 2026-04-03

このドキュメントは、`PDS / PLC / Relay / Moderation(Labeler) / AppView` の対応関係をまとめたもの。

## 0. 採用方針 (このドキュメントの結論)

1. `atproto.etzhayyim.com` は各 DID の `AtprotoPersonalDataServer` として運用する
1. `api.etzhayyim.com` は将来的に廃止し、共通 AppView 入口としては使わない
1. `yoro.etzhayyim.com`, `maps.etzhayyim.com` など各サブドメインがそれぞれ AppView/API を提供する
1. Relay/Moderation は専用ホスト (`relay.etzhayyim.com`, `mod.etzhayyim.com`) を維持する

注記:
- `api.etzhayyim.com` は廃止済みで、dispatcher で `410 Gone` を返す。

## 1. 自前で公開しているエンドポイント

### 1.1 PDS (公開ホスト: `atproto.etzhayyim.com`)

- ルーティング:
  - `atproto.etzhayyim.com/*` → PDS Worker
  - 参照: [50-infra/cloudflare/workers/atproto/wrangler.jsonc](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/atproto/wrangler.jsonc):29
- 実装エントリ:
  - Hono app: [50-infra/cloudflare/workers/atproto/src/pds-app.ts](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/atproto/src/pds-app.ts):58
  - XRPC入口: [50-infra/cloudflare/workers/atproto/src/pds-app.ts](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/atproto/src/pds-app.ts):284

主要公開パス:

1. `https://atproto.etzhayyim.com/xrpc/:nsid`
1. `https://atproto.etzhayyim.com/.well-known/atproto-did`
1. `https://atproto.etzhayyim.com/.well-known/did.json`
1. `https://atproto.etzhayyim.com/.well-known/oauth-authorization-server`
1. `https://atproto.etzhayyim.com/.well-known/oauth-protected-resource`
1. `https://atproto.etzhayyim.com/xrpc/_health`

内部運用NSID (`/_pds` は廃止済み):

1. `com.etzhayyim.pds.emitOcel`
1. `com.etzhayyim.pds.getOcel`
1. `com.etzhayyim.pds.processCollectionJob`
1. `com.etzhayyim.pds.reconcile`

参照:
- [pds-app.ts](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/atproto/src/pds-app.ts):53
- [pds-app.ts](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/atproto/src/pds-app.ts):287
- [pds-app.ts](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/atproto/src/pds-app.ts):402

### 1.2 Relay相当 (公開ホスト: `relay.etzhayyim.com`)

Relay 用の公開面は専用 Worker に分離。

- ルーティング:
  - `relay.etzhayyim.com/*` → Relay Worker
  - 参照: [50-infra/cloudflare/workers/relay/wrangler.jsonc](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/relay/wrangler.jsonc):10
- 公開メソッド:
  - `com.atproto.sync.subscribeRepos`
  - `com.atproto.sync.listHosts`
  - `com.atproto.sync.getHostStatus`
  - `com.atproto.sync.requestCrawl`
  - 参照: [50-infra/cloudflare/workers/relay/worker.ts](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/relay/worker.ts):9

### 1.3 Moderation / Labeler 相当 (公開ホスト: `mod.etzhayyim.com`)

Moderation/Labeler の公開面は専用 Worker に分離。

- ルーティング:
  - `mod.etzhayyim.com/*` → Moderation Worker
  - 参照: [50-infra/cloudflare/workers/moderation/wrangler.jsonc](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/moderation/wrangler.jsonc):10
- 公開NSID:
  - `com.atproto.label.*`
  - `app.bsky.labeler.*`
  - 参照: [50-infra/cloudflare/workers/moderation/worker.ts](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/moderation/worker.ts):9

### 1.4 AppView 相当 (採用方針)

AppView は単一 `api.etzhayyim.com` ではなく、アプリごとのサブドメインで提供する。

- `yoro.etzhayyim.com` が yoro の AppView/API を提供
- `maps.etzhayyim.com` が maps の AppView/API を提供
- 独自NSIDは `com.etzhayyim.apps.{app}.*` を原則にする

補足:
- `api.etzhayyim.com` は後方互換のためドメイン自体は確保するが、API入口としては使わない。
- 実装参照: [50-infra/cloudflare/workers/dispatcher/worker.ts](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/dispatcher/worker.ts)
- `yoro.etzhayyim.com` / `maps.etzhayyim.com` は各 AppView Worker 側で `/xrpc/*` を提供し、共通 read NSID (`app.bsky.*` + 一部 `com.atproto.*`) を `PDS_SERVICE` 経由で `atproto.etzhayyim.com` にプロキシする。

## 2. 外部依存 (repo外サービス)

### 2.1 PLC Directory

`did:plc:*` 解決は外部の `plc.directory` を参照。

- 呼び出し: `https://plc.directory/{did}`
- 参照: [50-infra/cloudflare/workers/atproto/src/index.ts](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/atproto/src/index.ts):1019

### 2.2 外部 did:web

`did:web:*` 解決時は対象ホストの `/.well-known/did.json` を取得。

- 呼び出し: `https://{host}/.well-known/did.json`
- 参照: [50-infra/cloudflare/workers/atproto/src/index.ts](/Users/junkawasaki/etzhayyim/etzhayyim-root/50-infra/cloudflare/workers/atproto/src/index.ts):1033

### 2.3 Bluesky 公開基盤 (`bsky.network`, `api.bsky.app`, `mod.bsky.app`)

この repo は Bluesky と同様に責務分離を採用するが、AppView は単一 host ではなく appごとに分散する方針。

- `bsky.network` 相当: `relay.etzhayyim.com`
- `api.bsky.app` 相当: `yoro.etzhayyim.com`, `maps.etzhayyim.com` など app別 AppView
- `mod.bsky.app` 相当: `mod.etzhayyim.com`

## 3. まとめ (現状)

1. `PDS`: `atproto.etzhayyim.com` (この repo DID の `AtprotoPersonalDataServer`)
1. `PLC`: 外部 (`plc.directory`) 参照
1. `Relay`: `relay.etzhayyim.com` で公開
1. `Moderation/Labeler`: `mod.etzhayyim.com` で公開
1. `AppView`: `yoro.etzhayyim.com`, `maps.etzhayyim.com` など各 app host で公開
