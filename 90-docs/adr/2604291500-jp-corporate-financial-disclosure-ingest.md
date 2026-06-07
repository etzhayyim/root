---
id: adr-2604291500-jp-corporate-financial-disclosure-ingest
title: "ADR: JP Corporate Financial Disclosure Ingest — Kanpo, e-Koukoku, EDINET, and IR"
status: proposed
doc_type: adr
topic: jp-corporate-financial-disclosure-ingest
authoritative: true
last_verified: 2026-04-29
authoritative_for:
  - jp-corporate-financial-disclosure-ingest
  - kanpo-kessan-koukoku-ingest
  - jp-financial-disclosure-langgraph-worker
related:
  - adr-0035-jp-tax-money-flow-reverse-topology
  - adr-2604250836-langgraph-as-zeebe-servicetask
  - adr-2604271600-projector-l7-langgraph-integration
  - adr-0049-python-udf-shared-pool-runtime
  - adr-0056-bpmn-as-actor
  - adr-2604231349-timestamp-numbering-policy
supersedes: []
superseded_by: []
---

# Context

日本法人の決算情報は一つの公的 API では網羅できない。会社法上、株式会社
には決算公告義務があるが、公告方法は官報、日刊新聞紙、電子公告に分かれ、
有価証券報告書提出会社は会社法 440 条の計算書類公告の適用除外となる。
また、実務上は未公告も多い。

したがって本システムは「全法人の決算を取得できる」前提を置かない。
法人番号を母集団として、公開一次ソース別に disclosure evidence を集め、
coverage と missing reason を明示する。

# Decision

JP corporate financial disclosure ingest を **Zeebe + Python worker +
LangGraph** で実装する。Cloudflare Worker は XRPC / MCP の受付と
dispatcher 転送に限定し、長時間 fetch、PDF/OCR、LLM 抽出、照合は
Kubernetes 上の Python worker が担う。

## Scope

対象は公開情報のみ。

| Source | Coverage | Use |
|---|---|---|
| 国税庁 法人番号公表サイト | 法人母集団 | JCN anchor / name / address / status |
| EDINET v2 API | 上場会社・有報提出会社中心 | filings, XBRL facts, officers, securities reports |
| 官報 / 官報情報検索サービス / 官報発行サイト | 官報公告を選んだ会社の決算公告 | balance sheet summary / large-company PL summary |
| 法務省 電子公告システム | 電子公告の調査報告メタデータ | URL discovery / availability evidence |
| 会社 IR / 自社電子公告 URL | company-specific public page | PDF/HTML evidence and extracted statement rows |
| 日刊紙公告 | not bulk-first | on-request evidence only until source contract exists |

Non-goals:

- 税務申告書、非公開計算書類、登記情報提供サービスの有料画面 scraping。
- 「全法人の PL/BS/CF 完備」を KPI にしない。
- LLM 出力を source truth として扱わない。

# Data Model

既存の `vertex_ingest_run` / `vertex_ingest_cursor` /
`vertex_ingest_artifact` を orchestration spine とする。domain facts は
新規 `jp_corp_finance` 系 tables に投射する。

