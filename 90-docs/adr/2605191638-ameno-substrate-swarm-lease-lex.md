---
id: 2605191638-ameno-substrate-swarm-lease-lex
title: Ameno substrate-level swarm lease — com.etzhayyim.swarm.lease lex
status: proposed
doc_type: adr
topic: ameno-swarm
authoritative: true
last_verified: 2026-05-19
depends_on:
  - 2605191524-ameno-multi-tab-swarm-broadcast
  - 2605191603-ameno-swarm-leader-election
  - 2605191559-ameno-mst-checkpointer-stage-2-activation
related:
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
---

# ADR 2605191638: Ameno substrate-level swarm lease (lex)

## Context

ADR-2605191603 で **同 origin / 同 browser** 内の leader election を
実装した(lex-smallest DID = leader)。次のステップは **cross-device**
— 別マシン、別ユーザの ameno worker(browser + Path A + Path B
混在)が協調する仕組み。

substrate (MST + L2 anchor) を介すれば、 worker は時間軸的に monotonic
な lease を取り合える:

- 各 worker が自分の DID で `com.etzhayyim.apps.ameno.swarmLease` record を
  write
- `generation` カウンタが MST CAS + L2 anchor 順序で全 worker から
  一意に見える
- 期限切れ(`expiresAt < now`)で takeover 可能

本 ADR は **lex schema + 設計の確定のみ**。実装(MST write、
takeover algorithm)は別 PR(`ameno-swarm-lease-impl`)。

## Decision

**`00-contracts/lexicons/com/etzhayyim/apps/ameno/swarmLease.json` を導入。**

### Record shape

```json
{
  "scope": "firehose:app.bsky.feed.post",
  "holderDid": "did:web:host:simeon-mac-01HEY…",
  "generation": 42,
  "issuedAt": "2026-05-19T15:00:00Z",
  "expiresAt": "2026-05-19T15:05:00Z",
  "renewedAt": "2026-05-19T15:04:30Z",
  "computeMode": "daemon-b",
  "model": "gemma3:4b",
  "note": "previous holder expired at 2026-05-19T15:04:55Z"
}
```

### Identification

- collection: `com.etzhayyim.apps.ameno.swarmLease`
- rkey: literal `current`(`"key": "literal:current"`)
- repo: holder's PDS repo(`did:plc:…` or `did:web:…` per ADR-2605173000)
- → 1 lease per (repo, rkey) — single MST slot enforces single-writer
  semantics naturally

### Takeover algorithm(本 ADR 範囲外、設計のみ)

```
on heartbeat:
  read latest swarmLease record for scope
  if record.holderDid == self:
    publish updated record with renewedAt = now, expiresAt = now + 5min
  elif record.expiresAt < now:
    # Takeover. Publish with generation = record.generation + 1,
    # holderDid = self, note = "previous holder expired at X".
    publish takeover record
  else:
    follower mode — do not process briefs for this scope
```

`generation` の monotonicity は MST 内の record version + L2 anchor で
保証。同時 takeover が生じても、 L2 anchor 確定後に generation が
若い方が retract する。

### Browser-local lease との関係

- **同 origin 内**:既存 BroadcastChannel lease(ADR-2605191603)
  優先。MST 経由は overhead が大きい
- **cross-device / cross-browser**:本 ADR の substrate lease を使う
- 両者は **独立**:browser-local leader が "自分が substrate lease を
  取りに行く" だけ。同 browser 内の follower は substrate lease 検査
  すらしない(leader タブのみが substrate を読み書き)

### Scopes(将来運用上の名前空間)

| scope | 意味 |
|---|---|
| `firehose:app.bsky.feed.post` | bsky post firehose の処理担当 |
| `autoRespond:ameno` | ameno 全般の auto-respond loop |
| `briefDispatcher` | 全 brief を分配する metadata leader |

scope ごとに別 lease。複数 scope を同 worker が掛け持ち可。

### 必須 / 推奨フィールド

- 必須:`scope`、`holderDid`、`generation`、`issuedAt`、`expiresAt`
- 推奨:`renewedAt`、`computeMode`、`model`、`note`
  (debug / human inspect 用)

## Consequences

- ameno worker が **cross-device で 1 つの coordinated organism**
  として振る舞える基盤が確定
- 本 ADR は **lex + 設計のみ**。 implementation は別 PR で:
  - browser:`@etzhayyim/sdk` の write API 経由で lease 記録
  - daemon Path A/B:同じく SDK 経由で記録
  - takeover algorithm を `swarm.ts` / `kotodama.projects.ameno.swarm`
    に追加
- substrate write 1 lease ≒ 1 KB MST + L2 anchor cost。 5 分間隔
  renewal で 1 day ~288 writes per scope per worker。 brief 流量に
  比べ無視できる
- ADR-2605181100 の encrypted records と組合せ可。 holder DID
  だけ公開し、 lease body を AEAD seal する patten は future ADR で

## Alternatives Considered

1. **lex ではなく ephemeral firehose イベント**(`#lease/claim` 等) —
   replay できないため worker 起動時の current-holder 取得が困難
2. **scope を rkey に埋め込む**(`rkey: firehose:app.bsky.feed.post`)
   — 1 リポ複数 scope に必要だが record literal key 制約と整合せず
3. **L2 contract のみ**(MST skip) — gas 効率最悪、 chain reach 必要、
   ADR-2605172000 (MST first) と不整合
4. **chat.bsky.convo 系の messaging lex を流用** — semantic が違う、
   別 lex の方が明確

## References

- ADR-2605191524 / 2605191603(browser-local swarm + leader)
- ADR-2605171800(MST + L2 anchor pipeline)
- ADR-2605181100(MST encrypted records — future composition)
- ADR-2605173000(did:web pds resolution)
- Lex schema:`00-contracts/lexicons/com/etzhayyim/apps/ameno/swarmLease.json`
