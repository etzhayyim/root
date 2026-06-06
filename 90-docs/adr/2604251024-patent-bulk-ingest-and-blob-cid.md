---
id: adr-2604251024-patent-bulk-ingest-and-blob-cid
title: "ADR: Patent bulk ingest (USPTO + EPO free) + full PDF/webp/OCR persistence to B2"
status: proposed
doc_type: adr
topic: patent-coverage
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - patent ingest data sources (USPTO PatentsView, EPO OPS)
  - vertex_patent_blob schema (PDF + webp + OCR text CIDs)
  - PDF→webp conversion pipeline placement (Vultr pod, not CF Worker)
  - patent federable status (default non-federable)
related:
  - adr-0056-bpmn-as-actor
  - adr-0048-kotoba-vultr-b2-primary
  - adr-0081-worker-direct-hyperdrive-persistence
  - adr-0085-non-federable-nsid-firehose-gate
supersedes: []
superseded_by: []
---

# Context

`mv_world_coverage_live` 上で patent は world_total=200,000,000 に対して
collected=3,799 / vertex_count=81 (`coverage_rate ≈ 0.000019`)。trademark は
1 行、copyright (vertex_work) は 37,587 行。**公開知財の世界的網羅は実質ゼロ**。

一方、配線は 8 割完成している:

- Lexicon: `00-contracts/lexicons/com/etzhayyim/apps/patent/{patent,get,list,coverage}.json`
- Schema: `vertex_patent` (legacy 23 列), `vertex_open_patent_patent`
  (ADR-0056 wave 5, 2026-04-24, migration `20260424170000_vertex_open_patent.ts`)
  + `edge_patent_cites` + `edge_family_member` + `edge_open_patent_citation_pair`
  + `mv_open_patent_by_jurisdiction`
- Manifest: `20-actors/patent/actor-manifest.jsonld` (489 行)、4 source entity
  (JPO/USPTO/EPO/WIPO) を `did:web:patent.etzhayyim.com:source:*` で記述済
- Magatama: `60-apps/etzhayyim-project-patent/appview/etzhayyim-wasm-patent-p4t3nt01/magatama.jsonld`
  に `subscribeRepos` で 6 NSID 受信設定済
- Blob CID 前例: PDS `blobs/{repo}/{sha256hex}` content-addressed R2 dedup
  (`pds-blob-content-addressing`)、`vertex_gyosei_source_blob` /
  `vertex_fukkou_evidence_blob` / `vertex_media`

足りないのは **(a) ingest pipeline (bulk dump pull → INSERT)**、
**(b) PDF→webp 変換と CID 永続化**、**(c) BPMN-as-actor 化** の 3 点のみ。

## なぜ今やるか

1. **mv_world_coverage_live の最大ギャップ**: 460 domain 中で patent は
   "collected/world_total" 比が単独でワースト級 (0.00002%)。trademark / copyright も
   同水準だが、特許は市場・LEI・ISIC との cross-link 価値が最大 (R&D 投資 / 産業集積 /
   technology mapping の 1 次データ)。
2. **bulk dump が free**: USPTO PatentsView は granted patent 全データを TSV で
   weekly 公開 (g_patent / g_inventor / g_assignee / g_uspc_at_issue / g_cpc_at_issue /
   g_us_patent_citation)、auth 不要、CC0。EPO OPS REST も free tier (4GB/week) で
   citation/family を補完可能。商用 dump (EPO DOCDB 全件) は Phase 2 に先送り。
3. **基盤が整った**: ADR-0056 BPMN-as-actor (2026-04-23 active) で "INSERT 2 rows
   → 30s 後に live actor" の建付けが完成済。Vultr B2 primary (ADR-0048, 2026-04-22
   cutover) で大容量 blob storage が安価 ($0.006/GB)。Worker-direct Hyperdrive
   (ADR-0081) で bulk INSERT が PDS 経由ボトルネックを回避。

# Decision

**データ取得は無料ソースに限定 / 保存は B2 で全件永続化** という方針。

