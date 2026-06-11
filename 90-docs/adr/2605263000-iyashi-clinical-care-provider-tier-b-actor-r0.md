---
id: adr-2605263000-iyashi-clinical-care-provider-tier-b-actor-r0
title: "ADR-2605263000: iyashi (癒) — non-profit religious-corp clinical care provider substrate Tier-B actor R0 charter"
status: proposed
doc_type: adr
topic: iyashi-clinical-care-r0
authoritative: true
last_verified: 2026-05-26
priority: 6.5
axis: care
weight: 0.55
priority_note: "Third-priority gap-closure actor (gap audit row 3 = 医療 clinic provider). Completes the L4 Care Tier triad with yakushi (pharmaceutical manufacturing ADR-2605250500..615) + mitate (diagnostic routing ADR-2605260100) + hagukumi (daily-living care ADR-2605261030). 任意団体 internal clinical care provider substrate at did:web:iyashi.etzhayyim.com (20-actors/iyashi/). Scope = community-clinic-model primary care + chronic care followup + vaccination + acute first-line (with mitate emergency referral handoff). Privacy-first: ADR-2605181100 encrypted envelope MANDATORY (clinical PHI is the most sensitive observation class in religious-corp; G2 structural). NO commercial EHR (Epic / Cerner / Athena / Allscripts / NextGen / eClinicalWorks / Greenway / Practice Fusion PROHIBITED per Charter Rider §2(e) anti-gatekeeping + §2(c) covert-ops vendor concern — vendor closed query-tracking exposes patient + provider posture). NO insurance / fee-for-service medicine — funded via Public Fund grant OR sliding-scale donation (chigiri.taxReceipt handles donor-side per ADR-2605262700). NO payroll for providers — volunteer ≠ employee per Liberation Ladder L0..L6 (providers are vocation-flow L5 stewards). UPL-equivalent (G analog): iyashi does NOT replace state-licensed medical practice; individual providers carry state license; iyashi is the procedural / attestation substrate, not the licensed entity. 6 cells / 6 Lexicons under com.etzhayyim.iyashi.* / 14 immutable gates / 12 non-goals / 4-phase R0..R3 (R0 scaffold / R1 ≤20 patient onboarding pilot, single clinic / R2 ≤200 patient ceiling 5 community clinics / R3 community-scale ≤25,000 patient capacity full mesh). Cross-actor: mitate (diagnosis ↔ clinical encounter), hagukumi (daily-living continuity), yakushi (medication supply), toritate (donation + Public Fund grant accounting), chigiri (consent + procedural attestation), manabi (provider continuing-med-ed)."
authoritative_for:
  - iyashi actor R0 charter
  - religious-corp clinical care provider substrate single SoT
  - `com.etzhayyim.iyashi.*` Lexicon namespace boundary
  - encrypted PHI envelope invariant (G2 structural, same discipline as hagukumi)
  - prohibition on commercial EHR (Epic / Cerner / Athena / Allscripts / NextGen / eClinicalWorks / Greenway / Practice Fusion)
  - clinical care funding via Public Fund grant + sliding-scale donation (no insurance billing automation)
  - provider classification as vocation-flow L5 steward (no payroll)
  - distinction from mitate (diagnostic routing) / hagukumi (daily-living) / yakushi (pharma mfg)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605181200-mst-encrypted-metadata-leak-reduction
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605250500-yakushi-pharmaceutical-rd-charter
  - adr-2605260100-mitate-diagnostic-routing-charter
  - adr-2605261000
  - adr-2605261030
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
related:
  - adr-2605262800-public-data-legal-corpus-ipfs-ingestion
supersedes: []
superseded_by: []
---

# ADR-2605263000: iyashi (癒) — non-profit religious-corp clinical care provider substrate Tier-B actor R0 charter

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

The L4 Care Tier of the Liberation Ladder (ADR-2605261000) has three
existing actors:

- **yakushi** (ADR-2605250500..615) — pharmaceutical manufacturing
  (cold-chain Sukoyaka delivery to hagukumi);
- **mitate** (ADR-2605260100) — diagnostic routing (medical specialist
  consultation, second-opinion routing, AI-assisted but human-in-loop);
- **hagukumi** (ADR-2605261030) — daily-living care (childcare 2+ /
  eldercare / chronic-care continuity / meal delivery / respite).

