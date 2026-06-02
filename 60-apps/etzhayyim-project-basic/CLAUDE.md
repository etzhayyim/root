# etzhayyim-project-basic — 生活保証 App

共通ルールは `60-apps/CLAUDE.md` と `70-tools/CLAUDE.md` を参照。

## Overview

basic.etzhayyim.com — Society6 に conversion したユーザーに対する生活保証 (Basic Life Guarantee) コーディネーター。電気・水道・ガス・食料の 4 領域を統合管理し、受給者 (recipient) の well-becoming と growth を義務として追跡する。

## Domain Model

| 概念 | Graph 表現 |
|---|---|
| **受給者 (Recipient)** | `BsRecipient` node — society6 constituent から conversion |
| **受給資格 (Entitlement)** | `BsEntitlement` node — denki/suido/gas/food 各サービスへの受給権 |
| **義務 (Obligation)** | `BsObligation` node — well-becoming/growth 義務の追跡 |
| **配分 (Allocation)** | `BsAllocation` node — 月次リソース配分 |
| **イベント (Event)** | `BsEvent` node — 状態変更の監査ログ |

## Edge Predicates

| Predicate | Domain → Range | 説明 |
|---|---|---|
| `HAS_RECIPIENT` | BsOrg → BsRecipient | 組織の受給者 |
| `ENTITLED_TO` | BsRecipient → BsEntitlement | 受給権 |
| `HAS_OBLIGATION` | BsRecipient → BsObligation | 義務 |
| `ALLOCATED` | BsEntitlement → BsAllocation | 配分 |
| `CONVERTED_FROM` | BsRecipient → S6Constituent | society6 からの変換元 |

## Obligation Types

| Type | 説明 | 評価基準 |
|---|---|---|
| `well-becoming` | Well-becoming 指標の維持・向上 | well-becoming project の capability score |
| `growth` | 個人成長・スキル向上 | 学習記録、スキル取得、就労状況 |

## Cross-Project Dependencies

| Project | 関係 |
|---|---|
| `society6` | Constituent conversion source |
| `well-becoming` | Obligation 評価 (capability score) |
| `denki` | 電気サービス提供 |
| `suido` | 水道サービス提供 |
| `gas` | ガスサービス提供 |
| `food` | 食料サービス提供 |

## COFOG Classification

| COFOG Code | Description |
|---|---|
| 10.2 | Old age — income maintenance |
| 10.7 | Social exclusion n.e.c. — basic needs |
| 04.3 | Fuel and energy |
| 06.3 | Water supply |

## App Component

| Key | Value |
|---|---|
| Nanoid | `bs1c4l2f` |
| Folder | `wasm/etzhayyim-wasm-basic-bs1c4l2f/` |
| Service | `etzhayyim.basic.v1.BasicQueryService` / `etzhayyim.basic.v1.BasicCommandService` |
| Team room | `!team-bs1c4l2f` |
