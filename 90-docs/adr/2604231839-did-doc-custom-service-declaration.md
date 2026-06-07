---
id: adr-2604231839-did-doc-custom-service-declaration
title: "ADR: did:web:*.etzhayyim.com DID Doc に custom service endpoint を明示宣言 — chat.bsky.convo パターン"
status: active
doc_type: adr
topic: did-service-discovery
authoritative: true
last_verified: 2026-04-23
authoritative_for:
  - did:web:*.etzhayyim.com の DID Doc `service[]` 宣言規約
  - `etzhayyimActor` service type + fragment id 命名
  - 他 AT Protocol client からの actor discovery 経路
related:
  - adr-2604231800-atproto-permission-spec-integration
  - adr-2604231811-atproto-extension-service-layers
  - adr-0022-auth-topology-consolidation
  - adr-0023-auth-shannon-optimal-4-layer
  - adr-0029-did-etzhayyim-method-specification
supersedes: []
superseded_by: []
---

# Context

本 repo の `did:web:*.etzhayyim.com` (+ path-form) は 90+ の DID を持つ。各 DID の
`/.well-known/did.json` は現在以下しか service endpoint を宣言していない:

```json
{
  "service": [
    { "id": "#atprotoPds", "type": "AtprotoPersonalDataServer",
      "serviceEndpoint": "https://atproto.etzhayyim.com" }
  ]
}
```

つまり **PDS への委譲宣言のみ**。実際には各 `*.etzhayyim.com` Worker が自分自身の
NSID 向け XRPC (`/xrpc/com.etzhayyim.apps.<app>.*`) を serve しているにも関わらず、
DID Doc を読んだ client はその事実を知る方法がない。現状 discovery は:

- DNS 経由 (`<handle>.etzhayyim.com` に直接リクエスト) — 内部ツール / `etzhayyim xrpc` のみ
- PDS pipethrough 経由 (`atproto.etzhayyim.com/xrpc/<nsid>` → routing-gateway → 各 actor) — 暗黙

のどちらかに頼っていて、**AT Protocol spec のネイティブな discovery チャネル
である DID Doc を使っていない**。spec の `DidDocument.service[]` 機構は、まさに
この「PDS 以外の独自 service」を宣言するためのもので、Bluesky 自身が
`chat.bsky.convo.*` をこの方式で expose している:

```json
// did:web:api.bsky.chat/.well-known/did.json (概念)
{
  "service": [
    { "id": "#bsky_chat", "type": "BskyChatService",
      "serviceEndpoint": "https://api.bsky.chat" }
  ]
}
```

Client は `Atproto-Proxy: did:web:api.bsky.chat#bsky_chat` header で PDS に
pipethrough 依頼 → PDS が DID Doc resolve → service endpoint 発見 → 転送、という
spec-native flow で chat service に到達する。

我々の 90+ actor は **chat.bsky.convo と全く同じパターン**で機能しているのに、
DID Doc でその事実を宣言していない。結果:

- **外部 AT Protocol client (`@atproto/api`, Bluesky App, 3rd party) が actor 発見不可** —
  DNS を引いて各 actor hostname を直打ちする fallback しかなく、spec 準拠の client は reach できない
- **federation 時の interop 不完全** — 他 PDS / 他 AppView が `did:web:mangaka.etzhayyim.com` を
  resolve しても、custom NSID `com.etzhayyim.mangaka.*` の endpoint が発見できない
- **`Atproto-Proxy` header flow が未利用** — 既に PDS 側の pipethrough 実装はあるが
  DID Doc 側の service 宣言がないため形式不整合
- **ADR-2604231800 (permission spec) との相補性が欠落** — permission-set 側では
  "which NSID can be called" が discovery できるようになったが、"where to call them"
  が暗黙のまま

本 ADR はこのギャップを埋める。**我々の actor は `chat.bsky.convo` が「Bluesky DM
service」として declare されているのと同じ粒度で、独立した custom service として
DID Doc に明示される** べきである (既に前会話でユーザーと合意済み)。

# Decision

全 `did:web:*.etzhayyim.com` (root + path-form) の DID Doc `service[]` に以下 1 entry
を追加する:

```json
{
  "id": "#etzhayyim_actor",
  "type": "etzhayyimActor",
  "serviceEndpoint": "https://<self-hostname>"
}
```

## 規約

