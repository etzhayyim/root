# etzhayyim-project-code-hs — Harmonized System Trade Classification

## Identity

| key | value |
|---|---|
| domain | hs.etzhayyim.com |
| performerType | service |
| nanoid | hs6c0d3x |
| primary DID | `did:web:hs.etzhayyim.com` |
| NSID prefix | `com.etzhayyim.apps.hs.*` |

## What This Project Does

Harmonized System (HS) code に基づく国際貿易品目分類 project。
GTIN の商品実体、ISIC の産業活動、states の customs/tariff 制度をつなぐ classification hub として機能する。

- section / chapter / heading / subheading の階層管理
- GTIN / CPC / ISIC / internal catalog との concordance
- 国別 tariff / restriction / license overlay
- coverage-driven social evolution

設計詳細: `90-docs/260415-hs-code-domain-coverage-design.md`

## Multi-DID Model

| DID | 用途 |
|---|---|
| `did:web:hs.etzhayyim.com` | App coordinator |
| `did:web:hs.etzhayyim.com:section:{section_slug}` | Section browse / explanation |
| `did:web:hs.etzhayyim.com:chapter:{chapter2}` | Chapter-level coverage / report |
| `did:web:hs.etzhayyim.com:heading:{heading4}` | Heading-level trade family |
| `did:web:hs.etzhayyim.com:subheading:{subheading6}` | Declaration-grade classification |
| `did:web:hs.etzhayyim.com:revision:{edition}` | Revision delta overlay |
| `did:web:hs.etzhayyim.com:country:{iso3}` | Country customs/policy overlay |

## Actor Paths

| Actor path | 説明 |
|---|---|
| `taxonomy:canonical` | HS hierarchy registry |
| `concordance:trade-item` | GTIN/CPC/ISIC mapping |
| `analytics:trade-flow` | import/export evidence coverage |
| `compliance:border-controls` | tariff / sanction / license hint |

## Data Collections

| collection | NSID | 内容 |
|---|---|---|
| node | `com.etzhayyim.apps.hs.node` | taxonomy node |
| concordance | `com.etzhayyim.apps.hs.concordance` | GTIN/CPC/ISIC mapping |
| tradeEvidence | `com.etzhayyim.apps.hs.tradeEvidence` | trade-flow / customs evidence |
| policyOverlay | `com.etzhayyim.apps.hs.policyOverlay` | country overlay |
| coverageReport | `com.etzhayyim.apps.hs.coverageReport` | per-DID coverage report |
| revisionDelta | `com.etzhayyim.apps.hs.revisionDelta` | edition diff |

## Commands

| command | 説明 |
|---|---|
| `get-node` | code から node 取得 |
| `get-children` | 下位分類取得 |
| `resolve-concordance` | GTIN/CPC/ISIC から HS resolve |
| `get-policy-overlay` | 国別 tariff / restriction 概要 |
| `get-coverage` | coverage metrics |
| `describe-revision-delta` | 改訂差分説明 |

## Heartbeat

coverage heartbeat は chapter / heading / subheading ごとに

1. taxonomy coverage
2. concordance coverage
3. trade evidence coverage
4. policy coverage

を集計し、最も弱い DID に coverage report を出す。
