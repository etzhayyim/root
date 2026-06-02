# etzhayyim-project-denki — 電気サービス App

共通ルールは `60-apps/CLAUDE.md` と `70-tools/CLAUDE.md` を参照。

## Overview

denki.etzhayyim.com — basic.etzhayyim.com の電気領域。受給者への電力供給管理、使用量追跡、プラン管理。

## Domain Model

| 概念 | Graph 表現 |
|---|---|
| **電気アカウント (Account)** | `DkAccount` node — recipient に紐づく電力契約 |
| **使用量 (Usage)** | `DkUsage` node — 月次電力使用量記録 |
| **プラン (Plan)** | `DkPlan` node — 電力供給プラン (基本/節約/標準) |
| **イベント (Event)** | `DkEvent` node — 状態変更の監査ログ |

## Edge Predicates

| Predicate | Domain → Range | 説明 |
|---|---|---|
| `HAS_ACCOUNT` | BsRecipient → DkAccount | 受給者の電力アカウント |
| `SUBSCRIBED_TO` | DkAccount → DkPlan | プラン契約 |
| `HAS_USAGE` | DkAccount → DkUsage | 使用量記録 |

## COFOG Classification

| COFOG Code | Description |
|---|---|
| 04.3.5 | Electricity |

## App Component

| Key | Value |
|---|---|
| Nanoid | `dk3n7k8p` |
| Folder | `wasm/etzhayyim-wasm-denki-dk3n7k8p/` |
| Service | `etzhayyim.denki.v1.DenkiQueryService` / `etzhayyim.denki.v1.DenkiCommandService` |
| Team room | `!team-dk3n7k8p` |
