---
id: 2605191603-ameno-swarm-leader-election
title: Ameno swarm — deterministic leader election + auto-respond gating
status: proposed
doc_type: adr
topic: ameno-swarm
authoritative: true
last_verified: 2026-05-19
depends_on:
  - 2605191524-ameno-multi-tab-swarm-broadcast
related:
V05191135-ameno-tier2-daemon-residency
---

# ADR 2605191603: Ameno swarm — deterministic leader election + auto-respond gating

## Context

ADR-2605191524 が **presence**(他タブが存在することを知る)を導入し
た。が、auto-respond モード(`/threads/auto/...` で firehose brief を
処理する)を 2 タブで同時に有効化すると **同じ brief を二重処理する
バグ**が残っている。

タブ間で「誰が処理するか」を決める軽量 coordination が必要。
substrate-level lease(MST 上の lock record)が本筋だが、まず
browser 内に閉じた **deterministic leader election** で済ませる。

## Decision

**Lex-smallest active DID = leader.** 投票なし、tie 解消なし、O(1)。

```ts
function computeLeader(selfDid: string, peers: SwarmPeer[]): boolean {
  const allDids = [selfDid, ...peers.map((p) => p.did)].sort();
  return allDids[0] === selfDid;
}
```

- swarm.ts に `isLeader(): boolean` メソッド追加
- 1Hz poll で leader bit を再計算(peer 出入りで自動切替)
- App.svelte:
  - Daemon panel の自タブ行に **`★ leader`** バッジ
  - 他タブ行に `· follower`
  - `processBrief()` を `handle.isLeader()` でガード — false なら skip

### Failure semantics

- **single tab(peer = 0)** → self is leader trivially
- **leader tab closes** → 残タブが次 hello で leader 認識(最大 5s 遅延、HELLO_PERIOD_MS)
- **net split**(同 origin 内では不発生)→ 該当しない
- **DID 衝突**(同 DID 2 タブ)→ 起こらない設計(`getWorkerDid()` が UUID で生成、localStorage 一致時のみ重複だが同タブのみ)

### Substrate との関係

これは **browser ローカル協調**のみ。substrate lease(MST 上の
`com.etzhayyim.swarm.lease` record + L2 タイムスタンプ)は別 ADR で
扱う(`ameno-substrate-lease`)。本 ADR は同 origin / 同 browser
multi-tab に限定。

### auto-respond + leader 連携

| 状況 | 動作 |
|---|---|
| auto-respond OFF | 全タブ通常動作、 leader 関係なし |
| auto-respond ON, single tab | 自分が leader、全 brief 処理 |
| auto-respond ON, leader 自分 | 全 brief 処理 |
| auto-respond ON, follower | brief 着信を **silently skip**(UI には received count を表示し、processed = 0 と分かるように)|

UI で follower タブの auto-respond スイッチは ON でも「passive observer」と表示。

## Consequences

- ADR-2605191524 で約束した follow-up を回収。ameno swarm が "passive
  presence" から "coordinated processor" に格上げ
- multi-tab で auto-respond を安全に ON にできる → ユーザが間違って
  2 タブ開いても問題ないという確信
- 後続 ADR(substrate lease)が来ても本 ADR の API は維持。差替は
  swarm.ts 内部に閉じる
- leader 交代に 5s ラグがあるが、auto-respond の throughput は brief
  間隔より高速なので影響軽微

## Alternatives Considered

1. **Round-robin via Lamport clock** — peer 順序が不安定。lex-smallest
   の方が決定的・簡単。
2. **Token passing(leader が次 leader 指定)** — leader 急死時の復旧
   フローが複雑。
3. **Substrate lease 直行**(MST の lock record)— substrate
   reachability に依存。dev / offline で動かない。先に local で完結
   させる。
4. **No coordination, dedupe at substrate level**(brief result の MST
   write を idempotent に)— 二重 decode コスト(LLM call 2 倍)が
   不要な無駄。

## References

- ADR-2605191524(swarm presence、本 ADR の前提)
- ADR-2605191135(Tier-2 daemon residency、worker DID source)
- Lamport, "Time, Clocks, and the Ordering of Events" — 採用しなかった
  Lamport clock の参照