- **Acquisition (free only)**: USPTO PatentsView TSV (CC0)、EPO OPS REST (free tier
  4GB/week) に限定。商用 dump (EPO DOCDB / Google Patents BigQuery) は Phase 2 で
  別 ADR を経て予算合意してから着手。
- **Persistence (B2, paid OK)**: PDF / webp / OCR text は全件 B2 に持続化。
  ADR-0048 で確立した B2 が SSoT。CF R2 を経由しない (free tier 10GB は patent の
  scale に合わない)。
- **Conversion**: PDF→webp / OCR text は Vultr LAX の k8s pod に常駐 worker を
  立てて連続変換 (CF Worker は CPU 30s 制限 + ネイティブバイナリ unfit)。

ADR-0056 BPMN-as-actor で ingest pipeline を実装。CID は multibase (`b` base32) +
`raw` codec + sha2-256 multihash (ADR-0029 整合)。

## Sources (Phase 1 採用 / Phase 2 deferred)

| Source | License | Size | 採用 Phase | 備考 |
|---|---|---|---|---|
| **USPTO PatentsView TSV** | CC0 | granted ~8M / app ~12M / cite ~120M | **Phase 1** | weekly dump、normalized |
| **USPTO Bulk Data Storage System (XML)** | Public Domain | full text 1976+, ~4TB | Phase 1.5 | full-text 検索が必要になったら |
| **EPO OPS REST** | Free tier | 4GB/week throttle | **Phase 1** | citation/family/INPADOC 補完専用 |
| EPO DOCDB 全件 dump | 有料 (年 €€€) | 100M+ records | Phase 2 | EU/CN/KR/...全 jurisdiction 拡張時 |
| JPO J-PlatPat | 規約確認要 | ~8M JP | Phase 2 | XML feed の有無調査必要 |
| WIPO PATENTSCOPE | Free API throttle | 国際出願 | Phase 2 | PCT のみ optional |
| Google Patents Public Dataset (BigQuery) | CC-BY (?) | 130M records | 検討中 | 法務確認後採用可能性 |

**Phase 1 完了時の到達点**: USPTO granted ~8M (1976+) + citation ~120M を
Kotoba/Datomic に投入、世界 ~200M 中の **~4%** カバー (metadata = title / abstract /
inventor / assignee / IPC / CPC / filing / grant date / source_url)。EPO citation
補完で `edge_patent_cites` の cross-jurisdiction 解像度が向上。**granted 2010+
~1M に対して PDF / webp / OCR text を全件 B2 永続化** (CID は graph に保持)。
2010 未満 (~7M) は metadata のみ Phase 1、blob 化は Phase 2 で全件拡張。

## Architecture (ADR-0056 BPMN-as-actor)

新規 Worker コードはゼロ。BPMN file 2 本 + INSERT 2 rows per process。

```
ingest-uspto-weekly.bpmn  (Timer-start R/P7D, Sun 00:00 UTC)
  ├─ http.fetch  https://s3.amazonaws.com/data.patentsview.org/download/manifest.json
  ├─ http.fetch  g_patent.tsv.zip → stream unzip
  ├─ db.insert   vertex_open_patent_patent (batch 2000, ON CONFLICT は使わない / RW PK upsert)
  ├─ http.fetch  g_us_patent_citation.tsv.zip
  ├─ db.insert   edge_open_patent_citation_pair (batch 2000)
  ├─ db.insert   vertex_open_patent_citation
  └─ audit.emit  rows/sec, errors, manifest_version

ingest-epo-citation-fill.bpmn  (Event-trigger from new vertex_open_patent_patent rows OR cron R/PT6H)
  ├─ db.select   patents WHERE jurisdiction='US' AND citation_count IS NULL LIMIT 1000
  ├─ http.fetch  ops.epo.org/.../published-data/publication/.../biblio  (throttle 100 req/min)
  ├─ db.insert   edge_open_patent_citation_pair (cross-jurisdiction)
  └─ audit.emit
```

