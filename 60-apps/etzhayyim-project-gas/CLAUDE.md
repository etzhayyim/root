# etzhayyim-project-gas — ガスサービス App

共通ルールは `60-apps/CLAUDE.md` と `70-tools/CLAUDE.md` を参照。

## Overview

gas.etzhayyim.com — basic.etzhayyim.com のガス領域。受給者への都市ガス/LPG 供給管理、使用量追跡、プラン管理。

## Domain Model

| 概念 | Graph 表現 |
|---|---|
| **ガスアカウント (Account)** | `GsAccount` node — recipient に紐づくガス契約 |
| **使用量 (Usage)** | `GsUsage` node — 月次ガス使用量記録 |
| **プラン (Plan)** | `GsPlan` node — ガス供給プラン (基本/節約/標準) |
| **イベント (Event)** | `GsEvent` node — 状態変更の監査ログ |

## Edge Predicates

| Predicate | Domain → Range | 説明 |
|---|---|---|
| `HAS_ACCOUNT` | BsRecipient → GsAccount | 受給者のガスアカウント |
| `SUBSCRIBED_TO` | GsAccount → GsPlan | プラン契約 |
| `HAS_USAGE` | GsAccount → GsUsage | 使用量記録 |

## COFOG Classification

| COFOG Code | Description |
|---|---|
| 04.3.2 | Gas |

## App Component

| Key | Value |
|---|---|
| Nanoid | `gs5a6s1m` |
| Folder | `wasm/etzhayyim-wasm-gas-gs5a6s1m/` |
| Service | `etzhayyim.gas.v1.GasQueryService` / `etzhayyim.gas.v1.GasCommandService` |
| Team room | `!team-gs5a6s1m` |
