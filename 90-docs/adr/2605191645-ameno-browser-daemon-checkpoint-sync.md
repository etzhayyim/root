---
id: 2605191645-ameno-browser-daemon-checkpoint-sync
title: Ameno browser ↔ daemon checkpoint sync (v0.1 — pull-from-daemon)
status: proposed
doc_type: adr
topic: ameno-state-unification
authoritative: true
last_verified: 2026-05-19
depends_on:
  - 2605191407-ameno-browser-viewer-mode
  - 2605191257-ameno-daemon-path-b-kotodama-python
  - 2605191229-ameno-daemon-path-a-bun-langgraph
related:
V05191135-ameno-tier2-daemon-residency
V05191559-ameno-mst-checkpointer-stage-2-activation
---

# ADR 2605191645: Ameno browser ↔ daemon checkpoint sync (v0.1)

## Context

Browser appview の LocalCheckpointer(localStorage)と daemon の
FileCheckpointer / MstCheckpointSaver は **別々の persistence pool**。
viewer mode に切り替えても、 daemon が過去に処理した会話履歴は
browser に降りてこない(逆もまた然り)。

ADR-2605191407 の "state 分離" 表を引いた時点で、本 ADR がフォロー
すべきことを記録済。

完全双方向同期(LWW + CRDT)は中期 ADR。v0.1 は **片方向 pull**
だけ — "Pull from daemon" ボタンで daemon の `viewer` thread state
を browser に流し込む。これで「初めて viewer mode に入ったときに
最近の会話を見たい」ユースケースを安価に解決する。

## Decision

### Daemon side

両 daemon の `GET /threads/:tid/state` を **parsed graph values を
返すように upgrade**:

- Path A (TS): `graph.getState(config)` → `snapshot.values`
- Path B (Python): `await GRAPH.aget_state(cfg)` → `dict(snapshot.values)`

以前は raw checkpoint blob を返していて利用側でデコードが必要だっ
たが、parsed values なら `values.messages` が直接読める。

### Browser side

`viewer-mode.ts` に `pullThreadMessages()` 追加:

```ts
async function pullThreadMessages(
  baseUrl: string,
  threadId: string,
  signal?: AbortSignal,
  authToken?: string,
): Promise<ChatMessage[]>
```

- `/threads/:tid/state` を GET
- `values.messages` を `ChatMessage[]` に validate(role / content 型
  チェック、不正 entry は skip)
- 失敗時 / 空時は `[]`

### UI

Compute セレクタが `daemon-*` または `custom` の時、Reflection bar
近傍に **"Pull from daemon"** ボタン表示:

- 押下 → `pullThreadMessages(url, "viewer", auth)` → 返り値が空でな
  ければ `messages = pulled`
- pulling 中 / disabled 中 / 失敗 chip の状態管理は `pullingFromDaemon`
  / `pullError` $state

### Thread id 規約

browser viewer mode は **`thread_id = "viewer"`** を使う(既存
`invokeAmenoRemote` のデフォルト)。daemon 側の同 thread に対応。
複数 daemon を切り替えた場合は各 daemon 内の `viewer` thread を
取りに行く(=daemon 同士は別履歴のまま、本 ADR は browser 内で
1 つの履歴を持つ運用)。

### v0.1 で **やらない** こと

| 機能 | 理由 / 次の ADR |
|---|---|
| Push to daemon(browser → daemon write) | `invokeAmenoRemote` が既に各 turn を daemon thread に書く |
| Automatic 双方向同期 | LWW + tombstones が要る、別 ADR |
| Cross-daemon merge | substrate lease(ADR-2605191638)経由が正攻法 |
| Conflict resolution UI | v0.1 は newest-wins(browser overwrite local with daemon snapshot) |

### Auth

`resolveAuthToken()` 経由で `Authorization: Bearer …` を付与
(ADR-2605191407 + ameno-ingress の bearer middleware と整合)。
v0.2 では did:key 署名(ADR-2605191657 予定)に置き換え。

## Consequences

- ユーザが「local mode で 3 turn 話す → reload → daemon mode で続
  ける」ような操作で、 "Pull from daemon" を 1 クリックすれば直前
  状態が browser に流入
- daemon が `lg-ameno` pod 経由(Stage 2-4 全活性化、ADR-2605191559
  + 191608 + 191625)で MstCheckpointSaver を使っていれば、 pulled
  state は **MST 由来 → IPFS pinned → L2 anchored** な履歴
- "Pull from daemon" 後の browser ローカル変更は daemon thread に
  自動同期されない(invokeRemote 時に initial messages 渡しているの
  で次の turn 以降は再び一致)
- daemon 側 endpoint が parsed state を返すように変わったので
  `/threads/:tid/state` の互換性が壊れる(generic / pre-ADR caller
  が居れば修正必要、現状 viewer-mode.ts のみが叩いている)

## Alternatives Considered

1. **automatic background sync** — backoff / conflict UI が必要。
   v0.1 で過剰
2. **WebSocket bi-directional** — SSE + REST で十分、Yet Another
   Protocol を増やさない
3. **MST 直読み**(browser が `@etzhayyim/sdk` で MST から直接読む)
   — auth と quorum 必要、substrate 統合 ADR で扱う
4. **daemon push notifications**(daemon → browser SSE で thread の
   変化を流す)— browser viewer mode 中のみ意味があり、 既存 SSE
   stream に重複

## References

- ADR-2605191407(browser viewer mode、本 ADR の前提)
- ADR-2605191229 / 191257(daemon Path A / B、 endpoint 提供元)
- ADR-2605191638(substrate lease、cross-device sync の正攻法)
- ADR-2605191559(MST stage 2、pulled state の出所)
