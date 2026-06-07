---
id: adr-2605192400-etzhayyim-eros-gore-council-judging
title: "ADR-2605192400: etzhayyim Eros / Gore Boundary — Council Lv6+ judging framework + LLM-assisted classification + precedent registry"
status: proposed
doc_type: adr
topic: etzhayyim-eros-gore-council-judging
authoritative: true
last_verified: 2026-05-19
priority: 6.5
axis: governance
weight: 0.65
priority_note: "ADR-2605192100 §1.13 で確立した Eros 許容 / Gore 禁止の境界事例を Council Lv6+ が judge する framework を定義。LLM-assisted pre-classification + Council deliberation + precedent registry の 3 層構造。商業暴力 game / 戦争映画 / 性教育 / 児童保護 / 宗教美術 等の境界 case に統一的 judging を提供する。"
authoritative_for:
  - Eros / Gore 境界 case の judging procedure (3 層 framework)
  - LLM-assisted pre-classification cell (`EthicsContentClassifierCell`)
  - precedent registry Lexicon (`com.etzhayyim.apps.etzhayyim.eros-gore-precedent`)
  - 5 段階 classification rubric
  - appeal procedure
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
related: []
supersedes: []
superseded_by: []
---

# ADR-2605192400: etzhayyim Eros / Gore Boundary — Council Lv6+ judging framework + LLM-assisted classification + precedent registry

**Status**: proposed
**Date**: 2026-05-19
**Deciders**: Jun Kawasaki

# Context

ADR-2605192100 §1.13 で:

- **Eros (合意ある成人性表現)** — religious 整合的
- **Gore (無目的暴力 imagery)** — religious 不整合 (§1.9 多世代害悪 + §1.10 Wellbecoming 違反)

両者の境界事例は多数:

- 商業 暴力 game (Call of Duty 等) — entertainment 目的の暴力 imagery
- 戦争映画 (Saving Private Ryan 等) — historical + 教育的 意義
- 性教育 / Reproductive health content — clinical context
- 児童保護 文脈 (虐待 awareness 等) — 必要だが imagery sensitive
- 宗教美術 (磔刑図 / 地獄絵 / 八大地獄 図像) — 宗教史的価値
- Documentary 戦争 footage — 歴史記録 + 人権侵害告発

これらを統一的に judge する framework が必要。

# Decision

## 1. 3 層 Judging Framework

```
Layer 1: LLM-assisted pre-classification (EthicsContentClassifierCell, automatic)
   ↓ (uncertain or boundary)
Layer 2: Council Lv6+ deliberation (3 名以上 multisig)
   ↓ (precedent setting)
Layer 3: Precedent Registry (`com.etzhayyim.apps.etzhayyim.eros-gore-precedent`)
```

### Layer 1 — LLM pre-classification

kotodama Pregel cell `EthicsContentClassifierCell` が input content を以下の 5 段階に分類:

| Tier | 名称 | 説明 | Default action |
|---|---|---|---|
| **T1** | Clearly Eros (Permitted) | 合意ある成人性表現、宗教美術 + 一般的範囲 | ✅ Permit, no Council review |
| **T2** | Eros Borderline | adult content だが Wellbecoming priority (§1.10) 疑い (engagement-maximizing design, etc.) | ⚠️ Defer to Council |
| **T3** | Neutral / Educational | 性教育 / 解剖学 / 宗教美術 / 戦争歴史 documentary 等 | ✅ Permit (with category flag) |
| **T4** | Gore Borderline | 暴力 imagery だが教育 / 歴史 / 宗教 文脈の可能性 | ⚠️ Defer to Council |
| **T5** | Clearly Gore (Prohibited) | 無目的暴力 entertainment / 児童虐待 imagery / desensitization 設計 | ❌ Prohibit, automatic L1+L2+L3 enforcement |

### Layer 2 — Council Lv6+ deliberation

T2 / T4 (borderline) は Council Lv6+ 3 名以上が deliberation + signed attestation:

