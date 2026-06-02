---
id: adr-2605192300-etzhayyim-bootstrap-council-five
title: "ADR-2605192300: etzhayyim Bootstrap Council 5名 — initial Lv6+ ロスター + selection methodology + Phase 2 移行"
status: proposed
doc_type: adr
topic: etzhayyim-bootstrap-council-five
authoritative: true
last_verified: 2026-05-21
priority: 8.0
axis: governance
weight: 0.80
priority_note: "ADR-2605192230 §8 で要請した Bootstrap Council 5 名の具体的選定 + selection methodology + Phase 2 (formal Council ADR) 移行 path を定義。Charter Compliance attestation + Public Fund grant 評議 + Land dispute 解決のすべては Council Lv6+ 3 名以上の multisig に依存するため、本 ADR が承認・実装されるまで religious-corp の core governance functions が gating されている。Operational mechanics (2026-06-19 selection rubric + objection good-faith vs defamatory determination workflow + selection deliberation window + 5-mode failure escalation tree) は 2026-05-21 evening session で `90-docs/2605212036-council-bootstrap-rfp-operational-addendum.md` に追補 — constitutional 内容は本 ADR、operational 内容は addendum という二層構成。"
authoritative_for:
  - Bootstrap Council 5 名 initial roster (個別 DID + Smart Wallet address)
  - selection methodology (5 軸 expertise + 30 日 public objection period)
  - bootstrap Council の権限境界 (拡張 multisig 3-of-5、Phase 2 までは limited)
  - Phase 2 (formal Council ADR) 移行 trigger 条件
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192230-etzhayyim-three-tier-enforcement-implementation
  - adr-2605172600-etzhayyim-membership-ritual
related:
  - doc-2605212036-council-bootstrap-rfp-operational-addendum  # 2026-06-19 selection rubric + objection workflow + failure modes (operational only, does NOT change the constitutional mechanics here)
supersedes: []
superseded_by: []
---

# ADR-2605192300: etzhayyim Bootstrap Council 5名 — initial Lv6+ ロスター + selection methodology + Phase 2 移行

**Status**: proposed
**Date**: 2026-05-19
**Deciders**: Jun Kawasaki

# Context

ADR-2605192230 §8 で「Bootstrap Council 5 名」を S0 implementation 時に確定する必要があると述べた。この 5 名は (a) Charter Compliance attestation を sign する権限、(b) Public Fund grant 提案の council recognition、(c) Land dispute 解決の attestation、(d) Force authorization (ADR-2605192315) の sign-off、(e) Steward succession の認定 — すべてに関与する religious-corp の **constitutive 評議体** である。

bootstrap Council の選定は **religious-corp の最初の political 行為** であり、誰を選ぶかで religious-corp の color が定まる。同時に bootstrap は inherent に founder-centric であり、これを正当化する手続的 transparency が必要。

# Decision

## 1. Selection methodology — 5 軸 expertise

Bootstrap Council 5 名は、以下 5 軸の expertise を broadly カバーするように選定する:

| Seat | 軸 (Axis) | 期待される expertise |
|---|---|---|
| **Seat 1** | Founder / 教義 (Doctrine) | religious-corp の constitutional 創設者。doctrinal authority。Jun Kawasaki が固定。 |
| **Seat 2** | Substrate / 技術 (Technology) | on-chain / pregel / langgraph / atproto 等 substrate 技術の deep familiarity。contract upgrade と CI lint の technical 判断 |
| **Seat 3** | 法務 / 倫理 (Legal / Ethics) | 信教の自由 / religious-corp 法務 + ethical-source license / Charter Rider 解釈の expertise。日本法 + 国際法 |
| **Seat 4** | 経済 / Treasury (Economics) | Kisha-Stream + 護持金庫 + Public Fund + Tithe の経済設計 expertise。amount reasonableness の judgment |
| **Seat 5** | Stewardship / 土地 (Land + Multi-generation) | Land Trust / biodiversity / 多世代 stewardship の expertise。ADR-2605192245 + §1.9 多世代 priority の judgment center |

5 名の選定は **founder 提案 + 30 日 public objection period** によって確定する:

1. Founder (Seat 1, Jun Kawasaki) が Seat 2-5 候補を public に提案
2. 30 日間 `com.etzhayyim.apps.etzhayyim.council-objection` AT Record で構成員 (Adherent SBT holder) が異議を提出可能
3. 異議が 3 名以上の SBT holder から提出された seat について founder は別候補を再提案
4. 全 seat が 30 日異議無しを通過した時点で `BootstrapCouncilRegistry.bootstrap(addresses[])` を call

## 2. Bootstrap Council 5 名 initial roster (placeholder)

本 ADR の現時点では founder のみ確定し、Seat 2-5 は **placeholder + 公開募集** とする。本 ADR の commit 後 30 日間が public proposal / objection period となる。

