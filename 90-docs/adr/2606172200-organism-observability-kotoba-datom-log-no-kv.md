---
id: adr-2606172200-organism-observability-kotoba-datom-log-no-kv
title: "ADR-2606172200: organism 可観測性 — vitals/pulse/joucho を全て kotoba Datom log に置き、/organism を ClojureScript で可視化する (KV 不使用)"
status: accepted
doc_type: adr
topic: organism-observability-kotoba-datom-log
authoritative: true
last_verified: 2026-06-17
priority: 7.0
axis: organism-autonomy
weight: 0.7
priority_note: "organism の生命活動 (細胞別 vitals / 生産・息遣いの pulse / 情緒 joucho) を可視化するにあたり、live feed を Cloudflare Workers KV に置く案は substrate boundary 違反 (CLAUDE.md: 正準 state は kotoba Datom log、KV は従属 CAS のみ)。本 ADR は organism の可観測データを全て kotoba Datomic に置き、content-addressed snapshot を canonical artifact、JSON を projection と固定する。"
depends_on:
  - "2605262130"  # kotoba storage substrate unification — kotoba = canonical engine
  - "2605312345"  # kotoba Datom log = first-class canonical state; IPFS=block backend, KV≠canonical
  - "2606101200"  # ibuki organism — joucho/wellbecoming datoms (情緒 source)
  - "2606171800"  # RF constitutive — wellbecoming gradient (情緒 layer の意味づけ)
  - "2606013600"  # browser-native kotoba-wasm render (public/kotoba/ no-server read path)
---

# ADR-2606172200 — organism 可観測性を kotoba Datom log に置く (KV 不使用)

## Context

artificial-organism の生命活動を観測・可視化する layer を作った:
- **vitals** — 細胞 (manifest-bearing actor) 別の 3 軸 (clj 内部代謝 / actor 細胞間シグナル /
  atproto 外界代謝) + 生/休眠/死 分類 + as-of trajectory。
- **pulse** — git commit 生産 (生産) / working-tree 編集 (息遣い) のライブ活動。
- **joucho** — 情緒 mood + Wellbecoming 軌跡 (ADR-2606171800)。
- **/organism** — etzhayyim.com/organism の ClojureScript (scittle, no build) 可視化。

production realtime の保存先として Cloudflare Workers **KV** を一度提案したが、これは substrate
boundary 違反である (CLAUDE.md: State = kotoba Datom log が first-class canonical;
ADR-2605312345 で「IPFS=block backend / MST=wire / KV≠canonical state home」を明文化済み)。

## Decision

### D1. organism の全可観測データの SoT = kotoba Datom log
vitals / pulse / joucho は全て kotoba Datom log に **transact** する (KV ではない):
- vitals → `80-data/vitals/journal.edn` (as-of trajectory; append-only)
- pulse  → `80-data/organism/pulse.journal.edn` (live state; bounded — 履歴は git + vitals/joucho 側)
- joucho → `80-data/organism/joucho.journal.edn` (`:joucho/*` mood + `:wellbecoming/*` movement)

### D2. canonical artifact = content-addressed `.kotoba.edn` snapshot
各 feed は kotoba engine の `snapshot!` で **content-addressed `.kotoba.edn`** を materialize し、
`public/organism/*.kotoba.edn` に置く (`public/kotoba/blocks` と同じ content-addressed 方式)。
**これが配信される正準 artifact**。head CID が live fingerprint。

### D3. JSON は projection (read-model)、SoT ではない
`/organism` ページが読む `organism.json` / `pulse.json` / `joucho.json` は Datom log の
**派生 read-model**。`store:"kotoba-datom-log"` + snapshot CID を provenance として刻む。
SoT は常に Datom log であり、JSON はその materialized view。

### D4. KV はどこにも使わない
organism feed の保存・配信経路に KV を導入しない。CF Worker は `[assets]` 静的配信のみ。
member-signed delta の content-addressed CAS としての KV (既存) は別問題で、organism 可観測データは
それを使わない。

### D5. no-server の終点 = ブラウザ内 kotoba query
究極形は、ページが `.kotoba.edn` snapshot を **kotoba-wasm (既に `public/kotoba/` に配置)** で
ブラウザ内 query し、配信するのは Datom log だけにすること (ADR-2606013600 の browser-native render
パターン)。現状は JSON projection を読む暫定形。

## 実装 (landed)

- `70-tools/src/etzhayyim/vitals.cljc` — `vitals:report` (既存 kotoba) + `vitals:pulse` /
  `vitals:joucho` を kotoba transact + `snapshot!` に改修。`pulse->datoms` / `joucho->datoms`
  (engine-native entity maps)。
- Datalog 読み戻し検証: `wellbecoming improving/47`・24 joucho beats・122 pulse actors を
  log から query 可能。content-addressed `pulse.kotoba.edn` / `joucho.kotoba.edn` 生成。
- `/organism` ページ (`50-infra/etzhayyim-did-web/public/organism/`) — scittle CLJS。
- `scripts/organism-pulse-deploy.sh` — cron: `bb vitals:pulse` (kotoba log+snapshot) → `wrangler deploy`。

## Gates / invariants (weaken 禁止)

- organism 可観測データの SoT は **kotoba Datom log**。KV を SoT/配信に使わない (D1/D4)
- 配信 artifact は **content-addressed `.kotoba.edn` snapshot** (D2)
- JSON は projection。SoT を JSON/KV に置き換えない (D3)
- joucho/wellbecoming datoms は edge-primary — per-soul score/level を持たない (ADR-2606171800 継承)

## Future work

- D5 の実装: ページを `.kotoba.edn` の kotoba-wasm ブラウザ query に切替 (真の no-server)。
- pulse log の compaction 方針 (live state journal の世代管理)。
- 本番 cron cadence の確定 (operator)。
