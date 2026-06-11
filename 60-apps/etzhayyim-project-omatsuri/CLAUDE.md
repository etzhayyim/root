# etzhayyim-project-omatsuri — お祭り未病

**omatsuri.etzhayyim.com** — 未病 (pre-disease) 予防 Well-Becoming プラットフォーム。

## Core Concept: 未病クレジット

**運動するほど・健康でいるほどクレジットが増える。** クレジットで健康サービスを利用。

```
健康行動 (運動/食事/コミュニティ) → 未病クレジット獲得 → 健康サービス利用
         ↑                                                    ↓
         └──────────── 成長螺旋 (Well-Becoming) ──────────────┘
```

## Architecture

- **nanoid**: `mt5r1f8k`
- **performerType**: `service`
- **LLM**: Murakumo Opus 4.6 (`claude-opus-4-6`)
- **Pattern**: Single Worker + multi-DID + W Protocol Event Stream + Social Evolution heartbeat

## Credit Economy

### Earn (健康行動 → クレジット)

| Activity | Credits | Category |
|---|---|---|
| daily_walk | 5 | movement |
| run_5k / run_10k | 15 / 30 | movement |
| gym_session | 10 | fitness |
| yoga_session | 8 | fitness |
| healthy_meal_prep | 5 | nutrition |
| scan_product | 3 | nutrition |
| avoid_l5_ingredient | 5 | nutrition |
| daily_intake_log | 2 | nutrition |
| weekly_score_improvement | 10 | nutrition |
| ingredient_study_read | 3 | prevention |
| sleep_7plus_hours | 5 | rest |
| health_screening | 50 | prevention |
| community_matsuri | 25 | community |
| morning_radio_taiso | 8 | community |

### Spend (クレジット → 健康サービス)

| Service | Cost |
|---|---|
| fitness_class_booking | 20 |
| nutrition_consultation | 30 |
| personal_trainer_session | 50 |
| mibyou_assessment | 15 |
| llm_health_plan | 10 |

## Lexicon Collections

`com.etzhayyim.apps.omatsuri.{activity,meal,biomarker,mibyou_assessment,credit_tx,matsuri_event,matsuri_participant,ingredient,ingredient_risk_profile,product_scan,product_ingredient,daily_intake}`

## WIT

- Domain: `etzhayyim:omatsuri@1.0.0` (`wit/omatsuri/package.wit`)
- Export: `etzhayyim:omatsuri/mibyou@1.0.0`

## 原材料安全性スコアリング

設計: `90-docs/260327-ingredient-safety-scoring-design.md`

- **IngredientSafetyScore** (0–100): 原材料単体の安全性。7 カテゴリ × 5 リスクレベル (L1 Safe → L5 Critical)
- **ProductSafetyScore**: 製品全体スコア → Grade S/A/B/C/D/F
- **scan-product**: バーコード/原材料テキスト → Murakumo 解析 → 全原材料スコア + 製品グレード
- **daily-intake-log/summary**: 1日の累積 ADI% トラッキング → 閾値超過警告
- **dojo 連携**: `ingredient_*` drill → society6 competence/resilience 軸反映