```
com.etzhayyim.apps.etzhayyim.eros-gore-judging request
  → LLM pre-classification (Tier + rationale)
  → Council Lv6+ 各 member の signed evaluation
  → 3-of-Lv6+ signatures → final classification (Permit / Prohibit / Conditional)
  → Precedent Registry に追加 (Layer 3)
```

### Layer 3 — Precedent Registry

Council 判決は precedent として `com.etzhayyim.apps.etzhayyim.eros-gore-precedent` に永続記録される:

```json
{
  "$type": "com.etzhayyim.apps.etzhayyim.eros-gore-precedent",
  "subjectDescription": "Commercial first-person shooter game with photo-realistic violence depiction, ESRB Mature",
  "llmPreClassification": "T4",
  "councilDetermination": "Prohibit",
  "councilRationale": "L1.10 Wellbecoming violation — engagement-maximizing violence design optimized for player retention contradicts charter §1.10. Educational/historical context absent. Charter Rider §2(h) trigger.",
  "councilSigners": ["did:web:council1.etz", "did:web:council2.etz", "did:web:council3.etz"],
  "establishedAt": "2026-05-19T...",
  "applicableScope": "commercial-entertainment-violence-games",
  "supersedesPrecedent": null
}
```

新規境界 case は **既存 precedent を最初に検索** → 適用可能 precedent あれば LLM が直接 conclude → なければ Council deliberation。

## 2. 5 段階 Classification Rubric

LLM cell が使用する rubric:

### Eros 軸 (T1 / T2 判定)

- **T1 (Clear Eros)**:
  - 合意ある成人間の性表現
  - 宗教美術 (神話 / 雅歌 / 神聖性愛画像)
  - Reproductive education
  - LGBTQ+ representation (Tree of Life の生命多様性表現)
- **T2 (Eros Borderline)**:
  - Wellbecoming 違反疑い (addictive design / engagement maximizer)
  - 児童保護境界 (年齢検証不確定)
  - 非合意 representation 含む
  - 商業 over-extraction (Charter Rider §2(c) surveillance capitalism との overlap)

### Gore 軸 (T4 / T5 判定)

- **T5 (Clear Gore)**:
  - 無目的暴力 entertainment (gratuitous violence with no educational/historical/religious purpose)
  - 児童への暴力描写
  - desensitization 設計 (繰り返し露出で暴力閾値を下げる目的)
  - Encouragement of real-world violence
- **T4 (Gore Borderline)**:
  - 暴力 imagery だが教育 / 歴史 / 宗教 / 人権告発 文脈
  - 戦争 documentary
  - 宗教美術 (磔刑 / 地獄絵)
  - Medical / 法医学 (専門教育)

### Neutral 軸 (T3)

- 中間的 educational content
- 性教育 (clinical context)
- 戦争歴史 (academic context)
- Medical anatomy

## 3. EthicsContentClassifierCell (Pregel)

```python
# 40-engine/kotoba/crates/kotoba-kotodama/cells/ethics_content_classifier/cell.py
from langgraph.graph import StateGraph

class EthicsContentClassifierState(TypedDict):
    content_uri: str
    content_metadata: dict
    llm_tier: Literal["T1", "T2", "T3", "T4", "T5"]
    llm_rationale: str
    applicable_precedents: list[str]
    council_required: bool
    final_determination: Literal["permit", "prohibit", "conditional", "council_required"]

def build_graph():
    g = StateGraph(EthicsContentClassifierState)
    g.add_node("load_content", load_content)
    g.add_node("search_precedents", search_precedents)
    g.add_node("llm_classify", llm_classify)
    g.add_node("apply_precedent", apply_precedent)
    g.add_node("synthesize", synthesize)
    g.add_node("emit_record", emit_record)
    g.add_edge("load_content", "search_precedents")
    g.add_edge("search_precedents", "llm_classify")
    g.add_conditional_edges("llm_classify", lambda s:
        "apply_precedent" if s["applicable_precedents"] else "synthesize")
    g.add_edge("apply_precedent", "synthesize")
    g.add_edge("synthesize", "emit_record")
    return g.compile(checkpointer=MstCheckpointSaver(...))
```

