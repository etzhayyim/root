# etzhayyim-project-food — 食料サービス App

共通ルールは `60-apps/CLAUDE.md` と `70-tools/CLAUDE.md` を参照。

## Overview

food.etzhayyim.com — basic.etzhayyim.com の食料領域。受給者への食料配給管理、注文追跡、配送管理。food-processor (食肉加工) とは別の消費者向け食料供給サービス。

## Domain Model

| 概念 | Graph 表現 |
|---|---|
| **食料アカウント (Account)** | `FdAccount` node — recipient に紐づく食料配給契約 |
| **注文 (Order)** | `FdOrder` node — 食料注文記録 |
| **配送 (Delivery)** | `FdDelivery` node — 配送記録 |
| **プラン (Plan)** | `FdPlan` node — 食料配給プラン (基本/家族/個人) |
| **イベント (Event)** | `FdEvent` node — 状態変更の監査ログ |

## Edge Predicates

| Predicate | Domain → Range | 説明 |
|---|---|---|
| `HAS_ACCOUNT` | BsRecipient → FdAccount | 受給者の食料アカウント |
| `SUBSCRIBED_TO` | FdAccount → FdPlan | プラン契約 |
| `PLACED_ORDER` | FdAccount → FdOrder | 注文 |
| `DELIVERED_BY` | FdOrder → FdDelivery | 配送 |

## Cross-Project Dependencies

| Project | 関係 |
|---|---|
| `food-processor` | 食肉加工サプライチェーン (調達元) |

## COFOG Classification

| COFOG Code | Description |
|---|---|
| 10.7 | Social exclusion n.e.c. — food assistance |

## App Component

| Key | Value |
|---|---|
| Nanoid | `fd7o8d3n` |
| Folder | `wasm/etzhayyim-wasm-food-fd7o8d3n/` |
| Service | `etzhayyim.food.v1.FoodQueryService` / `etzhayyim.food.v1.FoodCommandService` |
| Team room | `!team-fd7o8d3n` |
