---
id: adr-2606111900-cc-wet-direct-datom-ingest-no-parquet
title: "ADR-2606111900: CC WET direct datom-native ingest — parquet を入力ワイヤからも排除"
status: accepted
doc_type: adr
topic: cc-wet-direct-datom-ingest
authoritative: true
last_verified: 2026-06-11
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "kotoba hybrid web search のコーパス投入経路から parquet を完全排除 — WET を datomic.transact で直接 Datom log + IPFS に永続化する pure-stdlib ingester。"
authoritative_for:
  - cc-wet-direct-datom-ingest tool (70-tools/scripts/cc-direct-ingest/)
  - parquet-free CC corpus ingestion path
depends_on:
  - adr-2606012300-kotoba-hybrid-web-search
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605262130-kotoba-storage-substrate-unification
related:
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
supersedes: []
superseded_by: []
---

# ADR-2606111900: CC WET direct datom-native ingest — parquet を入力ワイヤからも排除

**Status**: accepted
**Date**: 2026-06-11
**Deciders**: Jun Kawasaki

# Context

本セッションの起点質問は「parquet ではなく kotoba datomic, ipfs で永続化したい」。

監査結果: 永続化は ADR-2605312345 のとおり最初から **Datom log（canonical
state）→ block store → IPFS cold tier** であり parquet は at-rest には存在しない。
しかし `cc.ingest` endpoint の**入力ワイヤは parquet のみ**（`parquet_dir` 必須、
`cc-parquet` feature）で、CC コーパスを投入するにはローカルに parquet を
置くしかなかった。

一方、live 検証で以下を実証済み:

1. 汎用 `com.etzhayyim.apps.kotoba.datomic.transact`（EDN tx）で
   `cc:2026-12:chunks` graph に `cc/chunk/*` datoms を直接書ける
   （graph CID = `KotobaCid::from_bytes(b"cc:2026-12:chunks")`、
   `web_search` の読む `current_db_for_graph` と同一 head）。
2. transact の commit block + 全 6 index root（EAVT/AEVT/AVET/VAET/TEA/CEAVT）
   が Kubo (localhost:5001) に dag-cbor block として実在し `dag get` で読める。
3. `search.reindex` → BM25 構築 → `search.web` が英語 + CJK
   （バイグラム、分かち書き不要）でヒットする。

# Decision

**`70-tools/scripts/cc-direct-ingest/ingest_wet.py`** — pure-stdlib Python の
datom-native WET ingester を追加する。

- **入力**: Common Crawl の公開 WET アーカイブ（`--crawl CC-MAIN-…` で
  `wet.paths.gz` から先頭ファイル解決、または `--wet <url|path>`）。
  **crawler ではない** — ADR-2606012300 の "no crawler by design" を維持し、
  ソースは CC の公開アーカイブのみ。
- **有界ストリーミング**: CC の .gz は 1 レコード = 1 gzip member の
  multi-member 連結なので、member 境界をまたぐ増分 zlib デコーダを実装
  （単一 decompressobj では先頭 warcinfo で止まる — 実地で踏んだバグ）。
  `--max-pages` 到達で接続を切るため、~150 MB の WET でも小バッチは数 MB。
- **変換**: WARC `conversion` レコード → 行境界 ~800 文字チャンク →
  `cc/chunk/{text,url,domain,lang}` datoms（subject =
  `cc-wet:<sha256(url)[:16]>:<idx>`、決定的 = 再実行冪等）。lang は WET の
  `WARC-Identified-Content-Language`（ISO639-3）を 2 文字へマップ。
- **書き込み**: EDN tx を ≤768 KiB にバッチして `datomic.transact`
  （server 上限 1 MiB）。操作は operator JWT（edge-trust モデル、
  `sub` = node operator DID）。
- **索引**: `--reindex` で `search.reindex` を叩き BM25/PageRank を再構築。

# Consequences

**Done & tested（本セッション）**:

