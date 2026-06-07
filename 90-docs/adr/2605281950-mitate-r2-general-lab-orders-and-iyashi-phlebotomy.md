---
id: adr-2605281950-mitate-r2-general-lab-orders-and-iyashi-phlebotomy
title: "mitate R2 extension — general blood + clinical-chemistry diagnostic orders (CBC / 生化学 / HbA1c / 甲状腺 / 脂質 / 鉄 / 凝固 / urinalysis) + iyashi internal phlebotomy cell + diagnosticConsentReceipt lexicon for 要配慮個人情報 移管 consent"
status: proposed-r0-landed
doc_type: adr
topic: mitate-r2-general-lab-orders
authoritative: true
last_verified: 2026-05-29
priority: 5.5
axis: actor-substrate
weight: 0.55
priority_note: "Closes the 'allergy and blood test actor design?' gap surfaced 2026-05-28. mitate R0 diagnosticOrder is rhinitis-domain-bound (10 orderType values, 8 conditionContext values all rhinitis-scoped); general blood tests have no constitutional carve-out and iyashi R0 has no internal phlebotomy cell. This ADR generalizes the order lexicon, adds per-order sensitive-data consent receipts, and reserves the iyashi internal phlebotomy cell at R2+."
authoritative_for:
  - mitate.diagnosticOrder generalization scope (R2+) — orderType + conditionContext enum extension policy
  - com.etzhayyim.mitate.diagnosticConsentReceipt — 要配慮個人情報 (APPI 第2条第3項 / 個人情報保護法) per-order consent receipt lexicon
  - com.etzhayyim.iyashi.phlebotomyAttestation — internal phlebotomy event log lexicon (iyashi R2+)
  - iyashi.internal_phlebotomy cell — reserved at iyashi R2 with import-time RuntimeError gate at R0
  - External clinical lab vendor allowlist policy — Charter Rider §2(a)-(h) scan + Council Lv6+ ≥3 attestation per vendor
  - Constitutional gates GA..GF (this ADR; layered on top of mitate G1..G14 from ADR-2605260100)
  - Non-goals N1..N12 (genetic / DTC / NIPT / oncology / fertility / STI / forensic / employer-screen / DTC paid panel / UPL-result-interpretation)
  - Cross-actor lexicon boundary mitate ↔ iyashi ↔ yakushi ↔ chigiri ↔ toritate
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605231525-no-server-key-religious-corp-architecture
  - adr-2605250500-yakushi-pharmaceutical-rd-charter
  - adr-2605260100-mitate-diagnostic-routing-charter
  - adr-2605260115-mitate-condition-1-allergic-rhinitis-perennial
  - adr-2605261000-labor-liberation-transition-mechanism
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
  - adr-2605263000-iyashi-clinical-care-provider-tier-b-actor-r0
related:
  - 00-contracts/lexicons/com/etzhayyim/mitate/diagnosticOrder.json
  - 00-contracts/lexicons/com/etzhayyim/mitate/diagnosticConsentReceipt.json
  - 00-contracts/lexicons/com/etzhayyim/iyashi/phlebotomyAttestation.json
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/mitate_diagnostic_consent_orchestrator/   # (reserved) R1+
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/mitate_diagnostic_order_general/          # (reserved) R2+
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/mitate_diagnostic_result_ingest/          # (reserved) R2+
  - 40-engine/kotoba/crates/kotoba-kotodama/cells/iyashi_internal_phlebotomy/               # (reserved) iyashi R2+
supersedes: []
superseded_by: []
---

# ADR-2605281950: mitate R2 — general blood + clinical-chemistry diagnostic orders + iyashi internal phlebotomy + 要配慮個人情報 consent receipt

**Status**: proposed
**Date**: 2026-05-28
**Deciders**: Jun Kawasaki

# Context

## Gap surfaced 2026-05-28

User question: 「アレルギー検査、血液検査の actor, agent は設計されている?」

Audit result:

