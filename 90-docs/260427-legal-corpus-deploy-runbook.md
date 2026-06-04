---
id: 260427-legal-corpus-deploy-runbook
title: legal-corpus.etzhayyim.com Deploy Runbook (Phase A)
status: active
doc_type: how-to
topic: legal-corpus
authoritative: true
last_verified: 2026-04-27
related:
  - adr-0049-legal-corpus-global-ingest
  - adr-0056-bpmn-as-actor
  - adr-0048-risingwave-vultr-b2-primary
---

# legal-corpus.etzhayyim.com Deploy Runbook (Phase A)

ADR-0049 で設計した `legal-corpus.etzhayyim.com` を **production live** にする手順書。
T2 BPMN-as-actor (ADR-0056) のため CF Worker deploy は不要。
作業範囲は (1) 外部 API key 取得 (2) Vault / Workers AI binding (3) RW migration (4) Zeebe deploy (5) DNS (6) 5 source registerSource (7) 初回 fetch 検証。

## Pre-flight

- Actor: `did:web:legal-corpus.etzhayyim.com` (nanoid `lc0rpus0`)
- Migrations to apply: `20260427230000` / `230100` / `230200` / `230300` / `230400`
- Lexicons: `00-contracts/lexicons/com/etzhayyim/apps/legal-corpus/*.json` (6)
- BPMN: `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/legal-corpus/*.bpmn` (8)
- Embedding: Workers AI `@cf/baai/bge-m3` (1024d) + Murakumo MLX fallback

## T-3d: 外部 API key 取得

### CourtListener (US Fed + 州判例)

1. <https://www.courtlistener.com/sign-up/> でアカウント作成 (Free tier OK)
2. Profile → API → "Create token" で API token 発行
3. Free tier rate limit: 5,000 req/day。R/PT24H × 100 page_size = 100 req/day で十分

### CanLII / SCC (Canada)

1. <https://www.canlii.org/en/info/api.html> から CanLII Web API access を申請 (法律事務所 /アカデミック/ メディアの審査あり、~7-14 営業日)
2. 承認後 `https://api.canlii.org/v1/...?api_key=...` 形式で利用可

### EUR-Lex / BAILII / WorldLII

- EUR-Lex SPARQL: 認証不要 (公開 endpoint)
- BAILII Atom: 認証不要、ただし rate limit 不明 → 24h cadence は安全側
- WorldLII OAI-PMH: 認証不要、7d cadence

> **既に申請済みの場合**: API key を etzhayyim Vault に登録 (T-1d セクション参照)

## T-1d: Vault / Workers AI / DNS

### Vault に secret 登録

```bash
# CourtListener token (free tier)
etzhayyim vault add --folder legal-corpus --name COURTLISTENER_TOKEN --value "<token>"

# CanLII API key
etzhayyim vault add --folder legal-corpus --name CANLII_API_KEY --value "<key>"

# 確認
etzhayyim vault list --folder legal-corpus
```

### Workers AI binding (CF dispatcher Worker)

`50-infra/cloudflare/workers/dispatcher/wrangler.jsonc` に以下を追加:

```jsonc
{
  "ai": { "binding": "AI" },
  "vars": {
    "LEGAL_CORPUS_EMBED_FALLBACK": "murakumo"
  }
}
```

```bash
cd 50-infra/cloudflare/workers/dispatcher
npx wrangler deploy
# 確認: dispatcher が AI binding を認識
npx wrangler tail | grep "AI binding"
```

> **代替**: pyzeebe primitive `generic.http.fetch` から CF Workers AI REST を直接叩く構成は (ADR-0049 D3 採用) すでに `embedDocument.bpmn` に implemented。`CF_ACCOUNT_ID` + `CF_AI_API_TOKEN` を pyzeebe worker env に渡す:

```bash
kubectl -n zeebe set env deployment/zeebe-worker \
  CF_ACCOUNT_ID="$(security find-generic-password -s etzhayyim.cloudflare -a CF_ACCOUNT_ID -w)" \
  CF_AI_API_TOKEN="$(security find-generic-password -s etzhayyim.cloudflare -a CF_AI_API_TOKEN -w)"
```

### DNS

```bash
# legal-corpus.etzhayyim.com CNAME → CF routing-gateway
etzhayyim dns-sync --actor legal-corpus
# verify
dig +short legal-corpus.etzhayyim.com
```

## Day 0: 投入

### 1. Migration apply

