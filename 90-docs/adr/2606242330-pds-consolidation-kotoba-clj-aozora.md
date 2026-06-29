---
id: adr-2606242330-pds-consolidation-kotoba-clj-aozora
title: "ADR-2606242330: AT Protocol consolidation — app-aozora に PDS/AppView を集約し etzhayyim.com は PDS を持たない"
status: proposed
doc_type: adr
topic: pds-consolidation-kotoba-clj-aozora
authoritative: true
last_verified: 2026-06-24
priority: 7.0
axis: architecture
weight: 0.70
priority_note: "Operator-directed (2026-06-29): AT Protocol/PDS/AppView surface は app-aozora に集約。etzhayyim.com は組織サイト・DID/static public surface に限定し、PDS を持たない。"
authoritative_for:
  - app-aozora canonical AT Protocol implementation
  - PDS/AppView 実装の app-aozora 集約方針
  - etzhayyim.com does not host PDS
depends_on:
  - adr-2605262130  # kotoba canonical substrate engine
  - adr-2605312345  # kotoba Datom log = first-class canonical state
  - adr-2606015002  # refactor PDS onto kotoba-server (XRPC surface)
related:
  - adr-2605111300  # Bun reference PDS on K8s pod (現行本番 → bridge へ降格)
  - adr-2605203000  # kotoba write-target Option B (PDS XRPC e.write)
  - adr-2605231525  # no-server-key
  - adr-2606231200  # kotoba-rad sovereign per-actor identity (actor は github.io 静的)
  - adr-2605173000  # did:web:pds.etzhayyim.com worker (薄い resolver, 保持)
supersedes: []
superseded_by: []
---

# ADR-2606242330: AT Protocol consolidation — app-aozora に PDS/AppView を集約し etzhayyim.com は PDS を持たない

**Status**: proposed
**Date**: 2026-06-24
**Deciders**: Jun Kawasaki

## Addendum 2026-06-29 — `app-aozora` 集約 + `etzhayyim.com` no-PDS 方針

2026-06-24 時点の本 ADR は `pds.etzhayyim.com` を canonical PDS として整理していた。
2026-06-29 の operator 指示により、この境界を更新する:

**AT Protocol 関係は `app-aozora` に集約する。`etzhayyim.com` は PDS/AppView を持たない。**

新しい責務分界:

| 名称 | 責務 | 持ってよいもの | 持たないもの |
|---|---|---|---|
| `kotoba` | sovereign data/compute substrate | CID, Datom log, WASM runtime, auth/network primitives | domain actor identity policy |
| `kototama` | organism/actor common platform | artificial organism patterns, governed actor libs, runtime adapters | individual actor identity itself |
| `app-aozora` | AT Protocol product boundary | PDS, AppView, XRPC adapter, lexicons, feeds/search, actor profile publish target | etzhayyim.com marketing/static site ownership |
| `etzhayyim.com` | organization/public surface | corporate/religious-corp site, static DID/doc discovery, links to app-aozora | PDS, repo store, AppView, atproto write path |
| `com-etzhayyim-*` | domain artificial organism | domain code/data, actor manifest, kotoba-rad identity, aozora profile records | first-class PDS implementation |

`com-etzhayyim-kyoninka` などの repo は **domain artificial organism** であり、
AT Protocol actor として外界に出る場合も、write/read surface は `app-aozora` の PDS/AppView
を使う。repo 名は `com-etzhayyim-kyoninka` のように domain を正面に置く。`actor` は
implementation category なので first-class organism repo 名には入れない。

Canonical endpoint policy:

- canonical PDS/AppView endpoint: `https://aozora.app`（`app-aozora`）
- deprecated / legacy bridge only: `https://pds.etzhayyim.com`,
  `https://atproto.etzhayyim.com`
- `https://etzhayyim.com` は `/xrpc/*` を canonical に持たない。必要なリンク・リダイレクト・
  DID/static discovery は許すが、PDS state や repo write path は持たない。

これにより、古い「`pds.etzhayyim.com` canonical」という本文中の記述は歴史的な移行説明として
読む。今後の実装・deploy helper・DID serviceEndpoint・docs は `app-aozora` / `aozora.app`
を正準にする。

