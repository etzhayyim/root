# etzhayyim-project-gol-d-roger — Gold Asset Management

## Overview

Gold collection, portfolio management, and asset preservation platform.
金の収集・運用・管理保持を行う資産運用プラットフォーム。

- **Subdomain**: `gol-d-roger.etzhayyim.com`
- **nanoid**: `wy2zvdvd`
- **Proto**: `proto/etzhayyim/gol_d_roger/v1/gol_d_roger.proto`

## Architecture

```
Market Data Sources (XAU/USD, futures, ETF NAV)
  ↓ XRPC (scheduled ingestion)
Control Plane (App, SQL Graph)
  ├ Market Data Store (spot, futures curves, historical OHLCV)
  ├ Portfolio Manager (positions: physical, paper, digital)
  ├ Risk Engine (VaR, drawdown, macro correlation)
  ├ Physical Inventory (vault, serial, purity, custodian)
  ├ Trade Executor (spot/futures order management)
  └ Compliance Reporter (tax lots, capital gains, audit trail)
```

## Domain Model

### Asset Types

| Type | Description | Tracking |
|------|-------------|----------|
| Physical Gold | Bars, coins, jewelry | Serial number, weight (troy oz), purity (fineness), vault location |
| Paper Gold | ETFs (GLD, IAU), futures (COMEX GC), CFDs | Ticker, quantity, contract expiry |
| Digital Gold | Tokenized gold (PAXG, XAUT) | Wallet address, token quantity |

### Key Metrics

| Metric | Description |
|--------|-------------|
| XAU/USD Spot | London fix / real-time spot price |
| Portfolio NAV | Total gold holdings mark-to-market |
| Allocation % | Physical vs paper vs digital split |
| VaR (95%) | 1-day value-at-risk |
| DXY Correlation | USD index inverse correlation tracking |
| Real Rate Spread | Gold vs TIPS yield differential |

## Classifications

### COFOG (Classification of Functions of Government)

| Code | Class | Role |
|------|-------|------|
| 04.1.1 | General economic and commercial affairs | Commodity regulation compliance |
| 04.8.1 | R&D Economic affairs | Price analytics R&D |
| 01.1.2 | Financial and fiscal affairs | Tax/customs reporting |

### ISIC Rev.4 (Industry Classification)

| Code | Class | Role |
|------|-------|------|
| K-6612 | Security and commodity contracts brokerage | Spot/futures execution |
| K-6630 | Fund management activities | Portfolio fund management |
| K-6499 | Other financial service activities | Custody, vault management |
| B-0729 | Mining of other non-ferrous metal ores | Supply chain provenance |
| G-4662 | Wholesale of metals and metal ores | Bullion procurement |

### ISCO-08 (Occupation Classification)

| Code | Title | Actor Role |
|------|-------|------------|
| 1211 | Finance managers | Portfolio oversight, risk governance |
| 2413 | Financial analysts | Price analysis, trend forecasting |
| 2412 | Financial and investment advisers | Allocation advisory, hedging |
| 3311 | Securities and finance dealers and brokers | Trade execution |
| 3315 | Valuers and loss assessors | Physical gold appraisal |
| 4321 | Stock clerks | Vault inventory audit |
| 2411 | Accountants | Book-keeping, tax reporting |

## App Components

| Component | nanoid | Role |
|-----------|--------|------|
| `etzhayyim-wasm-gol-d-roger-wy2zvdvd` | wy2zvdvd | Control plane + UI |

## API Surface

| Service | Methods |
|---------|---------|
| `GoldCommandService` | compatibility ingress only. 正規 command contract は Matrix `org.etzhayyim.command.gold.*` |
| `GoldQueryService` | `GetSpotPrice`, `GetPortfolio`, `GetPositionHistory`, `GetRiskMetrics`, `ListPhysicalInventory`, `GetTaxReport` |

### Command Contract

- command room: `#gold-commands:etzhayyim.com`
- event types:
  - `org.etzhayyim.command.gold.ingest-market-data`
  - `org.etzhayyim.command.gold.create-position`
  - `org.etzhayyim.command.gold.close-position`
  - `org.etzhayyim.command.gold.register-physical-asset`
  - `org.etzhayyim.command.gold.execute-trade`
  - `org.etzhayyim.command.gold.rebalance-portfolio`
- UI mutation path は XRPC command を W Protocol command façade として使う

## Arrow Tables

| Table | Purpose |
|-------|---------|
| `gold_market_data` | Spot/futures price history (OHLCV) |
| `gold_positions` | Active/closed positions (physical, paper, digital) |
| `gold_physical_inventory` | Vault inventory with serial/purity/weight |
| `gold_trades` | Executed trade log |
| `gold_risk_snapshots` | Daily risk metrics (VaR, drawdown, correlations) |
| `gold_tax_lots` | Tax lot tracking for capital gains |

## Resource Entity Integration (etzhayyim-project-resources)

