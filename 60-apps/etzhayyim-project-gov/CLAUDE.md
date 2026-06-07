# etzhayyim-project-gov — 公的サービス Well-Becoming

**gov.etzhayyim.com** — 医療・保険・福祉・教育の公的サービスを横断的に統合する Well-Becoming ハブ。

## Architecture

- **nanoid**: `gv7ps2m1`
- **performerType**: `service`
- **DID**: `did:web:gv7ps2m1.etzhayyim.com` (yata App + Profile 登録済み)
- **uiType**: `redirect` (zero frontend)
- **LLM**: Murakumo Opus 4.6 (`claude-opus-4-6`)
- **Pattern**: Single Worker + multi-DID + W Protocol Event Stream + Social Evolution heartbeat

## Path-based DID Agents (COFOG-aligned)

| Agent | DID path | 役割 |
|---|---|---|
| healthcare | `did:web:gov.etzhayyim.com:healthcare` | 医療相談・プロバイダマッチング |
| insurance | `did:web:gov.etzhayyim.com:insurance` | 公的保険 (国保/社保/後期高齢者) |
| welfare | `did:web:gov.etzhayyim.com:welfare` | 社会福祉 (生活保護/障害者支援) |
| education | `did:web:gov.etzhayyim.com:education` | 教育・生涯学習・職業訓練 |
| prevention | `did:web:gov.etzhayyim.com:prevention` | 予防 (健診/ワクチン) |
| housing | `did:web:gov.etzhayyim.com:housing` | 住居支援 |
| employment | `did:web:gov.etzhayyim.com:employment` | 雇用・就労支援 |
| child_family | `did:web:gov.etzhayyim.com:child_family` | 子育て・児童福祉 |

## Key Features

- **Healthcare consultation**: Opus 4.6 による症状トリアージ + 診療科推奨
- **Insurance navigation**: 高額療養費計算、保険制度ナビゲーション
- **Welfare assessment**: 各種手当 (児童手当/障害者手当/生活保護) 受給資格判定
- **Life stage plan**: ライフイベント × 公的サービス横断統合プラン
- **Credit system**: Tier-based (free/basic/pro) 月間利用上限

## Lexicon Collections

`com.etzhayyim.apps.gov.{healthcare_consult,vaccination,education_plan,life_stage_plan,credit_usage}`

## WIT

- Domain: `etzhayyim:gov@1.0.0` (`wit/gov/package.wit`)
- Export: `etzhayyim:gov/public-service@1.0.0`
- Import: `kotodama:div/health`, `kotodama:div/social-protection`, `kotodama:div/education`, `kotodama:contract/agreement`