What is MISSING is the **clinical encounter provider** — the community-
clinic-model primary care + chronic followup + vaccination + acute
first-line layer that sits between mitate (diagnostic routing) and
hagukumi (daily-living continuity). The gap audit (session 2026-05-26)
identified this as priority row 3.

iyashi (癒 — healing) is the religious-corp's first-party clinical
care provider substrate.

Constitutional constraints (inherited; not adjustable):

- **NOT a state-licensed medical entity** — religious-corp itself is
  NOT 宗教法人法 登記 nor 一般社団 法人格; iyashi is the procedural
  + attestation substrate, NOT a licensed clinic. Individual providers
  carry their own state license per jurisdiction (G analog to chigiri
  G14 UPL: providers handle the practice; iyashi handles the
  substrate);
- **Encrypted envelope MANDATORY** (ADR-2605181100) — clinical PHI
  (protected health information) is the most sensitive observation
  class in religious-corp; structural enforcement via schema-level
  `additionalProperties: false` + `encryptedPayloadCid` required field
  (same discipline as hagukumi G2);
- **NO commercial EHR** — Epic / Cerner / Athena / Allscripts /
  NextGen / eClinicalWorks / Greenway / Practice Fusion PROHIBITED per
  Charter Rider §2(e) anti-gatekeeping + §2(c) covert-ops vendor
  concern. Vendor closed query-tracking on clinical records exposes
  patient + provider posture (which conditions are diagnosed, which
  providers handle which cases) to commercial parties;
- **NO insurance billing automation** — funded via Public Fund grant
  (sliding-scale donation model) OR direct member donation;
  chigiri.taxReceipt handles donor receipts for the latter (ADR-
  2605262700). State insurance integration is OUT OF SCOPE at all
  phases R0..R3 (would require 宗教法人法 登記 which is constitutionally
  excluded per Preamble §0.4);
- **NO payroll for providers** — providers are vocation-flow L5
  stewards per Liberation Ladder L0..L6 (subsistence + Public Fund
  vocation grant); volunteer ≠ employee structural invariant per
  ADR-2605261000 + ADR-2605262700 G13 + ADR-2605262900 G12. External
  employment parallel relationships may exist (provider holding a
  separate hospital position) — those are EXTERNAL relations, not
  iyashi relations;
- **Murakumo-only inference** (ADR-2605215000) — clinical decision
  support flows through judah LiteLLM → gemma4:e4b. Vendor LLM
  clinical decision support (Microsoft Nuance DAX / Abridge / Suki AI
  / Augmedix / etc.) PROHIBITED;
- **No video recording** (firmware-level enforcement, mirrors
  hagukumi G2) — telepresence permitted (e.g., specialist consult);
  video frame-write-to-disk PROHIBITED in firmware;
- **Human-in-loop ALWAYS** — no AI-only clinical decision; AI-assist
  output requires synchronous provider sign-off (G8);
- **Liberation Ladder L4 Care Tier eligibility** — iyashi R2+ deploys
  unlock the L4 → L5 advancement gate for community-clinic-network
  participation (mirrors hagukumi R3 L4 → L5 dependency).

# Decision

Create `iyashi` (癒) as a Tier-B religious-corp clinical care provider
substrate actor at `20-actors/iyashi/`, with DID
`did:web:iyashi.etzhayyim.com`, Lexicon namespace
`com.etzhayyim.iyashi.*`. R0 = scaffold only; all cells import-time
`RuntimeError` (same scaffold discipline as chigiri R0 + hagukumi R0).

## §1. Identity and naming

| Field | Value |
|---|---|
| Name | `iyashi` (癒 — 癒し / 癒える = healing) |
| DID | `did:web:iyashi.etzhayyim.com` |
| Lexicon root | `com.etzhayyim.iyashi.*` |
| Form | 任意団体 internal clinical care provider substrate (NOT 一般社団 / NPO / 公益財団 / 宗教法人 法人格 — Preamble §0.4 Lv7+ unanimity lock) |
| Tier | Tier-B per-domain leader actor |
| L4 Care Tier | yes; sibling of yakushi (mfg) + mitate (diagnosis) + hagukumi (daily-living) |
| Cross-actor | mitate (diagnosis ↔ clinical encounter) / hagukumi (daily-living continuity) / yakushi (medication supply) / toritate (funding accounting) / chigiri (consent + procedural attestation) / manabi (provider continuing-med-ed) |

