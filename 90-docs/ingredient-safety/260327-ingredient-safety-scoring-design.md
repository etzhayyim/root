---
id: ingredient-safety-scoring
title: 原材料安全性スコアリング設計 — コンビニ食品全原材料の Well-Becoming 評価
status: active
doc_type: adr
topic: ingredient-safety-scoring
authoritative: true
last_verified: 2026-03-27
authoritative_for:
  - ingredient safety scoring system
  - convenience store food ingredient evaluation
  - omatsuri × dojo × society6 food safety integration
related:
  - docs-omatsuri-claude
  - docs-dojo-claude
  - docs-society6-claude
---

# 原材料安全性スコアリング設計

**Status**: `[DESIGN]` Path A (DEFAULT)

## Goal

コンビニ等で販売される加工食品の**全原材料**を個別スコアリングし、omatsuri (未病予防) × dojo (readiness kata) × society6 (Well-Becoming Kyu/Dan) に統合する。消費者が「食べる前に知る」ための AI Agent-First 原材料評価基盤。

## Scope

- 日本のコンビニ食品 (セブン-イレブン, ファミリーマート, ローソン 等) の原材料表示を対象
- 食品添加物、加工助剤、アレルゲン、残留物質を網羅
- 国際基準 (WHO/JECFA, EFSA, Codex Alimentarius) + 日本基準 (厚労省, 消費者庁) の二軸評価
- omatsuri `meal-log` → 自動原材料スコア算出 → dojo kata → society6 competence 軸反映

## Executive Summary

原材料を 7 カテゴリ × 5 リスクレベルで分類し、各原材料に `IngredientSafetyScore` (0–100, 高い=安全) を付与。製品全体の `ProductSafetyScore` は原材料スコアの加重平均。omatsuri の `meal-log` にバーコード/原材料テキスト入力で自動スコア算出。dojo に食品安全 kata を追加し、society6 の competence/resilience 軸に反映。

## Decision

### 1. 原材料スコアリングモデル

#### 1.1 IngredientSafetyScore (0–100)

```
IngredientSafetyScore = BaseScore - RiskPenalty + BenefitBonus

BaseScore:    カテゴリ別初期値 (natural=90, processed=70, additive=50)
RiskPenalty:  リスク要因の累積減点
BenefitBonus: 栄養価/機能性の加点 (max 10)
```

#### 1.2 原材料カテゴリ (7 分類)

| Category | ID | BaseScore | 例 |
|---|---|---|---|
| **天然食材** | `natural` | 90 | 米, 小麦粉, 鶏肉, 大豆, 野菜 |
| **天然調味料** | `natural_seasoning` | 85 | 食塩, 砂糖, 醤油, 味噌, 酢 |
| **加工原料** | `processed` | 70 | 植物油脂, 加工でん粉, マーガリン, ショートニング |
| **食品添加物 (指定)** | `designated_additive` | 50 | 厚労省指定添加物 (472 品目) |
| **食品添加物 (既存)** | `existing_additive` | 60 | 既存添加物名簿 (357 品目) |
| **香料・一般飲食物** | `flavoring` | 65 | 天然香料, 一般飲食物添加物 |
| **残留・汚染物質** | `contaminant` | 10 | 残留農薬, 重金属, マイコトキシン |

#### 1.3 リスクレベル (5 段階)

| Level | RiskPenalty | 判定基準 | 色 |
|---|---|---|---|
| **L1 Safe** | 0 | ADI 十分, IARC 非該当, 厚労省承認 | `#22C55E` (緑) |
| **L2 Low** | -10 | ADI 設定あり, 通常摂取で問題なし | `#84CC16` (黄緑) |
| **L3 Moderate** | -25 | ADI 上限に近い摂取パターンあり, 一部研究で懸念 | `#EAB308` (黄) |
| **L4 High** | -40 | IARC Group 2B, 複数研究で健康影響示唆 | `#F97316` (橙) |
| **L5 Critical** | -60 | IARC Group 1/2A, 禁止国あり, 重篤健康被害報告 | `#EF4444` (赤) |

#### 1.4 リスク評価軸 (RiskPenalty 算出)

| 軸 | Weight | Source |
|---|---|---|
| **IARC 発がん性分類** | 30% | WHO IARC Monographs (Group 1/2A/2B/3/4) |
| **ADI 超過リスク** | 25% | JECFA/EFSA ADI vs 日本人平均摂取量 |
| **内分泌撹乱** | 15% | EU REACH, WHO/UNEP EDC リスト |
| **腸内細菌叢影響** | 10% | PubMed meta-analysis (emulsifiers, sweeteners) |
| **アレルゲン性** | 10% | 特定原材料 8 品目 + 準ずるもの 20 品目 |
| **禁止国数** | 10% | 他国で禁止/制限されている添加物 |

