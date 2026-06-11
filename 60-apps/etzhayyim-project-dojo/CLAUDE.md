# etzhayyim-project-dojo

Readiness-focused skill training, scenario drills, qualification gates, and AAR loops. **society6.etzhayyim.com well-becoming scoring の competence/resilience 軸の data source。**

**URL**: `https://dojo.etzhayyim.com`

## Scope

- `TrainingTrack` lifecycle (create/update/list)
- `DrillSession` lifecycle (start/complete) — **CompleteDrill が society6 scoring を WSend で通知**
- `AAR` capture and retrieval
- `Readiness` aggregation per track and org
- **食品安全 Kata** — omatsuri 原材料スコアリング連携 (`ingredient_*` drill types)

## society6 連携

- `CompleteDrill` → WSend(`dojo-feed`, `dojo.drill.completed`) で drill score を publish
- society6 が SQL `DojoDrill`/`DojoAAR` を cross-app query して competence/resilience 軸を計算

## Runtime

- Kotodama app component: `wasm/etzhayyim-wasm-dojo-d0j0k4t4/`
- Command/Query split via `app.Command(...)` and `app.Query(...)`
- W Protocol: `[space] dojo-feed` channel for drill completion events

## 食品安全 Kata (omatsuri 連携)

設計: `90-docs/260327-ingredient-safety-scoring-design.md`

| Drill Type | 内容 | Score Source |
|---|---|---|
| `ingredient_identification` | 原材料名からリスクレベル (L1–L5) を判定 | 正答率 |
| `product_label_reading` | 原材料表示から L4/L5 原材料を全て特定 | 検出率 |
| `adi_calculation` | 1日の食事から ADI% を計算 | 精度 |
| `safer_alternative` | L4/L5 製品の代替品を提案 | Murakumo 妥当性評価 |
| `allergen_check` | 特定原材料 8+20 品目の検出 | 検出率 |

- omatsuri の `ingredient` master を教材データとして使用
- `CompleteDrill(drill_type="ingredient_*")` → WSend → society6 competence/resilience 軸に反映

## Wellness Training System (Duolingo-style)

Duolingo 式の段階的 wellness training。society6 Well-Becoming 5 軸に対応する 5 domain track。

### Track → Unit → Step → Quiz

| 層 | 説明 |
|---|---|
| **WellnessTrack** | 5 domain (physical/nutritional/mental/social/financial) |
| **TrackUnit** | Track 内の章 (7 tiers: 白帯→カラーベルト→黒帯→師範)。帯でゲート |
| **Step** | Unit 内の個別レッスン (2-5 questions, 4 question types) |
| **Quiz** | multiple_choice / true_false / fill_in / scenario |

### 帯制度 (白帯 → カラーベルト → 黒帯 → 師範)

#### Phase 1: 白帯 (White Belt) — 入門

| 帯 | XP | 評価基準 | コンテンツ | 昇格条件 |
|---|---|---|---|---|
| **白帯** (Kyu 7) | 0+ | 参加率・steps 開始数 | 全 track 導入 lesson (TF+MC のみ, diff 1) | 3+ steps 完了, accuracy 50%+, 2+ track 開始 |

#### Phase 2: カラーベルト (Color Belts) — 成長

| 帯 | XP | 評価基準 | コンテンツ | 昇格条件 |
|---|---|---|---|---|
| **黄帯** (Kyu 6) | 150+ | 基礎 quiz 正答率 + streak | Unit 1 前半 (MC+TF, diff 1) | 1 track で 3+ steps, accuracy 60%+, streak 3+ |
| **橙帯** (Kyu 5) | 400+ | 知識定着 + daily goal + 復習 | Unit 1 後半 + review 解放 + fill_in (diff 2) | 2+ track Unit 1 完了, accuracy 65%+, daily goal 5日連続 |
| **緑帯** (Kyu 4) | 800+ | 中級正答率 + scenario 入門 | Unit 2 前半 + scenario 問題入門 (diff 2) | 1+ track Unit 2 開始, accuracy 70%+, streak 7+ |
| **青帯** (Kyu 3) | 1200+ | 中級定着 + fill_in + 時間管理 | Unit 2 後半 + fill_in 問題 (diff 3) | 2+ track Unit 2 進行, fill_in accuracy 70%+ |
| **紫帯** (Kyu 2) | 1700+ | scenario 対応力 + cross-domain | scenario deep-dive + cross-domain mini (diff 3) | 3+ track Unit 2 進行中, scenario accuracy 75%+ |
| **茶帯** (Kyu 1) | 2200+ | 全中級 mastery + 黒帯 readiness | 全 track Unit 2 + 昇段審査 preview (diff 3) | 全 5 track Unit 2 完了, overall accuracy 85%+, streak 21+ |

