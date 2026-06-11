---
id: adr-2605181050-uhl-overseas-referral-paths
title: "ADR-2605181050: UHL-R 海外 referral path — ABI (Manchester/GSTT) / optoCI (Göttingen) / SGN regen (Sheffield)"
status: proposed
doc_type: adr
topic: uhl-right-neural-overseas-referral
authoritative: true
last_verified: 2026-05-18
priority: 5.5
axis: process
weight: 0.50
priority_note: "国内では実施困難な3カテゴリ (小児ABI / optoCI 治験 / SGN 再生研究) の海外 referral path を定義する。プロジェクト V16 InstitutionMatcherActor が患者 substrate class に応じて選択する代替経路を凍結する。"
authoritative_for:
  - 3 named overseas referral paths (ABI, optoCI trial, SGN regen)
  - referral preconditions, contact pattern, ethics committee requirements
  - patient/family burden disclosure requirements
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605181040-uhl-medical-institution-registry
related:
  - adr-2605181060-otarmeni-access-path
supersedes: []
superseded_by: []
---

# ADR-2605181050: UHL-R 海外 referral path — ABI / optoCI / SGN regen

**Status**: proposed
**Date**: 2026-05-18
**Deciders**: Jun Kawasaki

# Context

`uhl-right-neural` プロジェクトの V06 substrate classifier の 4-way 出力のうち、以下のブランチは**国内では完結しない**:

| Substrate class | 国内現状 | 海外実施可能 |
|---|---|---|
| Nerve aplasia | ABI 累積 ~11 例 (2011時点)、自費診療、限定 2 施設 | Manchester / GSTT (NHS 指定 2 拠点、小児症例豊富) |
| SGN absent + nerve present | 臨床選択肢無し (eCI 効果限定) | Göttingen (optoCI、ヒト試験準備段階) |
| SGN regenerable + research consent | 国内研究シーズあり (Keio iPSC organoid) が臨床は無し | Sheffield (Rivolta lab、hESC→otic neural progenitor 移植の前臨床先行) |

referral には共通の障壁:

1. **規制**: 患者個人情報の越境移転 (改正個情法 + GDPR/UK GDPR)
2. **倫理**: 受け入れ側機関 IRB + 国内主治医 + 倫理委 3 者調整
3. **言語/医療通訳**: 専門医療通訳の確保
4. **費用**: 治療費 + 渡航 + 滞在 + 術後 follow-up
5. **継続ケア**: 帰国後の follow-up を国内施設が引き受けるか
6. **データ持ち帰り**: 海外実施の臨床データを国内 follow-up に渡す pipeline

これを ad-hoc に毎回設計すると患者・家族の負担が破滅的になる。**3 path を named pattern として凍結**し、V16 actor が "this path applies, see ADR-2605181050#path-abi-uk" と返せるようにする。

# Decision

## 3 path を named pattern として凍結

各 path は `ReferralPathRef.path_id` (ADR-2605181040 schema) で参照される。

### Path: `abi-uk-nhs-paediatric`

**適用**: substrate = `nerve_aplasia` (V06出力)、患者年齢 ≤ 12 歳、保護者同意あり。

**受け入れ候補**:
- Manchester University NHS FT / Royal Manchester Children's Hospital — Auditory Brainstem Implant Service (Lise Henderson 含む multidisciplinary team)
- Guy's and St Thomas NHS Foundation Trust (London)

両者ともに NHS England 指定 2 拠点。

**Preconditions**:
1. 国内画像 (側頭骨 high-res CT + IAC CISS/FIESTA MRI) で nerve aplasia 確定
2. 国内主治医による紹介状 (英訳)
3. 国内倫理委 (主治医の所属機関) の承認
4. 受け入れ側 MDT (multidisciplinary team) による case review (約 4-8 週)
5. ABI 後 follow-up を引き受ける国内施設の事前合意 (福島県立医大 or 日本医大 が現実的)

