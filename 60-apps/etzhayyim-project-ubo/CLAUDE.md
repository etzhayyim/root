# etzhayyim-project-ubo — Ultimate Beneficial Owner Analysis

`ubo.etzhayyim.com` — 土地・建物・法人・口座の所有構造を SQL graph で統合し、実質的支配者 (UBO) を特定・公開する App。

## Architecture: Design E + Intel Reactive Pipeline

```
intel.etzhayyim.com → Follow → com.etzhayyim.apps.intel.report commit
  → handleComAtprotoSyncSubscribeReposCommit
  → Murakumo LLM (ownership extraction)
  → ComAtprotoRepoCreateRecord("uboEntity"/"ubo_ownership") [Tier 2: domain]
  → AppBskyFeedPost(entityDID, analysis) [Tier 1: social]

legal-entity.etzhayyim.com → Follow → com.etzhayyim.apps.legal_entity.entity commit
  → auto-register as UBOEntity [Tier 2: domain]
```

## Domain Model

### Record Types (Design E Tier 2 — `com.etzhayyim.apps.ubo.*`)

| collection | 説明 |
|---|---|
| `ubo_entity` | 分析対象エンティティ (法人・土地・建物・口座・信託・ファンド) |
| `ubo_person` | 自然人 (UBO 候補) |
| `ubo_ownership` | 所有/支配関係 |
| `ubo_result` | UBO 分析結果 (is_ubo + effective_pct + chains) |
| `ubo_alert` | 閾値超過・循環所有・高リスク警告 |
| `ubo_report` | 公開レポート (分析 + リスク評価) |
| `ubo_risk_assessment` | Murakumo LLM リスク評価結果 |
| `ubo_intel_analysis` | intel レポート UBO 分析結果 |
| `ubo_legal_review` | 法務レビュー依頼 |

### Path-Based DIDs

| DID | entity_type |
|---|---|
| `did:web:ubo.etzhayyim.com:corporation` | 法人 |
| `did:web:ubo.etzhayyim.com:land` | 土地 |
| `did:web:ubo.etzhayyim.com:building` | 建物 |
| `did:web:ubo.etzhayyim.com:account` | 口座 |
| `did:web:ubo.etzhayyim.com:trust` | 信託 |
| `did:web:ubo.etzhayyim.com:fund` | ファンド |

### UBO 判定基準

- FATF 基準: 直接・間接所有 **25%** 以上 = UBO
- 間接所有率 = 経路上の所有率の積 (A→60%→B→50%→C = A の C に対する間接所有率 30%)
- 最大 **10 hop** トラバーサル
- 循環所有構造の検出・警告
- 複数経路の所有率は合算

## Murakumo LLM Integration

| Command | 用途 | Temperature |
|---|---|---|
| `InterpretOwnership` | 非構造テキストから所有関係を抽出 | 0.1 |
| `AssessRisk` | 5 軸リスク評価 (集中・複雑性・循環・法域・総合) | 0.3 |
| `AnalyzeIntelReport` | intel レポートから UBO 関連シグナル抽出 | 0.2 |
| reactive pipeline | intel commit → 自動所有関係抽出 | 0.1 |

## Cross-actor Integration

| app | 連携内容 |
|---|---|
| `intel.etzhayyim.com` (i7n73l0x) | Follow → intel.report/indicator commit を reactive 受信 → Murakumo で UBO 分析 |
| `legal-entity.etzhayyim.com` | Follow → entity commit を UBOEntity に自動同期 |
| `malak.etzhayyim.com` | 反社チェック・制裁リスト照合 (cross-actor invoke) |
| lawyer/lawfirm agent | `RequestLegalReview` → cross-actor discovery → 法務レビュー |

## Contract

- FATF Recommendation 24/25 (Beneficial Ownership)
- 犯罪収益移転防止法 (Japanese AML Act)
