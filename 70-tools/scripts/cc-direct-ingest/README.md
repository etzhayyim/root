# cc-direct-ingest — Common Crawl WET → kotoba Datom log（parquet 不要）

Common Crawl の WET（抽出テキスト）アーカイブを HTTP ストリーミングで読み、
`cc/chunk/*` datoms として `com.etzhayyim.apps.kotoba.datomic.transact` 経由で
canonical な `cc:2026-12:chunks` named graph に直接書き込む。永続化は
**kotoba Datom log（first-class canonical state）+ IPFS block backend** で完結し、
parquet は入力ワイヤとしても at-rest としても一切登場しない。

ADR: `90-docs/adr/2606111200-cc-wet-direct-datom-ingest-no-parquet.md`

## 性質

- **crawler ではない**（ADR-2606012300 の "no crawler by design" を維持）。
  ソースは Common Crawl の公開 WET アーカイブのみ。
- **ダウンロードは有界**: multi-member gzip を増分デコードし、`--max-pages`
  に達した時点で接続を切る。150 MB の WET でも小バッチなら数 MB で済む。
- **pure stdlib**(Python 3.10+)。依存ゼロ。
- 書き込み後 `--reindex` で BM25/PageRank を再構築 →
  `com.etzhayyim.apps.kotoba.search.web` で検索可能（lexical leg）。
  semantic leg(`cc/embed/*`)は別途 embed パス、authority leg は links graph
  が必要（WET にはリンクが無い — WAT/webgraph が将来増分）。
- **server 側の R0 read-path 壁に注意**(ADR 参照): corpus が ~30k datoms を
  超えると commit / cc.status / search.web がリクエスト毎の full-graph
  cold load で数分級になる。`--batch-kib`(default 96) を小さく保ち、
  `--timeout`(default 900s) を十分取ること。数千 datoms までは即応。

## 使い方

```bash
# 稼働ノードの operator DID を確認
grep -a "node identity" ~/.local/kotoba-etzhayyim/serve.log | tail -1

# crawl の先頭 WET ファイルから 50 ページ ingest → reindex
./ingest_wet.py --crawl CC-MAIN-2025-47 --max-pages 50 --reindex \
    --did did:key:z...

# WET URL / ローカルファイル直接指定、日本語のみ
./ingest_wet.py --wet https://data.commoncrawl.org/crawl-data/.../x.warc.wet.gz \
    --lang ja --max-pages 100 --reindex --did did:key:z...
```

主なオプション: `--server`(default `$KOTOBA_URL` / `http://127.0.0.1:8077`) /
`--max-chunks-per-page`(8) / `--chunk-chars`(800) / `--lang`(2文字フィルタ)。

## テスト

```bash
python3 -m unittest test_ingest_wet   # 15 tests, ネットワーク・サーバー不要
```

## 認証メモ

kotoba-server の operator auth は「edge が trust boundary」モデル
(`graph_auth.rs`)で、Bearer JWT は `sub`(operator DID)+ `exp` のみ検査される。
`KOTOBA_INTERNAL_SECRET` を設定したノードでは `x-internal-trust` ヘッダも必要
（本スクリプトは未対応 — その環境では edge BFF 経由で呼ぶこと）。