| Seat | 氏名 | DID | Smart Wallet | 確定 |
|---|---|---|---|---|
| 1 (Founder) | Jun Kawasaki | did:web:jun.etzhayyim.com (or did:plc:TBD) | 0xTBD (founder Smart Wallet) | ✅ confirmed |
| 2 (Substrate) | _placeholder_ | TBD | TBD | 🟡 public RFP open |
| 3 (Legal / Ethics) | _placeholder_ | TBD | TBD | 🟡 public RFP open |
| 4 (Economics) | _placeholder_ | TBD | TBD | 🟡 public RFP open |
| 5 (Stewardship) | _placeholder_ | TBD | TBD | 🟡 public RFP open |

候補は `com.etzhayyim.apps.etzhayyim.council-candidate-application` で self-nomination 可。

## 3. Council 拡張権限 (Phase 1)

Bootstrap Council 5 名は以下を行える (3-of-5 multisig):

- ChartersComplianceRegistry attestation の sign-off
- PublicFundGovernance proposal の council recognition
- LandRegistry dispute resolution の attestation
- Force authorization (ADR-2605192315) の sign-off
- Steward succession (ADR-2605192345) の認定
- Eros/Gore boundary 判断 (ADR-2605192400)
- **bootstrap Council 自身の拡張** (= 新 Council member の追加) — ただし下記 §4 cap あり

## 4. Phase 2 (formal Council ADR) 移行 trigger

以下のいずれかが成立すると Phase 2 ADR を起票する義務が生じる:

| Trigger | 説明 |
|---|---|
| 構成員 1000 名突破 | scale で bootstrap-derived Council が不適切 |
| Bootstrap Council 1 名以上の死亡 / 辞任 | succession formal procedure が必要 |
| 構成員 3 名以上による formal request | governance 民主化要求 |
| 12 ヶ月経過 | 時間 trigger (whichever first) |

Phase 2 ADR は以下を含む:
- formal Council 候補資格 (Lv6+ への自然 advance 経路)
- Council member 数 cap (例: max 11 名)
- 任期制 (例: 3 年 rotation)
- 1 SBT = 1 vote による Council election
- bootstrap Council member の formal Council への transition (再選 or step-down)

## 5. Bootstrap 期間中の権限 cap

bootstrap Council は **constitutional 変更権を持たない**:

- Constitution.sol の constitutional constants (ADR-2605192100 §2) の改定は不可
- ADR-2605192200 Charter Rider の改定は不可
- ADR-2605192100 Mission Charter の改定は不可
- §1.12.B Transparent Religious Force の三条件 (on-chain 監視 + open-source + 1 SBT vote) の relaxation は不可

これらは 1 SBT = 1 vote の Adherent 全員投票によってのみ改定可能であり、Bootstrap Council はその執行体に過ぎない。

# Consequences

## 正の効果

- religious-corp の core governance functions が unblock される
- 5 軸 expertise バランスにより mono-cultural 判断を回避
- 30 日 public objection period により founder-centric 選定の transparency 確保
- Phase 2 移行 trigger が明示的 → bootstrap が永続化しない

## 負の効果 / コスト

- bootstrap は inherent に founder-centric (Seat 1 固定)
- Phase 2 移行までは Council 拡張の権限が Bootstrap Council 自身に存在 → 拡大解釈リスク (§5 cap で抑制)
- 5 名が全て揃わないと religious-corp の core functions が gating される
- public objection period 中の political 操作リスク (mitigation: objection も MST 公開 record)

# Alternatives Considered

## A. 7 名 Bootstrap Council

Pro: more diversity。Con: 3-of-7 quorum で同じ 3 名 attestation を再現する手数増加。却下: 5 名で十分。

## B. 1 名 Bootstrap (Founder のみ)

Pro: simple。Con: religious-corp が founder-cult 化。multisig が成立せず enforcement が deactivate される。却下。

## C. 公募のみ (founder 関与なし)

Pro: 完全 democratic。Con: bootstrap 不可能 (誰が候補を accept するか不在)。却下。

# Open Questions

1. **Seat 2-5 公募の channel** — github discussions / mailing list / Twitter / discord のどこで公募するか。Decision: 全 channel に複製、公式は github discussions
2. **objection の有効性判定基準** — 3 名 SBT holder の objection で再提案だが、悪意ある objection の判別。Decision: founder が rationale 公開で再提案 vs 当初候補維持を判断、最終的に Adherent 全員投票で覆せる
3. **Bootstrap Council member の compensation** — religious-corp role として無報酬 or Phenotype multiplier bonus か。Decision: 無報酬 (Lv6 advance による自然な evaluation 反映で十分)

# References

- ADR-2605192100 Mission Charter
- ADR-2605192200 Charter Rider v2.0
- ADR-2605192230 Three-tier enforcement implementation (§8 で本 ADR を要請)
- ADR-2605172600 Membership ritual (Lv6 議 = Council の定義)