```bash
cd 30-graph/graph-schema
DATABASE_URL=postgres://... pnpm db:migrate latest
# 期待: 5 migrations applied
#   20260427230000_vertex_legal_corpus
#   20260427230100_seed_legal_corpus_bpmn_actors
#   20260427230200_seed_lawfirm_bpmn_actors
#   20260427230300_vertex_adr_legal_aid
#   20260427230400_seed_legal_logical_actors_bpmn

# 型再生成
DATABASE_URL=... pnpm db:gen
DATABASE_URL=... pnpm db:drift  # zero-drift 確認
```

### 2. Zeebe BPMN deploy 確認 (F5 watcher が自動)

```bash
# F5 watcher (30s interval) が vertex_bpmn_process_def を読んで Zeebe deploy
# 自動で進むはず。確認:
psql $DATABASE_URL -c "
  SELECT bpmn_process_id, status, deployed_at
  FROM vertex_bpmn_process_def
  WHERE owner_did = 'did:web:legal-corpus.etzhayyim.com'
  ORDER BY bpmn_process_id;
"
# 期待: 8 rows, status='active', deployed_at NOT NULL

# coverage gate
etzhayyim bpmn-coverage --project legal-corpus
# 期待: 8/8 PASS
```

### 3. registerSource × 5

```bash
bash 70-tools/scripts/legal-corpus-bootstrap.sh
```

このスクリプトは下記 5 行を順次実行:

```bash
etzhayyim xrpc com.etzhayyim.apps.legal-corpus.registerSource -d '{
  "sourceId": "courtlistener",
  "displayName": "CourtListener (US)",
  "baseUrl": "https://www.courtlistener.com/api/rest/v3",
  "jurisdictions": ["USA"],
  "cadenceIso8601": "R/PT24H",
  "authStrategy": "token",
  "secretRef": "vault://etzhayyim/legal-corpus/COURTLISTENER_TOKEN",
  "license": "CC0"
}'

etzhayyim xrpc com.etzhayyim.apps.legal-corpus.registerSource -d '{
  "sourceId": "eur-lex",
  "displayName": "EUR-Lex (EU)",
  "baseUrl": "https://publications.europa.eu/webapi/rdf/sparql",
  "jurisdictions": ["EU"],
  "cadenceIso8601": "R/PT24H",
  "authStrategy": "none",
  "license": "CC-BY-4.0"
}'

etzhayyim xrpc com.etzhayyim.apps.legal-corpus.registerSource -d '{
  "sourceId": "bailii",
  "displayName": "BAILII (UK + IE)",
  "baseUrl": "https://www.bailii.org",
  "jurisdictions": ["GBR", "IRL"],
  "cadenceIso8601": "R/PT24H",
  "authStrategy": "none",
  "license": "BAILII-Terms"
}'

etzhayyim xrpc com.etzhayyim.apps.legal-corpus.registerSource -d '{
  "sourceId": "worldlii",
  "displayName": "WorldLII (Commonwealth)",
  "baseUrl": "https://www.worldlii.org/cgi-bin/oai.pl",
  "jurisdictions": ["AUS", "NZL", "ZAF", "IND", "SGP", "HKG"],
  "cadenceIso8601": "R/P7D",
  "authStrategy": "none",
  "license": "WorldLII-Terms"
}'

etzhayyim xrpc com.etzhayyim.apps.legal-corpus.registerSource -d '{
  "sourceId": "canlii",
  "displayName": "CanLII / SCC (CA)",
  "baseUrl": "https://api.canlii.org/v1",
  "jurisdictions": ["CAN"],
  "cadenceIso8601": "R/PT24H",
  "authStrategy": "apiKey",
  "secretRef": "vault://etzhayyim/legal-corpus/CANLII_API_KEY",
  "license": "CanLII-API-Terms"
}'
```

検証:

```bash
psql $DATABASE_URL -c "
  SELECT source_id, display_name, cadence_iso8601, auth_strategy, status
  FROM vertex_legal_corpus_source
  ORDER BY source_id;
"
# 期待: 5 rows, status='active'
```

### 4. 初回 fetch を手動 invoke (timer 待たず)

timer-start BPMN (`fetchCourtListenerDelta` etc.) は次回 cadence まで起動しないため、初回は `etzhayyim xrpc` で直接呼ぶ:

```bash
# CourtListener (一番安全、free tier rate limit 余裕)
etzhayyim xrpc com.etzhayyim.apps.legal-corpus.fetchCourtListenerDelta -d '{}'

# 30 秒後 — ingestDocument が item ごとに発火、vertex_legal_corpus_document に行が増える
psql $DATABASE_URL -c "
  SELECT source_id, COUNT(*) AS doc_count, MAX(fetched_at) AS last_fetch
  FROM vertex_legal_corpus_document
  GROUP BY source_id;
"
# 期待: courtlistener N rows (page_size=100)
```