## Addendum 2026-06-24 — repo 層の kotoba-canonical 不変条件 + `app-aozora-repo`

PDS の repo 層（dag-cbor block → MST → 署名 commit → `com.atproto.sync.*`）を巡る
2026-06-24 調査で判明:

- **MST は既に実装されているが read 側 projector**（`50-infra/mst-projector/src/mst.ts`、
  公式 `@atproto/repo` の MST + dag-cbor CID + CAR を使用、firehose を消費）。clj PDS の
  **write 側 repo-MST/署名 commit は未実装**。
- 素朴に `@atproto/repo` を再利用すると、その既定 `MemoryBlockstore`/SQLite に repo state が
  載り **kotoba がバイパスされ二重台帳が復活**する（本 ADR が潰す対象そのもの）。

**不変条件（本 ADR の repo 層への適用）**: repo の dag-cbor block・commit head は
**kotoba Datom log 上の content-addressed Datom**でなければならない（ADR-2605312345:
Datom log = first-class canonical state / MST = interop wire / IPFS = block backend）。
`@atproto/repo` の MST/CID アルゴリズムを再利用する場合も、**blockstore は必ず
kotoba-backed**（`MemoryBlockstore` 禁止）。最終形は kotoba-server(Rust, ADR-2606015002)
が kotoba 自身の content-addressed block 上で MST をネイティブ計算する。

**実装の起点 = `50-infra/app-aozora-repo/`（kotoba-clj, R0, 本追補と同 PR）**: dag-cbor /
CIDv1(dag-cbor) / kotoba-backed blockstore / record-block + commit object。record の正準形は
dag-cbor block（`[<cid> :block/bytes ..]`）、`:record/*` は同一 log 上の datalog 射影。
**CID は go-ipfs `dag put` と byte 一致を検証**（spec 厳密、staged #2 を clj on kotoba で解決）。
MST tree / 署名 / CAR / sync は後続増分（README §Next）。これにより repo 層でも
「block の住処は常に kotoba」が構造的に保証される。

# Context

`pds.etzhayyim.com` の実装が **事実上複数並存**している（2026-06-24 survey）。これらは
別々の ADR で個別に立ち上がった結果で、どれが canonical かが曖昧になっている。

| # | 実装 | path | stack | 範囲 | status | kotoba? |
|---|---|---|---|---|---|---|
| 1 | atproto-pds-local | `50-infra/atproto-pds-local/` | Bun + 公式 `@atproto/pds` | full PDS（mini-01 ローカル参照） | scaffold/R0 | ❌ SQLite |
| 2 | **etzhayyim-atproto-pds-clj** | `50-infra/etzhayyim-atproto-pds-clj/` | **Clojure/bb + kotoba Datom** | server/repo/identity（federation 未完） | 🟡 R0 staged | ✅ EAVT backend |
| 3 | etzhayyim-pds-did-web | `50-infra/etzhayyim-pds-did-web/` | TS CF Worker | `did:web:pds.etzhayyim.com` の did.json のみ | ✅ LIVE | ❌（解決のみ） |
| 4 | etzhayyim-did-web | `50-infra/etzhayyim-did-web/` | TS CF Worker + cljs | apex `did:web:etzhayyim.com` + 動的 actor did | ✅ LIVE | ✅ profile bridge |
| 5 | **Bun PDS pod** | `50-infra/k8s/atproto-pds/` | TS Node `@atproto/pds` on Bun + CF Tunnel | full PDS + B2 blob | ✅ **現行本番(P1)** | ❌ **SQL + B2** |
| 6 | **kotoba-server PDS XRPC** | `40-engine/kotoba/crates/kotoba-server/` | Rust WASM Component | session PoP(D1) + XRPC port(D2 未) | 🟡 proposed | ✅ substrate 本体 |
| 7 | kg-appview | `30-graph/kg-appview/` | Rust OxiGraph SPARQL | RDF AppView（AT Proto ではない） | R0 | ❌ |
| 8 | bsky.etzhayyim.com AppView | （未実装） | TBD | full AT Proto AppView | R0 planned | TBD |
| 9 | **aozora (yoro AppView)** | `60-apps/etzhayyim-project-yoro/kotoba-appview/`（+ `gftdcojp/app-aozora`） | kotoba-native AppView | actor 登録 + feed/searchActors | 🟡 R0-R1 | ✅ |
| 10 | per-actor did:web workers | `50-infra/*-did-web/`（8x） | TS CF Worker | actor DID 解決 | LIVE | ❌ |