| 要素 | 値 | 根拠 |
|---|---|---|
| **service type** | `etzhayyimActor` | PascalCase (spec convention: `BskyChatService`, `AtprotoPersonalDataServer`, `BskyAppView`)。簡潔で namespace と一致 |
| **fragment id** | `#etzhayyim_actor` | snake_case underscore (spec convention: `#bsky_chat`, `#atproto_pds`)。`Atproto-Proxy` header の参照 key |
| **serviceEndpoint** | `https://<own-host>` (scheme + host only, no path) | spec convention。`/xrpc/*` / `/mcp` は type から暗黙 |

Root actor 例:

```json
// did:web:mangaka.etzhayyim.com/.well-known/did.json
{
  "@context": ["https://www.w3.org/ns/did/v1", "https://w3id.org/security/multikey/v1"],
  "id": "did:web:mangaka.etzhayyim.com",
  "verificationMethod": [...],
  "authentication": [...],
  "service": [
    { "id": "#atprotoPds", "type": "AtprotoPersonalDataServer",
      "serviceEndpoint": "https://atproto.etzhayyim.com" },
    { "id": "#etzhayyim_actor", "type": "etzhayyimActor",
      "serviceEndpoint": "https://mangaka.etzhayyim.com" }
  ]
}
```

Path-form sub-actor (ADR-0019 / ADR-0029 準拠):

```json
// did:web:mangaka.etzhayyim.com:actor:storyboard
// path → https://mangaka.etzhayyim.com/actor/storyboard/did.json
{
  "id": "did:web:mangaka.etzhayyim.com:actor:storyboard",
  "service": [
    { "id": "#atprotoPds", "type": "AtprotoPersonalDataServer",
      "serviceEndpoint": "https://atproto.etzhayyim.com" },
    { "id": "#etzhayyim_actor", "type": "etzhayyimActor",
      "serviceEndpoint": "https://mangaka.etzhayyim.com" }
  ]
}
```

Path-form の `serviceEndpoint` は **parent host** を指す (W3C did:web: spec 準拠、
sub-actor は独立 Worker を持たないため parent の NSID dispatcher が処理する)。

## Client routing semantics

1. **DNS direct (既存路、継続)**: client が `https://mangaka.etzhayyim.com/xrpc/com.etzhayyim.mangaka.foo` を直接叩く
2. **PDS pipethrough (既存路、継続)**: client が PDS に `Atproto-Proxy: did:web:mangaka.etzhayyim.com#etzhayyim_actor` header 付きで送信 → PDS が DID Doc resolve → service endpoint 発見 → routing-gateway 経由で forward
3. **DID Doc discovery (新規)**: client が `did:web:mangaka.etzhayyim.com` を直接 resolve → `service[].type=etzhayyimActor` を発見 → その `serviceEndpoint` に XRPC 直送。外部 AT client が spec-native に etzhayyim actor へ到達できる最小経路

# Implementation Plan

Single commit、additive only、既存 client への影響なし。

## I1. `host-web-router.ts` (per-actor Worker, 主経路)

`40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/host-web-router.ts:106-133` の
`/.well-known/did.json` handler を拡張:

```ts
service: [
  {
    id: `${appDID}#atproto-pds`, type: "AtprotoPersonalDataServer",
    serviceEndpoint: "https://atproto.etzhayyim.com",
    ...(caps.length > 0 ? { capabilities: caps } : {}),
    ...(appVersion ? { version: appVersion } : {}),
  },
  {
    id: `${appDID}#etzhayyim_actor`, type: "etzhayyimActor",
    serviceEndpoint: `https://${hostname}`,
  },
],
```

`hostname` は request URL から導出 (既存の `new URL(c.req.url).hostname` pattern)。

## I2. `50-infra/cloudflare/workers/atproto/src/app.ts` (canonical fallback)

`app.get("/.well-known/did.json", ...)` (line 667-719) を拡張。`isPds` の場合は
`etzhayyimActor` entry は不要 (PDS 自身は etzhayyim actor ではない)。per-actor 用 DID Doc を
atproto Worker が serve するケース (DNS 直打ち failback) では entry を足す:

```ts
service: [
  { id: "#atprotoPds", type: "AtprotoPersonalDataServer",
    serviceEndpoint: "https://atproto.etzhayyim.com" },
  ...(isPds
    ? [{ id: "#atprotoLabeler", type: "AtprotoLabeler",
         serviceEndpoint: "https://atproto.etzhayyim.com" }]
    : [{ id: "#etzhayyim_actor", type: "etzhayyimActor",
         serviceEndpoint: `https://${hostname}` }]),
],
```

## I3. `50-infra/cloudflare/workers/atproto/src/repo/keystore.ts` (DID Doc persist)

`keystore.ts:142` で keystore が DID Doc を graph に persist している。同じ
pattern で `etzhayyimActor` entry を含める。key rotation 時の DID Doc 再生成でも
保持される。

## I4. `50-infra/cloudflare/workers/atproto/src/handlers/plc/index.ts` (did:plc migration)

ADR-0014 Phase 5 の did:plc migration 時に発行される DID Doc にも同じ entry を入れる
(`plc.etzhayyim.com` が serve する did:plc 形式 DID Doc も同じ service taxonomy)。

## I5. Test

以下を新規テストとして追加:

- `host-web-router.test.ts`: `GET /.well-known/did.json` の response に
  `service[].type === "etzhayyimActor"` が含まれること、`serviceEndpoint` が request host と一致
- `app.ts` integration test: per-actor hostname への DID Doc request で `etzhayyimActor` entry 出現
- atproto Worker = PDS の場合は `etzhayyimActor` を含まないこと (`isPds === true` branch の否定)

## I6. Smoke (post-deploy)

```bash
curl -s https://mangaka.etzhayyim.com/.well-known/did.json | jq '.service'
# 期待:
# [
#   { "id": "did:web:mangaka.etzhayyim.com#atproto-pds", "type": "AtprotoPersonalDataServer",
#     "serviceEndpoint": "https://atproto.etzhayyim.com" },
#   { "id": "did:web:mangaka.etzhayyim.com#etzhayyim_actor", "type": "etzhayyimActor",
#     "serviceEndpoint": "https://mangaka.etzhayyim.com" }
# ]

curl -s https://atproto.etzhayyim.com/.well-known/did.json | jq '.service[].type'
# 期待: "AtprotoPersonalDataServer", "AtprotoLabeler" のみ (etzhayyimActor なし)
```

# Consequences

## Positive

- **Spec-native discovery**: 外部 AT Protocol client が `did:web:*.etzhayyim.com` を
  resolve するだけで actor endpoint に到達できる。`@atproto/api`, Bluesky App,
  3rd party agent が actor service を認識可能に
- **Federation 下地**: 他 PDS / 他 AppView が我々の actor DID を resolve した時に、
  service endpoint の位置が明確に分かる。将来の federation 拡張 (ADR-2604231811
  の extension layer taxonomy と組み合わせ) の foundation
- **`Atproto-Proxy` header flow の正統化**: 既存の PDS pipethrough 実装が spec 規約
  に完全準拠する。`Atproto-Proxy: did:web:mangaka.etzhayyim.com#etzhayyim_actor` が意味を持つ
- **ADR-2604231800 との相補性**: permission-set で "which NSID can be called" を
  discovery できたのに対し、本 ADR は "where to call them" を discovery できる。
  2 つ合わせて **認可 (what) + routing (where)** の discovery が spec-native に閉じる
- **現状破壊ゼロ**: 既存 client (DNS 直 + PDS pipethrough) はそのまま動作

## Negative

- **DID Doc サイズ微増**: `service[]` に 1 entry 追加 (~100 bytes)。90+ actor 分
  キャッシュで考えても誤差レベル
- **service type 命名の先取り**: 将来 atproto spec が公式に etzhayyim 的 custom service
  type を標準化した場合、`etzhayyimActor` は独自名のまま。ただし DID Doc の `service[]`
  は multiple entry 可なので、将来標準 type が出たら追加すれば済む
- **Path-form DID の `serviceEndpoint` 解釈**: sub-actor が parent host を指すという
  convention が spec で明示されていないため、ADR として明文化する必要がある (本 ADR
  で記録済)

## Neutral

- **既存 routing-gateway との関係**: routing-gateway は今も有効。DID Doc discovery
  は **並存する代替経路**。どちらを選ぶかは client 側の好み
- **MCP endpoint 宣言**: 現状 MCP 経路は `.well-known/mcp.json` (PDS level) で
  十分 discover できるので、本 ADR では MCP 用の service entry (e.g. `etzhayyimActorMcp`) は
  追加しない。必要になった時に別 ADR で追加

# Alternatives Considered

## A1. custom service 宣言をしない (現状維持)

- pros: 実装ゼロ
- cons: 外部 AT client が actor にリーチできない。`Atproto-Proxy` flow が spec
  不整合のまま。ADR-2604231800 で permission discovery は spec-native にしたのに
  routing discovery だけ DNS 依存、という asymmetry が残る。**却下**