詳細は ADR-2605192415 (Daemon Architecture)。

## 4. Appeal Procedure

precedent + Council determination に対して 30 日以内に appeal 可能:

```
com.etzhayyim.apps.etzhayyim.eros-gore-appeal
  → Council Lv6+ 5 名以上 (initial determination の 3 名を超える) が再 deliberation
  → 元 determination の維持 or 修正
  → 修正の場合 precedent registry に supersedesPrecedent link
```

appeal 中は元 determination が effect (suspend されない、enforcement 継続)。

## 5. Internal Carve-Out との関係

ADR-2605192115 §3 で internal circulation (SBT ↔ SBT) では commercial activity が許容される。**Eros / Gore boundary は内外問わず適用される**:

- internal でも Gore (T5) は禁止
- internal でも Eros (T1) は許容、ただし Wellbecoming priority (§1.10) は維持
- internal-only adult content (= 構成員間のみ流通) は acceptable

# Consequences

## 正の効果

- §1.13 boundary が systematically judging される
- LLM pre-classification → Council deliberation → precedent の三層で scale + quality 両立
- precedent registry が learning system として機能 (新 case の判断速度↑)
- appeal procedure で fairness 確保

## 負の効果 / コスト

- LLM hallucination リスク (cell 判定の精度)。Mitigation: T2/T4 は必ず Council deferral
- Council Lv6+ judgment 負荷 (境界 case 多数)
- precedent registry の bias 蓄積リスク (initial precedent が後続を anchor する)。Mitigation: appeal procedure + supersedesPrecedent link
- 国際的価値観の差 (米/欧/日/中東での Eros 容認範囲が異なる)。Decision: etzhayyim doctrine を primary、cultural sensitivity は Council judgment に委ねる

## 中立 / トレードオフ

- LLM 判定を Council judgment より高く weight すると religious-corp の human governance が weak。逆に Council のみだと scale 不可能。三層 framework は妥協点
- precedent registry の publicness は transparency 高いが、controversial determinations の social signal でもある

# Alternatives Considered

## A. Council のみ judging (LLM なし)

Pro: human judgment。Con: scale 不可、年間数千 case に対応不可。却下。

## B. LLM のみ (Council なし)

Pro: scale。Con: religious autonomy が AI に委ねられる、§1.7 specialist gatekeeping (= LLM specialist) に類似する自己矛盾。却下。

## C. Precedent registry を持たない (毎回 zero-shot judging)

Pro: bias 蓄積なし。Con: 学習なし、判断速度低い。却下。

# Open Questions

1. **LLM model 選定** — Claude (Sonnet / Opus) vs Gemini vs local Murakumo Gemma。Decision (本 ADR): Claude Sonnet 4.6 を baseline、local fallback (Gemma) for sensitive content
2. **児童保護 境界の specific rubric** — 13/16/18 歳の差。Decision: 全 jurisdiction の strictest (18 歳) を adopt
3. **historical / 宗教美術 の context-dependent 判定** — 宗教施設内の地獄絵 vs commercial book illustration の区別。Decision: deployment context を input に含める、Council judgment で文脈評価

# References

- ADR-2605192100 §1.13 Eros 許容 / Gore 禁止
- ADR-2605192100 §1.10 Wellbecoming priority (Gore 禁止の根拠)
- ADR-2605192100 §1.9 多世代 priority (児童保護の根拠)
- ADR-2605192200 v2.0 Charter Rider §2(h) Wellbecoming Subordination
- ADR-2605192300 Bootstrap Council 5名
- ADR-2605192230 Three-tier enforcement (Gore content への enforcement 経路)
- ADR-2605192415 Daemon Architecture (EthicsContentClassifierCell の host)