`vertex_bpmn_process_def` + `vertex_bpmn_lexicon_binding` に 2 行 INSERT →
F5 watcher (30s) → Zeebe deploy → live。

## Blob persistence: vertex_patent_blob (新規 vertex, B2 全件永続化)

新規 migration `20260425<NNNNNN>_vertex_patent_blob.ts`:

```sql
CREATE TABLE vertex_patent_blob (
  vertex_id varchar PRIMARY KEY,         -- at://did:web:patent.etzhayyim.com/com.etzhayyim.apps.patent.blob/{patent_number}
  _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,

  patent_vertex_id varchar NOT NULL,     -- FK vertex_open_patent_patent.vertex_id
  patent_number varchar NOT NULL,
  jurisdiction varchar NOT NULL,

  -- Original PDF (B2 key = `patent-blobs/pdf/{pdf_sha256}`)
  pdf_sha256 varchar,                    -- content-addressed dedup key
  pdf_bytes bigint,
  pdf_page_count int,
  pdf_source_url varchar,                -- patents.uspto.gov / register.epo.org

  -- webp 変換結果 (B2 key = `patent-blobs/webp/{webp_cid}`)
  webp_cid varchar,                      -- CIDv1 multibase b + raw codec + sha2-256 (ADR-0029 整合)
  webp_bytes bigint,
  webp_quality int,                      -- cwebp -q (default 80)

  -- OCR text (B2 key = `patent-blobs/text/{text_cid}`)
  ocr_text_cid varchar,
  ocr_engine varchar,                    -- 'pdftotext' (Phase 1) / 'tesseract' (Phase 1.5 OCR fallback)

  status varchar NOT NULL,               -- 'pending' | 'pdf_fetched' | 'webp_done' | 'ocr_done' | 'failed'
  last_error varchar,
  collected_at varchar
);

-- Streaming MV: 進捗ダッシュボード
CREATE MATERIALIZED VIEW mv_patent_blob_coverage AS
  SELECT
    jurisdiction,
    COUNT(*) AS total,
    COUNT(pdf_sha256) AS pdf_fetched,
    COUNT(webp_cid) AS webp_done,
    COUNT(ocr_text_cid) AS ocr_done,
    SUM(pdf_bytes)/1e12 AS tb_pdf,
    SUM(webp_bytes)/1e12 AS tb_webp
  FROM vertex_patent_blob
  GROUP BY jurisdiction;
```

PK は `at://...` 形式 (ADR-0056 canonical vertex_id 規約と整合)。`ON CONFLICT`
は使わない (RW 仕様: 同一 PK 再 INSERT で overwrite — Root CLAUDE Bsky/RW split rule)。

**Phase 1 対象**: granted 2010+ ~1M (filter `WHERE filing_date >= '2010-01-01'`)。
2010 未満 (~7M) は Phase 2 で予算追加して全件拡張。Ingest 時に metadata 行 (8M) と
ペアで 2010+ 限定で `vertex_patent_blob` 行 (status='pending') を作る。

## PDF→webp 変換 worker (Vultr pod, 常駐)

CF Worker は CPU 30s 制限 + ネイティブバイナリ unfit (`pdftocairo` / `cwebp` /
`pdftotext`) のため **Vultr LAX に k8s Deployment で常駐 pod** を立てる。
ADR-0048 で確立した Vultr 単一インフラに寄せる。B2 同 region (LAX) 配置で egress
$0 (Bandwidth Ally)。

```
patent-blob-converter (k8s Deployment, Vultr LAX, replicas=1)
  loop (every 30s):
    rows = SELECT vertex_id, pdf_source_url FROM vertex_patent_blob
           WHERE status='pending' ORDER BY _seq LIMIT 100
    for each row:
      1. HEAD pdf_source_url, abort if 404 → status='failed'
      2. download PDF → compute sha256 → B2 PUT patent-blobs/pdf/{sha256} (HEAD で skip)
      3. pdftocairo -png → cwebp -q 80 → compute CIDv1 → B2 PUT patent-blobs/webp/{cid}
      4. pdftotext 抽出 → CIDv1 → B2 PUT patent-blobs/text/{cid}
      5. UPDATE vertex_patent_blob SET pdf_sha256, webp_cid, ocr_text_cid, status='ocr_done'
```

