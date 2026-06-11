---
id: adr-0033-did-etzhayyim-federation-via-did-web-shim
title: "ADR-0033: did:etzhayyim Federation via did:web Shim — plc.directory 依存を排し did.etzhayyim.com に集約"
status: active
doc_type: adr
topic: did-etzhayyim-federation
authoritative: true
last_verified: 2026-04-23
authoritative_for:
  - did:etzhayyim actor が Bluesky / 外部 atproto ecosystem に federate する canonical 経路
  - did.etzhayyim.com resolver の did:web shim endpoint 仕様
  - federation-visible tier の境界条件 (vertex_etzhayyim_identity.federated)
  - plc.directory / plc.etzhayyim.com 依存の排除ルール
related:
  - 90-docs/adr/0010-per-did-signing-key-custody.md
  - 90-docs/adr/0014-self-hosted-did-plc.md
  - 90-docs/adr/0019-atproto-native-identifier-topology.md
  - 90-docs/adr/0023-auth-shannon-optimal-4-layer.md
  - 90-docs/adr/0029-did-etzhayyim-recursive-hash-merkle.md
  - 90-docs/adr/0030-did-etzhayyim-recursive-adoption-rollout.md
supersedes:
  - adr-0014-self-hosted-did-plc
superseded_by: []
---

# Context

ADR-0029 で採用した `did:etzhayyim` recursive Merkle method は、数千億 (10^11) order の
actor 発行を前提に設計されている (内部 agent / cohort / matter / document / grant /
session の 1 entity = 1 DID)。

ADR-0014 (自前 plc.etzhayyim.com) は `did:plc` を primary identity として federation する
前提で書かれていたが、前提が 2 つ変わった:

1. **Primary identity が `did:plc` ではなく `did:etzhayyim`** (ADR-0029)
2. **Scale が 10^11 order** — plc.directory への submit (one-way push / dual-register)
   はどの戦略でも物理的に不可能。Bluesky 公式 plc.directory は単一集中 service で
   あり、10^11 op を受入れる設計ではない

したがって ADR-0014 の前提 (plc.directory との federation を目指す) 自体が
成立せず、`did:etzhayyim` の federation 経路を **plc.directory に一切依存しない形** で
再設計する必要がある。

## Federation に求められる機能

「Bluesky client が etzhayyim actor の post / profile を見られる」ためには、外部
`@atproto/identity` が:

1. handle (`kami.etzhayyim.com`) → DID を resolve できる (`_atproto` TXT)
2. DID → DID document を resolve できる (method-dependent)
3. DID document から `atproto_pds` endpoint を取得できる
4. PDS から repo / record を取得できる

`@atproto/identity` は `did:plc` と `did:web` をネイティブに support している。
`did:etzhayyim` を 3rd-party で実装 / PR させるのは ecosystem outreach cost が大きい。

# Decision

**`did:etzhayyim` identity を `did:web` shim に転写して federate する。**
plc.directory / plc.etzhayyim.com に一切 op を投げない。

## R1. Tier separation

数千億 actor のうち、**federation-visible subset** のみが shim 対象。
残りは pure `did:etzhayyim` のまま内部運用。

- **境界**: `vertex_etzhayyim_identity.federated BOOLEAN DEFAULT false`
- **enable 条件**: `federate=true` にセットされた actor のみ did.etzhayyim.com が応答
- **scale 試算**: federate 対象は AI agent の大部分を除外し 10^3〜10^6 想定。
  10^11 全体の 0.0001% 以下
- **migration**: federated flag が立った時点で `pubkey_multibase` (ADR-0029 R
  "Storage" の root/pubkey segment 列) の backfill を確認。Phase 1 legacy hex
  DID は passkey 経路で既に pubkey 登録済

## B2. DID ↔ URL mapping

`did:web` spec に準拠 (ADR-0023 P4 で実装済の sub-actor path 機構を再利用)。
ADR-0029 の semantic path (sub / id / lexicon) をそのまま URL segment に転写:

