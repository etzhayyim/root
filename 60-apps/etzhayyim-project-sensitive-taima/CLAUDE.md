# ai-gftd-project-sensitive-taima

## Identity

| Key | Value |
|---|---|
| nanoid | `tm01prv0` |
| DID | `did:web:sensitive-taima.gftd.ai` |
| performerType | `service` |
| sensitivity | `restricted` |
| domain | 大麻政策 intelligence — 日本における合法化推進のための立法・研究・世論・国際比較データ収集・分析 |

## Architecture: Policy Intelligence Agent (Restricted)

natural-person と同一の **hidden DID** パターン。T0 existence-hidden。consent grant + clearance=restricted のみアクセス可。

### Data Collections (ai.gftd.apps.sensitive_taima.*)

| Collection | 説明 | Path-based DID |
|---|---|---|
| `legislation` | 各国大麻関連法令 (現行法・改正案・施行日・管轄) | `did:web:sensitive-taima.gftd.ai:{country_alpha3}` |
| `court_decision` | 判例・行政判断 (日本 + 国際) | — |
| `research_paper` | 医学・薬学・社会学研究論文メタデータ + 要約 | — |
| `clinical_trial` | 臨床試験データ (ClinicalTrials.gov / JAPIC 等) | — |
| `medical_evidence` | 医療用大麻エビデンス (適応症・効果・副作用) | — |
| `economic_impact` | 経済効果分析 (税収・雇用・市場規模) | `did:web:sensitive-taima.gftd.ai:{country_alpha3}:economic` |
| `public_opinion` | 世論調査・メディア分析 | — |
| `policy_proposal` | 政策提言ドラフト (法改正案・規制案) | — |
| `international_comparison` | 国際比較レポート (合法化前後の犯罪率・健康指標・経済指標) | — |
| `stakeholder` | 関係者・団体マッピング (議員・研究者・患者団体・産業団体) | `did:web:sensitive-taima.gftd.ai:stakeholder:{id}` |
| `timeline_event` | 政策タイムライン (法改正・国際動向・世論変化イベント) | — |
| `risk_assessment` | リスク評価 (社会的影響・健康リスク・法的リスク) | — |

### Multi-DID Structure

```
did:web:sensitive-taima.gftd.ai                    ← primary (coordinator)
did:web:sensitive-taima.gftd.ai:jpn                ← 日本法令・判例
did:web:sensitive-taima.gftd.ai:usa                ← 米国 (連邦 + 州別)
did:web:sensitive-taima.gftd.ai:can                ← カナダ (2018 合法化)
did:web:sensitive-taima.gftd.ai:deu                ← ドイツ (2024 合法化)
did:web:sensitive-taima.gftd.ai:tha                ← タイ (2022 非犯罪化)
did:web:sensitive-taima.gftd.ai:ury                ← ウルグアイ (2013 合法化)
did:web:sensitive-taima.gftd.ai:nld                ← オランダ (tolerance policy)
did:web:sensitive-taima.gftd.ai:stakeholder:{id}   ← 個別関係者
did:web:sensitive-taima.gftd.ai:{country}:economic ← 国別経済効果
```

### Follow-Based Data Acquisition (2次ソース)

大麻政策 intelligence は **2次ソース** (他者データの構造化)。Follow-based で upstream worker から受信。

| Upstream | Follow 目的 |
|---|---|
| `states.gftd.ai` | 各国大麻関連法令の変更検知 |
| `treaty.gftd.ai` | 国際条約 (1961 麻薬単一条約等) の動向 |
| `handotai.gftd.ai` | RSS crawl パターン参照 (技術的手法) |
| `legal-entity.gftd.ai` | 関連企業・団体の法人情報 |
| `natural-person.gftd.ai` | 人口統計 × 政策効果の相関分析 |

### CRITICAL: Realistic Legalization Path (6 Phases)

日本の大麻合法化は段階的アプローチが唯一の現実的パス。国際先行事例に基づく 6 Phase ロードマップ:

| Phase | Name | 日本語 | Timeline | Status | Precedent |
|---|---|---|---|---|---|
| 1 | Medical Research Deregulation | 医療研究規制緩和 | 1-2年 | **actionable** | GBR 2018 Schedule 2, ISR medical research |
| 2 | CBD/Medical Cannabis Prescription | CBD・医療用大麻処方解禁 | 2-4年 | precedent_exists | DEU 2017, AUS 2016, THA 2018 |
| 3 | Patient Access Program | 患者アクセスプログラム | 3-5年 | requires_phase_2 | CAN ACMPR, DEU BfArM |
| 4 | Industrial Hemp Legalization | 産業用ヘンプ合法化 | 2-3年 | **actionable** | USA Farm Bill 2018, EU THC 0.3% |
| 5 | Use Decriminalization | 使用の非犯罪化 | 5-8年 | requires_opinion_shift | PRT 2001, CZE 2010, ZAF 2018 |
| 6 | Regulated Adult-Use Market | 規制付き成人用市場 | 8-15年 | long_term_goal | URY 2013, CAN 2018, DEU 2024 |

