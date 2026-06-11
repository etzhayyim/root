---
id: 2605191524-ameno-multi-tab-swarm-broadcast
title: Ameno multi-tab swarm via BroadcastChannel
status: proposed
doc_type: adr
topic: ameno-swarm
authoritative: true
last_verified: 2026-05-19
depends_on:
  - 2605191135-ameno-tier2-daemon-residency
  - 2605191407-ameno-browser-viewer-mode
---

# ADR 2605191524: Ameno multi-tab swarm via BroadcastChannel

## Context

Each ameno tab is a Tier-2 worker(ADR-2605191135)で worker DID を持つ。
複数タブを開くと、それぞれ独立した worker として substrate に DID
登録されるが、お互いの存在を認識せず、二重に同じ brief を処理する
冗長性が発生し得る(現状の auto-respond は単一タブを暗黙の前提)。

substrate(MST / firehose)経由の peer discovery は本来のあるべき
姿だが、`atproto.etzhayyim.com` reachability に依存する。先に **同
origin の同 browser 内 multi-tab swarm** を BroadcastChannel で安価に
立ち上げる。

## Decision

**`svelte/src/lib/swarm.ts` を導入。**

### Wire

- channel name: `ameno-swarm-v1`
- 5s 間隔で `hello`(DID + role + compute mode + loaded model + sent
  timestamp)を broadcast
- 15s 無音で peer を roster から削除
- tab close 時に `bye` を best-effort post → 他 tab が TTL 待たず drop

### v0.1 スコープ

| 機能 | 状態 |
|---|---|
| Peer presence(他 tab の存在表示)| **本 ADR で実装** |
| Daemon panel に "Swarm: N peers"+ DID 一覧 | **本 ADR で実装** |
| Lease-based brief distribution(brief 1 件 = 1 tab だけが処理) | follow-up ADR |
| Cross-origin swarm(別 ブラウザ / 別マシン) | substrate 経由 = ADR-2605171800 以後 |
| Leader election(crash recovery) | lease ADR に同梱 |

### Non-goals

- BroadcastChannel は **同 origin / 同 browser profile** に限定。Safari Private や cross-device は対象外。それらは substrate で扱う
- 信頼境界はゼロ — 同 origin の任意 JS が swarm channel に乗れる。 brief processing leas を本 ADR で実装しなかった一因

## Consequences

- ameno daemon panel が "you are not alone" の signal を表示できる:
  `Swarm: 2 peers · daemon-a · daemon-b · …`
- 後段 lease ADR(brief 1 件を leader tab だけが処理)の前提が揃う
- DID は既に永続(localStorage)、`role` / `computeMode` の broadcast
  情報は ephemeral

## Alternatives Considered

1. **SharedWorker** — 古い API、Safari 互換性ムラ。BroadcastChannel
   は今や全 evergreen で利用可能。reject
2. **localStorage `storage` event** — payload が string-only、struct
   化が手間。BroadcastChannel の方が clean
3. **Substrate-only (PDS firehose peer discovery)** — 最終形。だが
   dev / offline で動かない。先に local 同期を入れて、後段で重ねる
4. **iframe postMessage** — UI tree が異なる tab に乗れない

## References

- ADR-2605191135 (Tier-2 daemon residency, worker DID)
- ADR-2605191407 (browser viewer mode)
- MDN BroadcastChannel
