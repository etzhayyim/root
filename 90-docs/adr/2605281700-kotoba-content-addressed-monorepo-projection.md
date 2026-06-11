---
id: adr-2605281700-kotoba-content-addressed-monorepo-projection
title: "ADR-2605281700: kotoba content-addressed monorepo projection — files SoT, IPFS+DataLad sync, kotoba quad index"
status: proposed
doc_type: adr
topic: kotoba-monorepo-projection
authoritative: true
last_verified: 2026-05-28
priority: 6.5
axis: architecture
weight: 0.70
priority_note: "Establishes the schema by which monorepo Markdown / TOML / JSON / Lexicon files are projected into kotoba's quad + content-addressed block layers without duplicating storage."
authoritative_for:
  - quad schema for monorepo data projection into kotoba
  - direction-of-truth between filesystem, IPFS, DataLad, and kotoba
  - phasing of monorepo-into-kotoba ingestion work
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262400-public-data-ingestion-organism-ecosystem
  - adr-2605241500-dataset-cid-substrate
  - adr-2605262500-robotics-sim-world-data-ingestion
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605231902-feed-post-membrane-and-feed-discover-projection
supersedes: []
superseded_by: []
---

# ADR-2605281700: kotoba content-addressed monorepo projection

**Status**: proposed
**Date**: 2026-05-28
**Deciders**: Jun Kawasaki

# Context

`etzhayyim/root` の主要データ — ADR (`90-docs/adr/*.md`)、Lexicon (`00-contracts/lexicons/**/*.json`)、SSoT registry (`deps.toml`)、Roster (`{MEMBERS,COUNCIL,LANDS}.md`)、`CLAUDE.md` Status 表 — はすべて **human-readable text** であり、git で履歴管理されている。

この repo にはすでに 3 つの content-addressed substrate が存在:

1. **IPFS / Kubo daemon (PID 21548, `127.0.0.1:5001`)** — ローカル node、`ipfs add` で任意ファイルから CIDv1 が得られる
2. **DataLad subdataset** (ADR-2605262400 / 2605262500) — git-annex `directory` backend で `.gitattributes` 越しに version 管理された CID 集合
3. **kotoba** (ADR-2605262130; subrepo at `40-engine/kotoba/`, upstream `a673a8ce6` as of pull `5e05ac98f`) — `TieredBlockStore<BudgetedMemory, KuboIpfs>` で cold tier として上記 Kubo daemon を直接参照する。EAVT/AEVT/AVET/VAET の 4-index Datalog 検索 surface

「データを kotoba 化する」を素直に解釈すると **(a) kotoba 内に重複ストアを作る** が浮かぶが、これは **content-addressed substrate の二重化** であり、ADR-2605262130 の SSoT 統合方針に反する。代わりに本 ADR は:

- **ファイル (git working copy) を canonical SoT** に保つ
- **同じ CID** を IPFS / DataLad / kotoba-BlockStore が共有(Kubo daemon が物理保持先)
- **kotoba の quad 層** は metadata + relation index として薄く被さる
- 文章 (blob) は kotoba から `block.get <CID>` で取得可能(透過的に Kubo 経由)、ただし正本は依然ファイル

を採用する。

# Decision

## 5.1 Direction-of-Truth (G1)

```
                ┌─ git (canonical, human edit) ─────┐
file (md/toml/json)                                  │
     │                                               │
     ▼                                               │
ipfs add (Kubo) ──► CID ──► DataLad subdataset ─────┘
                     │
                     ├─► kotoba KuboBlockStore (cold tier; transparent fetch)
                     │
                     └─► kotoba quad (subject=resource_iri, predicate=hasCid, object=CID)
                              │
                              └─► kotoba quad layer:
                                  status / supersedes / depends_on / title / topic / ...
```

**Invariants**:

- **D1 (file SoT)**: 文章本文の正本は常に git。`git checkout` + 編集 + commit が一次操作。
- **D2 (kotoba 読み取り専用)**: kotoba は **ファイルシステムに書き戻さない**。すべての更新は file → kotoba 一方向。
- **D3 (同一 CID 共有)**: 同一ファイルに対する CID は IPFS / DataLad / kotoba で同一(全部 Kubo daemon 経由 CIDv1 sha2-256)。
- **D4 (再現性)**: 任意 git HEAD で再 ingest した結果の quad 集合は決定論的。