#### Phase 3: 黒帯 (Black Belt) — 熟達

| 帯 | XP | 評価基準 | コンテンツ | 昇格条件 |
|---|---|---|---|---|
| **黒帯初段** (Dan 1) | 3000+ | 全基礎・中級 mastery + 応用 readiness | Unit 3 (応用) + challenge + AAR (diff 4) | 全 5 track Unit 1-2 完了, streak 30+, review retention 80%+ |
| **黒帯二段** (Dan 2) | 4500+ | 応用正答率 + 時間効率 + scenario 分析 | Unit 3 応用 + scenario deep-dive (diff 4) | 2+ track Unit 3 開始, accuracy 80%+ |
| **黒帯三段** (Dan 3) | 6000+ | 応用 scenario + AAR 分析力 + 実践力 | challenge + AAR テンプレート + ワークショップ (diff 5) | 3+ track Unit 3 完了, AAR 10+, challenge accuracy 80%+ |
| **黒帯四段** (Dan 4) | 7500+ | cross-domain 応用 + 実践ケース | cross-domain 統合 + ケーススタディ (diff 5) | 4+ track Unit 3 完了, scenario accuracy 85%+ |
| **黒帯五段** (Dan 5) | 9000+ | 全 domain mastery + 指導準備 | Shihan 準備 + 指導法入門 + master challenge (diff 5) | 全 5 track 完了, cross-domain 90%+, AAR 20+ |

#### Phase 4: 師範 (Shihan) — 指導

| 帯 | XP | 評価基準 | コンテンツ | 権限 |
|---|---|---|---|---|
| **準師範** (Shihan 1) | 12000+ | メンタリング実績 + レビュー品質 | 全 + レビュー + メンタリング | `review_content`, `mentor` |
| **師範** (Shihan 2) | 15000+ | クイズ作成品質 + 弟子の成長率 | 全 + クイズ作成 + 弟子管理 | + `create_quiz`, `view_analytics` |
| **大師範** (Shihan 3) | 20000+ | カリキュラム設計 + 認定実績 | 全 + カリキュラム設計 + 認定 | + `create_curriculum`, `create_track`, `issue_certification` |

### Gamification

- **Hearts**: 1 session 5 hearts。不正解 → -1。0 → session end。Gems (10) で refill
- **Daily Goal**: configurable XP target (5-200)
- **Spaced Repetition**: SM-2 algorithm。不正解 → review queue (4h → 1d → 6d → interval*EF)
- **XP**: step 完了 15 XP, perfect 25 XP, review 10 XP, 導入 10 XP, 応用 35-50 XP

### Collections

- `com.etzhayyim.apps.dojo.step_attempt` — step 挑戦記録
- `com.etzhayyim.apps.dojo.step_completed_event` — society6 連携イベント
- `com.etzhayyim.apps.dojo.track_progress` — track 進捗
- `com.etzhayyim.apps.dojo.review_item` — spaced repetition queue
- `com.etzhayyim.apps.dojo.daily_goal` — daily XP goal config

### Commands

| Command | 説明 |
|---|---|
| `list_wellness_tracks` | 5 domain track 一覧 |
| `get_wellness_track` | track 詳細 (rank ゲート付き) |
| `get_track_progress` | actor の track 進捗 |
| `start_step` | step 開始 (questions を正答なしで返却) |
| `submit_step_answer` | 1 問回答 (正誤 + 解説を返却) |
| `complete_step` | step 完了 (XP 付与 + society6 通知) |
| `refill_hearts` | gems で hearts 回復 |
| `set_daily_goal` | daily XP goal 設定 |
| `get_daily_status` | 今日の進捗 vs goal |
| `get_review_queue` | 復習待ち items (SM-2) |
| `submit_review` | 復習回答 (interval 更新) |

## Conventions

- First-party API surface is XRPC facade; business semantics are normalized to W Protocol command/query model.
- New REST mutation endpoints are prohibited.
- Multi-tenant isolation requires `org_id` filtering on all reads/writes.