```
did:etzhayyim:{s0}                   ↔ did:web:did.etzhayyim.com:{s0}
did:etzhayyim:{s0}:{s1}              ↔ did:web:did.etzhayyim.com:{s0}:{s1}
did:etzhayyim:{s0}:{s1}:…:{sN}       ↔ did:web:did.etzhayyim.com:{s0}:…:{sN}   (N≤6)
```

URL 側:

```
https://did.etzhayyim.com/{s0}/did.json                      (depth=1, root)
https://did.etzhayyim.com/{s0}/{s1}/did.json                  (depth=2)
https://did.etzhayyim.com/{s0}/{s1}/.../{sN}/did.json         (depth=N)
```

具体例 (3-segment standard form `sub:id:lexicon`):

```
did:etzhayyim:user:kami:com.etzhayyim.yoro.profile
  ↔ did:web:did.etzhayyim.com:user:kami:com.etzhayyim.yoro.profile
  ↔ https://did.etzhayyim.com/user/kami/com.etzhayyim.yoro.profile/did.json

did:etzhayyim:lawfirm-kagoshima-univ:matter-2026-001:com.etzhayyim.apps.sashiosae.case
  ↔ https://did.etzhayyim.com/lawfirm-kagoshima-univ/matter-2026-001/com.etzhayyim.apps.sashiosae.case/did.json
```

`did:web` spec は colon を path separator として解釈する (`did:web:host:a:b:c` →
`https://host/a/b/c/did.json`)。`@atproto/identity` はこの経路を標準で通す。

Phase 1 grandfather hex DID も同一 rule で serve:

```
did:etzhayyim:3k2vfg8qnwxhealoxy123456                       (legacy)
  ↔ https://did.etzhayyim.com/3k2vfg8qnwxhealoxy123456/did.json
```

## R3. Handle binding

federated actor の handle は etzhayyim 既存の `{name}.etzhayyim.com` をそのまま使う:

- **handle**: `kami.etzhayyim.com`
- **DID**: `did:web:did.etzhayyim.com:h0:h1:…` (DID host と handle host を分離)
- **`_atproto` TXT record**: `kami.etzhayyim.com` の TXT に `did=did:web:did.etzhayyim.com:...`

handle host (`kami.etzhayyim.com`) と DID host (`did.etzhayyim.com`) を分離することで:

- handle は既存 routing-gateway で配信 (ADR-0013)
- DID document は did.etzhayyim.com に集約 (1 Worker で全 federated actor を serve)
- handle 変更が DID 変更を引き起こさない (did:etzhayyim が content-addressed なので本来不変)

## R4. DID document 生成

did.etzhayyim.com Worker は `vertex_etzhayyim_identity` から on-demand 生成:

```json
{
  "@context": ["https://www.w3.org/ns/did/v1"],
  "id": "did:web:did.etzhayyim.com:user:kami:com.etzhayyim.yoro.profile",
  "alsoKnownAs": [
    "at://kami.etzhayyim.com",
    "at://kami/com.etzhayyim.yoro.profile/self"
  ],
  "verificationMethod": [{
    "id": "did:web:did.etzhayyim.com:user:kami:com.etzhayyim.yoro.profile#atproto",
    "type": "Multikey",
    "controller": "did:web:did.etzhayyim.com:user:kami:com.etzhayyim.yoro.profile",
    "publicKeyMultibase": "z..." /* from vertex_etzhayyim_identity.pubkey_multibase of nearest pubkey/root ancestor */
  }],
  "service": [{
    "id": "#atproto_pds",
    "type": "AtprotoPersonalDataServer",
    "serviceEndpoint": "https://atproto.etzhayyim.com"
  }]
}
```

- **Cache**: CF edge cache 60s (ADR-0023 multi-key rotation の propagation 窓と整合)
- **Resolution**: `GET /{s0}/.../did.json` → D1 / Kotoba/Datomic から `vertex_etzhayyim_identity`
  lookup → `federated=true` 確認 → did.json 生成 → 200 / 404 (非 federated or revoked)
- **Depth**: recursive form (`/{s0}/.../{sN}/did.json`) は ancestor chain verify が成立
  (ADR-0029 resolver) した場合のみ 200