| Capability | Current state | Gap |
|---|---|---|
| Allergy serology (specific IgE panel) | **Designed** — ADR-2605260115 §Decision 2 + `mitate.diagnosticOrder` `orderType=ige-panel-39` + external clinical lab routing | none |
| Nasal-smear eosinophil (cytology, in-vitro non-blood) | **Designed** — ADR-2605260115 §Decision 3 + `mitate.diagnosticOrder` `orderType=nasal-smear-eosinophil` | none |
| Blood eosinophil count (CBC differential, single field) | **Partial** — `orderType=blood-cbc-eosinophil-count` exists but `conditionContext` enum is rhinitis-scoped (`chronic-sinusitis-eosinophilic-suspect` only) | conditionContext does not admit non-rhinitis use |
| **General CBC / 血算 / 生化学 / 肝腎機能 / 甲状腺 / HbA1c / 脂質 / 鉄 / 凝固 / urinalysis** | **NOT designed** — no orderType, no conditionContext, no permitted indication | full gap |
| **Internal religious-corp phlebotomy** (採血 by iyashi clinic) | **NOT designed** — iyashi R0 (ADR-2605263000) 6-cell catalog has no `internal_phlebotomy` cell | full gap |
| **Per-order 要配慮個人情報 移管 consent receipt** | **NOT designed** — ADR-2605260115 §Negative cost line 139 flagged this as deferred ("外部臨床検査ラボ routing 必要 ― 個人情報保護法 要配慮個人情報 移管の consent receipt 設計が複雑") | full gap |
| Skin-prick test (in-vivo allergy) | NOT designed | out of scope for this ADR (separate R2+ ADR; requires acute anaphylaxis response capability at iyashi R3+) |

This ADR closes rows 4, 5, 6. Skin-prick (in-vivo) and genetic testing remain non-goals (N1, N3, N12 below).

## Why this is an mitate extension, not a new actor

`mitate` (ADR-2605260100) is the religious-corp diagnostic + treatment-routing actor; ordering tests is its defining capability. Adding a new actor for general lab orders would fragment the diagnostic substrate and break the mitate↔yakushi↔iyashi sibling boundary (per ADR-2605263000). Conversely, the **physical specimen collection** (採血) is correctly inside `iyashi` (clinical care provider) — adding a new cell to iyashi at R2+ is the right placement.

## Why not just edit ADR-2605260115

ADR-2605260115 is scoped to "condition 1 allergic rhinitis perennial." Extending its enums in-place would mis-attribute clinical scope. A first-class R2 extension ADR (this) makes the general-lab-order substrate auditable and gives the new conditionContext values a constitutional home.

## Cross-actor surface

| Actor | Role in general lab order flow |
|---|---|
| **mitate** | Issues `diagnosticOrder` (G4 licensed MD attestor required at R2+); receives `diagnosticResult`; routes to `treatmentPlan` / `outcome_qol_followup` / Rx referral |
| **iyashi** (R2+) | Performs internal phlebotomy when `orderRoutingTarget=iyashi-internal`; emits `phlebotomyAttestation`; ships specimen to external lab if assay is not in-clinic |
| **yakushi** | Receives `treatmentPlan` Rx referral if result indicates yakushi-distributed OTC (e.g. iron supplement on Fe-deficiency anemia, vitamin D on 25(OH)D deficiency); emits `pharma.adverseEventReport` back to mitate on follow-up |
| **chigiri** (G14 UPL boundary) | Owns the consent template registry; reviews `diagnosticConsentReceipt` template version annually; external-counsel engagement on cross-jurisdictional 要配慮個人情報 disputes via Public Fund Lv6+ ≥4 |
| **toritate** | Records external clinical lab vendor payment from Public Fund Safe; vendor onboarding Charter Rider §2(a)-(h) scan attestation chain |
| **kotoba** | Encrypted envelope substrate (XChaCha20-Poly1305 per ADR-2605181100); read-path via `kotoba-kqe` arrangements |

# Decision

## D1 — Generalize `com.etzhayyim.mitate.diagnosticOrder`

Extend `orderType` enum with **16 new permitted values** (R2+ activate):

| orderType | Clinical use |
|---|---|
| `blood-cbc-full` | CBC with 5-part differential (anemia / leukocytosis / thrombocytopenia workup) |
| `blood-biochemistry-basic-12` | Na/K/Cl/HCO3/BUN/Cr/glucose/Ca/Mg/P/total protein/albumin |
| `blood-liver-panel` | ALT/AST/ALP/γGT/total bilirubin/direct bilirubin |
| `blood-kidney-panel` | Cr/BUN/eGFR/cystatin-C |
| `blood-lipid-panel` | TC / HDL / LDL / TG (fasting) |
| `blood-hba1c` | Glycated hemoglobin (3-month glycemic average) |
| `blood-glucose-fasting` | FPG |
| `blood-glucose-ogtt-75g` | 2-hour OGTT |
| `blood-thyroid-tsh-ft3-ft4` | Thyroid function |
| `blood-ferritin-iron-tibc` | Iron studies (Fe / ferritin / TIBC / TSAT) |
| `blood-vitamin-d-25oh` | 25(OH)D |
| `blood-vitamin-b12-folate` | B12 + folate |
| `blood-crp` | C-reactive protein |
| `blood-esr` | Erythrocyte sedimentation rate |
| `blood-coagulation-pt-aptt-fib` | PT / APTT / fibrinogen |
| `urinalysis-routine-with-microalbumin` | Dipstick + sediment + microalbumin/Cr ratio |