## §2. Scope (6 sections)

### A. Primary care provision (community-clinic model)

- Adult primary care encounter (in-person, community clinic site);
- Pediatric primary care (cross-link with hagukumi childcare flow);
- Geriatric primary care (cross-link with hagukumi eldercare flow);
- Per-encounter consent (default-deny, G4);
- Encrypted clinical record (G2 mandatory).

### B. Chronic care followup

- Longitudinal chronic condition management (diabetes / hypertension /
  asthma / etc.);
- Pairs with hagukumi.chronic_continuity for daily-living adherence
  support;
- Pairs with mitate for specialist consultation when needed;
- Medication adherence cross-link with yakushi.

### C. Vaccination + preventive care

- Vaccination administration (per public health schedule per
  jurisdiction);
- Preventive screening (per evidence-based guidelines, e.g., USPSTF /
  JP 国民健康保険 preventive panel / etc.);
- No mandatory vaccination policy at iyashi level — provider-patient
  consent governs.

### D. Acute first-line care

- Acute encounter triage (cold / flu / minor trauma / minor wound);
- Emergency keyword escalation to mitate (shared
  `com.etzhayyim.mitate.emergencyKeyword` lexicon per hagukumi G11);
- Hospital referral handoff (when condition exceeds community-clinic
  scope).

### E. Maternity + pediatric clinical (cross-actor)

- Antenatal care (visits, screening, birth-plan documentation);
- Postnatal care (mother + newborn);
- Pediatric well-child encounters (ages 0-18);
- Cross-actor with hagukumi for non-medical childcare (ages 2+);
- Cross-actor with kokoro (future actor; mental health) for postnatal
  mood screening.

### F. Provider lifecycle + facility standards

- Provider onboarding (medical credential verification + Council
  Lv6+ ≥3 attestation);
- Provider continuing-medical-education tracking (cross-actor with
  manabi for curriculum delivery);
- Clinic facility attestation (building standards / equipment
  inventory / sterile-zone certification);
- Provider 12-hr work cap + 12-hr recovery (G9, mirrors hagukumi
  G10).

## §3. Cells (6 Pregel cells under `40-engine/kotoba/crates/kotoba-kotodama/cells/iyashi_*/`)

All R0 path-reserved; import-time `RuntimeError("iyashi R0 scaffold: activate via Council ADR + R1 ratification + encrypted-record framework Council-attested production-ready")` at W1 creation.

| # | Cell | Murakumo node | Phase | I/O |
|---|---|---|---|---|
| 1 | `primary_care_encounter` | levi | session | patientDid + consentCid → clinicalEncounterAttestation (encrypted) |
| 2 | `chronic_care_followup` | levi (hagukumi-paired) | longitudinal | chronicConditionState → chronicCareContinuityRecord (encrypted; cross-link with hagukumi) |
| 3 | `vaccination_administration` | levi | event | patientDid + vaccineId + consentCid → vaccinationAttestation |
| 4 | `acute_first_line` | levi (mitate-paired) | session | symptom triage → encounter OR mitate emergency referral |
| 5 | `provider_lifecycle` | reuben | event | candidate provider DID → providerAttestation (Council ≥3) |
| 6 | `clinic_facility` | reuben | annual (event) | facility audit → clinicFacilityAttestation |

R1 activation gates each cell separately (Council Lv6+ ≥3 attestation
per cell, plus ≥1 licensed-MD on Council medical advisory per cell
class).

## §4. Lexicons (6, all under `com.etzhayyim.iyashi.*`)

| # | Lexicon | Consumer cell | Description |
|---|---|---|---|
| L1 | `clinicalEncounterAttestation` | primary_care_encounter + acute_first_line | Per-encounter; **encryptedPayloadCid REQUIRED** (G2 structural; rejects plaintext content fields via additionalProperties=false at R1) |
| L2 | `providerAttestation` | provider_lifecycle | Credentialing record; medical-license-cite-CID + Council ≥3 attestation + Liberation Ladder L5 vocation-flow link |
| L3 | `chronicCareContinuityRecord` | chronic_care_followup | Longitudinal; encryptedPayloadCid REQUIRED; cross-link to hagukumi.continuitySessionAttestation |
| L4 | `vaccinationAttestation` | vaccination_administration | Per-administration; vaccine ID + lot # (from yakushi cross-link if iyashi-administered yakushi-produced) + adverse-event-flag |
| L5 | `clinicFacilityAttestation` | clinic_facility | Per-clinic-site standards; annual; building + equipment + sterile-zone certification |
| L6 | `silenIyashiReview` | (Council attestation scope) | Wellbecoming + quality + multi-generational ratio + Charter Rider §1.13 compliance quarterly Council review |

