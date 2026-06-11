# com.etzhayyim.mitate.* — mitate diagnostic + treatment routing lexicons

Per mitate master charter [ADR-2605260100](../../../../../90-docs/adr/2605260100-mitate-diagnostic-routing-charter.md)
+ 5 condition sub-ADRs ([2605260115](../../../../../90-docs/adr/2605260115-mitate-condition-1-allergic-rhinitis-perennial.md)
/ [2605260130](../../../../../90-docs/adr/2605260130-mitate-condition-2-vasomotor-rhinitis.md)
/ [2605260145](../../../../../90-docs/adr/2605260145-mitate-condition-3-chronic-sinusitis.md)
/ [2605260160](../../../../../90-docs/adr/2605260160-mitate-condition-4-septal-deviation.md)
/ [2605260175](../../../../../90-docs/adr/2605260175-mitate-condition-5-rhinitis-medicamentosa.md)).

9 lexicons covering the full diagnostic + treatment routing substrate from patient
intake through longitudinal outcome followup (8 at R0 per master charter +
`diagnosticConsentReceipt` added at R2 per [ADR-2605281950](../../../../../90-docs/adr/2605281950-mitate-r2-general-lab-orders-and-iyashi-phlebotomy.md)):

| Lexicon | Purpose | Encryption |
|---|---|---|
| `rhinitisIntake` | patient symptom + consent + medication history intake | `encryptedSymptomEnvelope` XChaCha20-Poly1305 (G2) |
| `triageVerdict` | 5-condition Bayesian classifier output (top-3 posterior + escalation + disclaimer) | `encryptedTriageEnvelope` (G2) |
| `diagnosticOrder` | 検査 ordering (IgE / smear / endoscopy / rhinomanometry / CT + R2 general blood / chemistry / urinalysis per ADR-2605281950) | consent receipt mandatory (G1) |
| `diagnosticConsentReceipt` | per-order 要配慮個人情報 (APPI 第2条第3項 / GDPR Art. 9) 移管 consent (R2+ per ADR-2605281950) | structurally sealed-recipient set (G7 + GD) |
| `diagnosticResult` | 検査結果 (lab / DICOM / image classification) | `encryptedResultEnvelope` (G2) |
| `treatmentPlan` | 治療経路 advisory (INN-only, brand 不可 except yakushi-distributed) | `disclaimerAccepted` mandatory (G3) |
| `outcomeFollowup` | longitudinal QOL + adherence + AE tracker (yakushi cross-feed leg) | encrypted patient identity; aggregated public |
| `silenMitateReview` | Council Lv6+ ≥ 3 multisig attestation (G9 + bias audit) | public (council attestation transparency) |
| `emergencyEscalation` | G5 red-flag detected → ER routing + on-call DID + ack receipt | public ack only (no patient identity) |

All lexicons enforce:
- **G1** (consent receipt CID for any patient-data-carrying record)
- **G2** (encrypted envelope for any health data — sealed-recipient = patient + Council medical advisory + R2+ licensed MD)
- **G3** (advisory disclaimer for treatmentPlan)
- **G4** (licensed MD attestor DID for R2+ diagnostic order / Rx-tier treatment plan)
- **G7** (no insurance / employer / advertiser recipient in sealed-recipient set)
- **G8** (INN-only content, brand 不可 except `did:web:etzhayyim.com:yakushi:product:*`)
- **G9** (witness N ≥ 2 for diagnosticResult / treatmentPlan / silenMitateReview)
- **G10** (no patient identity in aggregated feed payloads)
- **G14** (substrate boundary: `@etzhayyim/sdk` only)

## yakushi cross-actor lexicon emit boundary

Per master charter §Decision 8, mitate and yakushi share substrate boundary:
- `outcomeFollowup` → yakushi `pharma.adverseEventReport` (individual handoff + aggregated feed)
- yakushi `pharma.adverseEventReport` → mitate `outcomeFollowup` (back-feed for longitudinal tracking)

No new namespace introduced. Cross-actor lexicon emit uses existing yakushi
`com.etzhayyim.pharma.adverseEventReport` schema (mitate adds `apiInn` knownValue if mitate-side
detects a new INN not in yakushi catalog — requires joint mitate-yakushi silen-review).
