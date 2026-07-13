---
id: adr-2607141900-sanae-g2-displacement-dividend-coupling-gap
title: "ADR-2607141900: sanae autonomous_weeding — G2 displacement-dividend coupling を pass_logged 終端に配線"
status: active
doc_type: adr
topic: sanae-g2-displacement-dividend-coupling-gap
authoritative: true
last_verified: 2026-07-14
status_note: "etzhayyim root成熟度向上タスク(item 4「R0→R1 advancement」)の継続。yadori/watari(ADR-2607141600)と同じ監査手法(actor CLAUDE.mdのgate表 vs 実装コード)を追加のR0actor群に適用した結果、sanaeで発見。同ADR対(2606032100+2606032130)・同一G2文言を持つ兄弟actor hataoriの`finishing_packing/state_machine.cljc`に既に実装済みの、証明済みパターンをそのまま踏襲した。"
priority: 6.0
axis: safety
weight: 0.45
priority_note: "sanaeの唯一のcoded cell(autonomous_weeding)の終端遷移(transition-to-pass-logged)に、CLAUDE.mdが既に明記する制約(「Do not let a deployment displace field labour without a funded displacement cohort (G2 → ADR-2606032130)」)を実装するもの。新しい制約の導入ではなく実装ギャップの解消。hataoriの同一ADR・同一文言のG2実装が既に存在し証明済みのパターンだったため、設計判断の余地は小さい(何を追加すべきかは兄弟actorが既に示している)。"
authoritative_for:
  - "sanae autonomous_weeding cell の G2(displacement-dividend coupling)配線の正本"
depends_on:
  - adr-2606032100-labor-liberation-robotics-actor-wave-isic-isco-unspsc-ranking
  - adr-2606032130-displacement-dividend-tenure-weighted-basic-high-income
related:
  - adr-2607141600-yadori-watari-documented-gate-implementation-gaps
supersedes: []
superseded-by: []
---

# ADR-2607141900: sanae autonomous_weeding — G2 displacement-dividend coupling を pass_logged 終端に配線

**Status**: active
**Date**: 2026-07-14
**Scope**: `20-actors/sanae/cells/autonomous_weeding/state_machine.cljc` の
`transition-to-pass-logged` のみ。他cell(field_preparation/precision_seeding/
harvest_coordination/soil_regeneration_audit、いずれもR0 raise-onlyスタブ)・
robotics・G3/G9等の既存gate実装には一切触れない。

## Context

yadori/watari(ADR-2607141600)に続き、同じ監査手法(actor CLAUDE.mdのgate表 vs
実装コード)を他のR0 actor群に適用した。sanaeのCLAUDE.mdは:

> **G2 displacement-dividend coupling** (no live displacement without the
> displaced cohort registered for the tenure-weighted dividend, ADR-2606032130)

および明示的な"Do not"項目:

> Do not let a deployment displace field labour without a funded displacement
> cohort (G2 → ADR-2606032130).

を定めているが、sanaeの唯一のcoded cellである`autonomous_weeding/state_machine.cljc`
の終端遷移`transition-to-pass-logged`は、G3(witness quorum)・G9(herbicide method、
前段の`transition-to-weed-cleared`)は実装していたものの、G2は一切チェックしておらず、
`displaced_cohort_id`/`dividend_attested`に相当するフィールドすら状態に存在しなかった
(`grep -rn "dividend|displac"`はsanae全体でヒットなし)。

同じADR対(ADR-2606032100 + ADR-2606032130)・同一のG2文言を持つ兄弟actor **hataori**
(labour-liberation waveの LPS #2)は、対応する終端cell
(`finishing_packing/state_machine.cljc`の`transition-to-lot-attested`)で既にこの
チェックを実装済みで、`dividend_attested`/`displaced_cohort_id`の欠落時に
`:hataori/violation :g2`で`ex-info`をraiseする。sanaeにはこの実装が欠けていた
——これは同一ADR対を参照する複数actorのうち一部にのみ実装が及んでいた、という
実装ギャップである。

## Decision

hataoriの`transition-to-lot-attested`のG2チェックを、sanaeの
`transition-to-pass-logged`にそのまま踏襲する。

```clojure
;; state-defaults に追加
"displaced_cohort_id" ""
"dividend_attested" false

;; transition-to-pass-logged 冒頭に追加
(when (or (not dividend-attested) (empty? displaced-cohort-id))
  (throw (ex-info "G2 violation: displaced cohort not registered for the Displacement Dividend (ADR-2606032130)"
                  {:gate "G2"})))
```

pass recordのpayloadにも`displacedCohortId`/`dividendAttested`を追加し、
hataoriの`fair_labor_provenance`と同様に監査可能にした。

sanae自身が既に持つG3(witness quorum)は例外的に**非throw**(quorum未達成でも
`witnessQuorumMet: false`を記録するのみで終端は許可される、R0の設計判断)だが、
G2はhataoriの実装・CLAUDE.mdの"Do not let"という文言の強さから、throwする
constitutional invariantとして扱う——G3とG2は異なる性質のgateであり、G3の
非throw運用をG2に一般化しない。

## Consequences

- (+) sanaeの唯一のcoded cellに、既に文書化済みだが未実装だったG2 gateが閉じた。
- (+) hataoriと同一ADR対を参照する他のlabour-liberation actor群(現状autonomous_weeding
  相当のcoded cellを持つのはこの2つ)で、G2実装が同一パターンに揃った。
- (+) 既存のG9/G3テストは、`run`ヘルパーのデフォルト引数(`dividend-attested` true /
  `displaced-cohort-id`にダミーDIDを設定)を通過するよう更新——kuni-umi
  (ADR-2607141200)/yadori・watari(ADR-2607141600)と同型の「gate実装により
  無条件成功を仮定していた既存テストの現実的な入力値への更新」。
- (−) `displaced_cohort_id`/`dividend_attested`は現状呼び出し側が渡す値をそのまま
  信頼するのみで、実際の tenure-weighted dividend registry との照合(kuni-umiの
  governed-advisorパターンのような独立検証)は行っていない——hataori側も同水準の
  簡易実装であり、本ADRのスコープ外(dividend registry統合はfollow-up)。

## Artifacts

- `20-actors/sanae/cells/autonomous_weeding/state_machine.cljc`(state-defaults 2
  フィールド追加 + `transition-to-pass-logged`へのG2 throw追加)
- `20-actors/sanae/cells/autonomous_weeding/test_state_machine.cljc`(`run`ヘルパー
  更新 + 2 tests追加: unattested-dividend blocks / missing-cohort-id blocks)

動作確認: `bb`(canonical classpath、`require`経由)で
`sanae.cells.autonomous-weeding.test-state-machine` 7 tests / 14 assertions green。
clj-kondo: 新規エラー・警告0件(pristine origin/mainの同一ファイルと比較——既存の
1 error(Unresolved symbol: clojure、cljs文脈での`clojure.lang.ExceptionInfo`)・
1 warning(未使用require)は変更前から存在し変更なし)。

## References

- ADR-2606032100(labour-liberation robotics actor wave、sanae/hataori共通の親ADR)
- ADR-2606032130(displacement-dividend coupling、G2文言の出典)
- ADR-2607141200(kuni-umi jurisdiction-eligibility)・ADR-2607141600
  (yadori/watari)——同型の欠陥クラスの先例
- `20-actors/sanae/CLAUDE.md` / `20-actors/hataori/CLAUDE.md`(gate表 + 実装済み
  パターンの出典)