**Contact pattern**: 受け入れ側は NHS なので、当面は自費診療 (英国国民向け NHS 枠は不可)。国際患者向け窓口は Manchester Rare Conditions Centre の "Highly Specialised Services" 部門。

**Burden disclosure (患者・家族向け mandatory)**:
- 手術費 自費 (~£80,000-150,000 推定、見積取得必須)
- 渡英 × 3 回 (assessment / surgery / activation)
- 滞在 4-6 週間 (surgery + initial mapping)
- 英国側 follow-up 推奨 2 年、年 1-2 回再渡英
- 帰国後 follow-up を国内が引き受けないと完結不能

### Path: `optoci-de-trial`

**適用**: substrate = `sgn_absent_or_severely_reduced + nerve_present`、年齢 18+ (現状ヒト試験は成人候補のみ想定)、臨床試験参加同意。

**受け入れ候補**:
- Universität Göttingen / Else Kröner Fresenius Centre for Optogenetic Therapies (EKFZ OT) — Tobias Moser group
- ChReef opsin による低出力光刺激 + multichannel optical CI

**現状 (2026-05)**: EKFZ OT は 2024 から建設中、霊長類成功段階、ヒト first-in-human は準備中。**現時点で recruiting trial は無い**。本 path は "watch list" として登録、recruitment 開始時に activate。

**Preconditions** (recruitment 開始後):
1. 国内 substrate classifier で SGN absent + nerve present 確定
2. AAV-opsin 投与 + 光プローブ implant の inclusion criteria 合致
3. ドイツ語 or 英語での informed consent
4. 国内倫理委 + 国内 follow-up 施設合意

**Burden disclosure**:
- 治験参加は通常治療費無料だが、渡独 + 滞在は自己負担
- 試験プロトコル準拠 (中途離脱可、ただし follow-up は数年)
- AAV 投与歴がつくため、将来別の AAV 治療への影響あり (中和抗体)

### Path: `sgn-regen-uk-research`

**適用**: substrate = `sgn_absent + nerve_present`、研究参加 (治療ではない)、年齢制限は Sheffield 側プロトコル次第。

**受け入れ候補**:
- University of Sheffield — Marcelo Rivolta lab (hESC → otic neural progenitor 移植、gerbil 機能回復報告済)

**現状 (2026-05)**: 前臨床、ヒト試験未着手。本 path は **research participation only** として記述。臨床 referral path として activate するのはヒト試験開始後。

**Preconditions** (research participation):
1. Rivolta lab の研究プロトコルに sample/data donor として参加
2. 国内検体採取 + 越境移転 (改正個情法 + UK GDPR 経路で de-identified)
3. 治療効果の保証は無い旨を informed consent で明示

**Burden disclosure**:
- 治療ではなく研究貢献
- 渡英不要のケースが多い (検体送付で完結することあり)
- 将来の臨床応用に間接的に貢献

## 共通要件 (全 path)

### データ越境

患者検体・画像・遺伝情報の越境は **改正個情法 (個人関連情報) + 受け入れ国 (UK GDPR / DSGVO) の二重審査**。

- 国内側: 個情委届出が必要なケースあり、JIS Q 15001 準拠を推奨
- de-identification: Shamir 分散 + k-anonymity (k ≥ 5) を最低基準
- 検体: 匿名化 ID + 暗号化郵送、生体試料に関する MTA (Material Transfer Agreement) 必須

(個別の de-identification 手順は別 ADR で凍結、本 ADR では requirement のみ宣言)

### 倫理委調整

最低 2 倫理委 (国内主治医所属機関 + 受け入れ機関) の承認。**国内倫理委承認なしの referral は不可**。承認には通常 3-6 ヶ月。

### 国内 follow-up 受け入れ施設の事前合意

海外実施の臨床データ持ち帰り + 継続ケアを引き受ける国内施設の事前文書合意を、referral 開始の precondition とする。**「帰国後の主治医が決まっていない」状態での海外渡航は本 path 不可**。

