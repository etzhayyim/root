# etzhayyim-project-public-sento — 銭湯立ち上げ運営 Fund

共通ルールは `60-apps/CLAUDE.md` を参照。

## Overview

`public-sento.etzhayyim.com` — 銭湯の立ち上げ・運営を対象にした公共資金ファンド。
開業準備から運営改善までを、Fund Campaign / Eligibility / Disbursement で一貫管理する。

## Domain Model

- `SentoFundCampaign`: 銭湯ファンド募集単位
- `SentoFacilityPlan`: 設備導入/更新計画
- `SentoOperationGrant`: 運営補助金申請
- `SentoReviewDecision`: 審査結果 (approve/reject/hold)
- `SentoDisbursement`: 分配実行レコード

## Capability Focus

- 開業資金調達 (クラウド型)
- 衛生・安全・省エネの設備投資
- 地域コミュニティ施策 (子ども/高齢者支援入浴など)
- 監査証跡 + 公開ダッシュボード

## Components

| Component | 役割 |
|---|---|
| `etzhayyim-wasm-public-sento-s3nt0fnd` | Public Sento Fund app (command/query/UI) |