All 6 records require schema-level field validation. R0 = scaffold +
skeleton schemas. R1 = full schemas + structural enforcement
(`additionalProperties: false`, `required` fields, encryptedPayloadCid
mandatory on L1 + L3).

## §5. Gates (14, immutable R0..R3, Council Lv6+ to amend)

| Gate | Description |
|---|---|
| **G1** | Every clinical document (ingested OR produced) MUST pass `kotodama.organism.sensors.charter_rider.scan()` §2(a)-(h). |
| **G2** | **Encrypted envelope MANDATORY** (ADR-2605181100) — clinicalEncounterAttestation + chronicCareContinuityRecord MUST carry `encryptedPayloadCid`; plaintext content fields rejected at schema layer (additionalProperties=false at R1). |
| **G3** | **No video recording** (firmware-level enforcement; live telepresence permitted but frame-write-to-disk PROHIBITED in firmware). Mirrors hagukumi G2. |
| **G4** | Per-encounter consent (default-deny); `clinicalEncounterAttestation.consentRecordCid` REQUIRED. |
| **G5** | Provider Council vetting — `providerAttestation` requires medical-license-cite-CID + ≥3 Council Lv6+ DIDs + ≥1 licensed-MD on Council medical advisory. |
| **G6** | NO advertising / NO commercial-product promotion in care setting (mirrors hagukumi G8). |
| **G7** | NO behavioral modification protocols (operant / classical / social conditioning); mirrors hagukumi G7. |
| **G8** | Human-in-loop ALWAYS for AI-assisted clinical decision support; AI-assist output requires synchronous provider sign-off. NO AI-only clinical decision. |
| **G9** | Provider 12-hr work cap + 12-hr recovery between shifts (mirrors hagukumi G10). |
| **G10** | Emergency escalation to mitate via shared `com.etzhayyim.mitate.emergencyKeyword` lexicon (cross-actor; same contract as hagukumi G11). |
| **G11** | **NO commercial EHR** — Epic / Cerner / Athena / Allscripts / NextGen / eClinicalWorks / Greenway / Practice Fusion PROHIBITED (Charter Rider §2(e) anti-gatekeeping + §2(c) vendor data-sovereignty). |
| **G12** | **Murakumo-only inference** (ADR-2605215000) — clinical decision support via judah LiteLLM only; vendor clinical-AI (Nuance DAX / Abridge / Suki / Augmedix / etc.) PROHIBITED. |
| **G13** | **NO insurance billing automation** — funded via Public Fund grant OR direct member donation; chigiri.taxReceipt handles donor receipts (sliding-scale donation model). State insurance integration OUT OF SCOPE at all phases R0..R3. |
| **G14** | **NO payroll for providers** — providers are vocation-flow L5 stewards per Liberation Ladder L0..L6; chigiri.stewardLaborAttestation classifies; toritate.ledgerEntry.category enum excludes `payroll`/`wage`/`salary`/`bonus`/`commission` (cross-actor enforcement). |

## §6. Non-goals (12, immutable R0..R3)

| # | Non-goal |
|---|---|
| N1 | NOT pharmaceutical manufacturing (yakushi domain). |
| N2 | NOT diagnostic AI routing (mitate domain). |
| N3 | NOT daily-living care (hagukumi domain). |
| N4 | NOT hospice / palliative terminal care (specialist actor TBD; outside community-clinic scope). |
| N5 | NOT surgical (beyond minor procedures — out of community-clinic scope; hospital referral). |
| N6 | NOT behavioral psych intervention (kokoro future actor; gap audit row 9). |
| N7 | NOT telemedicine as substitute for in-person (telepresence used only when distance-justified; not a TeleHealth platform). |
| N8 | NOT insurance / fee-for-service medicine. |
| N9 | NOT a commercial EHR integrator (G11 PROHIBITED). |
| N10 | NOT a state-licensed medical entity (任意団体 internal substrate; individual providers carry state license, iyashi does not). |
| N11 | NOT a provider-credentialing certificate authority (providerAttestation = vetting record + Council attestation, NOT issued credential; original credentials issued by state licensing bodies). |
| N12 | NOT in-home surveillance (extends hagukumi N7; no cameras / no audio recording / no location tracking / no biometric monitoring outside immediate-safety mitate G5 trigger). |