### 2. 主要リスク原材料データベース (コンビニ食品頻出)

#### 2.1 L5 Critical — 健康被害リスク高

| 原材料 | IARC | ADI | 主な健康被害 | 頻出製品 |
|---|---|---|---|---|
| トランス脂肪酸 (部分水素添加油脂) | — | WHO: 総エネルギー1%未満 | 心血管疾患, LDL 上昇 | マーガリン, ショートニング, 揚げ物 |
| 亜硝酸ナトリウム (発色剤) | 2A (加工肉) | 0.07 mg/kg/day | ニトロソアミン生成→胃がん | ハム, ソーセージ, ベーコン |
| タール系合成着色料 (赤色2号等) | 3 (一部 2B) | 品目別 | アレルギー, 注意欠如 (EU 警告) | 菓子, 飲料, 漬物 |
| 臭素酸カリウム | 2B | 使用後残存不可 | 腎毒性 (動物実験) | 一部パン (残存検出例) |
| アスパルテーム | 2B | 40 mg/kg/day | IARC 2023 発がん性可能性 | ダイエット飲料, 低カロリー食品 |

#### 2.2 L4 High — 過剰摂取で健康影響

| 原材料 | リスク | ADI/基準 | 頻出製品 |
|---|---|---|---|
| アセスルファムK | 動物実験で甲状腺影響 | 15 mg/kg/day | ゼロカロリー飲料 |
| スクラロース | 腸内細菌叢変化 (Duke 2008) | 15 mg/kg/day | 低糖質食品 |
| 安息香酸ナトリウム | ビタミンC共存でベンゼン生成 | 5 mg/kg/day | 炭酸飲料, ドレッシング |
| ソルビン酸カリウム | 亜硝酸と反応で変異原性 | 25 mg/kg/day | 漬物, かまぼこ, チーズ |
| カラメル色素 (III, IV) | 4-MEI 含有 (発がん性懸念) | — | コーラ, ソース, 醤油加工品 |
| リン酸塩 (各種) | Ca 吸収阻害, 腎負荷 | MTDI 70 mg/kg/day | ハム, プロセスチーズ, 麺 |
| TBHQ (t-ブチルヒドロキノン) | 高用量で胃腫瘍 (動物) | 0.7 mg/kg/day | 食用油, カップ麺 |

#### 2.3 L3 Moderate — 一部研究で懸念

| 原材料 | リスク | 頻出製品 |
|---|---|---|
| 加工でん粉 (ヒドロキシプロピル化等) | 未消化物の腸内影響 | おにぎり, 弁当, 惣菜 |
| 増粘多糖類 (カラギナン) | 腸炎症 (動物実験, 分解型) | プリン, ゼリー, ドレッシング |
| 乳化剤 (ポリソルベート80等) | 腸内バリア機能低下 (Chassaing 2015) | パン, アイスクリーム, チョコ |
| グルタミン酸ナトリウム (MSG) | 過敏症 (一部), 過剰摂取で頭痛 | 弁当, スナック, カップ麺 |
| 植物油脂 (パーム油) | 飽和脂肪酸 50%, 3-MCPD 生成 | 菓子, カップ麺, 揚げ物 |
| 果糖ぶどう糖液糖 (HFCS) | 肝脂肪, 尿酸上昇, 肥満 | 清涼飲料水, 菓子パン |

#### 2.4 L2 Low — 通常摂取で問題なし

| 原材料 | 備考 | 頻出製品 |
|---|---|---|
| ビタミンC (酸化防止剤) | 栄養素兼用, 安全性高 | 飲料, ハム |
| トコフェロール (酸化防止剤) | ビタミンE, 天然抽出 | 食用油, スナック |
| 炭酸水素ナトリウム (重曹) | 膨張剤, 長い使用歴 | 菓子, パン |
| レシチン (乳化剤) | 大豆/卵由来, 栄養素 | チョコレート, パン |
| ペクチン (増粘安定剤) | 食物繊維, 天然 | ジャム, ゼリー |

#### 2.5 L1 Safe — 安全性確立

| 原材料 | 備考 |
|---|---|
| 食塩 (過剰摂取は別問題) | 精製度で微差あり |
| 砂糖 (過剰摂取は別問題) | 上白糖, グラニュー糖 |
| 醤油, 味噌 | 発酵食品, 伝統調味料 |
| 寒天 | 天然海藻由来 |
| にがり (塩化マグネシウム) | 豆腐凝固剤 |

### 3. ProductSafetyScore (製品全体スコア)