### V16 actor の出力強制

`InstitutionMatcherActor` が referral path を返すときは必ず:

```yaml
output:
  paths: [...]
  requires_human_review: true   # 不可変
  burden_summary_url: <link to this ADR + specific path anchor>
  ethics_committee_required: true
  data_export_requires_review: true
```

# Consequences

## 正の効果

- **国内で打つ手がない 3 ブランチ** (aplasia / SGN-absent / regen research) に対して **structured な選択肢** を提示できる
- **患者・家族の意思決定に必要な burden disclosure が schema 強制** — 後付けで聞いていなかった、を防ぐ
- **倫理委・国内 follow-up の precondition が明文化** — ad-hoc な海外渡航を抑止

## 負の効果 / コスト

- **実適用ケースは年間数件レベル** — ABI は国内年間数例、optoCI は trial 開始前、SGN regen は研究のみ。レジストリ整備の労力に対して直接受益患者は少ない
- **path の鮮度維持** — 受け入れ機関の受け入れ方針・コスト・recruiting 状況は変化する。`last_verified_at` 180 日 staleness を本 ADR の path にも適用
- **legal/regulatory 専門外** — 越境データ移転と海外医療 referral の法務は本 repo の専門外。実適用前に専門家 review 必須

## Out of scope

- **個別法務 review** — 各 path 適用時の個別 IRB / 越境同意書作成は本 ADR 範囲外
- **financial assistance scheme** — 公的支援・寄付・保険外給付制度の整理は別 ADR
- **米国 referral (Mass Eye and Ear)** — Eaton-Peabody は研究機関であり臨床 referral path は現状無し。activate 時に本 ADR を update

# Alternatives Considered

## A. 海外 referral path をプロジェクト外に押し出す

却下理由: V06 substrate classifier が `nerve_aplasia` を返したときに actor が「国内では選択肢無し」しか返せないと、プロジェクトの臨床価値が崩壊する。少数でも path として持つことに意味がある。

## B. 受け入れ機関を発見する活動 (機関名のメンテ) を半自動化

却下選択: 将来課題。当面は手動 + 180 日 staleness で警告。

## C. 国内 follow-up 合意を precondition にしない

却下理由: 海外で術後感染や device failure が起きたとき、国内に受け皿がないと患者が孤立する。前提条件として強制。

## D. burden disclosure を任意化 (UI で skip 可)

却下理由: informed consent の核心。skip 不可で良い。

# References

- ADR-2605181040 — UHL-R 医療機関レジストリ schema (this PR sibling)
- ADR-2605181060 — Otarmeni access path (this PR sibling)
- ADR-2605172000 — RW-free substrate
- [Manchester ABI Service — Highly Specialised Services](https://www.mrcc.org.uk/clinical-diagnostics/highly-specialised-services/auditory-brainstem-implant-service/)
- [Royal Manchester Children's Hospital — Paediatric CI Programme](https://mft.nhs.uk/rmch/services/manchester-paediatric-cochlear-implant-programme/)
- [Manchester Royal Infirmary — ABI](https://mft.nhs.uk/mri/services/audiology/abi/)
- [DZHK — Light as medicine (ChReef / EKFZ OT)](https://dzhk.de/en/newsroom/news/latest-news/article/licht-als-medizin-neuer-zellschalter-bringt-hoffnung-fuer-seh-hoer-und-herzerkrankungen)
- [Multichannel optogenetic CI in rats (J Neural Eng 2025)](https://iopscience.iop.org/article/10.1088/1741-2552/adf00f)
- [Direct reprogramming fibroblasts → SGN (PMID 39551613, 2024)](https://pubmed.ncbi.nlm.nih.gov/39551613/)
- [SGN regeneration as therapeutic strategy (PMC 2022)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8811300/)
- [Improved optogenetic SGN modification (Theranostics 2025)](https://www.thno.org/v15p4270.htm)