**docker image**: `python:3.12-slim` + `poppler-utils` + `webp` + `boto3` +
`psycopg2-binary`。B2 endpoint は `s3.us-west-004.backblazeb2.com` (Vultr LAX と
同 region pair で egress 無料)。

**resource**: 1 CPU / 1 GiB RAM / pvc 不要 (B2 直送)。並列度は pod replica で調整
(Phase 1 = 1 replica で ~3 weeks / 1M 件、replica=3 で 1 week)。

## CID 仕様 (ADR-0029 整合)

- multibase prefix: `b` (base32)
- multicodec: `raw` (`0x55`) — opaque bytes (webp / text 共通)
- multihash: `sha2-256` (`0x12`)
- 例: `bafkreigh2akiscaildc...` (webp), `bafkreid7e6vsfh...` (OCR text)

ADR-0029 の did:etzhayyim CID 仕様と同じ codec/hash 群を使うので、将来 patent blob を
did:etzhayyim path-form sub-DID で参照する拡張が容易 (e.g. `did:web:patent.etzhayyim.com/blob/{cid}`)。

## Federation policy

`com.etzhayyim.apps.patent.*` は **default non-federable** (ADR-0085 / `federable-nsid-allowlist`):

- Tier 1 PII あり (inventor 名 / assignee 法人名) だが公開情報のみ
- 商業情報 — 競合他社 firehose 経由 mass scrape のリスクは中
- bsky.app 等の社外 PDS が patent feed を購読する合理的理由は低

**判定**: Phase 1 は non-federable 維持、graph SQL XRPC + `getPatent` /
`listPatents` query 経由で外部公開。Phase 2 で公開 feed (`patent.feed.daily`) の
federable opt-in を再検討。

## Coverage MV update

`dim_world_domain` の patent エントリに `world_total=200_000_000` を維持しつつ、
`mv_world_coverage_live` 上で patent.etzhayyim.com の vertex_count が 8M レンジに到達する。

新規 MV `mv_patent_coverage_by_year_jurisdiction`:

```sql
CREATE MATERIALIZED VIEW mv_patent_coverage_by_year_jurisdiction AS
  SELECT
    jurisdiction,
    SUBSTRING(filing_date, 1, 4) AS filing_year,
    COUNT(*) AS app_count,
    COUNT(grant_date) AS granted_count,
    AVG(novelty_score) AS avg_novelty
  FROM vertex_open_patent_patent
  WHERE filing_date IS NOT NULL
  GROUP BY jurisdiction, SUBSTRING(filing_date, 1, 4);
```

# Implementation plan

| Step | Deliverable | ETA |
|---|---|---|
| 1 | Migration `20260425<NNNNNN>_vertex_patent_blob.ts` | day 1 |
| 2 | BPMN files: `ingest-uspto-weekly.bpmn` / `ingest-epo-citation-fill.bpmn` / `patent-blob-convert.bpmn` (新 primitive `generic.pdf.to_webp` + `generic.cid.compute`) | day 2 |
| 3 | INSERT 3 rows in `vertex_bpmn_process_def` + binding (seed migration) | day 2 |
| 4 | Smoke test: USPTO `g_patent.tsv` 1 file, 100 行 INSERT + 1 件 PDF→webp→B2 PUT 動作確認 | day 3 |
| 5 | B2 bucket `patent-blobs` 作成 (us-west-004, Vultr LAX 同 region) + IAM key + Vultr Secret 登録 | day 3 |
| 6 | Backfill: granted 1976+ ~8M rows metadata (full TSV pull, ~4h LAN) | day 4-5 |
| 7 | converter pod deploy (Vultr LAX, replicas=1) | day 5 |
| 8 | EPO OPS citation fill BPMN live | week 2 |
| 9 | granted 2010+ ~1M PDF→webp→OCR 全件変換 (replicas=3 で 1 week / replicas=1 で 3 week) | week 2-4 |
| 10 | `mv_world_coverage_live` + `mv_patent_blob_coverage` 確認 (patent: 0.00002% → ~4%, blob 1M / 1M) | week 4 |

