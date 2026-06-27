# ADR-2606272030: kenchi (検地) — 全世界・不動産価値 EXTERNAL-MARKET 透明性 Tier-B アクター (R0 scaffold)

- Status: Proposed (2026-06-27)
- Tier: Tier-B（公共財・外部市場透明性）
- DID: `did:web:kenchi.etzhayyim.com`（公開 `did:web:etzhayyim.github.io:com-etzhayyim-kenchi`）
- Namespace: `com.etzhayyim.kenchi.*`
- Parent ADRs: ADR-2605192245（Land Trust 主権 — 譲渡不能地の境界）, ADR-2605192330（拡張 land sovereignty）, ADR-2605262900（toritate sibling）, ADR-2605192200（Charter Rider）, ADR-2605215000（Murakumo-only 推論）
- 実装: `git@github.com:com-junkawasaki/kenchi-actor`（langgraph-clj エンジン。fusion/governor/parcel StateGraph + ingest adapters + Common Crawl + flywheel。18 tests / 60 assertions green、HM Land Registry + BIS + Common Crawl で live 検証済み）

## 課題

全世界の不動産価値を**複数の独立 authority から分析し、公開する**アクターを etzhayyim の
公共財として持ちたい。しかし etzhayyim の憲法（ADR-2605192245）は **Land Trust の保有地を
譲渡不能（inalienable）**と定め、「譲渡不能の土地に市場価格は無い」。toritate も N12 で
「Land Trust valuation engine ではない」と明示している。したがって不動産価値アクターは、
**外部市場**を評価しつつ、**自分たちの譲渡不能地には一切市場価格を付けない**という境界を
構造的に保証しなければならない。

加えて、現実のデータは単一ソースが真値を持たず（記録取引・公的評価・指数・ポータル売出しは
互いに食い違い、鮮度・通貨・**ライセンス(ToS)**も異なる）、単一 AVM を信用すると誤る。

## 決定

### 1. EXTERNAL-MARKET のみ。譲渡不能地は構造的に除外（G5）

`valuation.assetClass` を **`external-market` のみ**に固定する。kenchi は Land Trust の
inalienable 保有地に市場価格を**決して付けない**（ADR-2605192245）。内部の commons-asset
価値（非市場・imputed STOCK・ACCESS-NOT-TITLE）は `toritate.commons_asset_value` の領分で、
両者は二重計上しない。kenchi → toritate は **1-way**（Land Registry 取得 due-diligence 向けの
外部 comparable 提供のみ。取得後に Trust に入った瞬間 kenchi の scope を外れる）。

### 2. PROVENANCE-OR-SILENCE（G3）— 単一不変条件

> kenchi は、**独立 recorded comps ≥3** かつ **独立 authority ≥2** かつ **新鮮なアンカー**が
> 揃わない限り、点推定を公開しない。

不足時は MRV（広い帯）か `insufficient-evidence` を出し、偽の精度を出さない。£ の点は
**記録された価格 comps のみ**が投票し、指数（BIS/OECD）は corroboration 専用で中央値に
混ざらない。独立性は **source-id でなく authority** で数える（同一機関の複数フィードは1）。

### 3. DERIVED/AGGREGATE ライセンス規律（G4）

ToS 制限ソースは **derived-only** で公開（生データ再配布禁止）。per-parcel 公開不可地域は
**aggregate-only**（`regionReport` の H3 中央値/四分位）で公開。published レコードの
`license` 列挙は **`{open, derived-only}` のみ**（`raw`/`restricted` は表現不可）。
restricted ソースは `sourceLicense` で印を付け Murakumo-only 推論（G7）で扱う。

### 4. NO-PII（G6）・NO-ADVICE（G10）

parcel は場所であって人ではない。owner/person 等の PII 列は valuation に存在させない。
個人の資産推計は行わない（それは toritate basicHighIncome の aggregate-only 領分）。
個人向けの投資/評価助言は出さない（鑑定の UPL 相当）。

### 5. アクター構成（6 cells / 4 Lexicons / 10 gates / 10 non-goals）

実装は `com-junkawasaki/kenchi-actor`（langgraph-clj）。本セルは**公開アイデンティティ
（DID）+ 憲章 + lexicons + ソース registry**。cells: ingest / fusion / provenance_governor /
publish / region_aggregate / flywheel（naphtali・judah に path-reserved）。
Lexicons: `valuation` / `regionReport` / `provenanceAttestation` / `sourceLicense`。

### 6. 10 gates

G1 Charter Rider scan · G2 datomic lineage · **G3 PROVENANCE-OR-SILENCE** ·
**G4 derived/aggregate license** · **G5 INALIENABLE-LAND EXCLUSION** · **G6 NO-PII** ·
G7 Murakumo-only inference · G8 open-source + open-data-first · G9 ≥3y provenance pin ·
G10 NO-ADVICE。

## 帰結

- **実物**: lexicons（4）+ charter-gate テスト（G3/G4/G5/G6/N8 を schema 層で pin、
  `./run_tests.sh` で 6/6 green）+ manifest + DID + ソース registry。エンジンは上流で
  live 検証済み（HM Land Registry + BIS + Common Crawl、3 authority で publishable=TRUE、
  Common Crawl が license を derived-only 化）。
- **公開**: `etzhayyim/com-etzhayyim-kenchi` を **public** リポジトリとして GitHub Pages 公開
  → `did:web:etzhayyim.github.io:com-etzhayyim-kenchi` を解決可能にする（R0 → R1 で PDS/Aozora 連携）。
- **未決**: Council Lv6+ ≥3 の批准（R1）、on-mesh デプロイ（naphtali/judah）、ソース registry の
  attestation、per-jurisdiction の per-parcel 公開法規の精査。
- **境界の検証**: G5（inalienable 除外）と toritate N12 が二重に同じ不変条件を pin し、外部市場と
  内部 commons-asset が衝突しないことを構造的に保証する。