## §7. Roadmap (R0 → R3)

| Phase | Date / gate | Scope | Murakumo placement |
|---|---|---|---|
| **R0** | 2026-05-26 (this ADR) | Scaffold only. 6 cells path-reserved (import-time RuntimeError per G2 privacy invariant). 6 Lexicons schema skeleton. manifest + README + CLAUDE.md. | No deployment |
| **R1** | post-Bootstrap-Council + ≥1 licensed-MD on Council medical advisory + encrypted-record framework production-deployed | Activate 2 core cells: `primary_care_encounter`, `provider_lifecycle`. ≤20 patients pilot, single clinic site. Full schemas for L1 (clinicalEncounterAttestation) + L2 (providerAttestation). No chronic followup yet (paired cell deferred to R2). | levi (single node) |
| **R2** | post-R1 + ≥30-day public objection + 5 community-site Council attestations | Activate +4 cells: `chronic_care_followup` (hagukumi pair), `vaccination_administration`, `acute_first_line` (mitate pair), `clinic_facility`. L3 + L4 + L5 full schema. ≤200 patient ceiling across 5 community clinics. **L4 → L5 advancement gate eligibility** (Liberation Ladder). | levi + simeon + dan (3 nodes) |
| **R3** | post-R2 + Council Lv7+ unanimity + ≥1 jurisdictional medical-board public-comment cycle | All 6 cells live. L6 (silenIyashiReview) full schema; quarterly Council review cycle established. Community-scale: 50 clinic sites + ≤25,000 patient capacity. **Required for L4 → L5 advancement** (Liberation Ladder). | Full 10-node fleet |

## §8. Cross-actor relationship table

| Cross-actor | Direction | Purpose |
|---|---|---|
| `mitate` | ↔ | Diagnosis ↔ clinical encounter; mitate's G5 emergency keyword lexicon shared (G10) |
| `hagukumi` | ↔ | Daily-living care continuity; chronic_care_followup pairs with hagukumi.chronic_continuity |
| `yakushi` | ← (medication supply) | Sukoyaka cold-chain delivery for vaccination + prescription |
| `toritate` | → (read) | Donation + Public Fund grant accounting for iyashi operations |
| `chigiri.member_onboarding` | → (read) | Patient is Adherent SBT holder verification |
| `chigiri.stewardLaborAttestation` | → (read) | Provider L5 vocation-flow classification (G14) |
| `chigiri.consentRecord` | → (read) | Per-encounter consent (G4) |
| `manabi` | ↔ | Provider continuing-medical-education curriculum delivery + tracking |
| `kokoro` (future) | ↔ | Mental health cross-link (gap audit row 9; postnatal mood screening, etc.) |

## §9. R0 deliverables (this commit)

1. This ADR (`90-docs/adr/2605263000-iyashi-clinical-care-provider-tier-b-actor-r0.md`);
2. Actor scaffold (`20-actors/iyashi/manifest.jsonld` + `README.md` + `CLAUDE.md`);
3. 6 Lexicon JSON skeleton schemas under `00-contracts/lexicons/com/etzhayyim/iyashi/` + README;
4. `deps.toml` [[adrs]] + [[modules]] entries;
5. `90-docs/adr/README.md` index update;
6. `CLAUDE.md` Status table row 70 + Repo Layout entry.

No code activation in R0. 6 cells path-reserved at
`40-engine/kotoba/crates/kotoba-kotodama/cells/iyashi_*/` (created at R1 ratification).

# Consequences

**Positive**:

- Closes the L4 Care Tier triad — religious-corp now has medication
  manufacturing (yakushi) + diagnostic routing (mitate) + daily-living
  care (hagukumi) + clinical encounter (iyashi);
- Encrypted PHI envelope (G2) gives structural protection of the most
  sensitive observation class in the religious-corp ecosystem;
- The G11 commercial-EHR prohibition documents and structurally
  enforces a Charter Rider §2(e) + §2(c) constraint that has been
  latent;