# Cost estimate

データ取得は **無料ソースのみ** (USPTO PatentsView TSV CC0 / EPO OPS free tier 4GB
per week)。保存・変換は B2 + Vultr で課金。

| Item | Phase 1 (granted 2010+ ~1M blob 化) | 備考 |
|---|---|---|
| USPTO PatentsView TSV | **$0** | CC0 public, no auth |
| EPO OPS REST | **$0** | free tier 4GB/week (citation fill のみ) |
| Kotoba/Datomic 増分 (~10M vertex + 120M edge) | **$0** | 既存 Vultr cluster の空き容量で吸収 |
| B2 storage (PDF ~10TB) | ~$60/mo | 1M × ~10MB |
| B2 storage (webp ~1TB) | ~$6/mo | webp -q 80 で ~10x 圧縮 |
| B2 storage (OCR text ~50GB) | ~$0.30/mo | UTF-8 plain text |
| B2 egress (Vultr LAX 同 region Bandwidth Ally) | **$0** | Vultr ↔ B2 LAX 無料 |
| Vultr converter pod (1 vCPU / 1 GiB, replicas=1) | ~$6/mo | $0.012/h × 24 × 30 |
| **合計 (Phase 1)** | **~$72/mo** | replicas=3 にすると converter +$12/mo |

Phase 2 (granted 全件 webp 化 ~7M 追加 + EPO/JP/CN/KR 全 dump、~100M patent +
~50TB PDF) で B2 storage ~$300/mo + Vultr pod scale up ~$30-50/mo の試算。
別 ADR で予算合意してから着手。

# Consequences

## Positive

- patent coverage 0.00002% → ~4% (200M 中 ~8M) で `mv_world_coverage_live` 上の
  ワースト drag が解消
- LEI / ISIC / natural-person との cross-link で R&D / 産業集積 / technology
  mapping query が実装可能 (kenkyusha / talent / legal-entity actor 連携)
- citation graph (~120M edge) で PageRank / forward-citation 影響度の `mv_*` 系列を
  追加可能 (Phase 1.5)
- 同パターンを trademark (WIPO Madrid bulk) / copyright (Crossref DOI dump) に
  適用可能 — 3 actor 同形 ingest framework が確立

## Ingest Safety (added 2026-04-25 after smoke-test incident)

Smoke test on 2026-04-25 ran Wikidata SPARQL → direct `psql` INSERT of ~4K
rows. Part-way through the second batch, `kotoba-compute-0` was
OOMKilled; the cold-restart Foyer refill then tripped B2's per-account
rps quota, producing a ~20-minute Hummock `ObjectStore RateLimited` storm
that blocked all RW readers. Root cause was two-fold:

1. **Missing throttle config** — the Linode-era
   `[storage.cache_refill]` + `data_file_cache.insert_rate_limit_mb=450` +
   `meta_file_cache.insert_rate_limit_mb=50` + `statement_timeout_secs=120`
   blocks from `50-infra/linode/kotoba-iceberg/helm/values-dedicated-32.yaml`
   were **not ported** to `50-infra/vultr/kotoba/helm/values.yaml`
   during ADR-0048 Vultr cutover. Ported 2026-04-25; see
   `50-infra/vultr/kotoba/deps.toml [kotoba_vultr.incident_2026_04_25]`
   and `[[migrations]] rw-foyer-insert-rate-limit-port-to-vultr-2026-04-25`
   in root `deps.toml`.
2. **Ingest had no self-throttle** — bulk INSERT ran at wire speed with
   `dml_rate_limit = -1` (unlimited).

This ADR therefore adds two **mandatory runtime invariants** for the
patent / trademark / copyright bulk pipelines (both the BPMN-as-actor
path and any manual `psql` backfills):