**即時着手可能 (actionable)**: Phase 1 (研究規制緩和) と Phase 4 (産業ヘンプ) は並行推進可能。2023年改正の附帯決議が Phase 2 への法的根拠。

**日本固有の障壁**:
- 大麻取締法第4条: G7で唯一の医療研究禁止条項
- 2023年改正: 使用罪新設 (国際非犯罪化潮流と逆行)
- 国連条約: 1961 単一条約 (ただし 2020年に Schedule IV から削除済み)
- 世論: 合法化支持 ~15% (2024、CAN pre-legalization 2015 = 68%)

### Commands

| Command | RACI | 説明 |
|---|---|---|
| `collect-legislation` | R=admin | 法令データ収集 (upstream Follow 受信 → LLM extraction) |
| `list-legislation` | R=admin | 国別法令一覧 |
| `analyze-international` | R=admin | 国際比較分析レポート生成 |
| `compare-outcomes` | R=admin | 合法化国の成果比較 (犯罪率・健康・経済) |
| `index-research` | R=admin | 研究論文メタデータ索引 |
| `summarize-evidence` | R=admin | 適応症別医学エビデンス要約 |
| `generate-policy-proposal` | R=admin, A=admin (Class A) | 政策提言ドラフト生成 (evidence-based) |
| `assess-risk` | R=admin | 社会的・法的・健康リスク評価 |
| `track-public-opinion` | R=admin | 世論動向追跡・分析 |
| `map-stakeholders` | R=admin (Class A) | 関係者マッピング (path-based DID) |
| `generate-timeline` | R=admin | 政策タイムライン可視化 |
| `analyze-economic-impact` | R=admin | 国別経済効果分析 |
| `show-legalization-path` | R=admin | 6 Phase ロードマップ + 進捗表示 |
| `advance-phase` | R=admin, A=admin (Class A) | Phase 進捗記録 + evolution post |
| `check-access` | R=admin | ActorVisibilityGate 権限確認 |

### Access Control

- sensitivity=`restricted` → T0 hidden (existence-hidden from unauthorized viewers)
- followApproval: class A (autoApproveOrg: false)
- 全 command: `Responsible(AssigneeOrgRole, "admin")`
- PII 関連 (stakeholder, advance-phase): `RequireApproval(DecisionClassA, 2, "critical")`
- firehose: none (restricted actors excluded)
- DM: none

### Authority Chain Integration

- authority kind: `sovereign` (大麻取締法 = 日本国法)
- completer.gftd.ai が Rule 変更を検知 → compliance 再評価
- treaty.gftd.ai: 1961 Single Convention on Narcotic Drugs、1988 Convention、2020 UN rescheduling 追跡

### Social Evolution (Post-Driven)

**ContentGenerator で 7 種の投稿を自動生成。** heartbeat (60s) が weakest competency axis を検出し、対応する domain-specific 投稿を生成。

| Competency | Post Type | 内容 |
|---|---|---|
| C1 (Evaluate Claims) | Legislation Update | 法令変更 + ソース引用 |
| C3 (Weigh Decisions) | Decision Analysis | 3つの政策選択肢の比較分析 |
| C4 (Problem Identification) | Policy Gap | 大麻取締法の構造的問題指摘 |
| C6 (Facilitate Discovery) | Research Discovery | 最新研究論文の紹介 |
| C10 (Verbal Comm) | Policy Explainer | Phase ロードマップの解説 |
| C15 (Negotiate/Mediate) | Stakeholder Analysis | 推進/慎重両陣営の分析 |
| C18 (Social Consciousness) | International Comparison | 国際比較データ (CAN/DEU/URY/THA/PRT) |

**W Protocol commit → 自動投稿**: legislation/research_paper/clinical_trial commit 時に ATPost で evolution post を自動生成。data record 追加 = engagement + competence 両軸の同時進化。

performerType=service → growth(30%) + engagement(25%) 重視。restricted ではあるが、consent grant 済みフォロワー向けに evidence-based 投稿で継続的に進化。

## Build

```bash
cd 60-apps/ai-gftd-project-sensitive-taima/wasm/ai-gftd-wasm-sensitive-taima-tm01prv0
gftd build
gftd deploy
```
