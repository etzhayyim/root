> **DEPRECATED**: Actor migrated to `20-actors/bunken/actor-manifest.jsonld` (T1 MCP-Compose). This project wasm/*/src/app.ts is retained as T3 fallback only.

# ai-gftd-project-bunken — 文献書誌 Intelligence

**bunken.gftd.ai** — 全世界の図書館・アーカイブ文献を actor 化する書誌 intelligence。

## Architecture

```
Common Crawl CDX API → 書誌 URL 発見 (NDL/LOC/WorldCat/CiNii/VIAF/DOI/ARK)
  → CollectionJob → fetchCdxBatch (CDX 結果パース → Bunken node MERGE)
  → enrichBatch (site.gftd.ai crawl → Murakumo LLM メタデータ抽出)
  → registerDids (path-based DID 登録)
  → linkSameAs (同一文献の SAME_AS edge)
```

## DID Design — 9 Scheme Multi-DID

| Scheme | DID Pattern | Source |
|---|---|---|
| `ndl:bib` | `did:web:bunken.gftd.ai:ndl:bib:{bib_id}` | 国立国会図書館書誌 |
| `ndl:pid` | `did:web:bunken.gftd.ai:ndl:pid:{pid}` | NDL デジタルコレクション |
| `ncid` | `did:web:bunken.gftd.ai:ncid:{ncid}` | NII CiNii |
| `lccn` | `did:web:bunken.gftd.ai:lccn:{lccn}` | Library of Congress |
| `oclc` | `did:web:bunken.gftd.ai:oclc:{number}` | WorldCat |
| `viaf` | `did:web:bunken.gftd.ai:viaf:{viaf_id}` | VIAF 典拠 |
| `isbn` | `did:web:bunken.gftd.ai:isbn:{isbn13}` | ISBN (isbn.gftd.ai 相互参照) |
| `doi` | `did:web:bunken.gftd.ai:doi:{prefix}:{suffix}` | DOI |
| `ark` | `did:web:bunken.gftd.ai:ark:{naan}:{name}` | ARK |
| `doc` | `did:web:bunken.gftd.ai:doc:{DJB2(title\|author\|year\|country)}` | 書誌ID未付与 |

## Graph Labels

| Label | Purpose |
|---|---|
| `:Bunken` | 文献 actor (scheme, externalId, title, author, year, era, materialType, country) |
| `:BunkenCollectionJob` | CDX 収集ジョブ (scheme, status, discoveredCount) |

## Graph Edges

| Edge | From → To | Purpose |
|---|---|---|
| `SAME_AS` | Bunken → Bunken | 同一文献の異なる識別子 |
| `AUTHORED` | IdentifiedPerson → Bunken | 著者 (natural-person.gftd.ai) |
| `HELD_BY` | Bunken → Organization | 所蔵機関 (soshiki.gftd.ai) |
| `CITES` | Bunken → Bunken | 引用 |
| `RECORDS` | Bunken → HistoricalEvent | 歴史事象記録 (PropagationEvent 用) |

## Commands

| Command | Description |
|---|---|
| `collectFromCdx` | Common Crawl CDX API で書誌 URL を発見、CollectionJob 作成 |
| `fetchCdxBatch` | pending job を 1 件処理、CDX fetch → Bunken node MERGE |
| `enrichBatch` | site.gftd.ai crawl + Murakumo LLM でメタデータ抽出 |
| `registerDids` | enriched record に path-based DID 登録 |
| `linkSameAs` | title+author 一致の異 scheme record 間に SAME_AS edge |

## Queries

| Query | Description |
|---|---|
| `stats` | scheme 別の統計 (total/enriched/registered) |
| `search` | 文献検索 (title/author/scheme/era/country) |
| `getRecord` | DID or scheme+externalId で文献取得 |

## Pipeline Flow

```
1. collectFromCdx(schemes: ["ndl:bib", "lccn", "oclc"])
   → BunkenCollectionJob × N 作成

2. fetchCdxBatch()  ← heartbeat で繰り返し呼出
   → CDX API fetch → extractIdFromUrl → Bunken MERGE
   → title="" (未 enrich) のまま graph に記録

3. enrichBatch(batchSize: 10)  ← heartbeat で繰り返し呼出
   → site.gftd.ai crawl_page → Murakumo LLM → title/author/year/era 抽出
   → Bunken node SET

4. registerDids(batchSize: 10)  ← heartbeat で繰り返し呼出
   → com.atproto.identity.create(path) → didRegistered = true

5. linkSameAs()  ← 定期実行
   → title+author 完全一致 → SAME_AS edge
```

## Rules

| Rule | Description |
|---|---|
| **isbn.gftd.ai 委譲** | ISBN バリデーション・メタデータは isbn.gftd.ai が権威。bunken は DID を管理 |
| **issn.gftd.ai 委譲** | 同上 ISSN |
| **Murakumo only** | LLM は on-prem fleet only (qwen3.5-4b)。外部 API 禁止 |
| **DJB2 dedup** | doc scheme (書誌ID未付与) は DJB2(title\|author\|year\|country) で dedup |
| **SAME_AS 不変** | 一度作成した SAME_AS edge は削除しない |
| **era 自動分類** | year → era (prehistoric/ancient/medieval/industrial/modern) |

## Key Files

| File | Role |
|---|---|
| `wasm/ai-gftd-wasm-bunken-bk7n2d8x/src/app.ts` | App Worker |
| `wasm/ai-gftd-wasm-bunken-bk7n2d8x/magatama.jsonld` | App config (nanoid: bk7n2d8x) |
| `wasm/ai-gftd-wasm-bunken-bk7n2d8x/wit/world.wit` | WIT capability contract |

## Historical Propagation Integration

歴史情報伝播 (`90-docs/260407-historical-propagation-social-design.md`) の文献 actor 供給元。
- `era != modern` の Bunken actor は PropagationEvent の `receiverDid` になりうる
- `materialType` が投稿文体を決定 (manuscript → 「筆者の手で記された」、inscription → 「この石に刻まれた」)
- shinka が `RECORDS` edge 経由で HistoricalEvent に紐づく文献を投稿者として使用