## 5.2 Quad Schema

**Graph**:`kotoba:graph:etzhayyim-root` (single canonical graph; sub-graph 分割は将来検討)。

**Predicate vocabulary** (CURIE-like; full form `com.etzhayyim.apps.kotoba.monorepo:<short>`):

| Predicate | Domain | Range | 説明 |
|---|---|---|---|
| `hasCid` | any resource | CIDv1 (multibase) | リソース本文の content-CID |
| `filePath` | any resource | string | git working-copy path (repo-relative) |
| `docType` | doc | `adr` / `reference` / `how-to` / `tutorial` / `explanation` / `lexicon` / `roster` / `registry` | YAML front matter `doc_type` の写像 + lexicon/roster/registry の拡張 |
| `status` | adr/doc | `active` / `proposed` / `deprecated` / `superseded` | YAML `status` |
| `title` | doc | string | YAML `title` |
| `topic` | doc | string | YAML `topic` |
| `authoritative` | doc | bool | YAML `authoritative` |
| `lastVerified` | doc | ISO-8601 date | YAML `last_verified` |
| `supersedes` | adr | adr-id | DAG edge |
| `supersededBy` | adr | adr-id | reverse of `supersedes` |
| `dependsOn` | adr | adr-id | dependency edge |
| `relatedTo` | doc | doc-id | weak relation |
| `nsid` | lexicon | string | AT Proto NSID |
| `lexiconType` | lexicon | `record` / `query` / `procedure` / `subscription` | from `defs.main.type` |
| `roster` | roster | `members` / `council` / `lands` | which roster file |
| `registryEntry` | deps.toml row | string | `[[adrs]]` / `[[modules]]` / `[[charters]]` table identifier |
| `gitSha` | ingest-run | sha1 | git HEAD at ingest time (provenance) |
| `ingestRun` | any resource | ingest-run-id | リソースを emit した ingest run |

**Subject IRI naming**:

- ADR: `adr:2605281700` (just ID; ファイル名ではなく ADR id)
- Lexicon: `lex:com.etzhayyim.feed.discover` (NSID)
- deps.toml row: `deps:adrs:adr-2605281700` (table.row)
- Roster: `roster:members` / `roster:council` / `roster:lands`
- CLAUDE.md Status row: `status:row-<N>` (table row index)
- Free-form doc: `doc:<repo-relative-path-slugified>`
- Ingest run: `ingest:<git-sha>:<utc-iso>`

**Object encoding**:

- CIDs are CIDv1 multibase base32 (e.g., `bafkrei...`)
- Dates are ISO-8601 UTC strings
- IRIs are bare strings (subject/predicate vocabulary documented in this ADR)
- Booleans are `true` / `false` string literals (per current kotoba quad object encoding)

## 5.3 Ingest Pipeline

**Tool**:`70-tools/kotoba-monorepo-ingest/` (new; Rust binary `kotoba-monorepo-ingest`)。

**Steps per ingest run**:

1. `git rev-parse HEAD` → `git_sha`
2. Walk repo tree per *.gitignore* respecting + per per-type matcher
3. For each matched file `F`:
   a. Compute CID: `curl -s -F file=@F http://127.0.0.1:5001/api/v0/add?cid-version=1` → CID
   b. Pin: `curl -s -X POST "http://127.0.0.1:5001/api/v0/pin/add?arg=<CID>"`
   c. Parse YAML front matter (markdown) or schema fields (JSON/TOML)
   d. Emit quads via `kotoba quad put` (or batch XRPC)
4. Emit `ingestRun` provenance quad: `(ingest:<git_sha>:<utc>, hasCid, <CID-of-manifest>)` + per-resource `(resource, ingestRun, ingest:...)`.

**Idempotency**:

- Quad creation is idempotent (kotoba's `quad.create` semantics: same subject+predicate+object = no-op).
- CIDs are deterministic from content → re-run on unchanged file produces no diff.
- `ingestRun` provenance creates a new row per run (intentional — provenance trail).

## 5.4 Phasing

- **Phase 0 (this ADR)** — schema 凍結、ファイル SoT 不変、quad vocabulary lock。
- **Phase 1** — ADR コーパス (`90-docs/adr/*.md`) ingest tool + CLI query macro (`kotoba adr deps-of <id>`)。最小 surface。
- **Phase 2** — Lexicon (`00-contracts/lexicons/**/*.json`) ingest。NSID lookup + `lexiconType` index。
- **Phase 3** — `deps.toml` ingest。`[[adrs]]` / `[[modules]]` / `[[charters]]` を quads 化。
- **Phase 4** — Roster 3 + CLAUDE.md Status 表 ingest。テキスト構造抽出が重い分後回し。
- **Phase 5** — `e7m verify` 系 lint を kotoba query に置換(現状 grep ベースの依存検査を SPARQL/Datalog ベースに移行)。
- **Phase 6** — git hook 起動 (post-commit) で increment 再 ingest を自動化。

各 Phase は独立 ADR (R0..R6)。R0 が本 ADR、R1 以降は実装と同時に投下。

# Consequences

## 6.1 Gates (R0 invariants — Council Lv6+ ≥3 to amend)

- **G1**: 同一 git HEAD + 同一ファイル → 同一 CID 集合(Kubo の CIDv1 sha2-256 決定論性に依存)。
- **G2**: kotoba quad 層は **読み取り専用 projection**。`kotoba quad put` を file から file に逆方向に流す経路を実装しない。
- **G3**: ingest tool は `127.0.0.1:5001` (ローカル Kubo) のみを呼び、商用 IPFS pinning service (Pinata 等) を直接たたかない。Religious-corp Murakumo-only 制約 (ADR-2605215000) と整合し、外部依存を増やさない。
- **G4**: 各 ingest run は `ingestRun` provenance quad を emit し、`gitSha` 予測語経由で git history と 1-to-1 で照合可能。
- **G5**: schema の Predicate 追加は本 ADR 改定(Council Lv6+ ≥3) で行う。`G5-relaxed`: ADR-level に限り、新 predicate の追加は新規 ADR の `supersedes/superseded_by` で表現できれば本 ADR 改定不要(将来 R1+ ADR で実例を確立)。
- **G6**: `kotoba server` 側は `KOTOBA_STORE_PATH` + `KOTOBA_IPFS_ENDPOINT=http://127.0.0.1:5001` での起動を前提とする(TieredBlockStore の cold tier 必須)。`KOTOBA_NO_SWARM=1` での起動は P2P 配布を犠牲にするが本 ADR の機能には影響しない。
- **G7**: Charter Rider scan は ingest 入口で実施(本 ADR は public-data 前提だが、構成的に Rider §2(a)-(h) の侵害が紛れ込まないよう watch dog として保持)。違反検出 → ingest abort + quad emit 拒否。

## 6.2 Non-goals

- **N1**: kotoba を authoritative SoT にしない。`git revert` で完全に戻せる構造を保つ。
- **N2**: real-time sync しない。ingest は手動 or post-commit hook トリガで足りる。
- **N3**: encrypted content の ingest はしない。Per user 2026-05-28 「etzhayyim のデータは public なので public 前提 OK」。private/restricted 系は別 ADR で `com.etzhayyim.encrypted.*` (ADR-2605181100) 経路を併用。
- **N4**: 双方向 sync しない。kotoba → ファイルへの書き戻し経路は実装しない(D2)。
- **N5**: AT Protocol MST projection (`app.bsky.feed.post` 等) の置換ではない — それは ADR-2605231902 の領域。本 ADR は monorepo 内 file 系のみを対象。
- **N6**: e7m-dataset (ADR-2605262400) の置換ではない — 大規模 dataset (RIR / GeoLite2 / Common Crawl など) は引き続き e7m-dataset で扱う。本 ADR は monorepo 内の "doc / schema / registry" 階層を対象。
- **N7**: CHARTER-RIDER.md 削除の upstream 方針との直接整合確認は別 ADR。本 ADR は ingest schema のみを scope とし、kotoba subrepo 内の Rider の有無自体は ADR-2605192200 と別途整理する(2026-05-28 時点では subrepo は remote-wins で Rider 不在、commit `a4bb5cf89`)。

## 6.3 Risk

| Risk | Severity | Mitigation |
|---|---|---|
| Kubo daemon 未起動でingest 全停止 | High | ingest tool が起動チェック + actionable error message |
| CID 衝突 (Kubo 設定変更で algorithm 変化) | Low | Kubo の `--cid-version 1 --hash sha2-256` を強制(`api/v0/add?cid-version=1`) |
| Schema drift (predicate vocabulary が ADR と乖離) | Medium | R1+ 各 ADR で vocabulary diff を明示。`G5-relaxed` 適用 |
| ingest tool が religious-corp 制約 を破る (例: 外部 PSA に pin) | High | G3 + G7 で構造的に阻止 |
| 並列 ingest 競合 | Low | kotoba `quad.create` は idempotent。並列 run は実害なし |
| file CID と quad object のラップアラウンド (mtime 違い等) | Low | Kubo の add は内容 hash のみで mtime 非依存 |

# Alternatives Considered

## A. kotoba を SoT、ファイルを projection (棄却)

ADR-2605262130 の最終形に近いが:

- **理由**: 既存の git workflow (PR review / blame / log) を喪失。LLM が markdown を読む現行の読みやすさが消える。adoption コスト過大。
- **将来再検討**: Phase 5-6 で `e7m verify` ベースの kotoba query が安定し、人間編集も kotoba 経由になる十分な tooling が揃ったら R3 ADR で再検討。

## B. ファイル本文を kotoba block に複製 (棄却)

`block put` でファイル全文を kotoba BlockStore に投入し独立コピーを持つ案:

- **理由**: 同じ blob を IPFS と kotoba block の両方に書き込むのは content-addressed 二重化。Kubo daemon を BlockStore の cold tier とする現在のアーキ (`TieredBlockStore<BudgetedMemory, KuboIpfs>`) が **すでに同じ CID を共有** しているので不要(本 ADR 採用案で透過的アクセスが既に得られる)。

## C. Quad schema を RDF/Schema.org full vocabulary に揃える (棄却)

- **理由**: schema.org / dc:terms / SKOS の語彙を全部 import すると vocabulary が肥大。本 ADR の scope (monorepo 内 file projection) には過剰。R5+ で SPARQL federation を導入する段になれば、necessary subset を明示マップで吸収。

## D. e7m-dataset (ADR-2605262400) substrate に統合 (一部採用)

`e7m-dataset` は IPFS-pinned DataLad subdataset を扱う substrate。本 ADR の対象 (monorepo 内 markdown / json / toml) は **粒度が小さく頻度高く更新** されるため、e7m-dataset の "datasetPin" Lexicon を毎ファイル emit するのは過剰。

ただし **共通の Kubo daemon を経由** する点と **CID-addressed** である点は同じ。R3-4 の ingest tool 実装時に `e7m-dataset` の helper (`pin/unpin/sha` 経路) を再利用可能であれば再利用する(複数の `ipfs add` パス共存を避ける)。

# References

- ADR-2605262130 (kotoba storage substrate unification — supersedes kotoba-datomic composition + projection)
- ADR-2605262400 (public-data ingestion organism ecosystem — IPFS-pinned DataLad subdataset 機構)
- ADR-2605241500 (e7m-dataset substrate)
- ADR-2605262500 (robotics-sim world-data ingestion — sibling on geospatial axis)
- ADR-2605215000 (Murakumo-only inference — applies to "ingest tool が外部に出ない" 原則)
- ADR-2605192100 (mission charter — public data 前提との整合)
- ADR-2605192200 (Charter Rider v2.0 — G7 scan の根拠)
- ADR-2605170900 (etzhayyim/root ADR canonical home — placement policy)
- ADR-2605231902 (feed-post membrane + feed-discover projection — separate concern, AT Proto MST 上の projection)
- `40-engine/kotoba/crates/kotoba-cli/src/main.rs` (CLI subcommands: serve / block {put,get} / quad {put,retract,query} / health)
- `40-engine/kotoba/crates/kotoba-store/src/kubo_block_store.rs` (KuboBlockStore — TieredBlockStore cold tier の実装)
- Kubo HTTP API: `POST /api/v0/add?cid-version=1`, `POST /api/v0/pin/add`, `GET /api/v0/block/get`