## A2. `AtprotoXrpcService` など汎用名

- pros: federation 友好
- cons: atproto spec で予約される可能性がある汎用名を独自に先取りすると、
  将来公式定義が出た時に conflict する。Bluesky が `BskyChatService` と
  prefix 付きで naming しているのと同じ理由で、組織 prefix (`etzhayyim`) を付けるのが
  安全。**却下**

## A3. 複数 service type を宣言 (`etzhayyimActorXrpc`, `etzhayyimActorMcp`, `etzhayyimActorWeb` 等)

- pros: endpoint ごとに type を分離
- cons: 今のところ **1 actor = 1 hostname = 1 Worker** で XRPC / MCP / Web UI が
  すべて同 host から serve されるので、type を分けても `serviceEndpoint` は全部
  同じ値。分離の実利なし。将来 endpoint が物理分離した時に追加すれば済む。**却下**

## A4. DID Doc ではなく独自 `.well-known/etzhayyim-actor.json` を serve

- pros: 自由な schema 設計
- cons: AT Protocol spec は service discovery を DID Doc 経由に統一しているので、
  独自 .well-known を増やすと spec 準拠度が下がる (ADR-2604231800 と同じ哲学違反)。
  **却下**

# Migration

本 ADR は forward-only additive。既存 service entry を削除しない。

- **Phase 0 (本 ADR land)**: registry entry 追加、本 ADR を active 化
- **Phase 1 (1 commit)**: `host-web-router.ts` + `app.ts` + `keystore.ts` +
  `plc/index.ts` の 4 箇所を additive 更新、test 追加、smoke 成功で deploy
- **Phase 2 (monitoring, 1 week)**: DID Doc を fetch してくる client の User-Agent
  を `atproto-worker` Logpush で観測。外部 AT client (Bluesky App, `@atproto/api`
  SDK, 3rd party) が増えるかを確認
- **Phase 3 (将来)**: 必要に応じて `etzhayyimActorMcp`, `etzhayyimActorWeb` 等の追加 service
  type を別 ADR で議論

全 phase は既存 Worker の additive deploy。DNS / route / schema 変更なし。

# References

## 公式仕様

- [W3C DID Core 1.0](https://www.w3.org/TR/did-core/) §5.4 Service — `service[]` の定義
- [AT Protocol: DID](https://atproto.com/specs/did) — AT Protocol における DID 利用規約
- [AT Protocol: Atproto-Proxy header](https://atproto.com/specs/xrpc#service-proxying) —
  service type fragment による pipethrough routing
- [AT Protocol: The AT Stack](https://atproto.com/ja/guides/the-at-stack) — PDS/AppView/
  AppView/Feed Generator/Labeler/Chat の layer taxonomy (本 ADR は chat 層と同じ mode
  に actor を位置付ける)

## 関連 ADR

- `adr-2604231800-atproto-permission-spec-integration` — permission discovery の
  spec 準拠整備。本 ADR は routing discovery の spec 準拠整備で、セット
- `adr-2604231811-atproto-extension-service-layers` — Worker layer taxonomy。本 ADR
  は "actor layer" Worker が DID Doc でどう自己紹介するかを決める
- `adr-0022-auth-topology-consolidation` — 2-token model。`Atproto-Proxy` header に
  乗せる Service Auth JWT の source
- `adr-0023-auth-shannon-optimal-4-layer` — did:web multi-key rotation, routing-gateway
- `adr-0029-did-etzhayyim-method-specification` — did:etzhayyim method spec。DID Doc の上位構造
  convention の source

## 実装 citations (本 ADR 実装時に touch する)

- `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/host-web-router.ts:106-133` — per-actor DID Doc
- `50-infra/cloudflare/workers/atproto/src/app.ts:667-719` — atproto Worker DID Doc
- `50-infra/cloudflare/workers/atproto/src/repo/keystore.ts:140-150` — DID Doc persist to graph
- `50-infra/cloudflare/workers/atproto/src/handlers/plc/index.ts:210-220` — did:plc DID Doc

## 先行例 (分析の根拠)

- `chat.bsky.convo.*` = Bluesky DM service。`did:web:api.bsky.chat` が `BskyChatService` type
  を宣言、client が `Atproto-Proxy: did:web:api.bsky.chat#bsky_chat` で pipethrough。
  **本 ADR はこのパターンを etzhayyim actor に適用するもの**