- unit 15/15 green（WARC parse / multi-member gzip / chunking / EDN escape /
  graph-CID が live server と一致 / JWT claims。ネットワーク・サーバー不要）。
- live e2e: CC-MAIN-2025-47 先頭 WET から実ページを ingest（chunk 137 +
  BM25 30,507 terms 着地）→ `datomic.transact` commit（IPNS head 前進、
  commit + 全 6 index root block が Kubo に実在、`dag get` 可読）→
  `search.web q=information` が**実 CC ページにヒット**
  （`fused:["lex"]`、所要 333 s は下記 server R0 壁による）。
- multi-member gzip バグを実地で検出・修正（CC の .gz は 1 record = 1 gzip
  member 連結 — 単一 decompressobj では先頭 warcinfo で止まり 0 page になる）。
- これで CC コーパス投入の全経路が parquet-free:
  **WET (HTTP stream) → datoms → Datom log → IPFS**。

**Honest limitations / deferred**:

- **lexical leg のみ**。WET にはリンクが無いので authority (PageRank) は
  links graph 未投入のまま（WAT / CC webgraph ingest が次の data increment、
  ADR-2606012300 と同じ deferral）。semantic leg（`cc/embed/*`）は
  Murakumo embed パスを通す既存 `cc.ingest` 側の仕事で、本 tool は書かない。
- **server 側 R0 スケーリング壁（実測、本 tool の外）**: 実 ingest で
  commit 時間が corpus 成長とともに 21 ms → 1 s → 9 s と悪化し、
  ~30k datoms（chunk 137 + bm25 30,507 terms）時点で `cc.status` 325 s /
  `search.web` 333 s — ただし**実 CC ページに正しくヒット**する
  （リクエスト毎の full-graph cold load が支配項）。
  数千 datoms までは即応。kotoba-server の read-path resident cache /
  増分 index（ADR-2606012300 の "incremental maintenance is a later
  optimisation"）が R1 の前提条件。tool 側は `--batch-kib`（default 96 KiB）
  + `--timeout`（default 900 s）で対症。
- **スループット**: HTTP 経由 1-tx-at-a-time。大規模（>10⁵ ページ）は
  kotoba 側に Rust `cc.ingest.wet` endpoint を生やすのが R1 候補。
- **ディスク監視前提**: cold-put は fire-and-forget（2026-06-03 に disk-full
  で 14,436 件 silent fail の前科）。大量 ingest 前に Kubo ディスク残量を
  確認するか、`KOTOBA_FS_BLOCKS_DIR`（ADR-2606041151 A）の durable local
  tier を有効化すること。
- `KOTOBA_INTERNAL_SECRET` 設定ノードでは `x-internal-trust` 未対応
  （edge BFF 経由で呼ぶ）。

# Alternatives Considered

- **kotoba (Rust) に `cc.ingest.wet` endpoint を実装** — 正攻法だが kotoba は
  別 repo の submodule で PR 境界が重い。サーバーは既に正しい primitive
  （`datomic.transact`）を公開しており、R0 は外側の tool で十分。R1 候補。
- **parquet 経由の現行 `cc.ingest` を使い続ける** — 永続化自体は同じだが、
  CC parquet 派生データセットの用意という余計な段が残る。WET は CC の
  一次配布物であり直接読める。
- **URL リストの直接 fetch（crawler 化）** — ADR-2606012300 の
  "no crawler by design" に反するため不採用。

# References

- `70-tools/scripts/cc-direct-ingest/{ingest_wet.py,test_ingest_wet.py,README.md}`
- ADR-2606012300（kotoba hybrid web search — BM25 + PageRank + RRF）
- ADR-2605312345（Datom log = first-class canonical state、IPFS = block backend）
- ADR-2606041151（embedded durable local block tier）
- `40-engine/kotoba/crates/kotoba-server/src/xrpc.rs`（`datomic.transact`）
