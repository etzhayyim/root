# nyusatsu — JP Public Procurement Aggregator

Self-hosted, etzhayyim-native alternative to NJSS (入札情報速報サービス).

## 責務

全省庁 (GEPS) + 47 都道府県 + 1,718 市町村 + 独法 + 特殊法人 の 入札公告 / 開札結果 を crawl → Murakumo LLM で structured extract → `com.etzhayyim.apps.jpFiscal.procurementBid` record として emit。

NJSS 等の paid aggregator には依存しない。**情報公開法 + 会計法 29 条 + 地方自治法 234 条** により一次ソースが公表義務を負うため、robots.txt を順守する限り自前集約は合法。

## 非責務 (DO NOT)

- 契約 record (`com.etzhayyim.apps.jpFiscal.contract`) は **issuer agency DID** が owner。nyusatsu は bid → contract の link (`resolveAward`) のみ担当。
- 個人情報 (入札参加者の個人事業主住所等) は PII Tier 3 扱い (ADR-0018)。redaction hook 必須。
- paid API (NJSS / 官公需ウォッチャー / etc.) の呼び出し禁止。

## Source registry

`actor-manifest.jsonld` `sources[]` に列挙。追加時は:
- `tier` ∈ {central, prefecture, municipality, incorp}
- `kind` ∈ {html, pdf, csv, rss, api}
- `entry` = crawl 起点 URL
- `rate_ms` ≥ 1500 (robots.txt に明記なき場合)
- `note` = site-specific 解釈メモ (日付 format, ページング方式)

## Extraction pipeline

1. `http.fetch.batch` で list page を取得 (per-source rate limit)
2. `agent.map` で LLM structured extract (schema = `com.etzhayyim.apps.jpFiscal.procurementBid`)
3. `graph.write` で MERGE (dedup key = `tenderNo`)
4. `resolveAward` XRPC で落札者 link (award ↔ contract)

## Shinka loop

自己進化ループで新規 source 発見 + extraction template の精度向上を回す。steady-state の source 数が増えるたび `shinkaEvolution` record を発行し、coverage snapshot に反映。

## Related

- ADR-0035 §Data sources §B 調達
- `00-contracts/lexicons/com/etzhayyim/apps/jpFiscal/procurementBid.json`
- `00-contracts/lexicons/com/etzhayyim/apps/jpFiscal/contract.json`
- `20-actors/gov/actor-manifest.jsonld` (issuer DID 発行元)