- **Revocation**: ancestor の `revoked_at IS NOT NULL` が 1 件でもあれば 404
- **Pubkey 解決**: child DID (role / grant / session / lexicon 等 keyless segment) の
  `verificationMethod` は ADR-0029 R "Key Custody" に従い最寄り ancestor の
  `pubkey_multibase` を採用

## R5. plc.directory / plc.etzhayyim.com 依存の排除

- `plc.directory` への op submit を**禁止**。どの戦略でも投げない
- `plc.etzhayyim.com` は本 ADR で **non-goal** に確定。ADR-0014 を supersede
  - 未 deploy の場合: deploy しない (CF Worker project 作成も不要)
  - deploy 済の場合: archive 予約 (別 task で archive 手順を確定)

## R6. 生命サイクル

```
Phase 1 (current, 2026-04-19)  pure did:etzhayyim, federation なし
Phase 2 (on demand)            did.etzhayyim.com Worker 実装 (本 ADR の R1-R4 実装)
Phase 3 (Bluesky outreach 時)  最初の federated actor に federated=true を立てる
Phase 4 (必要時)               account-level Worker 分割 (ADR-0028 sharding pattern)
```

**実装は federation 実需要が発生するまで延期**。本 ADR は設計を確定するのみで、
Phase 2 以降の実装は別 task で起票する (CLAUDE.md "Don't design for hypothetical
future requirements" — しかし設計判断として記録は残す必要がある)。

# Rationale

## Why did:web shim instead of native did:etzhayyim PR to @atproto/identity?

- **即時性**: did:web は `@atproto/identity` の built-in resolver で今日から動く
- **ecosystem outreach なし**: Bluesky, Ozone, atproto tooling の code 変更なし
- **sovereignty 保持**: did.etzhayyim.com を etzhayyim が運用、key material は ADR-0010 custody
- **scale neutral**: CF Worker + edge cache で federation 視認 actor 数に線形スケール

native `did:etzhayyim` resolver の PR は長期 option として open、ただし Phase 2 以降
federation 需要が実測で 10^4 order を超えてから再評価。

## Why `did.etzhayyim.com` と handle host の分離?

`did:web:{handle}.etzhayyim.com` (handle == DID host) は 1 Worker per actor を要求し、
federated subset が 10^4 を超えると CF Worker account 上限 (500/zone) に衝突する。
`did:web:did.etzhayyim.com:h0:h1` は 1 Worker で N actor を serve するため上限に当たらない。

また ADR-0029 の content-addressed identity の「DNS 非依存」性質は handle 変更で
DID が変わらないことを保証する。handle host と DID host を分離することで、
将来の handle rename / custom domain が DID identity を破壊しない。

## Why tier separation (federated flag) ?

10^11 actor 全てを federate 可視にする需要は存在しない:

- AI agent / cohort / session は内部 identity で十分 (外部可視性不要)
- matter / document / grant は parent actor の federation で間接的に参照可能
- 真の federation 対象は "自然人 / 法人 / プロジェクト公式 account" 相当の 10^3-10^6

flag を false default にすることで、**federate していない actor は did.etzhayyim.com に
leak しない** (privacy default)。`federated=true` は明示的な opt-in。

## Why Phase 2 実装を延期?

- 現時点で federated visibility を要求する actor が存在しない
- 実装 cost (Worker + D1 schema + CLI + E2E) を先行投資しても dead code になる
- Phase 3 で最初の対象 actor が決まった時点で実装開始 = YAGNI 遵守
- 設計を ADR で確定しておけば、需要発生時に即着手可能

# Consequences

## Positive

- plc.directory 負荷 0 → Bluesky ecosystem への無害性保証
- plc.etzhayyim.com 運用 cost 0 (ADR-0014 を実装しなくて済む)
- `did:etzhayyim` の content-addressed 性質 (handle 変更で DID 不変) を維持したまま
  federation 互換を得る
- ADR-0010 の per-DID signing key custody がそのまま使える (federated actor は
  ADR-0010 Stage 1 / Stage 2 の key custody に乗る)
- η 試算 ~0.91 を federation 追加後も保持 (identity axis は non-federated と同一、
  federation axis が追加されるだけ)

## Negative

- `@atproto/identity` の did:web 実装に依存 → upstream が did:web spec を変える場合
  追随が必要 (現時点で did:web spec は stable)
- handle host (`{name}.etzhayyim.com`) と DID host (`did.etzhayyim.com`) の分離を運用で意識する
  必要 (docs で明示)
- Bluesky client 側から見た etzhayyim actor は全て `did:web:did.etzhayyim.com:*` prefix を
  持つため、etzhayyim origin の actor が識別しやすい (privacy 観点でのリスクは限定的、
  handle で既に .etzhayyim.com origin は判る)

# Alternatives Considered

## A. Dual-registration to plc.directory (却下)

ADR-0014 の mirror 戦略。10^11 scale では plc.directory 側の rate limit / storage /
policy いずれかで破綻する。たとえ 10^6 に絞っても plc.directory 運営者に明確に
敵対的な行為。

## B. One-way push to plc.directory (却下)

A と同じ scale 問題。加えて plc.directory の policy 変更で任意時点で切られる
リスク。

## C. `@atproto/identity` に did:etzhayyim resolver PR (将来 option、非採用)

long-term ecosystem work。Bluesky 側の maintainer review + publish + 各 SDK 反映で
6-12 ヶ月 order。Phase 4 以降 federation 需要が定常化してから再評価。

## D. AppView peer federation (PLC bypass, 却下)

Bluesky AppView と etzhayyim AppView (yoro) の subscribeRepos peer は現状 AT Protocol
spec 外。Bluesky 側 outreach が成立しない限り動かない。repo 層 federation として
別途検討価値はあるが、identity 層の本 ADR のスコープ外。

## E. Lazy did:plc minting (却下)

Bluesky 側 lookup 駆動で shadow did:plc を on-demand mint。ADR-0014 の一種だが、
2 identity 並走 (did:etzhayyim primary + did:plc shadow) の運用 cost が高い。しかも
plc.directory への真の需要分 submit が残るため scale 問題が部分的に残存。

# Implementation Scope (Phase 2 以降、別 task)

## Phase 2 Worker 実装 (federation 需要発生時)

- `50-infra/cloudflare/workers/did-resolver/` 新規 Worker (`did.etzhayyim.com` route)
  - `GET /:h0/did.json` (depth 1)
  - `GET /:h0/:h1/did.json` ... (depth 2-6)
  - D1 or Kotoba/Datomic lookup → chain verify (ADR-0029 resolver ロジック再利用)
  - edge cache 60s、revocation は cache-busting 不要 (TTL で propagate)
- migration: `vertex_etzhayyim_identity` に `federated BOOLEAN DEFAULT false` + index
- `70-tools/etzhayyim/etzhayyim/actor_federate.go` — `etzhayyim actor federate --did {did}` CLI
- E2E: federated actor を `@atproto/identity` ベースの client で resolve

## 非スコープ (identity 層のみ)

本 ADR は identity 層の federation shim のみ。以下は別 ADR / 別 task:

- 実際に Bluesky 側から post / profile が見える federation (PDS subscribeRepos /
  AppView peer / firehose 相互接続)
- Bluesky AppView との repo index 同期
- Ozone / 他 moderation service との integration

# References

- ADR-0010 — per-DID signing key custody (key material 管理)
- ADR-0014 — self-hosted plc.etzhayyim.com (本 ADR で supersede)
- ADR-0019 — atproto-native identifier topology (5-layer model の土台)
- ADR-0023 — auth Shannon-optimal 4-layer (did:web sub-actor path 実装の前例)
- ADR-0029 — did:etzhayyim recursive Merkle (primary identity method)
- ADR-0030 — did:etzhayyim rollout (adoption schedule)
- did:web spec — https://w3c-ccg.github.io/did-method-web/
- `@atproto/identity` — https://www.npmjs.com/package/@atproto/identity