```
ProductSafetyScore = Σ(IngredientScore_i × Weight_i) / Σ(Weight_i)

Weight_i = 配合順序の逆数 (原材料表示は多い順)
  1番目: weight=1.0
  2番目: weight=0.9
  3番目: weight=0.8
  ...
  10番目以降: weight=0.3 (下限)
```

**製品グレード**:

| Grade | Score | 表示 | 説明 |
|---|---|---|---|
| **S** | 85–100 | 極めて安全 | 天然食材中心, 添加物最小限 |
| **A** | 70–84 | 安全 | 一般的な添加物使用, リスク低 |
| **B** | 55–69 | 注意 | L3 以上の原材料含有 |
| **C** | 40–54 | 要注意 | L4 原材料複数, 常食非推奨 |
| **D** | 25–39 | 危険 | L5 原材料含有, 摂取頻度制限推奨 |
| **F** | 0–24 | 非推奨 | 複数 L5 原材料, 健康被害リスク |

### 4. omatsuri 統合 — 未病クレジット連動

#### 4.1 新規 Lexicon Collections

```
com.etzhayyim.apps.omatsuri.{
  ingredient,              // 原材料マスタ (name, category, risk_level, score, evidence)
  ingredient_risk_profile, // 原材料リスクプロファイル (IARC, ADI, banned_countries, studies)
  product_scan,            // 製品スキャン結果 (barcode, ingredients[], product_score, grade)
  product_ingredient,      // 製品×原材料関連 (product_id, ingredient_id, order, weight)
  daily_intake,            // 1日摂取量トラッキング (per-ingredient cumulative ADI%)
}
```

#### 4.2 クレジット連動

| Activity | Credits | Category | 条件 |
|---|---|---|---|
| `scan_product` | 3 | nutrition | 製品バーコード/原材料スキャン |
| `avoid_l5_ingredient` | 5 | nutrition | L5 原材料の代替品を選択 (比較スキャン) |
| `daily_intake_log` | 2 | nutrition | 1日の摂取原材料を記録 |
| `weekly_score_improvement` | 10 | nutrition | 週平均 ProductSafetyScore が前週比 +5 以上 |
| `ingredient_study_read` | 3 | prevention | 原材料リスク解説を読了 |

#### 4.3 Murakumo LLM 統合

- `scan-product`: バーコード or 原材料テキスト → Murakumo が原材料を個別解析 → `IngredientSafetyScore` 一括算出
- `ingredient-risk-explain`: 特定原材料のリスクを Murakumo が論文ベースで解説 (PubMed/EFSA/JECFA 引用)
- `meal-plan-safe`: 1日の食事プランから累積 ADI% を計算し、安全な代替品を提案
- `product-compare`: 2 製品の原材料比較 → どちらが安全か根拠付きで回答

### 5. dojo 統合 — 食品安全 Kata

#### 5.1 新規 DrillSession 種別

| Drill | 内容 | Score Source |
|---|---|---|
| `ingredient_identification` | 原材料名からリスクレベルを判定 | 正答率 |
| `product_label_reading` | 原材料表示から危険原材料を全て特定 | 検出率 + 誤検出ペナルティ |
| `adi_calculation` | 1日の食事から特定添加物の ADI% を計算 | 精度 |
| `safer_alternative` | L4/L5 原材料を含む製品の代替品を提案 | 妥当性 (Murakumo 評価) |
| `allergen_check` | 特定原材料 8 品目 + 20 品目の検出 | 検出率 |

#### 5.2 society6 連携

```
dojo CompleteDrill(drill_type="ingredient_*")
  → WSend("dojo-feed", "dojo.drill.completed")
  → society6 Cypher query: DojoDrill WHERE drill_type STARTS WITH "ingredient_"
  → competence 軸 (25%) に食品安全 drill score を反映
  → resilience 軸 (10%) に AAR (なぜ間違えたか) を反映
```

### 6. society6 統合 — Nutrition Awareness 軸

既存 5 軸に**直接介入せず**、competence 軸の drill source として食品安全 kata を追加:

```
Competence (25%) = avg(
  existing_drill_scores,        // 既存ドリル
  ingredient_drill_scores,      // 食品安全ドリル (新規)
)
```

追加で `omatsuri.daily_intake` の weekly average を Growth 軸 (20%) の delta 計算に含める:

```
Growth (20%) = score_delta(
  wellbecoming_score_30d_ago,
  current_wellbecoming_score + nutrition_awareness_bonus
)

nutrition_awareness_bonus = min(50, weekly_avg_product_safety_score / 2)
```

### 7. Data Flow

