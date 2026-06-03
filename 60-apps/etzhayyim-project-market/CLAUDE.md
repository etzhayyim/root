# etzhayyim-project-market

Crypto market intelligence — transaction history, market visualization, portfolio, risk assessment, and crypto resource-flow.

## Architecture

This project is implemented as extensions to `etzhayyim-project-global` (global-ui-w5n8p3q6 component):

| Layer | Location | Description |
|-------|----------|-------------|
| Backend (Go) | `60-apps/etzhayyim-project-global/wasm/global-ui-w5n8p3q6/global-crypto-routes.go` | KV-backed transaction history, portfolio, risk assessment, crypto flow tools |
| Frontend (Svelte) | `60-apps/etzhayyim-project-global/wasm/global-ui-w5n8p3q6/svelte/src/routes/markets/` | Market board, portfolio, history, risk pages |
| Crypto Flow | `60-apps/etzhayyim-project-global/wasm/global-ui-w5n8p3q6/svelte/src/routes/crypto-flow/` | Crypto resource-flow visualization |
| Types | `svelte/src/lib/types/market.ts` | CryptoTransaction, CryptoPortfolio, CryptoRiskAssessment, CryptoFlow |
| Stores | `svelte/src/lib/stores/crypto.ts` | Svelte stores for crypto data fetching |

## KV Storage

Transaction history and portfolio data are persisted to sql graph RDBMS via `performer/rdbms`:

| Key Pattern | Data |
|-------------|------|
| `crypto.tx.{id}` | Individual transaction JSON |
| `crypto.txidx.{symbol}` | Transaction ID index per symbol |
| `crypto.hold.{symbol}` | Holding/position per symbol |
| `crypto.symbols` | Known symbol list |

KV bucket: `global_crypto_history`

## Tools (MCP)

| Tool | Description |
|------|-------------|
| `global.record_crypto_transaction` | Record buy/sell/transfer, updates holdings |
| `global.list_crypto_transactions` | List transaction history (by symbol or all) |
| `global.get_crypto_portfolio` | Get portfolio with holdings, PnL, allocation |
| `global.get_crypto_risk` | Risk assessment per asset or portfolio-level |
| `global.list_crypto_flows` | List crypto resource flows |

## External Data Sources

- **CoinGecko API** (free tier): Real-time prices, market cap, volume
- **DEXScreener API**: Uniswap/DEX pair data
- **Demo fallback**: Embedded demo data when APIs are unavailable