```sql
CREATE TABLE vertex_jp_corp_disclosure (
  vertex_id VARCHAR PRIMARY KEY,
  jcn VARCHAR,
  edinet_code VARCHAR,
  company_name VARCHAR,
  fiscal_year BIGINT,
  period_start VARCHAR,
  period_end VARCHAR,
  disclosure_kind VARCHAR,      -- KANPO_KESSAN, E_KOUKOKU, EDINET_YUHO, IR_PDF, NEWSPAPER
  statement_scope VARCHAR,      -- BS_ONLY, BS_PL, BS_PL_CF, SUMMARY_ONLY, METADATA_ONLY
  source_id VARCHAR,
  source_record_id VARCHAR,
  source_url VARCHAR,
  artifact_uri VARCHAR,
  source_published_at VARCHAR,
  observed_at VARCHAR,
  extraction_status VARCHAR,    -- raw, normalized, extracted, needs_review, failed
  confidence DOUBLE PRECISION,
  status VARCHAR,
  actor_did VARCHAR NOT NULL,
  org_did VARCHAR NOT NULL,
  created_at TIMESTAMP
);

CREATE TABLE vertex_jp_corp_financial_fact (
  vertex_id VARCHAR PRIMARY KEY,
  disclosure_vid VARCHAR NOT NULL,
  jcn VARCHAR,
  edinet_code VARCHAR,
  fiscal_year BIGINT,
  period_end VARCHAR,
  statement_type VARCHAR,       -- BS, PL, CF, NOTES
  concept VARCHAR,              -- normalized local concept, e.g. assets_total
  label_ja VARCHAR,
  value_jpy DOUBLE PRECISION,
  value_text VARCHAR,
  unit VARCHAR,
  source_location VARCHAR,      -- page/line/xpath/xbrl concept
  extraction_method VARCHAR,    -- xbrl, table_parser, ocr_llm, regex, manual
  confidence DOUBLE PRECISION,
  actor_did VARCHAR NOT NULL,
  org_did VARCHAR NOT NULL,
  created_at TIMESTAMP
);

CREATE TABLE vertex_jp_corp_finance_coverage (
  vertex_id VARCHAR PRIMARY KEY,
  jcn VARCHAR NOT NULL,
  company_name VARCHAR,
  disclosure_method VARCHAR,    -- kanpo, newspaper, electronic, unknown
  latest_period_end VARCHAR,
  latest_disclosure_vid VARCHAR,
  coverage_status VARCHAR,      -- current, stale, not_required_edinet, missing, source_unknown
  missing_reason VARCHAR,       -- no_source, not_published, paid_source, parser_failed, not_applicable
  checked_at VARCHAR,
  actor_did VARCHAR NOT NULL,
  org_did VARCHAR NOT NULL,
  created_at TIMESTAMP
);
```

Deterministic IDs:

| Table | `vertex_id` seed |
|---|---|
| `vertex_jp_corp_disclosure` | `jp-corp-disclosure:{source_id}:{source_record_id}` |
| `vertex_jp_corp_financial_fact` | `{disclosure_vid}:{statement_type}:{concept}:{source_location}` |
| `vertex_jp_corp_finance_coverage` | `jp-corp-finance-coverage:jcn:{jcn}` |

# Ingest Families

Do not build one giant crawler. Each source has different cursor and parser
failure modes.

| Family | Source ID | Cadence | Shard key | Output |
|---|---|---:|---|---|
| `jp-corp-finance.jcn-baseline` | `nta-jcn-bulk` | weekly | prefecture / zip member | coverage baseline |
| `jp-corp-finance.edinet-daily` | `edinet-v2` | daily | date | disclosure + XBRL facts |
| `jp-corp-finance.kanpo-daily` | `kanpo` | daily | publication date + issue | disclosure artifacts |
| `jp-corp-finance.e-koukoku-daily` | `moj-e-koukoku` | daily | report date / page | URL evidence |
| `jp-corp-finance.ir-repair` | `company-ir` | on-demand | jcn / edinet_code | disclosure artifacts + facts |
| `jp-corp-finance.coverage-refresh` | derived | daily | JCN range | coverage rows |

## Kanpo Strategy

官報は source truth ではあるが complete registry ではない。worker は次を
実施する。

1. 発行日ごとの issue metadata を取得する。
2. 記事 index から `会社その他の公告` / `決算公告` 候補を抽出する。
3. PDF または画像 PDF を raw artifact として保存する。
4. PDF は page 単位で WebP に変換し、各 WebP を `ipfs.etzhayyim.com` に pin
   する。OCR は WebP の IPFS URL を `llm.etzhayyim.com` の Gemma 4 に渡して
   実行し、PDF を直接 VLM に渡さない。
5. OCR/table extraction で会社名、住所、代表者、貸借対照表要旨、公告日を
   normalized JSON にする。
6. JCN resolver で法人番号候補を付与する。曖昧なら `needs_review`。
7. 財務 fact は confidence gate を通ったものだけ書く。

## EDINET Strategy

EDINET は listed/public company path として扱う。

- `documents.json` を date shard で取得する。
- 有価証券報告書、半期報告書、四半期報告書、臨時報告書を
  `vertex_jp_corp_disclosure` に入れる。
- XBRL zip を artifact 化し、XBRL parser で主要 facts を直接抽出する。
- JCN / EDINET code / ticker を `vertex_isin_security` と cross-link する。
- 会社法決算公告 coverage では `coverage_status='not_required_edinet'`
  を許容する。

## e-Koukoku / IR Strategy

電子公告は URL discovery と availability evidence を主目的にする。
決算公告そのものは会社サイト URL 側の HTML/PDF を fetch して artifact 化する。

電子公告調査対象外の決算公告もあるため、法務省電子公告システムだけで
決算公告 URL が網羅されるとは扱わない。JCN baseline から `source_unknown`
を残し、会社サイト探索は on-demand repair と coverage gap healing で行う。