```
[Consumer]
  │ バーコードスキャン / 原材料テキスト入力
  ▼
[omatsuri] scan-product
  │ Murakumo LLM → 原材料パース → IngredientSafetyScore 算出
  │ → ComAtprotoRepoCreateRecord("product_scan", result)
  │ → ComAtprotoRepoCreateRecord("daily_intake", cumulative)
  │ → AppBskyFeedPost("製品X: Grade B (Score 62) — L4原材料: リン酸塩")
  ▼
[dojo] ingredient_identification drill
  │ omatsuri の ingredient master を教材として使用
  │ → CompleteDrill → WSend("dojo-feed")
  ▼
[society6] CalculateScore
  │ Cypher cross-app query:
  │   DojoDrill WHERE drill_type STARTS WITH "ingredient_" → competence
  │   OmatsuriDailyIntake → nutrition_awareness_bonus → growth
  ▼
[Consumer] Kyu/Dan ランク反映
```

### 8. Graph Nodes

```cypher
// 原材料マスタ
(:Ingredient {
  id, name, name_en, category, risk_level, safety_score,
  iarc_group, adi_mg_kg_day, banned_country_count,
  cas_number, e_number,
  org_id, user_id, actor_id
})

// 原材料リスクプロファイル
(:IngredientRiskProfile {
  ingredient_id, axis, score, evidence_url, evidence_summary,
  org_id, user_id, actor_id
})

// 製品スキャン
(:ProductScan {
  id, barcode, product_name, brand, store_chain,
  product_score, grade, ingredient_count, l4_count, l5_count,
  scanned_by_did,
  org_id, user_id, actor_id
})

// 製品×原材料
(:ProductScan)-[:CONTAINS {order: 1, weight: 1.0}]->(:Ingredient)

// 1日摂取トラッキング
(:DailyIntake {
  did, date, ingredient_id, amount_mg, adi_percentage,
  org_id, user_id, actor_id
})
```

### 9. WIT Interface 追加 (omatsuri)

```wit
// etzhayyim:omatsuri/mibyou@1.0.0 に追加

/// Scan product barcode or ingredient text → IngredientSafetyScore + ProductSafetyScore.
scan-product: func(params: string) -> result<string, string>;

/// Get ingredient risk profile with evidence links.
ingredient-risk-profile: func(params: string) -> result<string, string>;

/// Compare two products by ingredient safety.
compare-products: func(params: string) -> result<string, string>;

/// Track daily ingredient intake and ADI%.
daily-intake-log: func(params: string) -> result<string, string>;

/// Get cumulative daily intake summary with ADI warnings.
daily-intake-summary: func(params: string) -> result<string, string>;

/// Search ingredient database by name or category.
ingredient-search: func(params: string) -> result<string, string>;
```

### 10. Evidence Sources

| Source | 用途 | URL |
|---|---|---|
| WHO IARC Monographs | 発がん性分類 | monographs.iarc.who.int |
| JECFA (WHO/FAO) | ADI 設定 | apps.who.int/food-additives-contaminants-jecfa-database |
| EFSA OpenFoodTox | 欧州リスク評価 | efsa.europa.eu/en/data-report/chemical-hazards-database |
| 厚生労働省 食品添加物リスト | 日本基準 | mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/shokuhin/syokuten/ |
| 消費者庁 食品表示基準 | 表示ルール | caa.go.jp/policies/policy/food_labeling/ |
| Open Food Facts | バーコード→原材料 DB | world.openfoodfacts.org |
| PubMed | 個別研究 | pubmed.ncbi.nlm.nih.gov |
| Codex Alimentarius | 国際食品規格 | fao.org/fao-who-codexalimentarius |

## Exceptions

- `IngredientSafetyScore` は**摂取量を考慮しない**単体リスク評価。実際の健康影響は `daily-intake-summary` で ADI% として評価
- 天然食材の過剰摂取リスク (食塩, 砂糖) は `IngredientSafetyScore` ではなく `daily-intake-log` で管理
- 原材料マスタの初期データは Murakumo LLM + Open Food Facts + 厚労省データの統合。人的レビュー (HC) で精度向上

## References

- `60-apps/etzhayyim-project-omatsuri/CLAUDE.md` — 未病クレジット設計
- `60-apps/etzhayyim-project-dojo/CLAUDE.md` — readiness kata 設計
- `60-apps/etzhayyim-project-society6/CLAUDE.md` — Well-Becoming Kyu/Dan 設計
- `60-apps/etzhayyim-project-yabai/260303-yabai-wellbecoming-risk-design.md` — リスクスコア参考
- `60-apps/etzhayyim-project-government-body/FOOD_SAFETY_MOLD_PREVENTION.md` — 食品安全法規
