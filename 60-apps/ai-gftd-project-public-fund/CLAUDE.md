# ai-gftd-project-public-fund — Public Fund App Rules

共通ルールは `60-apps/CLAUDE.md` と `70-tools/CLAUDE.md` を参照。

## Overview

`pb.gftd.ai` — クラウドファンディング方式の公共資金ファンド。COFOG/ISIC/APQC ベースの起案・審査・分配。

## Domain Model

権威ソース: `90-docs/260303-public-fund-app-design.md`

- FundCampaign, Pledge, FundProgram, EligibilityPolicy, Application, Decision, Disbursement

## Education & Family Fund Agents

権威ソース: `90-docs/260315-education-family-fund-agents-design.md`

| Agent | ISCO | Name | COFOG | Role |
|---|---|---|---|---|
| Education Fund Manager | 1345 | 学 (Manabu) | 09 | 教育ファンド審査・予算配分 |
| Early Childhood Specialist | 2342 | 芽 (Mei) | 09.1 | 幼児教育プログラム評価 |
| Family Welfare Manager | 1344 | 結 (Yui) | 10.4 | 家庭支援ファンド管理 |
| Social Worker | 2635 | 心 (Kokoro) | 10.4, 10.7 | 個別ケース支援・セーフガード |

## Components

| Component | 役割 |
|---|---|
| `public-fund-orchestrator-component` | 旧 orchestrator (Adapter 方式) |
| `ai-gftd-wasm-pb-p8bl1cfn` | 標準 App (Command/Query/UI) |

## CRITICAL: Cross-Project Matrix Conversation (with well-becoming)

→ `gftd dodaf tv1 query --id ai-gftd-project-public-fund-cross-project-matrix-conversatio` / MCP `gftd.dodaf.tv1.query`

## Nested Reference

- Daily Evolution: daily evolution multi-agent design
- Cross-project Matrix: `90-docs/260315-cross-project-matrix-conversation-design.md`
- Capability agents: `60-apps/ai-gftd-project-well-becoming/90-docs/260315-child-capability-agents-design.md`
