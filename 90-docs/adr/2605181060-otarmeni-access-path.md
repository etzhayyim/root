---
id: adr-2605181060-otarmeni-access-path
title: "ADR-2605181060: Otarmeni (lunsotogene parvec-cwha) access path — CHORD JP 参加 → PMDA 承認待ち → 個人輸入"
status: proposed
doc_type: adr
topic: otarmeni-access-path
authoritative: true
last_verified: 2026-05-18
priority: 6.0
axis: process
weight: 0.55
priority_note: "Otarmeni (FDA accelerated approval 2026-04-23) の国内 access path を 3 段階で定義する。CHORD trial JP site 参加が現時点で唯一の現実解。両側性 DFNB9 確定が前提で、片側性 (本プロジェクトの主対象) は通常適応外であることを明示する。"
authoritative_for:
  - 3-tier access path (CHORD JP trial / PMDA approval / personal import)
  - DFNB9 inclusion screening hard gate
  - unilateral case exclusion default + exception escalation
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605181040-uhl-medical-institution-registry
  - adr-2605181050-uhl-overseas-referral-paths
related:
  - adr-2605180900-unispsc-isic-langserver-actor-lexicon-xrpc-mcp
supersedes: []
superseded_by: []
---

# ADR-2605181060: Otarmeni access path — CHORD JP / PMDA / 個人輸入

**Status**: proposed
**Date**: 2026-05-18
**Deciders**: Jun Kawasaki

# Context

