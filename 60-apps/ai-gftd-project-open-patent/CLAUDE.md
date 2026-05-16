# ai-gftd-project-open-patent — Open Patent IP Factory

> **T1 Logical Actor** `open-patent.gftd.ai` (nanoid: `op3np4t1`).
> 特許コーパスを基盤に新しい IP を継続生成し、人間のクレーム起草・出願判断を支援する。

`did:web:open-patent.gftd.ai` — 知的財産生成 + 多管轄特許取得 enrichment actor。

## Role

- **Ingest (Follow-based)**: `patent.gftd.ai` (+ jurisdiction actors) を Follow → AT Protocol firehose から特許データを受信 → `vertex_open_patent_*` に書き込む
- **Enrich**: EPO OPS 引用補填 / JPO / WIPO citation cross-link
- **Generate (Pregel)**: 既存コーパスから技術トレンドを抽出 → LLM が invention seed を生成 → prior art 探索 → novelty スコアリング → HITL flag
- **HITL boundary**: novelty ≥ 60 の seed を `novelty_status='review'` で保存。クレーム起草・出願は人間が行う

## Actor DIDs

| DID | 用途 |
|---|---|
| `did:web:open-patent.gftd.ai` | Controller |
| `did:web:open-patent.gftd.ai:actor:inventor` | Invention seed 生成 出力 DID |
| `did:web:open-patent.gftd.ai:actor:analyst` | Novelty report 出力 DID |

## Collections (NSID)

| Collection | 用途 |
|---|---|
| `ai.gftd.apps.openPatent.patent` | 特許 record (ingest 経由) |
| `ai.gftd.apps.openPatent.citation` | 引用 record |
| `ai.gftd.apps.openPatent.inventionSeed` | LLM 生成 invention idea |
| `ai.gftd.apps.openPatent.noveltyReport` | Prior art + novelty スコアリング |

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
| `open_patent_ingest_multi.py` | `ai.gftd.apps.openPatent.ingestMulti` | 日次 CronJob (0 2 * * *) |
| `open_patent_synthesize_invention.py` | `ai.gftd.apps.openPatent.synthesizeInvention` | 週次 CronJob (0 3 * * 1) |

## Ingest Architecture (Follow-based)

```
patent.gftd.ai  →  AT firehose  →  open-patent subscribeRepos
                                     └→ onCommit(ai.gftd.apps.openPatent.patent)
                                          └→ enrich (EPO citations, JPO cross-link)
```

自前 HTTP pull 禁止。upstream actor (patent.gftd.ai) が PatentsView/EPO OPS/JPO を pull し
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
| USPTO | ✅ ingest済 | patent.gftd.ai via PatentsView |
| EPO | ✅ citation fill済 | patent.gftd.ai via EPO OPS |
| JPO | 🚧 skeleton | future: patent.gftd.ai:jp |
| WIPO/CN/KR | 🚧 skeleton | future: patent.gftd.ai:wo |

## Component

| Component | nanoid |
|---|---|
| `ai-gftd-wasm-open-patent-op3np4t1` | `op3np4t1` |
