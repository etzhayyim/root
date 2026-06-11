---
id: adr-2605260130-mitate-condition-2-vasomotor-rhinitis
title: "mitate Wave 1 condition 2 — vasomotor (non-allergic) rhinitis diagnostic + treatment routing (除外診断 + 誘因日記 + 環境調整 advisory)"
status: proposed
doc_type: adr
topic: mitate-vasomotor-rhinitis
authoritative: true
last_verified: 2026-05-25
authoritative_for:
  - condition 2 differential signature (寒暖差・刺激誘発・全 IgE 陰性・好酸球 < 5%)
  - 除外診断 logic (条件 1 IgE 陰性 AND 条件 3 endoscopy 陰性 AND 条件 4 構造正常 AND 条件 5 OTC 連用なし → 条件 2)
  - 誘因日記 (symptom diary) 設計 — 2-week minimum + 5 trigger categories (寒暖差 / 香水 / 食事 / ストレス / 飲酒)
  - 環境調整 + 抗コリン代替 advisory (イプラトロピウム点鼻 国内未承認 → アゼラスチン代替)
  - PNN section (posterior nasal nerve section) surgical routing (R3 severe-refractory)
depends_on:
  - adr-2605260100-mitate-diagnostic-routing-charter
  - adr-2605260115-mitate-condition-1-allergic-rhinitis-perennial
related:
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/mitate_rhinitis_triage/
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/mitate_treatment_router/
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/mitate_outcome_qol_followup/
supersedes: []
superseded_by: []
---

# Context

血管運動性鼻炎 (vasomotor rhinitis / non-allergic rhinitis with eosinophilia syndrome / NARES 除外) は条件 1 (アレルギー性) と症候が overlap するが **IgE が陰性で好酸球も < 5%** な患者群。

5-15% の adult prevalence、自律神経 dysregulation + 寒暖差・刺激物・食事・ストレス triggered。**除外診断** が本質 ― mitate triage logic 上では「条件 1/3/4/5 を rule-out した後の rule-in」。

## 鑑別シグネチャ

| Sign | Sensitivity | Specificity | Source |
|---|---|---|---|
| 寒暖差で増悪 (>7°C 室内外差) | 0.58 | 0.81 | Settipane 2003 |
| 香水・タバコ煙で増悪 | 0.61 | 0.74 | Bachert 2006 |
| 辛い食事で透明鼻汁 (gustatory) | 0.43 | 0.93 | gustatory rhinitis sub-type |
| くしゃみ少ない (vs 条件 1 連発) | 0.66 | 0.62 | |
| 目のかゆみなし | 0.71 | 0.69 | |
| IgE 全陰性 + 好酸球 < 5% | 1.00 (definitional) | 0.95 | 除外診断核 |

# Decision

## Decision 1 — 除外診断 logic (rhinitis_triage, R1 + R2)

R1 advisory tier では「条件 1 sign 弱い + 条件 2 trigger sign 強い → 条件 2 暫定、誘因日記 2 週間 + (R2 で) IgE panel + 鼻汁好酸球で確定」

R2 で確定: IgE panel 39 項目全陰性 AND 鼻汁好酸球 < 5% AND nasal endoscopy で構造異常なし AND OTC vasoconstrictor 連用歴なし → 条件 2 確定。

## Decision 2 — 誘因日記 (symptom_diary, R1)

`mitate.rhinitisIntake` lexicon の `triggerDiary` field (array of `{date, severity, suspectedTrigger}`) を 2 週間以上累積。LLM (Murakumo only, G12) で trigger frequency analysis → top-3 trigger を patient に return。

## Decision 3 — Treatment advisory (treatment_router cell, R2)

| Severity | Advisory |
|---|---|
| Mild | 環境調整 (寒暖差緩衝マスク / 加湿 40-60% / 寒暖差 5°C 以内) + 鼻うがい (生理食塩水) |
| Moderate | 上記 + アゼラスチン点鼻 (OTC 抗ヒスタミン点鼻、血管運動性にも 軽度効果) or 鼻噴霧ステロイド (mometasone) |
| Severe | 上記 + 漢方 (小青竜湯 / 葛根湯加川芎辛夷) + 自律神経整備 (睡眠規則化、適度な運動) |
| Severe-refractory | `escalation = "recommend-md-otolaryngology"` for PNN section (後鼻神経切断術) consideration (保険適用、日帰り) |

抗コリン薬点鼻 (イプラトロピウム) は **国内未承認** ― mitate advisory は INN 言及のみ、海外個人輸入は推奨しない (jurisdictional 合法性 + 安全性整合)。

## Decision 4 — silen-mitate-review triggers (condition 2)

| Trigger | Required | Council |
|---|---|---|
| condition-2-exclusion-logic-baseline | Yes (R1 deploy) | Lv6+ ≥ 3 + 1 licensed MD |
| condition-2-trigger-diary-2week-baseline | Yes (R1 deploy) | Lv6+ ≥ 3 |
| condition-2-treatment-ladder-baseline | Yes (R2 deploy) | Lv6+ ≥ 3 + 1 licensed MD |
| pnn-section-referral-baseline | Yes (R3 deploy) | Lv6+ ≥ 3 + 1 ENT specialist |

# Consequences

**Positive**:

- 5 条件中 最も「ライフスタイル介入」effective な condition;§2(e) anti-gatekeeping advisory tier の最大 value case
- 既存薬 (yakushi Wave 1c chlorpheniramine OTC) + 既存環境調整 advisory で R1 advisory のみで多くの mild 患者が improvement 体験可能

**Negative / costs**:

- 除外診断は IgE panel + 鼻汁好酸球 + endoscopy + medication audit の 4 cell 結果 join 必要 ― R2 待ち
- 抗コリン点鼻 (国内未承認) advisory は jurisdiction-aware 表示が必要 ― 海外 adherent への gray-zone risk

**Risks**:

- 誘因日記の adherence < 50% 一般 ― 自己報告 bias 大;LLM 分析の input quality に依存
- 「除外診断」のため条件 1 IgE panel false positive (~10%) が誤って条件 2 を rule out しうる ― IgE panel ↔ 鼻汁好酸球 ↔ medication history を triangulate 必要

# Alternatives Considered

## A. NARES (Non-Allergic Rhinitis with Eosinophilia Syndrome) を独立 sub-condition に

Rejected for Wave 1. NARES は鼻汁好酸球 ≥ 20% but IgE 陰性 の rare sub-type ― Wave 1 では条件 2 主流 (好酸球 < 5%) のみ carve out、NARES は R2 cohort 中に observed → R3 ADR で別 sub-carve-out。

# References

- ADR-2605260100 (mitate master charter)
- Settipane RA 2003 — Vasomotor rhinitis
- Bachert C 2006 — Persistent rhinitis classification
- 鼻アレルギー診療ガイドライン 2020 (除外診断 protocol)