**Otarmeni™ (lunsotogene parvec-cwha, Regeneron)** が 2026-04-23 に FDA accelerated approval を取得 ([FDA press release](https://www.fda.gov/news-events/press-announcements/fda-approves-first-ever-gene-therapy-treatment-genetic-hearing-loss-under-national-priority-voucher))。世界初の遺伝性難聴 gene therapy で、dual-AAV1 ベースで OTOF coding region を分割搭載。

CHORD trial (NCT05788536) の確定的データ:
- 治療済 20 例中 16 例 (80%) が primary endpoint (24週時 ≤70 dB HL) 達成
- 42% が正常聴力到達 (whisper 知覚可能)
- Multicentre 42 例 / 2.5 年 follow-up で 90% 奏効、106 dB → 52 dB 平均改善 ([Nature 2026](https://www.nature.com/articles/s41586-026-10393-y))
- CHORD trial は **US / UK / Spain / Germany / Japan** の多施設で confirmatory portion 継続中

**uhl-right-neural プロジェクトとの関係 — critical caveat**:

| 項目 | 状況 |
|---|---|
| Otarmeni 適応 | biallelic OTOF 変異 + 外有毛細胞機能保たれている + 同側 CI 未実施 |
| DFNB9 (OTOF難聴) の典型形 | **両側性、重度〜深度** |
| 本プロジェクト主対象 (先天性右側単独) | **通常 DFNB9 ではない** (片側性は cochlear nerve deficiency が主因、25-48%) |
| 結論 | **片側性 = 通常 Otarmeni 適応外**。例外的に右側のみ DFNB9 のケースは極稀 |

ただし V02 `GeneticScreenActor` が DFNB9 確定 + 片側性の例外症例を発見した場合の access path は事前に定義しておく必要がある (見つかってから「どう繋ぐか」では遅い)。また将来 PMDA 承認後は単一遺伝子片側性難聴への適用拡大も理論的にあり得る。

# Decision

## 3-tier access path

### Tier 1: CHORD JP site 治験参加 (現時点で唯一の現実的経路)

**適用**: DFNB9 確定 + CHORD trial inclusion criteria 合致 (年齢・両側性が原則)。

**Action**:
1. V02 `GeneticScreenActor` が biallelic OTOF pathogenic variant を確定
2. ClinicalTrials.gov NCT05788536 で JP recruiting site の確認 (site list が public update 次第)
3. Regeneron Japan / CHORD JP site PI への inquiry
4. 標準的治験 informed consent + 国内主治医経由の正式 enrollment

**実装**: ADR-2605181040 schema で `Institution.capabilities` に `kind: GENE_TX_OTOF, procedure_record.reimbursement: trial` として CHORD JP site を登録 (site が public 公表され次第)。

**現状 (2026-05)**: JP site の具体施設名は公表 search で未確認。Regeneron 公表 ([investor PR](https://investor.regeneron.com/news-releases/news-release-details/otarmenitm-lunsotogene-parvec-cwha-approved-fda-first-and-only)) は国別までで施設名は出ていない。継続 watch。

### Tier 2: PMDA 承認後の国内 routine 適応

**適用**: PMDA 承認 (時期未定) + 保険収載 後の標準診療経路。

**現状予測**:
- FDA accelerated approval (2026-04) は confirmatory data 待ち
- PMDA への新有効成分含有医薬品 (生物学的製剤区分、おそらく **再生医療等製品 第二種**) 申請は通常 12-18 ヶ月
- 国内承認の earliest plausible: 2027 後半 〜 2028
- 保険収載まで更に 3-6 ヶ月

**Action (承認後)**:
- 国内基幹施設 (CHORD JP site が継承される可能性が高い) で標準診療
- ADR-2605181040 schema を更新、`reimbursement: hoken` に変更
- V16 `InstitutionMatcherActor` が自動で routing

### Tier 3: 個人輸入 (deprecated path)

**適用**: Tier 1/2 不可、かつ患者が urgent + DFNB9 確定の例外症例。

**現状**: 遺伝子治療は薬機法上の個人輸入対象として極めて困難。実質的に access 不可能と判断。**本 path は文書化のみで、V16 actor からは default で返さない**。例外的に医師確認の上で escalation する場合のみ。

## Hard gate: DFNB9 inclusion screening

V02 `GeneticScreenActor` が **biallelic OTOF pathogenic variant (ACMG class 4-5)** を確定しない限り、本 ADR の path は activate しない。

```yaml
gate:
  required:
    - gene: OTOF
    - zygosity: biallelic
    - acmg_class: [4, 5]   # likely pathogenic or pathogenic
    - phenotype: severe_to_profound_sensorineural_hearing_loss
  preferred:
    - bilateral: true       # 本プロジェクト主対象は片側性なので通常 false
    - age: pediatric        # CHORD は infant-adolescent 主対象
```

## 片側性症例の例外処理

本プロジェクトの主対象 (先天性右側単独) は通常 DFNB9 ではない。V02 が片側性 OTOF 確定の極稀ケースを発見した場合:

1. **V16 actor は Tier 1 path を `requires_human_review: true` + `unilateral_exception: true` 付きで返す**
2. CHORD trial の inclusion criteria に片側性が含まれるか sponsor (Regeneron / 治験責任医師) への inquiry を必須化
3. 国内倫理委 + 主治医 + Regeneron 3 者の事前協議無しには enrollment 不可
4. enrollment 拒否時は patient education として ADR-2605181050 の `optoci-de-trial` + `sgn-regen-uk-research` を併せて提示 (将来の選択肢として)

## V16 actor 出力例 (DFNB9 確定時)

```yaml
matched_paths:
  - path_id: chord-jp-trial
    tier: 1
    institutions: [<CHORD JP site, 公表後>]
    inclusion_gate_passed: true
    unilateral_exception: <true if 単側>
    requires_human_review: true
    references:
      - ADR-2605181060#tier-1
      - https://clinicaltrials.gov/study/NCT05788536
  - path_id: pmda-routine
    tier: 2
    estimated_available: "2028"
    activate_after: <PMDA approval date>
    requires_human_review: true
fallback_paths:  # DFNB9 inclusion gate failed
  - path_id: not_applicable
    reason: <ACMG insufficient | not biallelic | not OTOF>
    redirect: <V16 → 他 substrate path>
```

# Consequences

## 正の効果

- **DFNB9 確定症例が発見されたときの行動 protocol が事前確定** — 見つけてから慌てない
- **片側性主対象に対する false-positive expectation を抑制** — 本プロジェクトは Otarmeni 適応症例を量産しない、と明示
- **PMDA 承認後の Tier 2 への自動遷移経路** — ADR-2605181040 schema 更新で V16 actor が自動 routing
- **個人輸入の deprecate を明文化** — 個別判断で逸脱しないための文書根拠

## 負の効果 / コスト

- **DFNB9 確定症例の発生頻度が低い** — 本プロジェクトの片側性主対象では稀
- **CHORD JP site の不透明性** — 施設名が public でないため、registry 登録が watch task になる
- **PMDA 承認時期の不確実性** — 2027-2028 推定は外れる可能性あり

## Out of scope

- **DB-OTO 以外の OTOF gene therapy** — Akouos AK-OTOF / 上海 Refreshgene 等は本 ADR の範囲外。出現次第 sibling ADR で追加
- **OTOF 以外の gene therapy (STRC, TMC1 base editing 等)** — 本 ADR は Otarmeni 専用。他遺伝子は別 ADR
- **個人保険・公費負担制度** — 治験参加時の経済負担スキームは別 ADR

# Alternatives Considered

## A. Otarmeni を初期 capability に含めない (DFNB9 が稀すぎる)

却下理由: 片側性プロジェクトでも遺伝学的 screening は実施する。確定症例が出たときの protocol を持たないと臨床現場で混乱する。`V02 → V16` chain は必ず実装する。

## B. CHORD JP site が公表されるまで本 ADR を保留

却下理由: site 公表は受動的待ち、policy 凍結は能動的に可能。policy 先行で OK。

## C. 個人輸入 path を完全削除

却下選択: 文書化のみ残し、actor からは default で返さない。将来の例外症例 escalation の文書根拠として価値あり。

## D. Tier 2 PMDA 経路を 2030+ と保守的に置く

却下: 2027-2028 が業界 consensus の reasonable estimate。保守的に置きすぎると Tier 1 watch を怠るリスク。

# References

- ADR-2605181040 — UHL-R 医療機関レジストリ schema (this PR sibling)
- ADR-2605181050 — UHL-R 海外 referral path (this PR sibling)
- [FDA Approves First Gene Therapy for Genetic Hearing Loss (Otarmeni, 2026-04-23)](https://www.fda.gov/news-events/press-announcements/fda-approves-first-ever-gene-therapy-treatment-genetic-hearing-loss-under-national-priority-voucher)
- [Regeneron — Otarmeni FDA approval press release](https://investor.regeneron.com/news-releases/news-release-details/otarmenitm-lunsotogene-parvec-cwha-approved-fda-first-and-only)
- [DB-OTO NEJM 2025](https://www.nejm.org/doi/full/10.1056/NEJMoa2400521)
- [Multicentre AAV1-hOTOF 2.5yr follow-up (Nature 2026)](https://www.nature.com/articles/s41586-026-10393-y)
- [CHORD trial NCT05788536](https://clinicaltrials.gov/study/NCT05788536)
- [OTOF Gene Therapy: Breakthroughs to Roadmaps (PMC 2026)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12954134/)
- [Zeng — Treating Hearing Loss: CI to Gene Therapy (Adv Sci 2025)](https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202509960)
- [Clinical Perspectives on Pediatric CI in Cochlear Nerve Deficiency (PMC 2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12382941/)