**問題**: 現行本番（#5 Bun PDS pod）は **kotoba を使わない（SQL + B2）**ため、
repo の上位方針（kotoba Datom log = first-class canonical state, ADR-2605312345 /
canonical substrate engine, ADR-2605262130）と **二重台帳**になっている。さらに
`pds.etzhayyim.com` は 2026-06-24 時点で **HTTP 530（origin down）**で、actor の
aozora 登録（PDS profile-write）が実行できない（ADR-2606231200 パイロットで判明）。

**既存の統合マンデート**: ADR-2606015002（proposed）は既に *"PDS の XRPC surface を
kotoba-server で提供し、別建ての TS PDS worker を退役させる"* と宣言している。しかし
本番が Bun pod のまま残り、**「どの実装に寄せるか」の最終決定がされていない**。本 ADR
はその決定を operator 指示（2026-06-24）として確定する。

# Decision

**AT Protocol の canonical 実装を `app-aozora` に一本化する。**
`etzhayyim.com` は PDS/AppView を持たない。古い PDS 系実装は bridge-only /
dev-scaffold / 薄い resolver として降格・整理する。

## 単一スタック（canonical）

```
endpoint        : https://aozora.app（app-aozora）
状態(state)     : kotoba Datom log（EAVT, content-addressed, ADR-2605312345）
                  — PDS の repo/record は at://<did>/<collection>/<rkey> を Datom 化
record 変換層    : etzhayyim-atproto-pds-clj（clj/bb・Datom-native, #2）
                  — com.atproto.server/repo/identity を kotoba 上に実装する SoT
XRPC 実行 runtime: kotoba-server（Rust WASM Component, #6 / ADR-2606015002 D2）
                  — clj 層が定義した record 操作の XRPC surface を最終的にここで提供
                  — no-server-key（session PoP verify, zero-access, ADR-2605231525）
AppView/PDS     : app-aozora（yoro kotoba-appview + PDS/XRPC adapter, #9）
                  — 単一 AppView。actor 登録(profile-write)・searchActors・feed
                  — bsky.etzhayyim.com の別建て計画(#8)は廃し aozora に畳む
did:web 解決     : etzhayyim.com 系は薄い静的 resolver / public discovery としてのみ保持
                  （PDS 実装ではない）。apex の動的 per-actor did は退役し、
                  actor は github.io 静的 DID + app-aozora profile を使う。
```

**「kotoba + clj + aozora」の役割分担**: kotoba = 基盤（状態 + Rust runtime）、
clj = PDS の record 意味論を Datom 上に書く層（移行中の SoT・参照実装）、aozora =
読み手（AppView）。3 つで 1 本のパイプ（書込み→Datom→索引→検索/feed）を成す。

## 降格・整理（非 canonical）

- **#5 Bun PDS pod（ADR-2605111300）**: **bridge-only に降格**。clj-on-kotoba(#2)
  が server/repo/identity parity に達するまでの暫定本番として*のみ*残す。parity 後に
  退役。新規機能は Bun pod に足さない（移行先は #2/#6）。
- **#1 atproto-pds-local（Bun 参照）**: **dev/参照 scaffold** に留める（canonical 非）。
  公式 `@atproto/pds` 互換性検証用。
- **#8 bsky.etzhayyim.com 別建て AppView**: **不採用**。aozora(#9) に一本化。
- **#3/#4 did:web worker**: 実装としては保持（PDS ではなく DID 解決層）。

## 移行フェーズ（2026-06-29 改訂）

