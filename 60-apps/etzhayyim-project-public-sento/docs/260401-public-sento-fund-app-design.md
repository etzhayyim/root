# 260401 Public Sento Fund App Design

## Goal

`etzhayyim-project-public-sento` は、銭湯の立ち上げと運営改善に必要な資金を公共型に集約し、透明に審査・分配する。

## Core Workflow

1. Fund Campaign 起案 (`SentoFundCampaign`)
2. credits による拠出 (`Pledge`)
3. 申請 (`SentoOperationGrant`)
4. 審査 (`SentoReviewDecision`)
5. 分配 (`SentoDisbursement`)
6. KPI 公開 (運営継続率、衛生適合率、地域利用率)

## Initial Policy

- 優先配分: 衛生設備更新、燃料/光熱効率改善、地域福祉入浴枠
- 申請要件: 営業計画、衛生計画、月次運営実績
- 監査: 全分配は `actor_id`, `org_id`, `created_at` を必須記録

## Open Points

- COFOG/ISIC/APQC の詳細マッピング
- 既存 `etzhayyim-project-public-fund` とのクロスファンド連携
- 公募審査の自動化ポリシー (human-in-the-loop 境界)
