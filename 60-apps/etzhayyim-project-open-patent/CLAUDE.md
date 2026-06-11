# etzhayyim-project-open-patent — Open Patent IP Factory

> **T1 Logical Actor** `open-patent.etzhayyim.com` (nanoid: `op3np4t1`).
> 特許コーパスを基盤に新しい IP を継続生成し、人間のクレーム起草・出願判断を支援する。

`did:web:open-patent.etzhayyim.com` — 知的財産生成 + 多管轄特許取得 enrichment actor。

## Role

- **Ingest (Follow-based)**: `patent.etzhayyim.com` (+ jurisdiction actors) を Follow → AT Protocol firehose から特許データを受信 → `vertex_open_patent_*` に書き込む
- **Enrich**: EPO OPS 引用補填 / JPO / WIPO citation cross-link
- **Generate (Pregel)**: 既存コーパスから技術トレンドを抽出 → LLM が invention seed を生成 → prior art 探索 → novelty スコアリング → HITL flag
- **HITL boundary**: novelty ≥ 60 の seed を `novelty_status='review'` で保存。クレーム起草・出願は人間が行う

## Actor DIDs

| DID | 用途 |
|---|---|
| `did:web:open-patent.etzhayyim.com` | Controller |
| `did:web:open-patent.etzhayyim.com:actor:inventor` | Invention seed 生成 出力 DID |
| `did:web:open-patent.etzhayyim.com:actor:analyst` | Novelty report 出力 DID |

## Collections (NSID)

| Collection | 用途 |
|---|---|
| `com.etzhayyim.apps.openPatent.patent` | 特許 record (ingest 経由) |
| `com.etzhayyim.apps.openPatent.citation` | 引用 record |
| `com.etzhayyim.apps.openPatent.inventionSeed` | LLM 生成 invention idea |
| `com.etzhayyim.apps.openPatent.noveltyReport` | Prior art + novelty スコアリング |

## RisingWave Tables

| Table | 用途 |
|---|---|
| `vertex_open_patent_patent` | 特許 (USPTO/EPO/JPO/WIPO) |
| `vertex_open_patent_citation` | 引用関係 |
| `edge_open_patent_citation_pair` | 引用 edge |
| `vertex_open_patent_invention_seed` | 生成 invention seed |
| `vertex_open_patent_novelty_report` | Novelty assessment |

## LangGraph Graphs

| Graph module | NSID | Cadence |
|---|---|---|
| `open_patent_ingest_multi.py` | `com.etzhayyim.apps.openPatent.ingestMulti` | 日次 CronJob (0 2 * * *) |
| `open_patent_synthesize_invention.py` | `com.etzhayyim.apps.openPatent.synthesizeInvention` | 週次 CronJob (0 3 * * 1) |

## Ingest Architecture (Follow-based)

```
patent.etzhayyim.com  →  AT firehose  →  open-patent subscribeRepos
                                     └→ onCommit(com.etzhayyim.apps.openPatent.patent)
                                          └→ enrich (EPO citations, JPO cross-link)
```

自前 HTTP pull 禁止。upstream actor (patent.etzhayyim.com) が PatentsView/EPO OPS/JPO を pull し
AT record として公開。open-patent は Follow 経由でのみデータを受信する。

## Generation Pipeline

```
gather_tech_trends
  └→ synthesize_seeds  (LLM, temperature=0.6, per tech_domain)
       └→ search_prior_art  (TEXT search against vertex_open_patent_patent)
            └→ assess_novelty  (LLM, novelty_score 0-100)
                 └→ flag_for_review  (novelty_score ≥ 60 → status='review')
                      └→ emit_audit  → END
```

## Jurisdictions

| Jurisdiction | Status | Source actor |
|---|---|---|
| USPTO | ✅ ingest済 | patent.etzhayyim.com via PatentsView |
| EPO | ✅ citation fill済 | patent.etzhayyim.com via EPO OPS |
| JPO | 🚧 skeleton | future: patent.etzhayyim.com:jp |
| WIPO/CN/KR | 🚧 skeleton | future: patent.etzhayyim.com:wo |

## Component

| Component | nanoid |
|---|---|
| `etzhayyim-wasm-open-patent-op3np4t1` | `op3np4t1` |