# Zeebe BPMN

`etzhayyim-root/00-contracts/bpmn/com/etzhayyim/jp-corp-finance/` に process を置く。

| Process ID | Start | Task family |
|---|---|---|
| `jp_corp_finance_daily` | timer daily + manual | EDINET, Kanpo, e-Koukoku |
| `jp_corp_finance_backfill` | manual | date range / JCN range |
| `jp_corp_finance_repair_one` | XRPC / MCP | one company evidence repair |
| `jp_corp_finance_coverage_refresh` | timer daily | coverage projection |

Canonical skeleton:

```text
start
  -> create_run
  -> rw_health_gate
  -> plan_shards
  -> shard_loop
       -> acquire_cursor
       -> fetch_source
       -> persist_raw_artifact
       -> normalize_source
       -> langgraph_extract_and_resolve
       -> validate_rows
       -> write_graph
       -> verify_visibility
       -> advance_cursor
  -> refresh_coverage
  -> emit_audit
end
```

Zeebe task types:

| Task type | Handler | Notes |
|---|---|---|
| `jpCorpFinance.createRun` | Python | insert `vertex_ingest_run` |
| `jpCorpFinance.planShards` | Python | source-specific shard planner |
| `jpCorpFinance.acquireCursor` | Python | TTL lock on `vertex_ingest_cursor` |
| `jpCorpFinance.fetchSource` | Python | HTTP/API/PDF fetch, rate limit aware |
| `jpCorpFinance.webpOcr` | Python | PDF/image → WebP → IPFS → Gemma 4 OCR |
| `jpCorpFinance.normalize` | Python | deterministic parser before LLM |
| `generic.langgraph.run` | Python | extraction / entity resolution graph |
| `jpCorpFinance.validateRows` | Python | schema + confidence + privacy gates |
| `jpCorpFinance.writeGraph` | Python | deterministic upserts |
| `jpCorpFinance.verifyVisibility` | Python | count and sample readback |
| `jpCorpFinance.refreshCoverage` | Python/SQL | coverage rows / MV hint |

# Python Worker

Production package:

```text
20-actors/magatama/py/src/pymagatama/ingest/jp_corp_finance/
  __init__.py
  worker_main.py          # pyzeebe registration
  config.py               # source registry + rate limits
  models.py               # pydantic row contracts
  ids.py                  # deterministic vertex_id helpers
  artifacts.py            # B2/S3/local artifact refs
  jcn_resolver.py         # JCN matching from name/address/EDINET code
  sources/
    nta_jcn.py
    edinet.py
    kanpo.py
    e_koukoku.py
    company_ir.py
  normalize/
    edinet_xbrl.py
    kanpo_pdf.py
    html_tables.py
  graphs/
    disclosure_extract.py
    entity_resolution.py
    coverage_decision.py
  writers.py
  verify.py
```

Worker registration:

```python
client.task(task_type="jpCorpFinance.createRun")(create_run)
client.task(task_type="jpCorpFinance.planShards")(plan_shards)
client.task(task_type="jpCorpFinance.acquireCursor")(acquire_cursor)
client.task(task_type="jpCorpFinance.fetchSource")(fetch_source)
client.task(task_type="jpCorpFinance.normalize")(normalize_source)
client.task(task_type="jpCorpFinance.validateRows")(validate_rows)
client.task(task_type="jpCorpFinance.writeGraph")(write_graph)
client.task(task_type="jpCorpFinance.verifyVisibility")(verify_visibility)
client.task(task_type="jpCorpFinance.refreshCoverage")(refresh_coverage)
```

Operational constraints:

- `fetchSource` writes raw artifacts before any extraction.
- `normalize` must produce deterministic JSON without LLM.
- `generic.langgraph.run` receives only normalized text/tables and artifact refs,
  not unbounded PDFs.
- Cursor advances only after `verifyVisibility`.
- Parser drift creates Zeebe incident; it must not silently skip the shard.
- OCR/LLM degraded path writes `extraction_status='needs_review'`.

# LangGraph Design

LangGraph is used for bounded, auditable extraction and resolution, not for
general web crawling.

## Graph: `jp_corp_finance.disclosure_extract_v1`

State:

```python
class DisclosureExtractState(TypedDict):
    run_id: str
    source_id: str
    artifact_uri: str
    source_url: str
    normalized_text: str
    normalized_tables: list[dict]
    candidates: list[dict]
    jcn_candidates: list[dict]
    disclosure: dict | None
    facts: list[dict]
    review_flags: list[str]
    confidence: float
```