金関連の resource entity を `etzhayyim-project-resources` に配置し、gol-d-roger から XRPC で参照する。

| Entity | nanoid | Description |
|--------|--------|-------------|
| `svc-entity-gold-mining-land` | gm1n3l4d | 採掘可能な土地・鉱区・鉱業権 |
| `svc-entity-gold-corporation` | gc0rp5r8 | 金鉱山法人・生産企業 |
| `svc-entity-gold-technology` | gt3ch7k9 | 採掘・精錬・分析技術 |
| `svc-entity-gold-distribution` | gd1str6b | 流通チャネル・取引所・ディーラー |

### Entity → Capability マッピング

```
GoldMiningLand ──realizes──→ cap/gold-supply-chain (採掘 → 供給)
GoldCorporation ──realizes──→ cap/trade-execution + cap/portfolio-management
GoldTechnology ──realizes──→ cap/physical-inventory (精錬・分析技術)
GoldDistribution ──realizes──→ cap/trade-execution + cap/compliance-reporting
```

## ISIC / ISCO Actor Integration

### ISIC Actors (Industry — etzhayyim-project-open-isic)

| ISIC Code | nanoid | Service | Capability |
|-----------|--------|---------|------------|
| B-0729 | b07g0ld2 | GoldMiningService | 金鉱業 — 探査・採掘・鉱石処理・環境コンプライアンス |
| K-6612 | k66br0k4 | CommodityBrokerageService | 商品ブローカー — 注文執行・スプレッド・決済 |
| K-6630 | k66fnd8m | GoldFundManagementService | ファンド管理 — ETF追跡・配分・NAV計算 |
| G-4662 | g46mt1w3 | GoldWholesaleService | 金属卸売 — 地金調達・在庫・LBMA認証 |

### ISCO Actors (Occupation — etzhayyim-project-open-isco)

| ISCO Code | nanoid | Service | Actor Role |
|-----------|--------|---------|------------|
| 1211 | fm12g0ld | FinanceManagersService | ポートフォリオ監督・リスクガバナンス |
| 2413 | fa24g0ld | FinancialAnalystsService | 価格分析・トレンド予測・マクロ相関 |
| 3311 | sd33g0ld | SecuritiesDealersService | 取引執行・OTC・スプレッド管理 |
| 3315 | va33g0ld | ValuersAssessorsService | 現物鑑定・純度検証・保険評価 |

### Cross-Project XRPC Communication

```
gol-d-roger (wy2zvdvd)
  ├─ XRPC → svc-entity-gold-mining-land (gm1n3l4d)     # 鉱区データ参照
  ├─ XRPC → svc-entity-gold-corporation (gc0rp5r8)      # 企業データ参照
  ├─ XRPC → svc-entity-gold-technology (gt3ch7k9)       # 技術カタログ参照
  ├─ XRPC → svc-entity-gold-distribution (gd1str6b)     # 流通チャネル参照
  ├─ XRPC → isic-b-0729 (b07g0ld2)                      # 採掘オペレーション委譲
  ├─ XRPC → isic-k-6612 (k66br0k4)                      # 取引執行委譲
  ├─ XRPC → isic-k-6630 (k66fnd8m)                      # ファンド管理委譲
  ├─ XRPC → isic-g-4662 (g46mt1w3)                      # 地金調達委譲
  ├─ XRPC → isco-1211 (fm12g0ld)                         # 承認・ガバナンス
  ├─ XRPC → isco-2413 (fa24g0ld)                         # 分析・予測
  ├─ XRPC → isco-3311 (sd33g0ld)                         # ディーラー執行
  └─ XRPC → isco-3315 (va33g0ld)                         # 鑑定・評価
```

## Matrix Integration (etzhayyim-project-matrix)

プロジェクト進行は matrix (br8bojxp) で管理する。

| Room Topic | Purpose | Participants |
|--------------|---------|--------------|
| `gold-portfolio-review` | ポートフォリオ定期レビュー | isco-1211 (FM), isco-2413 (FA) |
| `gold-trade-execution` | 取引執行ワークフロー | isco-3311 (SD), isic-k-6612 |
| `gold-mining-ops` | 採掘オペレーション進捗 | isic-b-0729, entity-mining-land |
| `gold-appraisal-queue` | 現物鑑定キュー | isco-3315 (VA), entity-gold-tech |
| `gold-distribution-logistics` | 流通・物流追跡 | isic-g-4662, entity-distribution |
| `gold-compliance-audit` | コンプライアンス監査 | isco-1211 (FM), all entities |

### Room → Actor Mailbox Flow

```
Room message (br8bojxp.etzhayyim.com)
  ↓ XRPC (SendMessage)
Actor Mailbox (performer-framework)
  ↓ envelope delivery
Target Actor (ISIC/ISCO/Entity)
  ↓ handler dispatch
Response → Room reply
```