### 5. Embedding 検証 (1 doc embed)

```bash
# 任意の 1 doc を取って embed を kick
DOC_VID=$(psql $DATABASE_URL -tAc "SELECT vertex_id FROM vertex_legal_corpus_document WHERE source_id='courtlistener' LIMIT 1")
etzhayyim xrpc com.etzhayyim.apps.legal-corpus.embedDocument -d "{\"vertexId\":\"$DOC_VID\"}"

# 確認
psql $DATABASE_URL -c "
  SELECT vertex_id, embedding_dim, embedding_model, embedding_at
  FROM vertex_legal_corpus_document
  WHERE vertex_id = '$DOC_VID';
"
# 期待: embedding_dim=1024, embedding_model='@cf/baai/bge-m3'
```

## T+1d: timer-fired ingestion 検証

24h 後、各 timer-start BPMN が自動発火。検証:

```bash
psql $DATABASE_URL -c "
  SELECT source_id, last_fetched_at, last_cursor IS NOT NULL AS has_cursor
  FROM vertex_legal_corpus_source
  WHERE last_fetched_at > NOW() - INTERVAL '25 hours'
  ORDER BY last_fetched_at DESC;
"
# 期待: 4 rows (courtlistener / eur-lex / bailii / canlii。worldlii は 7d cadence で除外)
```

```bash
psql $DATABASE_URL -c "
  SELECT * FROM mv_legal_corpus_jurisdiction_coverage
  ORDER BY document_count DESC LIMIT 20;
"
# 期待: USA / EU / GBR / IRL / CAN の document_count > 0
```

## T+7d: IVF index health

```bash
# embedding カバレッジ
psql $DATABASE_URL -c "
  SELECT
    COUNT(*) AS total,
    COUNT(embedding) AS embedded,
    COUNT(*) - COUNT(embedding) AS pending
  FROM vertex_legal_corpus_document;
"

# IVF cluster 分布 (lists=200 想定、均等性確認)
psql $DATABASE_URL -c "
  SELECT ivf_cluster_id, COUNT(*)
  FROM vertex_legal_corpus_document
  WHERE ivf_cluster_id IS NOT NULL
  GROUP BY ivf_cluster_id
  ORDER BY COUNT(*) DESC LIMIT 10;
"
# 期待: top cluster でも total/lists × 5 を超えない (歪みが大きい場合は lists 再調整)
```

## Rollback

問題発生時:

```bash
# 1. timer-start BPMN を一旦 status='disabled' に
psql $DATABASE_URL -c "
  UPDATE vertex_bpmn_process_def
  SET status = 'disabled'
  WHERE owner_did = 'did:web:legal-corpus.etzhayyim.com'
    AND bpmn_process_id LIKE 'legal_corpus_fetch_%';
"
# F5 watcher が次サイクルで Zeebe undeploy

# 2. ingest 済 data 削除 (必要時のみ、慎重に)
# psql $DATABASE_URL -c "DELETE FROM vertex_legal_corpus_document WHERE source_id = 'courtlistener';"

# 3. Migration revert
cd 30-graph/graph-schema
DATABASE_URL=... pnpm db:migrate down
```

## Acceptance criteria

| # | 項目 | コマンド | 期待値 |
|---|---|---|---|
| 1 | 5 migrations applied | `pnpm db:migrate list` | `up` × 5 |
| 2 | 8 BPMN active | `etzhayyim bpmn-coverage --project legal-corpus` | 8/8 PASS |
| 3 | 5 source registered | `SELECT count(*) FROM vertex_legal_corpus_source WHERE status='active'` | 5 |
| 4 | 1st fetch ≥ 1 doc | `SELECT count(*) FROM vertex_legal_corpus_document WHERE source_id='courtlistener'` | ≥ 1 |
| 5 | 1 doc embedded | `SELECT count(*) FROM vertex_legal_corpus_document WHERE embedding IS NOT NULL` | ≥ 1 |
| 6 | DNS resolves | `dig +short legal-corpus.etzhayyim.com` | CNAME present |
| 7 | T+24h auto-fetch | `mv_legal_corpus_jurisdiction_coverage` jurisdictions | ≥ 5 distinct |

7 個全て PASS で Phase A 完了。Phase B (read path 実装) に移行可。

## 関連

- ADR-0049 (本 actor の設計 ADR)
- ADR-0056 (BPMN-as-actor 規約)
- ADR-0048 (RisingWave Vultr / B2 primary — 物理 storage)
- `60-apps/etzhayyim-project-legal-corpus/CLAUDE.md` (actor の運用 rule)