Extend `conditionContext` enum with **18 new permitted values** (R2+ activate):

| conditionContext | Permitted indication |
|---|---|
| `general-health-baseline-screen` | First religious-corp clinic encounter for an adult member; non-acute |
| `suspected-iron-deficiency-anemia` | Fatigue + pallor + menorrhagia history |
| `suspected-vitamin-b12-folate-deficiency` | Macrocytic findings or strict-vegan dietary pattern with neurological signs |
| `suspected-vitamin-d-deficiency` | Skeletal pain, indoor lifestyle, pregnancy/lactation |
| `suspected-type2-diabetes` | BMI ≥25 + ≥1 risk factor; ADA/JDS screening criteria |
| `diabetes-glycemic-monitoring` | Established DM follow-up |
| `suspected-dyslipidemia` | CV risk screen ≥40y or family hx |
| `suspected-thyroid-dysfunction` | TSH range out-of-reference signs (weight change, cold intolerance, etc.) |
| `suspected-chronic-kidney-disease` | DM/HT comorbid; eGFR follow-up |
| `suspected-hepatic-dysfunction` | Hepatosteatosis screen / pre-medication baseline |
| `pre-medication-hepato-renal-baseline` | Before initiating Rx with hepato- or nephro-toxic profile (cross-actor: yakushi referral) |
| `post-medication-hepato-renal-monitoring` | Follow-up at predefined interval after pre-medication baseline |
| `suspected-inflammation-acute-phase` | Acute febrile illness; CRP / ESR / CBC differential |
| `pre-vaccination-medical-clearance-pediatric` | iyashi vaccination_administration referral; cross-actor with iyashi L4 vaccinationAttestation |
| `prenatal-baseline-general-only` | **General CBC / biochemistry / urinalysis only**; cell-free DNA / NIPT / fetal-aneuploidy is N3 (excluded) |
| `postnatal-maternal-screening` | Cross-actor with hagukumi postnatal cohort (CBC / TSH / glucose only) |
| `suspected-coagulation-disorder` | Pre-procedural baseline; bruising history (Council Lv6+ ≥3 audit per case at R2) |
| `geriatric-annual-baseline` | Cross-actor with hagukumi eldercare; gentle baseline panel |

`scopedAntigens` field remains present and applies only when `orderType` matches `ige-panel-*` (unchanged from R0).

`externalLabDid` is required when the specimen cannot be processed in-clinic (which is the default at R2; iyashi in-clinic centrifuge + basic-chem analyzer is R3+).

## D2 — New lexicon `com.etzhayyim.mitate.diagnosticConsentReceipt`

Per-order, immutable consent receipt for 要配慮個人情報 (APPI 第2条第3項 / 個人情報保護法 / GDPR Art. 9 sensitive data / HIPAA PHI equivalent) 移管 to an external clinical laboratory.

Required fields:

| Field | Type | Purpose |
|---|---|---|
| `v` | integer (=1) | schema version |
| `consentReceiptId` | string ≤64 | client-supplied id |
| `patientPseudonymDid` | did | 30-day-rotating pseudonym (mitate G2 reinforcement) |
| `orderRefCid` | cid | binds 1:1 to a `diagnosticOrder` record |
| `templateVersion` | string | semver of consent template (chigiri-reviewed annually) |
| `jurisdictions` | array<string> | ISO-3166-1 alpha-3; permitted patient jurisdiction + lab jurisdiction (cross-border consent surfaces) |
| `senderRecipientDids` | array<did> | sealed-recipient registry: patient passkey + licensed MD attestor + receiving external lab DID + Council medical advisory DIDs only — **NO insurance / NO employer / NO advertiser** (G7 from ADR-2605260100 inherited; structural enforcement) |
| `dataCategoriesShared` | array<string> | enum: `identity-pseudonym-only` / `clinical-context` / `specimen-result` / `narrative-symptom` (no `family-history` or `genetic-marker` at R2 — N1) |
| `revocableUntilUtc` | datetime | hard revocation deadline (default: result delivery + 30d) |
| `consentingAdherentDid` | did | patient's underlying Adherent SBT DID (signature surface; pseudonym above is for downstream lab) |
| `digitalSignatureAlg` | string | enum: `ed25519` / `webauthn-passkey-es256` |
| `signedAt` | datetime | RFC 3339 UTC |