### Invariant A — `SET dml_rate_limit` at session start

All ingest sessions that emit more than ~500 rows in aggregate MUST
issue `SET dml_rate_limit = <N>;` before the first INSERT, with
N chosen so that `N × streaming_parallelism` stays below
**~2000 rows/sec total** (the observed safe steady-state on the Vultr
compute pod). The BPMN `generic.db.insert` primitive must carry this as
a default `SET` block, not a per-row option. See `[[conventions]]
rw-bulk-insert-throttle` in root `deps.toml` for the canonical wording.

### Invariant B — 3-point health gate before INSERT

The BPMN `patent_ingest_uspto_weekly` / `patent_ingest_epo_citation_fill`
/ `patent_blob_convert` processes MUST precede any `generic.db.insert`
task with a health-gate service task (new primitive
`rw.health.probe`) that checks:

1. `SELECT 1;` via `psql` with 5-second timeout (meta-plane)
2. `kotoba-compute-0` pod age since last restart > 15 min (Foyer warm)
3. B2 `SlowDown` event rate in the last 60 s of compute logs < 10/min

On any failure, the process pivots to **pre-fetch-only mode** — the
SPARQL / HTTP fetch still happens and the result is staged to B2
(`patent-blobs/staging/{run_id}.jsonl`), but the Hyperdrive INSERT is
skipped and the cursor for that source advances only on a future
healthy fire. See `[[conventions]] rw-health-gate-before-ingest` in
root `deps.toml`.

## Negative

- **B2 storage cost が逓増**: Phase 1 ~$72/mo は granted 2010+ ~1M に絞った値。
  Phase 2 で全 8M + EPO 拡張すると $300-400/mo オーダー。EPO DOCDB 全 dump 採用なら
  さらに上ぶれ。Phase ごとに再評価。
- **EPO OPS rate limit (4GB/week free)**: citation fill が滞る可能性 — fallback
  で cron を遅らせる、Phase 2 で有料 tier 検討。
- **USPTO TSV schema 変更**: PatentsView は時々 column 追加/rename — manifest
  version を `audit.emit` で記録、sentinel value で gate。
- **Kotoba/Datomic 増分 ~10M vertex + 120M edge** は既存 Vultr cluster の空き容量に
  依存。OOM を踏むなら ingest pace を絞る (BPMN timer 週次 → 隔週次)、cluster
  scale-up は別 ADR で扱う。
- **2010 未満 ~7M は metadata only**: 古い patent の PDF/webp は Phase 2 まで
  CID 永続化されない (source_url のみ保持、再取得可能)。

## Neutral

- `vertex_patent` (legacy 23 列) と `vertex_open_patent_patent` (ADR-0056 22 列) の
  二重持ちは継続 — legacy migration は別 ADR で扱う
- WIPO ST.96 XML 互換は Phase 1 では `coverageReport` レベルのみ (XML 全 mapping は
  Phase 2)

# Out of scope

- Trademark / copyright bulk ingest (同パターン適用、後続 ADR)
- patent worker の T2 化 (現 T1 logical actor 維持、BPMN-as-actor で十分)
- Search ranking / vector embedding (Phase 1.5 別 ADR)
- Patent claim 自然言語解析 / Murakumo LLM 連携 (Phase 2)
- Federable feed (Phase 2 再検討)

# References

- ADR-0056 BPMN-as-actor (`90-docs/adr/0056-bpmn-as-actor.md`)
- ADR-0048 Kotoba/Datomic Vultr+B2 primary (`90-docs/adr/0048-kotoba-vultr-b2-primary.md`)
- ADR-0081 Worker-direct Hyperdrive persistence
- ADR-0085 Non-federable NSID firehose gate
- ADR-0029 did:etzhayyim method specification (CID 仕様)
- USPTO PatentsView bulk: https://patentsview.org/download/data-download-tables
- EPO OPS REST: https://developers.epo.org/ops-v3-2
- WIPO ST.96 XML: https://www.wipo.int/standards/en/st96/