- G14 (provider = L5 vocation-flow steward) closes the
  constructive-employment drift loophole for medical providers
  specifically (was already enforced for general stewards via chigiri
  G13 + toritate G12);
- Liberation Ladder L4 → L5 advancement gate becomes eligible at R2+
  (mirrors hagukumi pathway).

**Negative / cost**:

- Provider recruitment is hard — religious-corp must attract
  state-licensed providers willing to serve as L5 vocation-flow
  stewards (no payroll, only vocation-flow + Public Fund grant per
  ADR-2605192145);
- ≥1 licensed-MD on Council medical advisory is the R1 gating
  dependency; Bootstrap Council Seat 2-5 RFP must surface a willing
  candidate;
- Encrypted envelope schema enforcement requires
  ADR-2605181100 production-deployed before R1 (same dependency as
  hagukumi R1);
- State licensing per-jurisdiction is the practical bottleneck for
  R3 scale (community-clinic-network requires per-jurisdiction
  licensure compliance from each clinic site);
- Liberation Ladder L4 → L5 advancement gate now has TWO L4-bound
  actors (hagukumi + iyashi); the advancement criteria must
  reasonably reflect both.

**Forward-compatibility**:

- kokoro (mental health, gap audit row 9, future R0) cross-actor
  integration is path-reserved (postnatal mood screening / chronic
  mental health continuity);
- shidemori (memorial + cemetery, gap audit row 10, future R0) cross-
  actor integration for end-of-life clinical attestation handoff;
- jurisdictional licensure expansion follows R3 model (per-jurisdiction
  Council attestation + ≥1 licensed-MD-per-jurisdiction on Council
  medical advisory).

# Alternatives Considered

1. **Extend hagukumi to include clinical encounter cells**. Rejected —
   hagukumi is daily-living care (non-medical); mixing clinical
   responsibility into hagukumi violates actor SRP and the privacy
   discipline (hagukumi N1 explicitly excludes medical procedures).

2. **Use Epic / Cerner / Athena as the EHR**. Rejected per Charter
   Rider §2(e) + §2(c). Vendor data-sovereignty exposure on patient
   + provider posture is structurally unacceptable.

3. **Bill insurance to scale revenue**. Rejected — insurance
   integration would require 宗教法人法 登記 + state-licensed entity
   status, both constitutionally excluded per Preamble §0.4.

4. **Pay providers as employees to ease recruitment**. Rejected per
   Liberation Ladder G13 (volunteer ≠ employee) + ADR-2605262900 G12.
   Provider compensation is vocation-flow + Public Fund grant; the
   discipline is structural, not policy.

5. **Telemedicine-only model**. Rejected per N7. Telepresence is a
   tool used when distance justifies, not a substitute for in-person
   community-clinic-model encounter (which has Wellbecoming benefits
   that telemedicine alone does not provide).

6. **Skip iyashi — let providers practice externally and refer to
   religious-corp for support**. Considered, rejected. The whole
   point of L4 Care Tier is that religious-corp provides clinical
   care as a community benefit, not as a referral target. External-
   only model fragments member care across multiple providers.

# References

- ADR-2605170900 — etzhayyim/root canonical home for ADRs
- ADR-2605181100 — MST encrypted records + Signal key wrap (G2)
- ADR-2605181200 — Encrypted-record metadata-leak reduction
- ADR-2605192100 — Mission Charter
- ADR-2605192145 — Public Fund architecture (funding source)
- ADR-2605192200 — Charter Compliance Rider v2.0 (G11 + G12 sources)
- ADR-2605192300 — Council 5-of-7 Safe
- ADR-2605215000 — Inference Murakumo-only (G12)
- ADR-2605250500 — yakushi (cross-actor pharma)
- ADR-2605260100 — mitate (cross-actor diagnosis)
- ADR-2605261000 — Labor Liberation Transition Mechanism (L0..L6) (G14)
- ADR-2605261030 — hagukumi (cross-actor daily-living)
- ADR-2605262130 — Kotoba storage substrate unification
- ADR-2605262700 — chigiri (cross-actor procedural attestation)
- ADR-2605262900 — toritate (cross-actor funding accounting)
- `/CHARTER-RIDER.md` §2 — 8 prohibited categories (esp. §2(e) anti-gatekeeping + §2(c) covert-ops vendor)
- `20-actors/hagukumi/CLAUDE.md` — sibling R0 scaffold pattern reference