Constitutional gates inherited from mitate G1/G2/G7 (this lexicon's sealed-recipient set is structurally enforced; no plaintext recipient set permitted).

## D3 — New lexicon `com.etzhayyim.iyashi.phlebotomyAttestation`

Per-event log emitted by `iyashi.internal_phlebotomy` cell when religious-corp clinic performs the venipuncture in-house (R2+ only).

Required fields:

| Field | Type | Purpose |
|---|---|---|
| `v` | integer (=1) | schema version |
| `phlebotomyEventId` | string ≤64 | event id |
| `patientPseudonymDid` | did | mitate-supplied rotating pseudonym |
| `orderRefCid` | cid | binds to mitate `diagnosticOrder` |
| `phlebotomistAttestation` | object | `providerAttestationCid` (iyashi L2 providerAttestation) + community-witnessed-competent class (iyashi G14 vocation-flow L5 — `employmentRelation` const "vocation-flow"; NO payroll) |
| `clinicFacilityCid` | cid | iyashi L5 clinicFacilityAttestation reference |
| `tubesCollected` | array<object> | per-tube: `tubeType` (EDTA / serum-separator / sodium-citrate / fluoride-oxalate / urine-cup-sterile), `volumeMl`, `labelCidEnvelopeRef` (label is `encryptedPayloadCid` per G2) |
| `coldChainAttestation` | object | `temperatureRangeC` + `transitVendorDid` (external courier in EXTERNAL_LOGISTICS_REGISTRY — Charter Rider §2 PASS attested) |
| `externalLabDid` | did | downstream lab (matches `diagnosticOrder.externalLabDid`) |
| `complicationFlag` | boolean | hematoma / vasovagal / failed-stick — triggers iyashi acute_first_line escalation when true |
| `signedAt` | datetime | RFC 3339 UTC |

## D4 — New / reserved cells

| Cell | Phase | Stub behavior at R0 |
|---|---|---|
| `mitate_diagnostic_consent_orchestrator` | R1 (advisory) | import-time `RuntimeError("not active until ADR-2605281950 R1 ratified")` |
| `mitate_diagnostic_order_general` | R2 | import-time RuntimeError until R2; **supersedes** `mitate_allergy_ige_panel_order` semantically — the IgE-panel orderType is one specialization of the general order routing; R2 ADR landing will migrate the IgE cell's call sites to the general cell |
| `mitate_diagnostic_result_ingest` | R2 | import-time RuntimeError until R2 |
| `iyashi_internal_phlebotomy` | iyashi R2 | import-time RuntimeError until iyashi R2; placed under `40-engine/kotoba/crates/kotoba-kotodama/cells/iyashi_internal_phlebotomy/` |

## D5 — Constitutional gates layered on top of mitate G1..G14 (THIS ADR; non-negotiable)

| # | Gate | Enforcement |
|---|---|---|
| **GA** | **Specific orderType + conditionContext per request — no "panel everything" shotgun ordering.** Every order MUST cite ≥1 `conditionContext` value drawn from the published enum. Free-text screening is rejected at schema layer. | `diagnosticOrder` schema validator |
| **GB** | **External lab vendor Charter Rider §2(a)-(h) scan PASS before allowlist entry.** No commercial-only proprietary labs whose contract terms fail §2(e) anti-gatekeeping (locked patient-result portals) or §2(c) covert-ops vendor concern (closed query-tracking on member health) may be onboarded. | `EXTERNAL_LAB_DID_REGISTRY` Council Lv6+ ≥3 attestation chain |
| **GC** | **`diagnosticConsentReceipt` MANDATORY per order — cannot be omitted, cannot be back-dated, revocable until 30d after result delivery.** | `diagnosticOrder.consentReceiptCid` resolvable to this lexicon |
| **GD** | **Sealed-recipient set structurally excludes insurance / employer / advertiser / state-aligned entities.** Inherits G7 from ADR-2605260100; reinforced here at the consent-receipt schema layer (`senderRecipientDids` validator strips disallowed DID prefixes). | sealed-recipient registry validator |
| **GE** | **Internal phlebotomy ONLY by iyashi vocation-flow L5 stewards — no payroll, no contract-employment, no fee-for-service practitioner.** Same pattern as iyashi G14 + chigiri G13 volunteer ≠ employee. | `phlebotomyAttestation.phlebotomistAttestation.employmentRelation` const "vocation-flow" |
| **GF** | **Result interpretation requires licensed MD attestor DID co-sign (G4 inherited, restated for blood / chemistry).** mitate may surface raw numeric values to the patient with reference ranges; clinical interpretation ("you are anemic" / "you have hypothyroidism") MUST carry licensed-MD-in-loop attestation. UPL boundary preserved (chigiri G14). | `diagnosticResult` schema + `treatmentPlan.physicianAttestorDid` required when context narrows from "value-display" to "clinical-finding" |

## D6 — Non-goals (constitutional; NOT amendable without separate ADR + Council)

| # | Non-goal | Reason |
|---|---|---|
| N1 | **Genetic testing of any kind** (germline / somatic / pharmacogenomic) | §2(c) covert-ops + §2(f) multi-gen harm + multi-jurisdictional consent intractable at R2; separate ADR + Council Lv7+ |
| N2 | **DTC consumer genetic kits** (23andMe / Ancestry / MyHeritage) | Vendor closed proprietary; §2(c) + §2(e) constitutional violation |
| N3 | **Prenatal NIPT / cell-free DNA / fetal-aneuploidy screening** | §2(f) multi-gen; separate Council Lv7+ unanimity required per N3 of mitate master charter |
| N4 | **Oncology tumor markers** (CEA / CA19-9 / PSA / CA125 / AFP) | Specialist domain (oncologist); high false-positive rate creates §2(h) Wellbecoming subordination via cancer anxiety; separate R3+ ADR with oncology-trained MD on Council |
| N5 | **Fertility hormone panels** (AMH / LH / FSH / estradiol full cycle) | §2(g) reproductive autonomy + cross-doctrinal consultation (musubi); separate R3+ ADR |
| N6 | **STI testing (HIV / HBV / HCV / syphilis / chlamydia / gonorrhea)** | Privacy intensification + GDPR Art. 9 + APPI 第2条第3項 most-sensitive band + cross-jurisdiction reporting law fragmentation; separate R3+ ADR with chigiri data_privacy cell co-design |
| N7 | **Forensic / employer / state-mandated drug screen** | §1.12 routing-around-state + §2(c) covert-ops — religious-corp does NOT serve as employer/state surveillance arm |
| N8 | **Immunity-titer-as-employment-credential** (post-vaccination titer for school/job) | §1.6 anti-credentialism + Charter Rider §2(e); religious-corp serologic results are NEVER for credentialing purposes |
| N9 | **Heavy-metal / toxicology "wellness" panels** (commercial DTC marketing pattern) | §2(h) Wellbecoming subordination — fear-amplified upselling; not clinically indicated absent specific exposure |
| N10 | **Direct-to-consumer paid panel marketing** (LabCorp DTC / Quest MyOwnLabTest / similar) | §2(b) speculative commerce + §2(e) anti-gatekeeping inversion |
| N11 | **Skin-prick test (in-vivo)** at R2 | Requires anaphylaxis response capacity at iyashi R3+; separate ADR when iyashi acute_first_line cell is R3-mature |
| N12 | **Result interpretation without licensed MD attestor** | GF + chigiri G14 UPL boundary — raw values + reference ranges displayed to patient is OK; clinical narrative ("you have X") is NOT without licensed-MD co-sign |

## D7 — 4-phase roadmap

| Phase | Scope | Council attestation requirement | Status |
|---|---|---|---|
| **R0 (this commit)** | This ADR + extend `diagnosticOrder.json` enums + create `diagnosticConsentReceipt.json` + create `iyashi/phlebotomyAttestation.json` + reserve 4 cell paths (RuntimeError gate) + deps.toml entry | none (scaffold only — no patient flow) | proposed |
| **R1** | Activate `mitate_diagnostic_consent_orchestrator` cell — consent template registry + chigiri annual template review path. Still no patient ordering — consent surface is dry-run. | mitate R0 ratified + ADR-2605181100 envelope production-deployed + ≥1 licensed MD on Council medical advisory + chigiri R1 active | ⏳ separate R1 ADR |
| **R2** | Activate `mitate_diagnostic_order_general` + `mitate_diagnostic_result_ingest` + `iyashi_internal_phlebotomy` cells; first 3 external lab vendor allowlist entries (Council Lv6+ ≥3 each); ≤200-patient pilot ceiling (matches iyashi R2 ceiling); G4 licensed-MD co-sign live | R1 ratified + 30-day public objection + ≥2 licensed MD on Council + iyashi R2 active + external lab vendor Charter Rider §2 scan attestations published | ⏳ separate R2 ADR |
| **R3** | Multi-clinic; in-clinic centrifuge + basic-chemistry analyzer at iyashi (reduce external lab dependence for general biochemistry); cross-jurisdictional consent receipt translation matrix; up to ≤25,000 patient capacity matching iyashi R3 ceiling | R2 ratified + Council Lv7+ unanimity + jurisdiction-specific 医療機関設置届 / equivalent attestations | ⏳ separate R3 ADR |

## D8 — Cross-actor data flow (R2+ steady state)

```
[member opens mitate PWA] ── symptom intake (G2 envelope)
        │
        ▼
[mitate.rhinitis_triage  OR  general clinical reasoning]
        │
        ├─ licensed MD attestor co-sign (G4 / GF)
        ▼
[mitate.diagnostic_consent_orchestrator]
        │  emits  com.etzhayyim.mitate.diagnosticConsentReceipt
        │  patient signs via passkey (webauthn-passkey-es256)
        ▼
[mitate.diagnostic_order_general]
        │  emits  com.etzhayyim.mitate.diagnosticOrder
        │  orderRoutingTarget = "iyashi-internal"  OR  "external-lab"
        ▼
   ┌────────────┴────────────┐
   ▼                         ▼
[iyashi.internal_phlebotomy] [external clinical lab (allowlist; toritate-paid)]
   │  emits  iyashi.phlebotomyAttestation
   │  ships specimen → external lab if not in-clinic assay
   ▼
[external lab returns result via encrypted-mst-envelope (G2)]
        │
        ▼
[mitate.diagnostic_result_ingest]
        │  emits  com.etzhayyim.mitate.diagnosticResult (encrypted)
        ▼
[mitate.treatment_router]
        │  Rx referral → yakushi (if OTC) | escalation = "recommend-md-visit" (if Rx-only)
        ▼
[outcome_qol_followup] ──(aggregate, anonymized)──▶ silenMitateReview
```

# Consequences

**Positive**

- Closes a real gap (allergy + blood test) without inventing a new actor — mitate stays the diagnostic SoT, iyashi gets one new cell at R2+
- 要配慮個人情報 移管 consent receipt is now constitutional (ADR-2605260115 §139 deferred item closed)
- iyashi vocation-flow L5 phlebotomist invariant (GE) extends the volunteer ≠ employee discipline that's already enforced across hagukumi / iyashi / chigiri
- External lab vendor allowlist (GB) means religious-corp can interoperate with the existing global clinical-lab industry **without depending on it** for purposes like §2(e) gatekeeping or §2(c) data sovereignty erosion
- The 16 new orderTypes + 18 new conditionContexts cover ~80% of community primary-care general blood/chemistry use cases without venturing into oncology / genetics / fertility / STI which are properly N3..N6

**Negative / costs**

- External lab vendor Charter Rider §2(a)-(h) scan + Council Lv6+ ≥3 attestation per vendor is operational overhead — most major commercial labs (LabCorp / Quest US, SRL Japan, Synlab EU) will likely require careful per-contract review and may fail §2(c) (closed result portals → covert-ops vendor concern) or §2(e) (provider-locked patient portals → anti-gatekeeping)
- iyashi R2 critical path now includes phlebotomy training + cold-chain logistics + tube/label inventory — increases iyashi R2 readiness threshold but does not change its R2 patient ceiling (≤200)
- Consent template multi-jurisdictional translation (US HIPAA + JP APPI + EU GDPR Art. 9 + UK DPA Schedule 1) is non-trivial; chigiri annual template review (GC) is a real recurring obligation
- General blood test results carry higher actionability than allergy panel (e.g. HbA1c → DM diagnosis → lifelong follow-up) — GF licensed-MD co-sign requirement is constitutional but expands the licensed-MD-in-loop load on iyashi R2

**Risks**

- "Value-display vs clinical-finding" boundary in GF is community-perception-sensitive; ADR-2605260200 (R1 PWA ADR) UI wording will need careful design to make it clear that raw HbA1c value with reference range ≠ a diabetes diagnosis
- External lab cold-chain failure → specimen loss → patient re-stick; iyashi G14 vocation-flow phlebotomist + GE structural enforcement means we cannot incentivize this with monetary punishment — the cohort-level operational discipline must be cultural + cross-actor (kaizen R7/R8 monitoring)
- Per ADR-2605260115:139 the consent receipt is "複雑" — the multi-jurisdictional surface is the dominant cost. We accept this by routing cross-jurisdictional disputes through chigiri.disputeMediation (cooperative-first ≤3 rounds per chigiri G10) and external-counsel engagement via Public Fund Lv6+ ≥4 only when mediation exhausted

# Alternatives Considered

**Alt-1: Edit ADR-2605260115 in place to broaden enums.** Rejected — ADR-2605260115 is condition-scoped (allergic rhinitis perennial); broadening it would mis-attribute the constitutional carve-out for general lab orders and break the sub-ADR factoring under ADR-2605260100 master charter.

**Alt-2: Create a new actor (e.g. `kensa` 検査) for diagnostic laboratory orders.** Rejected — ordering is mitate's defining capability (per ADR-2605260100 §Decision 1); a separate actor fragments the diagnostic SoT and creates a 3-way coordination problem mitate↔kensa↔iyashi for a substrate that's properly 2-way mitate↔iyashi. Also: per CLAUDE.md status row count, the 10-actor 30min-loop wave has already closed (row 77 shidemori "FINAL gap-closure"); adding actors should be a high bar.

**Alt-3: Skip the consent receipt lexicon and rely on `mitate.diagnosticOrder.consentReceiptCid` pointing to a generic `mitate.encryptedConsent` envelope.** Rejected — APPI 第2条第3項 / GDPR Art. 9 sensitive-data transfer to external lab is materially different from in-clinic intake consent (purpose, recipient set, jurisdiction surface, revocation window all differ). Generic consent envelope obscures the cross-border surface (`jurisdictions` field) that's needed for cross-jurisdictional dispute routing.

**Alt-4: Allow Tier-C (commercial closed labs) under G13 fleet-internal carve-out** (per ADR-2605262100 / 2605262400 G13 precedent). Rejected for this domain — Tier-C carve-out is for training corpora; clinical lab results enter the patient's care trajectory and cannot be artificially "internal-only." If a commercial lab fails Charter Rider §2 scan, the right action is to NOT onboard them, not to onboard under a carve-out.

**Alt-5: Skin-prick (in-vivo) at R2.** Rejected — requires acute anaphylaxis response capability at iyashi which is R3+; tracked as N11 for separate ADR when iyashi acute_first_line cell is R3-mature.

# References

- ADR-2605260100 (mitate master charter — G1..G14 inherited)
- ADR-2605260115 (allergic rhinitis perennial — IgE panel reference; this ADR's §139 cost note is closed by D2 + GC)
- ADR-2605263000 (iyashi R0 — internal_phlebotomy cell added at R2 in this ADR)
- ADR-2605262700 (chigiri — G14 UPL boundary + consent template stewardship)
- ADR-2605262900 (toritate — external lab vendor payment + Public Fund Safe Council Lv6+ ≥4 path)
- ADR-2605250500 (yakushi — Rx referral target for results)
- ADR-2605261000 (Liberation Ladder L5 vocation-flow — GE phlebotomist invariant source)
- ADR-2605181100 (encrypted envelope substrate)
- ADR-2605215000 (Murakumo-only inference — applies to result interpretation LLM)
- ADR-2605192200 (Charter Rider §2(a)-(h) — GB external lab vendor scan basis)
- APPI 第2条第3項 (要配慮個人情報 definition; JP)
- GDPR Article 9 (special categories of personal data; EU)
- HIPAA 45 CFR §164.514 (de-identification standard; US; informs `dataCategoriesShared` enum)
- WHO IUIS Allergen Nomenclature (specific IgE antigen identifiers; unchanged from ADR-2605260115)
- JCCLS / JLAC10 / LOINC (clinical laboratory result coding; informational reference for R2 result ingest mapping)

# R0 Landing Record (session-close 2026-05-29)

Single-session arc from gap question ("アレルギー検査、血液検査の actor, agent は設計されている?") to landed R0 scaffold.

**Commit chain**: `4ff94642c` — 7 files, +778/-13 (single commit; all 15 pre-commit hooks pass after lexicon spec fix described below).

| Artifact | Path |
|---|---|
| This ADR | `90-docs/adr/2605281950-mitate-r2-general-lab-orders-and-iyashi-phlebotomy.md` |
| diagnosticOrder lexicon extension (+16 orderType / +18 conditionContext / +orderRoutingTarget) | `00-contracts/lexicons/com/etzhayyim/mitate/diagnosticOrder.json` |
| diagnosticConsentReceipt lexicon (NEW) | `00-contracts/lexicons/com/etzhayyim/mitate/diagnosticConsentReceipt.json` |
| phlebotomyAttestation lexicon (NEW) | `00-contracts/lexicons/com/etzhayyim/iyashi/phlebotomyAttestation.json` |
| 4 cell paths reserved via `(reserved)` markers | `40-engine/kotoba/crates/kotoba-kotodama/cells/{mitate_diagnostic_consent_orchestrator, mitate_diagnostic_order_general, mitate_diagnostic_result_ingest, iyashi_internal_phlebotomy}` |
| deps.toml `[[adrs]]` + 6 `[[modules]]` | `deps.toml` |
| mitate/iyashi lexicon README index bumps (8→9, 6→7) | `00-contracts/lexicons/com/etzhayyim/{mitate,iyashi}/README.md` |

**Lexicon-spec correction (pre-commit hook caught)**: First commit attempt failed `validate-religious-corp-lexicons` on two AT Protocol Lexicon discipline violations in `phlebotomyAttestation.json`:

1. `tubesCollected.items` was inline `type=object` → extracted to `#tubeRecord` def + array now uses `{"type": "ref", "ref": "#tubeRecord"}`
2. `volumeMl` was `type=number` → renamed `volumeMlTenths` and converted to `type=integer` with implied units (5..200 = 0.5..20.0 mL); avoids floating-point storage drift per spec

**Registry audit (5 PR-gate axes all EXIT 0)**:

| Axis | State |
|---|---|
| deps.toml-paths | 586/605 resolve + 19 accepted-reserved + 0 drift |
| docs.json freshness | 669 entries in sync |
| graph.jsonld freshness | 669 nodes in sync |
| docs+graph schemas | valid |
| kotodama manifests | 42/42 valid |

**Deferred to subsequent ADRs** (each becomes its own R1+ ADR with Council attestation gate):

1. **R1 ADR** — `mitate_diagnostic_consent_orchestrator` cell activation (consent template registry + chigiri annual template review path; dry-run-only consent surface, no patient ordering yet). Prerequisites: Bootstrap Council Seat 2-5 RFP close (2026-06-19), ADR-2605181100 envelope production deploy, ≥1 licensed MD on Council medical advisory, chigiri R1 active for stewardLaborAttestation read.
2. **R2 ADR** — `mitate_diagnostic_order_general` + `mitate_diagnostic_result_ingest` + `iyashi_internal_phlebotomy` cell activation; first 3 external clinical lab vendor allowlist entries (each Council Lv6+ ≥3 + Charter Rider §2(a)-(h) scan attestation chain); ≤200-patient pilot ceiling. Requires GB external lab vendor onboarding playbook.
3. **R3 ADR** — Multi-clinic; in-clinic centrifuge + basic-chemistry analyzer at iyashi (reduce external lab dependence); cross-jurisdictional consent receipt translation matrix; ≤25,000 patient capacity.
4. **Out of R2/R3 scope per N1..N12** — Genetic / DTC / NIPT (N1/N2/N3) require Council Lv7+ unanimity; oncology markers (N4) require oncology-trained MD on Council; fertility (N5) requires musubi cross-doctrinal consult; STI (N6) requires chigiri data_privacy co-design; in-vivo skin prick (N11) requires iyashi acute_first_line R3-mature.

**Session-question resolution**: Allergy serology (specific IgE panel) was already designed at ADR-2605260115 R0; general blood / clinical-chemistry / urinalysis lab orders + religious-corp internal phlebotomy + 要配慮個人情報 per-order consent receipt are now designed at R0 scaffold tier in this ADR. The actor surface answering 「アレルギー検査、血液検査」 is **mitate** (ordering) + **iyashi R2+** (in-house draw) + **external clinical lab vendors** (allowlist with GB §2 scan); no new actor introduced.
