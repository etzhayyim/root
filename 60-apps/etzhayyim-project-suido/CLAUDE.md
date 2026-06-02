# etzhayyim-project-suido — 水道サービス App

共通ルールは `60-apps/CLAUDE.md` と `70-tools/CLAUDE.md` を参照。

## Overview

suido.etzhayyim.com — basic.etzhayyim.com の水道領域。受給者への上下水道供給管理、使用量追跡、プラン管理。

## Domain Model

| 概念 | Graph 表現 |
|---|---|
| **水道アカウント (Account)** | `SdAccount` node — recipient に紐づく水道契約 |
| **使用量 (Usage)** | `SdUsage` node — 月次水道使用量記録 |
| **プラン (Plan)** | `SdPlan` node — 水道供給プラン (基本/節約/標準) |
| **イベント (Event)** | `SdEvent` node — 状態変更の監査ログ |

## Edge Predicates

| Predicate | Domain → Range | 説明 |
|---|---|---|
| `HAS_ACCOUNT` | BsRecipient → SdAccount | 受給者の水道アカウント |
| `SUBSCRIBED_TO` | SdAccount → SdPlan | プラン契約 |
| `HAS_USAGE` | SdAccount → SdUsage | 使用量記録 |

## COFOG Classification

| COFOG Code | Description |
|---|---|
| 06.3 | Water supply |

## App Component

| Key | Value |
|---|---|
| Nanoid | `sd9w2t4r` |
| Folder | `wasm/etzhayyim-wasm-suido-sd9w2t4r/` |
| Service | `etzhayyim.suido.v1.SuidoQueryService` / `etzhayyim.suido.v1.SuidoCommandService` |
| Team room | `!team-sd9w2t4r` |