1. **P0（本 ADR）**: canonical 宣言を `app-aozora` に更新し、`etzhayyim.com no-PDS`
   を明文化する。`aozora:deploy` は `https://aozora.app` を default とし、legacy
   `pds.etzhayyim.com` / `atproto.etzhayyim.com` / apex endpoint を bridge-only とする。
2. **P1**: `etzhayyim-atproto-pds-clj`(#2) を staged の残段（federation sync, 完全な
   com.atproto.repo/sync）まで進め、app-aozora の PDS backend として `KOTOBA_URL` で
   live engine に wire。`bb test` 緑。
3. **P2**: `aozora.app` / app-aozora の PDS origin を clj-on-kotoba PDS に切替。
   `pds.etzhayyim.com` は canonical ではなく、必要なら一時 redirect/bridge のみ。
4. **P3**: ADR-2606015002 D2 を実装し、XRPC surface を kotoba-server(#6, Rust WASM)
   へ移す。clj 層(#2)は record 意味論の参照実装/移行ブリッジとして残置 or 吸収。
5. **P4**: Bun pod(#5) 退役。app-aozora を単一 AppView として searchActors/feed 本番化
   → actor 登録（profile-write）は `aozora.app` に集約される。`etzhayyim.com` は検索・
   profile 表示の canonical host ではなく public entry/link surface に留める。

# Consequences

**正**
- 状態が **kotoba Datom log 1 本**に統一され、二重台帳（SQL+B2 ⊕ Datom）が解消。
  as-of 履歴・content-addressed snapshot・crash-resume を PDS も継承。
- 実装規約（clj/bb over kotoba）と substrate 方針（2605262130 / 2605312345）に整合。
- no-server-key（kotoba-server PoP, ADR-2605231525）を PDS の trust surface に持込める。
- AppView が aozora 1 つになり、actor 登録・検索の経路が単純化。

**負 / リスク**
- 移行中は **Bun pod(#5) と clj-on-kotoba(#2) の二系統が一時併存**（P1–P4）。bridge
  期間のデータ整合（Bun SQL → Datom 移送）が必要。
- `etzhayyim-atproto-pds-clj` は federation sync 未完。完全 PDS parity までの工数が残る。
- kotoba-server XRPC（#6 D2）は未実装で、`kotoba-runtime-web` の component build に依存。
- `pds.etzhayyim.com` 530 の即時復旧は本 ADR の P2（origin 切替）まで持ち越し。暫定で
  Bun pod を起こす運用は許容（bridge-only の役割そのもの）。

# Alternatives Considered

- **A. Bun 参照 PDS(#5) を canonical に据える**: 公式 `@atproto/pds` で federation
  完全・実績あり。却下理由 = kotoba を使わず二重台帳が固定化、clj/bb + Datom 規約と
  恒久的に乖離、no-server-key も持込めない。上位 ADR（2605262130/2605312345/2606015002）
  と矛盾。
- **B. kotoba-server(#6) に即全部移す**: 最終形だが D2 + `kotoba-runtime-web` 未完で
  今は本番化不能。→ 段階移行（clj 層を先に SoT 化し、後で runtime を Rust へ）。
- **C. 現状維持（複数実装併存）**: 却下。canonical 不在が actor 登録の詰まり・530 の
  放置・新規実装の乱立を生んでいる（本 survey の動機）。

# References

- 2026-06-24 PDS 実装 survey（本 ADR Context の表）
- `50-infra/etzhayyim-atproto-pds-clj/README.md` — clj-on-kotoba PDS（canonical record 層）
- `40-engine/kotoba/crates/kotoba-server/src/{pds_session,pds_xrpc}.rs` — kotoba-server PDS（ADR-2606015002）
- `60-apps/etzhayyim-project-yoro/kotoba-appview/README.md` — aozora AppView（Option B 登録モデル, ADR-2605203000）
- `50-infra/k8s/atproto-pds/` — Bun PDS pod（ADR-2605111300, bridge へ降格）
- ADR-2605262130 / 2605312345 — kotoba canonical substrate + Datom first-class state
- ADR-2606015002 — refactor PDS onto kotoba-server（本 ADR が canonical 化を確定）
- ADR-2606231200 — sovereign per-actor identity（actor 登録の前提・github.io 静的 did）
