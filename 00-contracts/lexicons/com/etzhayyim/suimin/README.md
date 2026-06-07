# com.etzhayyim.suimin.* lexicons

Lexicons for the **suimin (睡眠)** actor — sleep-disorder treatment-EVIDENCE research + synthesis.
Per [ADR-2606072800](../../../../../90-docs/adr/2606072800-suimin-sleep-disorder-evidence-research-charter.md).

| lexicon | 用途 |
|---|---|
| `sourceWhitelist` | Council-ratified の採用可能ソースクラス registry (G1 SSoT — PubMed/Cochrane/ICSD-3/ICD-11/AASM 等) |
| `evidenceRecord` | 単一エビデンス項目 (sourceClass + provenance PMID/DOI/CD-ID + studyType + GRADE + 要約) |
| `treatmentSynthesis` | 治療法ごとの集団レベル evidence landscape (非診断、disclaimer + 構成 evidenceRecord 参照) |
| `conditionProfile` | 睡眠障害 condition profile (ICSD-3 / ICD-11 coded、Wave 1 = OSA/CSA) |
| `referralPathway` | 地元医療機関 referral routing (睡眠専門外来 / 認定検査施設、予約はしない) |
| `silenSuiminReview` | Council Lv6+ ≥3 baseline attestation (witness ≥3) |
| `disclaimerText` | G3 disclaimer の canonical text registry (改竄不可、出力 path で参照) |

## Invariants

- **G1 source-whitelist + provenance**: 全 `evidenceRecord` / `treatmentSynthesis` の主張は whitelisted `sourceClass` + verifiable provenance を持つ。provenance なき主張は emit 不可。
- **G2 evidence-grade mandatory**: 全 `treatmentSynthesis` item は `evidenceGrade` + `studyType` 必須。
- **G3 disclaimer invariant**: 全患者向け出力に `disclaimerText` 参照必須 (`suimin_disclaimer_gate` 経由)。
- **G4 referral-not-treatment**: `referralPathway` は施設提示まで。予約・機器販売・個人診断なし。