Nodes:

| Node | Purpose | Determinism |
|---|---|---|
| `classify_document` | source kind, statement scope, period hints | LLM allowed |
| `extract_company_block` | company name/address/representative/JCN hints | LLM allowed |
| `extract_financial_tables` | map rows to BS/PL/CF concepts | LLM allowed after table parser |
| `resolve_jcn` | call deterministic JCN resolver tool | deterministic tool |
| `validate_accounting_shape` | sign/unit/range checks | deterministic |
| `decide_review` | confidence and ambiguity gate | deterministic |
| `emit_rows` | final disclosure/fact JSON | deterministic |

Edges:

```text
classify_document
  -> extract_company_block
  -> extract_financial_tables
  -> resolve_jcn
  -> validate_accounting_shape
  -> decide_review
  -> emit_rows
```

Tool surface:

| Tool | Backing implementation |
|---|---|
| `lookup_jcn(name, address)` | `jcn_resolver.py` + `vertex_legal_entity` |
| `lookup_edinet(jcn, ticker, name)` | EDINET metadata / `vertex_isin_security` |
| `read_artifact(uri)` | artifact store, bounded text/table only |
| `write_review_flag(payload)` | `vertex_ingest_artifact(kind='review')` |

## Graph: `jp_corp_finance.coverage_decision_v1`

This graph is optional and batch-oriented. It does not extract facts; it decides
coverage state from existing evidence.

Inputs: JCN row, latest disclosure rows, EDINET status, known announcement
method, parser failures.

Outputs:

- `coverage_status`
- `missing_reason`
- `next_action`: `none`, `kanpo_backfill`, `ir_repair`, `manual_review`

# XRPC / MCP Surface

Add lexicons under `00-contracts/lexicons/com/etzhayyim/apps/jpCorpFinance/`.

| NSID | Type | Purpose |
|---|---|---|
| `com.etzhayyim.apps.jpCorpFinance.startDailyIngest` | procedure | start daily process |
| `com.etzhayyim.apps.jpCorpFinance.backfillKanpo` | procedure | date range backfill |
| `com.etzhayyim.apps.jpCorpFinance.repairCompany` | procedure | one JCN / EDINET code repair |
| `com.etzhayyim.apps.jpCorpFinance.getCoverage` | query | coverage row by JCN |
| `com.etzhayyim.apps.jpCorpFinance.listMissing` | query | missing/stale companies |

All mutating procedures dispatch BPMN and return `{ runId, processInstanceKey }`.
They do not fetch PDFs or call LLM inside CF Worker.

# Rollout

| Phase | Deliverable | Exit condition |
|---|---|---|
| P0 | ADR + schema migration + lexicon stubs | migration compiles |
| P1 | EDINET daily worker | Toyota fixture writes disclosure + facts |
| P2 | Kanpo daily artifact + metadata ingest | one publication date writes raw artifacts and candidate disclosures |
| P3 | LangGraph extraction for Kanpo tables | reviewed sample reaches precision target |
| P4 | e-Koukoku / IR repair | one JCN repair path works end-to-end |
| P5 | coverage projection | `listMissing` explains missing reason for JCN sample |
| P6 | backfill controls | pause/resume/cursor replay tested |

Smoke fixtures:

- Toyota: EDINET code `E02144`, JCN `1180301008652`, ticker `7203`.
- A small unlisted Kanpo決算公告 sample with known JCN.
- A company-site electronic公告 PDF sample.

# Risks

| Risk | Mitigation |
|---|---|
| 官報 PDF is image-only | OCR artifact + `needs_review` gate |
| Company name ambiguity | JCN resolver uses address and EDINET cross-ref; ambiguity blocks fact write |
| Source incompleteness | coverage table records `missing_reason` instead of pretending completeness |
| LLM hallucinated numbers | deterministic table parser first, range/sign validation, source location required |
| Paid / restricted sources | artifact must include license/access class; no scraping behind auth |
| Kotoba/Datomic degraded writes | health gate + verify before cursor advancement |

# Open Questions

1. 官報情報検索サービスの production access contract and allowed automation
   terms must be confirmed before P2 production backfill.
2. 日刊紙公告 ingest remains on-request until a reliable licensed source exists.
3. Whether `vertex_isin_filing` should be linked by edge table or duplicated into
   `vertex_jp_corp_disclosure` needs schema review during P1.
